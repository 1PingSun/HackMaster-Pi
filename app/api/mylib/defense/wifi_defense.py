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
                    aps.append(current)
                current = {"bssid": line.split()[1]}
            elif "SSID:" in line:
                current["ssid"] = line.split("SSID:")[1].strip()
            elif "signal:" in line:
                current["signal"] = line.split("signal:")[1].strip()
            elif "RSN:" in line:
                current["encryption"] = "WPA/WPA2/WPA3"

        if current:
            aps.append(current)

        return aps

    def analyze(self, aps):
        issues = []
        ssid_map = {}

        for ap in aps:
            ssid = ap.get("ssid", "<hidden>")
            ssid_map.setdefault(ssid, []).append(ap.get("bssid"))

            if ap.get("encryption") is None:
                issues.append({
                    "type": "OPEN_NETWORK",
                    "ssid": ssid,
                    "risk": "HIGH",
                    "recommendation": "Enable WPA2/WPA3 encryption"
                })

        for ssid, bssids in ssid_map.items():
            if len(bssids) > 1 and ssid != "<hidden>":
                issues.append({
                    "type": "EVIL_TWIN",
                    "ssid": ssid,
                    "bssids": bssids,
                    "risk": "CRITICAL",
                    "recommendation": "Verify BSSID, disable auto-connect"
                })

        return issues
