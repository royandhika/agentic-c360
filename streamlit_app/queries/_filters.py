def build_where_clause(*, term="", tiers=None, churn_range=None, actions=None,
                        has_ticket=None, booking_types=None, omnichannel=False):
    parts = ["1=1"]

    if term:
        esc = term.replace("'", "''")
        parts.append(f"""
            (name_std ILIKE '%{esc}%'
             OR arrayExists(x -> positionCaseInsensitive(x, '{esc}') > 0, emails)
             OR arrayExists(x -> positionCaseInsensitive(x, '{esc}') > 0, phones)
             OR positionCaseInsensitive(hex(resolved_customer_id), '{esc}') > 0)
        """)

    if tiers and len(tiers) > 0:
        quoted = ",".join(f"'{t}'" for t in tiers)
        parts.append(f"loyalty_tier IN ({quoted})")

    if churn_range and len(churn_range) == 2:
        parts.append(f"churn_risk_score >= {churn_range[0]} AND churn_risk_score <= {churn_range[1]}")

    if actions and len(actions) > 0:
        quoted = ",".join(f"'{a}'" for a in actions)
        parts.append(f"recommended_action IN ({quoted})")

    if has_ticket:
        parts.append("has_support_ticket = 1")

    if booking_types and len(booking_types) > 0:
        parts.append(f"distinct_booking_types >= {booking_types[0]}")
        if len(booking_types) == 2:
            parts.append(f"distinct_booking_types <= {booking_types[1]}")

    if omnichannel:
        parts.append("length(source_systems) = 3")

    return " AND ".join(parts)


def build_order_clause(sort_by):
    mapping = {
        "clv_desc": "clv_idr DESC",
        "churn_risk_desc": "churn_risk_score DESC",
        "dormant_desc": "dormant_days DESC",
        "last_booking_desc": "last_booking_ts DESC NULLS LAST",
    }
    return mapping.get(sort_by, "clv_idr DESC")
