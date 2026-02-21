# scripts/defense/rfid_defense.py

class RFIDDefense:
    def analyze(self, card_info):
        issues = []

        if card_info.get("uid_only", False):
            issues.append({
                "type": "UID_ONLY_CARD",
                "risk": "HIGH",
                "recommendation": "Use secure RFID with authentication"
            })

        if not card_info.get("auth_enabled", True):
            issues.append({
                "type": "NO_AUTHENTICATION",
                "risk": "CRITICAL",
                "recommendation": "Enable password or crypto authentication"
            })

        if card_info.get("static_uid", False):
            issues.append({
                "type": "STATIC_UID",
                "risk": "MEDIUM",
                "recommendation": "Use random UID capable cards"
            })

        return issues
