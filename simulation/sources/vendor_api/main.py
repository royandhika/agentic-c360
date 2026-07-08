import os
import sqlite3
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

DB_PATH = os.getenv("VENDOR_DB_PATH", os.path.join(os.path.dirname(__file__), "store", "vendor.db"))

app = FastAPI(title="WanderFuel Vendor API", version="1.0.0")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS flight_bookings (
            booking_ref TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            airline TEXT NOT NULL,
            flight_number TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure_ts TEXT,
            arrival_ts TEXT,
            passenger_name TEXT,
            seat_class TEXT,
            amount_idr BIGINT NOT NULL,
            payment_method TEXT NOT NULL,
            booking_status TEXT DEFAULT 'confirmed',
            booking_ts TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS experience_bookings (
            booking_ref TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            experience_name TEXT NOT NULL,
            city TEXT NOT NULL,
            category TEXT,
            activity_date TEXT,
            participants INTEGER DEFAULT 1,
            amount_idr BIGINT NOT NULL,
            payment_method TEXT NOT NULL,
            booking_status TEXT DEFAULT 'confirmed',
            booking_ts TEXT NOT NULL
        )
    """)
    conn.commit()


def row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (date, datetime)):
            d[k] = v.isoformat()
    return d


def count_table(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
    return row["cnt"]


@app.on_event("startup")
def startup() -> None:
    conn = get_connection()
    try:
        ensure_tables(conn)
    finally:
        conn.close()


@app.get("/health")
def health():
    conn = get_connection()
    try:
        flights = count_table(conn, "flight_bookings")
        experiences = count_table(conn, "experience_bookings")
    finally:
        conn.close()
    return {
        "status": "ok",
        "bookings_flight": flights,
        "bookings_experience": experiences,
    }


@app.get("/flights")
def get_flights(
    since: Optional[str] = Query(None, description="Filter bookings with booking_ts >= this ISO date"),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    conn = get_connection()
    try:
        params = []
        where_clause = ""
        if since:
            where_clause = "WHERE booking_ts >= ?"
            params.append(since)

        total_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM flight_bookings {where_clause}", params
        ).fetchone()
        total = total_row["cnt"]

        rows = conn.execute(
            f"SELECT * FROM flight_bookings {where_clause} ORDER BY booking_ts DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        data = [row_to_dict(r) for r in rows]
    finally:
        conn.close()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": data,
    }


@app.get("/experiences")
def get_experiences(
    since: Optional[str] = Query(None, description="Filter bookings with booking_ts >= this ISO date"),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    conn = get_connection()
    try:
        params = []
        where_clause = ""
        if since:
            where_clause = "WHERE booking_ts >= ?"
            params.append(since)

        total_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM experience_bookings {where_clause}", params
        ).fetchone()
        total = total_row["cnt"]

        rows = conn.execute(
            f"SELECT * FROM experience_bookings {where_clause} ORDER BY booking_ts DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        data = [row_to_dict(r) for r in rows]
    finally:
        conn.close()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": data,
    }
