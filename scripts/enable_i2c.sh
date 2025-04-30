#!/bin/bash

# 啟用 I2C（需要 root 權限）
raspi-config nonint do_i2c 0

# 確保 i2c-tools 已安裝
apt-get update -y
apt-get install -y i2c-tools python3-smbus

# 確保 dtparam=i2c_arm=on 存在於 config.txt
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
  echo "dtparam=i2c_arm=on" >> /boot/config.txt
fi

# 確保 i2c-dev 在模組列表中
if ! grep -q "^i2c-dev" /etc/modules; then
  echo "i2c-dev" >> /etc/modules
fi

echo "I2C 已啟用，請重新啟動系統以使設定生效"