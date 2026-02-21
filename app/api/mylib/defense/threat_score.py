# scripts/defense/threat_score.py

def calculate_threat_score(issues):
    score = 0

    for issue in issues:
        level = issue.get("risk", "LOW")
        if level == "LOW":
            score += 10
        elif level == "MEDIUM":
            score += 25
        elif level == "HIGH":
            score += 40
        elif level == "CRITICAL":
            score += 60

    if score > 100:
        score = 100

    if score <= 30:
        status = "SAFE"
    elif score <= 60:
        status = "WARNING"
    else:
        status = "CRITICAL"

    return {
        "score": score,
        "status": status
    }
