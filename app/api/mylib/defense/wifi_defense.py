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
            line = line.strip()

            if line.startswith("BSS"):
                if current:
                    # 如果沒有 SSID，使用 BSSID 或標記為 <hidden>
                    if "ssid" not in current or not current["ssid"]:
                        current["ssid"] = current.get("bssid", "<unknown>")
                    aps.append(current)
                # 提取 BSSID (去除括號等符號)
                bssid = line.split()[1].replace("(", "").replace(")", "")
                current = {"bssid": bssid}
            elif "SSID:" in line:
                ssid = line.split("SSID:")[1].strip()
                # 只在 SSID 非空時設置
                if ssid:
                    current["ssid"] = ssid
            elif "signal:" in line:
                current["signal"] = line.split("signal:")[1].strip()
            elif "RSN:" in line or "WPA:" in line:
                current["encryption"] = "WPA/WPA2/WPA3"

        if current:
            # 處理最後一個 AP
            if "ssid" not in current or not current["ssid"]:
                current["ssid"] = current.get("bssid", "<unknown>")
            aps.append(current)

        return aps

    def analyze(self, aps):
        issues = []
        ssid_map = {}

        for ap in aps:
            ssid = ap.get("ssid", "<unknown>")
            bssid = ap.get("bssid", "unknown")
            
            # 只對真實的 SSID 進行 Evil Twin 檢測（排除 BSSID 作為 SSID 的情況）
            if ssid and not ssid.startswith("<") and ":" not in ssid:
                ssid_map.setdefault(ssid, []).append(bssid)

            # 檢測開放網絡
            if ap.get("encryption") is None:
                issues.append({
                    "type": "OPEN_NETWORK",
                    "ssid": ssid,
                    "bssid": bssid,
                    "risk": "HIGH",
                    "recommendation": "Enable WPA2/WPA3 encryption"
                })

        # 檢測 Evil Twin (同一 SSID 有多個 BSSID)
        for ssid, bssids in ssid_map.items():
            if len(bssids) > 1:
                issues.append({
                    "type": "EVIL_TWIN",
                    "ssid": ssid,
                    "bssids": bssids,
                    "count": len(bssids),
                    "risk": "CRITICAL",
                    "recommendation": "Verify BSSID, disable auto-connect"
                })

        return issues
