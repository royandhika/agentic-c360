CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    preferred_contact TEXT DEFAULT 'email',
    lifetime_value_idr BIGINT DEFAULT 0,
    address TEXT,
    city_prov TEXT,
    is_vip BOOLEAN DEFAULT false
);

-- UNIQUE constraints for upsert logic
ALTER TABLE customers ADD CONSTRAINT uq_customers_email UNIQUE (email);
ALTER TABLE customers ADD CONSTRAINT uq_customers_phone UNIQUE (phone);

CREATE TABLE tickets (
    ticket_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT REFERENCES customers(customer_id),
    subject TEXT,
    body TEXT,
    status TEXT DEFAULT 'open',
    priority TEXT DEFAULT 'normal',
    channel TEXT DEFAULT 'email',
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolution_note TEXT,
    category TEXT DEFAULT 'other',
    contact_email_snapshot TEXT
);

CREATE INDEX idx_tickets_customer_id ON tickets (customer_id);

CREATE TABLE interactions (
    interaction_id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT REFERENCES tickets(ticket_id),
    agent_id TEXT,
    agent_name TEXT,
    ts TIMESTAMP DEFAULT NOW(),
    direction TEXT,
    channel TEXT,
    note TEXT
);

CREATE INDEX idx_interactions_ticket_id ON interactions (ticket_id);
