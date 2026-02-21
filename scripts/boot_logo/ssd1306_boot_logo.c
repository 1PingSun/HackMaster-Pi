/*
 * ssd1306_boot_logo.c
 *
 * 顯示完整 Cat Logo (128×64)
 * 右下角轉圈圈，無限執行直到被取代
 *
 * 編譯: gcc -O2 -o ssd1306_boot_logo ssd1306_boot_logo.c
 * 執行: sudo ./ssd1306_boot_logo
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>

#include "cat_logo.h"
#include "font5x7.h"

/* ─────────────────────────────────────────
   設定區
   ───────────────────────────────────────── */
#define I2C_BUS         "/dev/i2c-1"
#define SSD1306_ADDR    0x3C
#define SCREEN_WIDTH    128
#define SCREEN_HEIGHT   64
#define PAGES           8

/* 轉圈圈位置（右下角）*/
#define SPIN_X          116     /* col：留 6 pixel 寬，離右邊 6px */
#define SPIN_Y          56      /* row：留 7 pixel 高，離底部 1px */

/* 每幀間隔（微秒），150000 = 約 6.7fps */
#define SPIN_DELAY_US   150000

/* ─────────────────────────────────────────
   SSD1306 協定常數
   ───────────────────────────────────────── */
#define CTRL_CMD    0x00
#define CTRL_DATA   0x40

/* ─────────────────────────────────────────
   Frame buffer
   ───────────────────────────────────────── */
static uint8_t framebuf[SCREEN_WIDTH * PAGES];

/* ─────────────────────────────────────────
   I2C
   ───────────────────────────────────────── */
static int i2c_fd = -1;

static int i2c_open(void)
{
    i2c_fd = open(I2C_BUS, O_RDWR);
    if (i2c_fd < 0) { perror("open I2C"); return -1; }
    if (ioctl(i2c_fd, I2C_SLAVE, SSD1306_ADDR) < 0) {
        perror("ioctl I2C_SLAVE"); close(i2c_fd); return -1;
    }
    return 0;
}

static int send_cmd(uint8_t cmd)
{
    uint8_t buf[2] = { CTRL_CMD, cmd };
    return write(i2c_fd, buf, 2) == 2 ? 0 : -1;
}

static int send_data(const uint8_t *data, size_t len)
{
    uint8_t buf[17];
    buf[0] = CTRL_DATA;
    size_t offset = 0;
    while (offset < len) {
        size_t chunk = len - offset;
        if (chunk > 16) chunk = 16;
        memcpy(buf + 1, data + offset, chunk);
        if (write(i2c_fd, buf, chunk + 1) != (ssize_t)(chunk + 1)) return -1;
        offset += chunk;
    }
    return 0;
}

/* ─────────────────────────────────────────
   SSD1306 初始化
   ───────────────────────────────────────── */
static int ssd1306_init(void)
{
    static const uint8_t cmds[] = {
        0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40,
        0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8, 0xDA, 0x12,
        0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40,
        0xA4, 0xA6, 0xAF,
    };
    for (size_t i = 0; i < sizeof(cmds); i++)
        if (send_cmd(cmds[i]) != 0) return -1;
    return 0;
}

/* ─────────────────────────────────────────
   只更新右下角那一塊區域（不刷整個螢幕）
   x_start ~ x_end（col），page_start ~ page_end
   ───────────────────────────────────────── */
static int fb_flush_region(uint8_t col_start, uint8_t col_end,
                            uint8_t page_start, uint8_t page_end)
{
    send_cmd(0x21); send_cmd(col_start);  send_cmd(col_end);
    send_cmd(0x22); send_cmd(page_start); send_cmd(page_end);

    for (uint8_t page = page_start; page <= page_end; page++) {
        const uint8_t *row = framebuf + page * SCREEN_WIDTH + col_start;
        size_t len = col_end - col_start + 1;
        if (send_data(row, len) != 0) return -1;
    }
    return 0;
}

/* 刷全螢幕（只用於初始顯示 Logo）*/
static int fb_flush_all(void)
{
    send_cmd(0x21); send_cmd(0x00); send_cmd(0x7F);
    send_cmd(0x22); send_cmd(0x00); send_cmd(0x07);
    return send_data(framebuf, sizeof(framebuf));
}

/* ─────────────────────────────────────────
   Frame buffer 操作
   ───────────────────────────────────────── */
