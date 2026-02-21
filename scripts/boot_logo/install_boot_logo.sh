#!/bin/bash
# 編譯
gcc -O2 -o ssd1306_boot_logo ssd1306_boot_logo.c
sudo cp ssd1306_boot_logo /usr/local/bin/

# 安裝 systemd service
sudo cp ssd1306-boot-logo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ssd1306-boot-logo.service
sudo systemctl start ssd1306-boot-logo.service