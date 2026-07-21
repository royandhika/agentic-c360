import pandas as pd
from clickhouse_connect.driver import Client

def fetch(ch: Client, rcid_hex: str) -> dict:
    """Return dict with: customer, mcl, bookings, tickets.
    rcid_hex is the hex(resolved_customer_id) value (30-char hex string)."""
    customer = ch.query("""
        SELECT *, hex(resolved_customer_id) AS rcid_hex
        FROM wanderfuel.dim_customer
        WHERE hex(resolved_customer_id) = %(rcid_hex)s
    """, parameters={"rcid_hex": rcid_hex}).first_row

    if customer is None:
        return {"customer": None, "mcl": None, "bookings": None, "tickets": None}

    mcl = ch.query("""
        SELECT *, hex(resolved_customer_id) AS rcid_hex
        FROM wanderfuel.mart_customer_clv
        WHERE hex(resolved_customer_id) = %(rcid_hex)s
    """, parameters={"rcid_hex": rcid_hex}).first_row

    bookings = ch.query_df("""
        SELECT
            booking_id, booking_type, provider, city,
            origin, destination, amount_idr, payment_method,
            booking_ts, status, check_in_date, check_out_date,
            departure_ts, arrival_ts, activity_date, seat_class,
            category, guests, participants
        FROM wanderfuel.fact_bookings
        WHERE hex(resolved_customer_id) = %(rcid_hex)s
        ORDER BY booking_ts DESC
    """, parameters={"rcid_hex": rcid_hex})

    emails = customer[1] if customer[1] else []
    phones_list = customer[2] if customer[2] else []

    tickets_df = pd.DataFrame()
    if emails or phones_list:
        email_conds = " OR ".join([f"customer_email = %(e{i})s" for i in range(len(emails))])
        phone_conds = " OR ".join([f"customer_phone = %(p{i})s" for i in range(len(phones_list))])
        conds = []
        params = {"rcid_hex": rcid_hex}
        if emails:
            conds.append(f"({email_conds})")
            for i, e in enumerate(emails):
                params[f"e{i}"] = e
        if phones_list:
            conds.append(f"({phone_conds})")
            for i, p in enumerate(phones_list):
                params[f"p{i}"] = p

        if conds:
            where = " OR ".join(conds)
            tickets_df = ch.query_df(f"""
                SELECT
                    ticket_id, customer_email, customer_phone, customer_name,
                    subject, body, status, priority, channel,
                    created_at, resolved_at, category, agent_name
                FROM wanderfuel.silver_tickets
                WHERE {where}
                ORDER BY created_at DESC
            """, parameters=params)

    return {
        "customer": customer,
        "mcl": mcl,
        "bookings": bookings,
        "tickets": tickets_df,
    }

def booking_type_gap(ch: Client, rcid_hex: str):
    row = ch.query("""
        SELECT distinct_booking_types, booking_type_mode
        FROM wanderfuel.mart_customer_clv
        WHERE hex(resolved_customer_id) = %(rcid_hex)s
    """, parameters={"rcid_hex": rcid_hex}).first_row
    if row is None:
        return 0, None
    return row[0], row[1]
