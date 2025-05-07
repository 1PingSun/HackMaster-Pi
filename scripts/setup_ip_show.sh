#!/bin/bash

# 必須以 root 權限執行
if [ "$EUID" -ne 0 ]; then
  echo "請使用 sudo 執行此腳本"
  exit 1
fi

# 獲取腳本所在目錄
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/oled_ip_display.py"

# 檢查 Python 檔案是否存在
if [ ! -f "$PYTHON_SCRIPT" ]; then
  echo "錯誤: 無法找到 OLED IP 顯示程式。請確保它與此腳本位於同一目錄。"
  exit 1
fi

# 安裝必要的套件
echo "安裝必要的套件..."
apt-get update
apt-get install -y python3-pip python3-pil python3-netifaces

# 安裝 luma.oled 套件
echo "安裝 luma.oled..."
pip3 install --break-system-packages luma.core luma.oled

# 將 Python 腳本複製到系統目錄
echo "複製 Python 腳本到 /usr/local/bin..."
cp "$PYTHON_SCRIPT" /usr/local/bin/oled_ip_display.py
chmod +x /usr/local/bin/oled_ip_display.py

# 創建 systemd 服務
echo "創建 systemd 服務..."
cat > /etc/systemd/system/oled-ip-display.service << EOF
[Unit]
Description=OLED IP Display
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/oled_ip_display.py
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# 啟用並啟動服務
echo "啟用並啟動服務..."
systemctl daemon-reload
systemctl enable oled-ip-display.service
systemctl start oled-ip-display.service

echo "完成! OLED IP 顯示器已設置為開機自動啟動。"
echo "查看狀態: sudo systemctl status oled-ip-display.service"
echo "查看日誌: sudo journalctl -u oled-ip-display.service"
