from labels import LABELS

def format_idr(value):
    if value is None or value == 0:
        return "Rp 0"
    sign = "-" if value < 0 else ""
    s = f"{abs(int(value)):,}".replace(",", ".")
    return f"Rp {sign}{s}"

def format_phone(phone):
    if not phone:
        return ""
    e164 = str(phone).strip()
    if e164.startswith("+62") and len(e164) >= 12:
        return f"{e164[:3]} {e164[3:6]}-{e164[6:10]}-{e164[10:]}"
    return e164

SHORT_PHONE = lambda p: f"+62...{p[-4:]}" if p and len(str(p)) >= 8 else str(p) if p else ""

def tier_badge_html(tier):
    colors = {
        "gold": "#f0b429",
        "silver": "#94a3b8",
        "churn_risk": "#f87171",
    }
    color = colors.get(tier, "#8b8fa3")
    label = LABELS["en"].get(f"{tier}_tier", tier)
    return f'<span style="background:{color}20;color:{color};padding:2px 10px;border-radius:12px;font-weight:600;font-size:0.8rem">{label}</span>'

def confidence_badge_html(confidence):
    colors = {"high": "#34d399", "phone_bridge": "#fb923c", "email": "#94a3b8"}
    color = colors.get(confidence, "#8b8fa3")
    label = LABELS["en"].get(confidence, confidence)
    return f'<span style="background:{color}20;color:{color};padding:2px 10px;border-radius:12px;font-weight:600;font-size:0.8rem">{label}</span>'

def status_badge_html(status):
    colors = {"completed": "#34d399", "cancelled": "#f87171", "no_show": "#fbbf24",
              "open": "#f87171", "in_progress": "#fb923c", "resolved": "#34d399", "closed": "#94a3b8"}
    color = colors.get(status, "#8b8fa3")
    return f'<span style="background:{color}20;color:{color};padding:2px 8px;border-radius:8px;font-weight:600;font-size:0.75rem">{status}</span>'

def priority_badge_html(priority):
    colors = {"critical": "#f87171", "high": "#fb923c", "medium": "#fbbf24", "low": "#34d399"}
    color = colors.get(priority, "#8b8fa3")
    return f'<span style="background:{color}20;color:{color};padding:2px 8px;border-radius:8px;font-weight:600;font-size:0.75rem">{priority}</span>'
