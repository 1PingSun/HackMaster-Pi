# scripts/defense/defense_manager.py

from .wifi_defense import WifiDefense
from .rfid_defense import RFIDDefense
from .threat_score import calculate_threat_score

class DefenseManager:
    def __init__(self, iface="wlan0"):
        self.wifi = WifiDefense(iface)
        self.rfid = RFIDDefense()

    def run_wifi_defense(self):
        aps = self.wifi.scan()
        issues = self.wifi.analyze(aps)
        score = calculate_threat_score(issues)

        return {
            "module": "Wi-Fi Defense",
            "issues": issues,
            "threat": score
        }

    def run_rfid_defense(self, card_info):
        issues = self.rfid.analyze(card_info)
        score = calculate_threat_score(issues)

        return {
            "module": "RFID Defense",
            "issues": issues,
            "threat": score
        }
