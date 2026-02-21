# scripts/defense/wifi_defense.py

import subprocess
import re

class WifiDefense:
    def __init__(self, iface="wlan0"):
        self.iface = iface

    def scan(self):
        try:
            output = subprocess.check_output(
                ["iw", "dev", self.iface, "scan"],
                stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
        except Exception:
            return []

        aps = []
        current = {}

        for line in output.splitlines():
            stripped = line.strip()

            # BSS 格式: "BSS 1c:f4:3f:14:a9:fc(on wlan0)"
            if stripped.startswith("BSS "):
                if current:
                    # 保存前一個 AP
                    if "ssid" not in current or not current["ssid"]:
                        current["ssid"] = f"<Hidden Network>"
                    aps.append(current)
                
                # 提取 BSSID: 取第二個元素，並去除括號部分
                parts = stripped.split()
                if len(parts) >= 2:
                    bssid = parts[1].split("(")[0]  # 去掉 "(on wlan0)" 部分
                    current = {"bssid": bssid.lower()}
                
            # SSID 是單獨一行，格式: "\tSSID: GraceK"
            elif stripped.startswith("SSID:"):
                ssid = stripped.split("SSID:", 1)[1].strip()
                if ssid:
                    current["ssid"] = ssid
            
            # 頻率 格式: "\tfreq: 2412"
            elif stripped.startswith("freq:"):
                freq = stripped.split("freq:", 1)[1].strip()
                current["frequency"] = f"{freq} MHz"
                # 根據頻率判斷頻段和頻道
                try:
                    freq_int = int(freq)
                    if 2412 <= freq_int <= 2484:
                        # 2.4GHz 頻段
                        current["band"] = "2.4 GHz"
                        current["channel"] = (freq_int - 2412) // 5 + 1
                    elif 5170 <= freq_int <= 5825:
                        # 5GHz 頻段
                        current["band"] = "5 GHz"
                        current["channel"] = (freq_int - 5000) // 5
                except:
                    pass
                    
            # Signal 格式: "\tsignal: -83.00 dBm"
            elif stripped.startswith("signal:"):
                signal_str = stripped.split("signal:", 1)[1].strip()
                # 提取數字部分
                signal_value = signal_str.split()[0]
                current["signal"] = signal_value
                # 計算信號質量百分比
                try:
                    signal_dbm = float(signal_value)
                    if signal_dbm >= -50:
                        quality = 100
                    elif signal_dbm <= -100:
                        quality = 0
                    else:
                        quality = 2 * (signal_dbm + 100)
                    current["signal_quality"] = f"{int(quality)}%"
                except:
                    pass
                
            # 檢測加密類型: RSN (WPA2/WPA3)
            elif stripped.startswith("RSN:"):
                current["encryption"] = "WPA2/WPA3"
                current["security"] = "Strong"
            
            # 檢測加密類型: WPA (WPA)
            elif stripped.startswith("WPA:"):
                if "encryption" not in current:
                    current["encryption"] = "WPA"
                    current["security"] = "Moderate"
            
            # 檢測 WEP (舊式加密)
            elif "Privacy" in stripped and "capability:" in stripped:
                if "encryption" not in current:
                    current["encryption"] = "WEP"
                    current["security"] = "Weak"
            
            # 檢測 WPS (可能的安全風險)
            elif stripped.startswith("WPS:"):
                current["wps_enabled"] = True

        # 處理最後一個 AP
        if current:
            if "ssid" not in current or not current["ssid"]:
                current["ssid"] = f"<Hidden Network>"
            # 如果沒有加密資訊，標記為開放網絡
            if "encryption" not in current:
                current["encryption"] = "Open"
                current["security"] = "None"
            aps.append(current)

        return aps

    def analyze(self, aps):
        issues = []
        ssid_map = {}
        ap_details = {}  # 儲存每個 AP 的詳細資訊

        for ap in aps:
            ssid = ap.get("ssid", "<unknown>")
            bssid = ap.get("bssid", "unknown")
            encryption = ap.get("encryption")
            signal = ap.get("signal", "N/A")
            channel = ap.get("channel", "N/A")
            band = ap.get("band", "N/A")
            frequency = ap.get("frequency", "N/A")
            signal_quality = ap.get("signal_quality", "N/A")
            wps_enabled = ap.get("wps_enabled", False)
            
            # 儲存 AP 詳細資訊
            ap_details[bssid] = {
                "ssid": ssid,
                "signal": signal,
                "signal_quality": signal_quality,
                "channel": channel,
                "band": band,
                "frequency": frequency,
                "encryption": encryption or "Open",
                "wps_enabled": wps_enabled
            }
            
            # 只對真實的 SSID 進行 Evil Twin 檢測（排除隱藏網絡）
            if ssid and not ssid.startswith("<"):
                ssid_map.setdefault(ssid, []).append(ap)

            # 檢測開放網路（無加密）
            if encryption is None or encryption == "Open":
                issues.append({
                    "type": "OPEN_NETWORK",
                    "ssid": ssid,
                    "bssid": bssid,
                    "signal": signal,
                    "signal_quality": signal_quality,
                    "channel": channel,
                    "band": band,
                    "frequency": frequency,
                    "risk": "HIGH",
                    "recommendation": "Enable WPA2/WPA3 encryption"
                })
            # 檢測 WEP 加密（已過時，不安全）
            elif encryption == "WEP":
                issues.append({
                    "type": "WEAK_ENCRYPTION",
                    "ssid": ssid,
                    "bssid": bssid,
                    "encryption": "WEP",
                    "signal": signal,
                    "signal_quality": signal_quality,
                    "channel": channel,
                    "band": band,
                    "frequency": frequency,
                    "risk": "MEDIUM",
                    "recommendation": "Upgrade to WPA2/WPA3 encryption (WEP is deprecated)"
                })
            # 檢測 WPS 啟用（可能的安全風險）
            elif wps_enabled and encryption not in ["Open", "WEP", None]:
                issues.append({
                    "type": "WPS_ENABLED",
                    "ssid": ssid,
                    "bssid": bssid,
                    "encryption": encryption,
                    "signal": signal,
                    "signal_quality": signal_quality,
                    "channel": channel,
                    "band": band,
                    "frequency": frequency,
                    "risk": "LOW",
                    "recommendation": "Disable WPS to prevent brute-force attacks"
                })

        # 檢測 Evil Twin (同一 SSID 有多個 BSSID)
        for ssid, ap_list in ssid_map.items():
            if len(ap_list) > 1:
                bssids = [ap.get("bssid") for ap in ap_list]
                # 收集所有 AP 的詳細資訊
                ap_info = []
                for ap in ap_list:
                    ap_info.append({
                        "bssid": ap.get("bssid"),
                        "signal": ap.get("signal", "N/A"),
                        "channel": ap.get("channel", "N/A"),
                        "encryption": ap.get("encryption", "Open")
                    })
                
                issues.append({
                    "type": "EVIL_TWIN",
                    "ssid": ssid,
                    "bssids": bssids,
                    "count": len(bssids),
                    "ap_details": ap_info,
                    "risk": "CRITICAL",
                    "recommendation": f"Multiple APs detected ({len(bssids)} APs). Possible Evil Twin attack - verify BSSID before connecting"
                })

        return issues
