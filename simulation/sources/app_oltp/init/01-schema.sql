CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL UNIQUE,
    full_name TEXT,
    address TEXT,
    city TEXT,
    province TEXT,
    postal_code TEXT,
    loyalty_tier TEXT DEFAULT NULL,
    preferred_airline TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hotel_bookings (
    booking_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    hotel_name TEXT NOT NULL,
    hotel_city TEXT NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    room_type TEXT NOT NULL,
    guests INTEGER DEFAULT 1,
    amount_idr BIGINT NOT NULL,
    payment_method TEXT NOT NULL,
    booking_status TEXT DEFAULT 'confirmed',
    booking_ts TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hotel_bookings_customer ON hotel_bookings(customer_id);
CREATE INDEX IF NOT EXISTS idx_hotel_bookings_status ON hotel_bookings(booking_status);
CREATE INDEX IF NOT EXISTS idx_hotel_bookings_ts ON hotel_bookings(booking_ts);
