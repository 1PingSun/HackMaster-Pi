from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, sh1106
import time
import socket
import netifaces
import os
import sys
import logging
import signal
from pathlib import Path
from PIL import ImageFont  # 導入 PIL 字體模組

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("/tmp/oled_display.log"), logging.StreamHandler()]
)
logger = logging.getLogger("OLED_IP_Display")

# 全局變量，用於保存設備實例，以便在關機時訪問
global_device = None

# 載入字體
# 使用系統字體
try:
    # 嘗試加載較大的字體 (18pt)
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    logger.info("已加載自定義字體")
except IOError:
    try:
        # 嘗試加載另一種常見字體
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 12)
        logger.info("已加載 FreeMono 字體")
    except IOError:
        # 如果無法加載字體，使用默認字體
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        logger.warning("無法加載自定義字體，使用默認字體")

# 關機信號處理函數
def signal_handler(sig, frame):
    global global_device
    logger.info(f"收到信號 {sig}，正在清除顯示並退出...")

    if global_device:
        # 顯示關機訊息
        try:
            with canvas(global_device) as draw:
                draw.text((5, 20), "系統關機中...", fill="white", font=font_large)
            time.sleep(1)  # 顯示關機訊息 1 秒

            # 清除顯示
            global_device.clear()
            # 關閉顯示 (關機/睡眠模式)
            global_device.hide()
            global_device.cleanup()
        except Exception as e:
            logger.error(f"清除顯示時發生錯誤: {e}")

    # 退出程式
    sys.exit(0)

# 註冊信號處理器
signal.signal(signal.SIGTERM, signal_handler)  # 終止信號
signal.signal(signal.SIGINT, signal_handler)   # 中斷信號 (Ctrl+C)

# 檢測您使用的是哪種控制器
def detect_device():
    serial = i2c(port=1, address=0x3C)
    try:
        device = ssd1306(serial, width=128, height=64)
        logger.info("檢測到 SSD1306 控制器")
        return device
    except Exception as e:
        logger.warning(f"嘗試 SSD1306 失敗: {e}")
        try:
            device = sh1106(serial, width=128, height=64)
            logger.info("檢測到 SH1106 控制器")
            return device
        except Exception as e:
            logger.warning(f"嘗試 SH1106 失敗: {e}")
            logger.info("無法檢測到支援的控制器，嘗試使用 SSD1306")
            return ssd1306(serial, width=128, height=64, rotate=0)

# 獲取IP地址
def get_ip_address():
    try:
        # 方法1: 使用 netifaces 獲取 IP 地址
        try:
            # 嘗試獲取有效的網路介面
            interfaces = netifaces.interfaces()
            for interface in interfaces:
                # 跳過 lo (loopback)
                if interface == 'lo':
                    continue

                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    ip_info = addrs[netifaces.AF_INET][0]
                    ip = ip_info['addr']
                    # 跳過 localhost
                    if not ip.startswith('127.'):
                        logger.info(f"從介面 {interface} 獲取到 IP: {ip}")
                        return ip
        except Exception as e:
            logger.warning(f"netifaces 方法失敗: {e}")

        # 方法2: 使用 socket 獲取 IP 地址
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 不需要真正連接
            s.connect(('8.8.8.8', 1))
            IP = s.getsockname()[0]
            logger.info(f"從 socket 獲取到 IP: {IP}")
            return IP
        except Exception as e:
            logger.warning(f"socket 方法失敗: {e}")
            return '127.0.0.1'
        finally:
            s.close()
    except Exception as e:
        logger.error(f"獲取 IP 時發生錯誤: {e}")
        return "等待網路連接..."

# 創建自啟動服務文件
def create_service_file():
    service_path = Path("/etc/systemd/system/oled-ip-display.service")

    # 如果已經存在，則不再創建
    if service_path.exists():
        return

    current_script = os.path.abspath(sys.argv[0])
    service_content = f"""[Unit]
Description=OLED IP Display
After=network.target
Before=shutdown.target reboot.target halt.target

[Service]
ExecStart=/usr/bin/python3 {current_script}
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1
# 確保服務收到關機信號
KillSignal=SIGTERM
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
"""

    try:
        # 需要 root 權限才能寫入到 /etc/systemd
        with open(service_path, 'w') as f:
            f.write(service_content)

        os.system("systemctl daemon-reload")
        os.system("systemctl enable oled-ip-display.service")
        logger.info("已創建並啟用開機自啟動服務")
    except Exception as e:
        logger.error(f"創建服務文件失敗: {e}")
        logger.info("請以 root 權限執行以下命令以啟用自動啟動:")
        logger.info(f"sudo cp {current_script} /usr/local/bin/")
        logger.info(f"echo '{service_content}' | sudo tee /etc/systemd/system/oled-ip-display.service")
        logger.info("sudo systemctl daemon-reload")
        logger.info("sudo systemctl enable oled-ip-display.service")
        logger.info("sudo systemctl start oled-ip-display.service")

# 主程式
def main():
    global global_device

    # 嘗試創建服務文件（需要 root 權限）
    create_service_file()

    # 初始化設備
    device = detect_device()
    # 保存到全局變量，以便在關機時使用
    global_device = device

    device.clear()

    # 調低亮度 (設定為30%)
    device.contrast(80)  # 0-255，默認值通常為255

    # 顯示「正在取得 IP...」
    with canvas(device) as draw:
        draw.text((5, 20), "正在取得 IP...", fill="white", font=font_large)

    # 等待網路連接
    ip_address = "等待網路連接..."
    retry_count = 0
    max_retries = 20  # 最多嘗試20次

    while ip_address == "等待網路連接..." and retry_count < max_retries:
        ip_address = get_ip_address()
        if ip_address != "等待網路連接...":
            break

        # 每次更新顯示
        with canvas(device) as draw:
            draw.text((5, 10), "正在取得 IP...", fill="white", font=font_large)
            draw.text((5, 40), f"嘗試 {retry_count+1}/{max_retries}", fill="white", font=font_small)

        retry_count += 1
        time.sleep(3)

    # 永久顯示 IP
    try:
        while True:
            # 定期刷新 IP 以防網路變更
            current_ip = get_ip_address()
            current_time = time.strftime("%H:%M:%S")

            with canvas(device) as draw:
                # 只顯示 "IP:" 和實際 IP 地址，使用較大字體
                draw.text((5, 5), "IP:", fill="white", font=font_large)
                draw.text((5, 25), current_ip, fill="white", font=font_large)
                draw.text((5, 45), current_time, fill="white", font=font_small)

            # 每10秒更新一次
            time.sleep(10)
    except Exception as e:
        logger.error(f"主循環發生錯誤: {e}")
        # 如果發生錯誤，嘗試清除顯示
        signal_handler(signal.SIGTERM, None)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # 按 Ctrl+C 也會清除顯示
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"程式發生錯誤: {e}")
        # 如果發生錯誤，嘗試清除顯示
        if global_device:
            try:
                global_device.clear()
                global_device.hide()
            except:
                pass
