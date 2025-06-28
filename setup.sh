#!/bin/bash

# 必須以 root 權限執行
if [ "$EUID" -ne 0 ]; then
  echo "請使用 sudo 執行此腳本"
  exit 1
fi

# ==== for ip show====
sudo ./scripts/enable_i2c.sh
sudo apt-get install -y python3-pip python3-dev python3-smbus i2c-tools
sudo pip3 install --break-system-packages netifaces
sudo pip3 install --break-system-packages luma.oled
cd ./scripts
sudo chmod +x setup_ip_show.sh
sudo ./setup_ip_show.sh
cd ..
sudo ./setup_hackmasterpi.sh

# ==== for PN532 ====
# sudo ./scripts/enable_i2c.sh
# sudo apt install -y i2c-tools
sudo apt install -y libnfc-dev libnfc-bin libnfc-examples
# sudo apt install -y python3-pip python3-dev

sudo mkdir -p /etc/nfc

cat > /etc/nfc/libnfc.conf << EOF
# PN532 via I2C connection
device.name = "PN532"
device.connstring = "pn532_i2c:/dev/i2c-1"
EOF

sudo usermod -a -G i2c $(whoami)
newgrp i2c

# ==== for apple_bleee ====
echo "pi ALL=(ALL) NOPASSWD: /usr/bin/python3 ./app/mylib/apple_blee/adv_airpods.py" | sudo tee /etc/sudoers.d/user-python && sudo chmod 440 /etc/sudoers.d/user-python
sudo apt install -y bluez libpcap-dev libev-dev libnl-3-dev libnl-genl-3-dev libnl-route-3-dev cmake libbluetooth-dev
sudo apt install git
sudo pip3 install --break-system-packages -r ./app/mylib/apple_bleeerequirements.txt
git clone https://github.com/seemoo-lab/owl.git && cd ./owl && git submodule update --init && mkdir build && cd build && cmake .. && make && sudo make install && cd ../..

# ==== for beacon ====
sudo apt install bluez bluez-tools -y

# === for ir ===
sudo apt-get install python3-rpi.gpio

# ==== for WiFi 網卡驅動 (8812AU) ====
echo "正在安裝 WiFi 網卡驅動 (8812AU)..."
cd ~
git clone https://github.com/morrownr/8812au-20210820.git
cd 8812au-20210820

# 安裝編譯所需的套件
sudo apt update
sudo apt install -y dkms build-essential bc

# 編譯和安裝驅動程式
sudo ./install-driver.sh

# 回到原始目錄
cd /home/pi/HackMaster-Pi

echo "WiFi 網卡驅動安裝完成，建議重新啟動系統以確保驅動程式正常載入"
echo "執行 'sudo reboot' 來重新啟動系統"
