"""Mock Indonesian e-commerce API. Genuinely returns orders in IDR, with Indonesian customer data."""

import json
import os
import sqlite3
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI(title="Mock E-Commerce API", version="0.1.0")

DB_PATH = os.getenv("ECOM_DB_PATH", "store/ecom_store.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class OrdersResponse(BaseModel):
    data: list = []
    next: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"


@app.get("/orders", response_model=OrdersResponse)
async def get_orders(
    since: Optional[str] = Query(None, description="ISO8601 timestamp filter"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    conn = get_db()
    cursor = conn.cursor()

    if since:
        cursor.execute(
            "SELECT * FROM orders WHERE order_ts >= ? ORDER BY order_ts ASC LIMIT ? OFFSET ?",
            (since, limit, offset),
        )
    else:
        cursor.execute(
            "SELECT * FROM orders ORDER BY order_ts ASC LIMIT ? OFFSET ?",
            (limit, offset),
        )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"data": [], "next": None}

    result = []
    for row in rows:
        order = dict(row)
        order["customer"] = {
            "email": order.pop("customer_email", None),
            "phone": order.pop("customer_phone", None),
            "name": order.pop("customer_name", None),
            "address": order.pop("customer_address", None),
        }
        order.pop("customer_city_prov", None)
        order["line_items"] = json.loads(order.pop("line_items_json", "[]") or "[]")
        result.append(order)

    return {
        "data": result,
        "next": str(offset + limit) if len(rows) == limit else None,
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}