static void fb_set_pixel(int x, int y, int on)
{
    if (x < 0 || x >= SCREEN_WIDTH || y < 0 || y >= SCREEN_HEIGHT) return;
    int page = y / 8;
    int bit  = y % 8;
    if (on)
        framebuf[page * SCREEN_WIDTH + x] |=  (1 << bit);
    else
        framebuf[page * SCREEN_WIDTH + x] &= ~(1 << bit);
}

static void fb_fill_rect(int x, int y, int w, int h, int on)
{
    for (int row = y; row < y + h; row++)
        for (int col = x; col < x + w; col++)
            fb_set_pixel(col, row, on);
}

/* 畫單一字元（5×7）*/
static void fb_draw_char(int x, int y, char c, int on)
{
    if (c < 32 || c > 126) c = 32;
    const uint8_t *glyph = font5x7[(uint8_t)(c - 32)];
    for (int col = 0; col < 5; col++) {
        uint8_t line = glyph[col];
        for (int row = 0; row < 7; row++)
            fb_set_pixel(x + col, y + row, (line >> row) & 1 ? on : 0);
    }
}

/* ─────────────────────────────────────────
   載入完整 Logo（128×64）到 framebuf
   ───────────────────────────────────────── */
static void fb_load_full_logo(void)
{
    memcpy(framebuf, cat_logo, sizeof(framebuf));  /* 直接複製全部 1024 bytes */
}

/* ─────────────────────────────────────────
   轉圈圈（右下角，無限迴圈）
   只更新 SPIN_X ~ SPIN_X+5, SPIN_Y ~ SPIN_Y+6 這塊
   ───────────────────────────────────────── */
static void anim_spinner_infinite(void)
{
    /* / - \ | 四個幀 */
    const char frames[] = { '/', '-', '\\', '|' };

    /* 計算需要刷新的 page 範圍 */
    const uint8_t COL_START  = (uint8_t)SPIN_X;
    const uint8_t COL_END    = (uint8_t)(SPIN_X + 5);          /* 6 cols */
    const uint8_t PAGE_START = (uint8_t)(SPIN_Y / 8);          /* page 7 */
    const uint8_t PAGE_END   = (uint8_t)((SPIN_Y + 6) / 8);    /* page 7 */

    int frame = 0;
    while (1) {
        /* 還原該區域到 Logo 原始 pixels（先從 cat_logo 復原）*/
        for (uint8_t page = PAGE_START; page <= PAGE_END; page++) {
            int idx = page * SCREEN_WIDTH + COL_START;
            memcpy(framebuf + idx,
                   cat_logo  + idx,
                   COL_END - COL_START + 1);
        }

        /* 在右下角畫轉圈字元（XOR 效果：用反色讓它在任何背景都看得到）*/
        const uint8_t *glyph = font5x7[(uint8_t)(frames[frame] - 32)];
        for (int col = 0; col < 5; col++) {
            uint8_t line = glyph[col];
            for (int row = 0; row < 7; row++) {
                int x = SPIN_X + col;
                int y = SPIN_Y + row;
                int page = y / 8;
                int bit  = y % 8;
                int idx  = page * SCREEN_WIDTH + x;
                /* XOR：不管 logo 背景是黑或白，spinner 都看得到 */
                if ((line >> row) & 1)
                    framebuf[idx] ^= (1 << bit);
            }
        }

        /* 只刷右下角那塊，不影響其他區域 */
        fb_flush_region(COL_START, COL_END, PAGE_START, PAGE_END);

        frame = (frame + 1) % 4;
        usleep(SPIN_DELAY_US);
    }
}

/* ─────────────────────────────────────────
   主程式
   ───────────────────────────────────────── */
int main(void)
{
    printf("=== SSD1306 Boot Logo ===\n");
    printf("bitmap size = %zu (should be 1024)\n", sizeof(cat_logo));

    if (i2c_open()     != 0) return EXIT_FAILURE;
    if (ssd1306_init() != 0) { close(i2c_fd); return EXIT_FAILURE; }

    /* 載入並顯示完整 Logo */
    fb_load_full_logo();
    fb_flush_all();
    printf("[OK] Logo displayed\n");
    printf("[OK] Spinner running at bottom-right (col=%d, row=%d)\n",
           SPIN_X, SPIN_Y);
    printf("     Kill this process when boot is complete.\n");

    /* 轉圈圈，永不停止 */
    anim_spinner_infinite();

    close(i2c_fd);
    return EXIT_SUCCESS;
}