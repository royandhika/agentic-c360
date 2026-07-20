import os
import sys
import random
import json
import hashlib
import sqlite3
import io

import yaml
import paramiko
import psycopg2
from faker import Faker

_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJ = os.path.dirname(_PARENT)
sys.path.insert(0, os.path.join(_PARENT, 'lib'))
sys.path.insert(0, _PARENT)
from world.world import WorldState
from lib.id_locales import (
    PROVINCES, INDONESIAN_CITIES, POSTAL_PREFIXES,
    PHONE_MOBILE_PREFIXES, LANDLINE_AREA_CODES, ID_MONTH_ABBR,
    HOTEL_NAMES, AIRLINES, AIRPORTS, DOMESTIC_ROUTES,
    INTERNATIONAL_ROUTES, EXPERIENCE_CATALOG, CATEGORIES,
    ROOM_TYPES, ROOM_TYPE_MULTIPLIERS,
    PAYMENT_METHODS_HOTEL, PAYMENT_METHODS_FLIGHT,
    PAYMENT_METHODS_EXPERIENCE, PAYMENT_METHODS_ALL,
    SEAT_CLASSES, SEAT_CLASS_WEIGHTS, SEAT_CLASS_MULTIPLIERS,
    LOYALTY_TIERS, LOYALTY_TIER_WEIGHTS,
    CRM_TICKET_CATEGORIES, CRM_TICKET_CATEGORY_WEIGHTS,
    CRM_TICKET_SUBJECTS, CRM_TICKET_BODIES, CRM_AGENT_NAMES,
    TOURIST_CITIES, TOURIST_CITY_WEIGHTS,
    HOTEL_BOOKING_STATUSES, FLIGHT_BOOKING_STATUSES,
    EXPERIENCE_BOOKING_STATUSES,
    weighted_choice, generate_indonesian_phone,
)


def _idr_fmt(val):
    s = str(val)
    parts = []
    while len(s) > 3:
        parts.insert(0, s[-3:])
        s = s[:-3]
    parts.insert(0, s)
    return '.'.join(parts)


def _date_ymd_no_sep(date_str):
    return date_str.replace('-', '')


def _date_dmy(date_str):
    y, m, d = date_str.split('-')
    return f"{d}/{m}/{y}"


class DailyGenerator:

    def __init__(self, config):
        self.config = config
        world_path = os.path.join(_PROJ, config['world_db_path'])
        self.world = WorldState(world_path)
        self.world.seed_data()
        self.rng = random.Random(config['seed'])
        self.fake = Faker(['id_ID'])

        pg_cfg = config.get('app_pg', {})
        pg_host = os.getenv('POSTGRES_APP_HOST', pg_cfg.get('host', 'localhost'))
        pg_port = int(os.getenv('POSTGRES_APP_PORT', pg_cfg.get('port', 5432)))
        pg_dbname = os.getenv('POSTGRES_APP_DB', pg_cfg.get('dbname', 'app_oltp'))
        pg_user = os.getenv('POSTGRES_APP_USER', pg_cfg.get('user', 'app_user'))
        pg_password = os.getenv('POSTGRES_APP_PASS', pg_cfg.get('password', 'app_pass'))
        self.pg_conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            dbname=pg_dbname,
            user=pg_user,
            password=pg_password,
        )
        self.pg_conn.autocommit = False
        self._pg_initialized = False

        vendor_db_path = os.path.join(_PROJ, config['vendor_db_path'])
        os.makedirs(os.path.dirname(vendor_db_path), exist_ok=True)
        self.vendor_conn = sqlite3.connect(vendor_db_path)
        self.vendor_conn.row_factory = sqlite3.Row
        self._vendor_db_initialized = False

        sftp_cfg = config.get('crm_sftp', {})
        self.sftp_host = os.getenv('CRM_SFTP_HOST', sftp_cfg.get('host', 'localhost'))
        self.sftp_port = int(os.getenv('CRM_SFTP_PORT', sftp_cfg.get('port', 2222)))
        self.sftp_user = os.getenv('CRM_SFTP_USER', sftp_cfg.get('user', 'crm_vendor'))
        self.sftp_password = os.getenv('CRM_SFTP_PASS', sftp_cfg.get('password', 'crm_pass'))
        self.sftp_path = os.getenv('CRM_SFTP_PATH', sftp_cfg.get('path', 'tickets'))

        self._customer_counters = {}
        self._booking_counters = {}

    def _next_customer_id(self, date_str, prefix="CST"):
        key = f"{prefix}-{date_str}"
        self._customer_counters[key] = self._customer_counters.get(key, 0) + 1
        return f"{prefix}-{_date_ymd_no_sep(date_str)}-{self._customer_counters[key]:06d}"

    def _next_booking_id(self, date_str, prefix):
        key = f"{prefix}-{date_str}"
        self._booking_counters[key] = self._booking_counters.get(key, 0) + 1
        return f"{prefix}-{_date_ymd_no_sep(date_str)}-{self._booking_counters[key]:06d}"

    def _init_pg(self):
        if self._pg_initialized:
            return
        cur = self.pg_conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                phone TEXT UNIQUE,
                full_name TEXT,
                address TEXT,
                city TEXT,
                province TEXT,
                postal_code TEXT,
                loyalty_tier TEXT DEFAULT NULL,
                preferred_airline TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hotel_bookings (
                booking_id TEXT PRIMARY KEY,
                customer_id TEXT,
                hotel_name TEXT,
                hotel_city TEXT,
                check_in_date DATE,
                check_out_date DATE,
                room_type TEXT,
                guests INTEGER,
                amount_idr BIGINT,
                payment_method TEXT,
                booking_status TEXT,
                booking_ts TIMESTAMP
            )
        """)
        self.pg_conn.commit()
        self._pg_initialized = True

    def _init_vendor_db(self):
        if self._vendor_db_initialized:
            return
        self.vendor_conn.execute("""
            CREATE TABLE IF NOT EXISTS flight_bookings (
                booking_ref TEXT PRIMARY KEY,
                email TEXT,
                airline TEXT,
                flight_number TEXT,
                origin TEXT,
                destination TEXT,
                departure_ts TEXT,
                arrival_ts TEXT,
                passenger_name TEXT,
                seat_class TEXT,
                amount_idr BIGINT,
                payment_method TEXT,
                booking_status TEXT,
                booking_ts TEXT
            )
        """)
        self.vendor_conn.execute("""
            CREATE TABLE IF NOT EXISTS experience_bookings (
                booking_ref TEXT PRIMARY KEY,
                email TEXT,
                experience_name TEXT,
                city TEXT,
                category TEXT,
                activity_date TEXT,
                participants INTEGER,
                amount_idr BIGINT,
                payment_method TEXT,
                booking_status TEXT,
                booking_ts TEXT
            )
        """)
        self.vendor_conn.commit()
        self._vendor_db_initialized = True

    # ── public API ──────────────────────────────────────────────

    def generate(self, date_str, holiday_mode=False):
        if self.world.was_generated(date_str):
            return

        seed = self.config['seed'] + int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16) % 999983
        self.rng.seed(seed)
        self.fake.seed_instance(seed)

        self._init_pg()
        self._init_vendor_db()

        hotel_cap = self.config['hotel_cap']
        flight_cap = self.config['flight_cap']
        experience_cap = self.config['experience_cap']
        crm_cap = self.config['crm_cap']

        if holiday_mode:
            hotel_count = hotel_cap
            flight_count = flight_cap
            experience_count = experience_cap
            crm_count = crm_cap
        else:
            volume = self.rng.randint(
                self.config['daily_volume_min'],
                self.config['daily_volume_max'],
            )
            remaining = volume
            hotel_count = self.rng.randint(0, min(remaining, hotel_cap))
            remaining -= hotel_count
            flight_count = self.rng.randint(0, min(remaining, flight_cap))
            remaining -= flight_count
            experience_count = self.rng.randint(0, min(remaining, experience_cap))
            remaining -= experience_count
            crm_count = self.rng.randint(0, min(remaining, crm_cap))

        self._generate_hotel_bookings(date_str, hotel_count)
        self._generate_flight_bookings(date_str, flight_count)
        self._generate_experience_bookings(date_str, experience_count)
        self._generate_crm_tickets(date_str, crm_count)

        total = hotel_count + flight_count + experience_count + crm_count
        self.world.log_day(date_str, total, hotel_count, flight_count,
                          experience_count, crm_count, holiday_mode)

    def close(self):
        self.world.close()
        if hasattr(self, 'pg_conn') and self.pg_conn and not self.pg_conn.closed:
            self.pg_conn.commit()
            self.pg_conn.close()
        if hasattr(self, 'vendor_conn') and self.vendor_conn:
            self.vendor_conn.commit()
            self.vendor_conn.close()

    # ── Hotel Bookings (App OLTP PostgreSQL) ───────────────────

    def _upsert_app_customer(self, world_customer, date_str):
        cur = self.pg_conn.cursor()
        email = world_customer.get('email') or self.fake.email()
        phone = world_customer.get('phone') or generate_indonesian_phone(self.rng)

        name = world_customer.get('canonical_name') or self.fake.name()
        addr = world_customer.get('address') or self.fake.address()
        app_city = world_customer.get('city') or self.fake.city()
        province = world_customer.get('province') or 'DKI Jakarta'
        postal = world_customer.get('postal_code') or '10110'
        loyalty = world_customer.get('loyalty_tier') or 'basic'

        # Time of day on date_str — keeps created_at/updated_at within the
        # simulated partition day so the bronze CDC filter
        # `WHERE updated_at >= start AND updated_at < end` returns rows.
        h = self.rng.randint(6, 23)
        m = self.rng.randint(0, 59)
        s = self.rng.randint(0, 59)
        ts_today = f"{date_str} {h:02d}:{m:02d}:{s:02d}"

        cur.execute(
            "SELECT customer_id FROM customers WHERE email = %s OR phone = %s",
            (email, phone),
        )
        row = cur.fetchone()

        if row:
            cid = row[0]
            cur.execute(
                "UPDATE customers SET full_name = %s, email = %s, phone = %s, "
                "address = %s, city = %s, province = %s, postal_code = %s, "
                "loyalty_tier = %s, updated_at = %s WHERE customer_id = %s",
                (name, email, phone, addr, app_city, province, postal, loyalty, ts_today, cid),
            )
        else:
            cid = f"CST-{world_customer['id']:06d}-{self.fake.random_int(100000, 999999)}"
            cur.execute(
                """INSERT INTO customers
                   (customer_id, email, phone, full_name, address, city, province,
                    postal_code, loyalty_tier, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (cid, email, phone, name, addr, app_city, province, postal, loyalty,
                 ts_today, ts_today),
            )

        return cid, email, phone, name

    def _generate_hotel_bookings(self, date_str, count):
        if count <= 0:
            return

        rows = []
        for i in range(count):
            is_new = self.rng.random() < 0.20
            if is_new:
                cust = self.world.get_or_create_customer(source='app')
            else:
                # Pull from the entire customer base (vendor/crm included) so
                # a customer who previously booked a flight/experience now
                # shows up as an app OLTP customer — the canonical anchor.
                existings = self.world.get_random_existing_customers(1, source=None)
                if existings and len(existings) > 0:
                    cust = existings[0]
                    self.world.set_source_flag(cust['id'], 'app')
                else:
                    cust = self.world.get_or_create_customer(source='app')

            customer_id, email, phone, name = self._upsert_app_customer(cust, date_str)

            hotel_city = self.world.get_random_itinerary_hotel_city()
            hotel = self.world.get_random_hotel(city=hotel_city)
            if hotel is None:
                hotel = self.world.get_random_hotel()
            if hotel is None:
                continue

            hotel_name = hotel['hotel_name']
            hotel_city_db = hotel['city']
            base_price = hotel['base_price_per_night_idr']

            room_type = self.rng.choices(
                ROOM_TYPES,
                weights=[30, 25, 8, 10, 5, 12, 6, 4],
            )[0]

            check_in_date = date_str
            if self.rng.random() < 0.10:
                from datetime import datetime, timedelta
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                offset = self.rng.choice([-3, -2, -1, 1, 2, 3, 4, 5])
                check_in_date = (dt + timedelta(days=offset)).strftime('%Y-%m-%d')

            nights = self.rng.choices(
                [1, 2, 3, 4, 5, 7, 10],
                weights=[0.15, 0.35, 0.25, 0.10, 0.07, 0.05, 0.03],
            )[0]

            from datetime import datetime, timedelta
            dt_in = datetime.strptime(check_in_date, '%Y-%m-%d')
            check_out_date = (dt_in + timedelta(days=nights)).strftime('%Y-%m-%d')

            guests = self.rng.choices(
                [1, 2, 3, 4, 5],
                weights=[0.10, 0.60, 0.15, 0.10, 0.05],
            )[0]

            multiplier = ROOM_TYPE_MULTIPLIERS.get(room_type, 1.0)
            amount = int(base_price * nights * multiplier)
            amount = max(100, int(round(amount / 100.0) * 100))

            payment_method = weighted_choice(PAYMENT_METHODS_HOTEL, self.rng)
            booking_status = weighted_choice(HOTEL_BOOKING_STATUSES, self.rng)

            booking_id = self._next_booking_id(date_str, "HTL")
            h, m, s = self.rng.randint(6, 23), self.rng.randint(0, 59), self.rng.randint(0, 59)
            booking_ts = f"{date_str} {h:02d}:{m:02d}:{s:02d}"

            if self.rng.random() < self.config['error_rate']:
                amount = self._mess_up_amount(amount)

            self.world.update_lifetime_value(cust['id'], amount)

            cur = self.pg_conn.cursor()
            cur.execute("""
                INSERT INTO hotel_bookings
                (booking_id, customer_id, hotel_name, hotel_city, check_in_date,
                 check_out_date, room_type, guests, amount_idr, payment_method,
                 booking_status, booking_ts)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                booking_id, customer_id, hotel_name, hotel_city_db,
                check_in_date, check_out_date, room_type, guests,
                amount, payment_method, booking_status, booking_ts,
            ))

            if self.rng.random() < self.config['dupe_rate']:
                dupe_amount = amount + self.rng.choice([-100, -50, -1, 1, 50, 100])
                dupe_amount = max(100, dupe_amount)
                dupe_id = self._next_booking_id(date_str, "HTL")
                cur.execute("""
                    INSERT INTO hotel_bookings
                    (booking_id, customer_id, hotel_name, hotel_city, check_in_date,
                     check_out_date, room_type, guests, amount_idr, payment_method,
                     booking_status, booking_ts)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    dupe_id, customer_id, hotel_name, hotel_city_db,
                    check_in_date, check_out_date, room_type, guests,
                    dupe_amount, payment_method, booking_status, booking_ts,
                ))

        self.pg_conn.commit()

    # ── Flight Bookings (Vendor API SQLite) ────────────────────

    def _generate_flight_bookings(self, date_str, count):
        if count <= 0:
            return

        rows = []
        for i in range(count):
            is_new = self.rng.random() < 0.20
            if is_new:
                cust = self.world.get_or_create_customer(source='vendor')
            else:
                # Shared customer base: pick any prior customer (incl. app) so
                # flight_bookings.email overlaps customers.email in app OLTP.
                existings = self.world.get_random_existing_customers(1, source=None)
                if existings and len(existings) > 0:
                    cust = existings[0]
                    self.world.set_source_flag(cust['id'], 'vendor')
                else:
                    cust = self.world.get_or_create_customer(source='vendor')

            is_domestic = self.rng.random() < 0.70
            origin_iata, dest_iata, typical_fare = self.world.get_random_route(domestic=is_domestic)
            airline = self.world.get_random_airline(domestic=is_domestic)

            flight_number = f"{airline['iata_code']}{self.rng.randint(100, 999)}"

            seat_class = weighted_choice(SEAT_CLASS_WEIGHTS, self.rng)
            seat_mult = SEAT_CLASS_MULTIPLIERS.get(seat_class, 1.0)

            fare = int(typical_fare * seat_mult)
            if is_domestic:
                fare += int(fare * 0.10)
            else:
                fare += int(fare * 0.15)
            fare = max(10000, int(round(fare / 100.0) * 100))

            email = cust.get('email') or self.fake.email()
            if self.rng.random() < self.config['error_rate']:
                email = self._mess_up_email(email)

            passenger_name = cust.get('canonical_name') or self.fake.name()
            if self.rng.random() < self.config['error_rate']:
                passenger_name = self._mess_up_name(passenger_name)

            from datetime import datetime, timedelta
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            dep_offset_hours = self.rng.randint(0, 23)
            departure_ts = (dt + timedelta(hours=dep_offset_hours,
                                           minutes=self.rng.randint(0, 59))).strftime('%Y-%m-%dT%H:%M:%S+07:00')
            flight_duration_minutes = self.rng.randint(60, 480) if is_domestic else self.rng.randint(120, 720)
            arrival_dt = datetime.strptime(departure_ts[:19], '%Y-%m-%dT%H:%M:%S') + timedelta(minutes=flight_duration_minutes)
            arrival_ts = arrival_dt.strftime('%Y-%m-%dT%H:%M:%S+07:00')

            payment_method = weighted_choice(PAYMENT_METHODS_FLIGHT, self.rng)
            booking_status = weighted_choice(FLIGHT_BOOKING_STATUSES, self.rng)

            booking_ref = self._next_booking_id(date_str, "FLT")
            h, m, s = self.rng.randint(0, 23), self.rng.randint(0, 59), self.rng.randint(0, 59)
            booking_ts = f"{date_str}T{h:02d}:{m:02d}:{s:02d}+07:00"

            if self.rng.random() < self.config['error_rate']:
                fare = self._mess_up_amount(fare)

            self.world.update_lifetime_value(cust['id'], fare)

            cur = self.vendor_conn.cursor()
            cur.execute("""
                INSERT INTO flight_bookings
                (booking_ref, email, airline, flight_number, origin, destination,
                 departure_ts, arrival_ts, passenger_name, seat_class,
                 amount_idr, payment_method, booking_status, booking_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking_ref, email, airline['airline_name'], flight_number,
                origin_iata, dest_iata, departure_ts, arrival_ts,
                passenger_name, seat_class, fare, payment_method,
                booking_status, booking_ts,
            ))

            if self.rng.random() < self.config['dupe_rate']:
                dupe_fare = fare + self.rng.choice([-100, -50, -1, 1, 50, 100])
                dupe_ref = self._next_booking_id(date_str, "FLT")
                cur.execute("""
                    INSERT INTO flight_bookings
                    (booking_ref, email, airline, flight_number, origin, destination,
                     departure_ts, arrival_ts, passenger_name, seat_class,
                     amount_idr, payment_method, booking_status, booking_ts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dupe_ref, email, airline['airline_name'], flight_number,
                    origin_iata, dest_iata, departure_ts, arrival_ts,
                    passenger_name, seat_class, max(100, dupe_fare),
                    payment_method, booking_status, booking_ts,
                ))

        self.vendor_conn.commit()

    # ── Experience Bookings (Vendor API SQLite) ────────────────

    def _generate_experience_bookings(self, date_str, count):
        if count <= 0:
            return

        for i in range(count):
            is_new = self.rng.random() < 0.15
            if is_new:
                cust = self.world.get_or_create_customer(source='vendor')
            else:
                # Same shared customer base so experiences overlap with the
                # app OLTP customers that hotel/CRM gen produces.
                existings = self.world.get_random_existing_customers(1, source=None)
                if existings and len(existings) > 0:
                    cust = existings[0]
                    self.world.set_source_flag(cust['id'], 'vendor')
                else:
                    cust = self.world.get_or_create_customer(source='vendor')

            hotel_city = self.world.get_random_itinerary_hotel_city()
            exp = self.world.get_random_experience(city=hotel_city)
            if exp is None:
                exp = self.world.get_random_experience()
            if exp is None:
                continue

            from datetime import datetime, timedelta
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            activity_offset = self.rng.randint(1, 7)
            activity_date = (dt + timedelta(days=activity_offset)).strftime('%Y-%m-%d')

            participants = self.rng.choices(
                [1, 2, 3, 4],
                weights=[0.20, 0.50, 0.15, 0.15],
            )[0]

            base_price = exp['base_price_per_person_idr']
            amount = base_price * participants
            amount = max(1000, int(round(amount / 100.0) * 100))

            email = cust.get('email') or self.fake.email()
            if self.rng.random() < self.config['error_rate']:
                email = self._mess_up_email(email)

            payment_method = weighted_choice(PAYMENT_METHODS_EXPERIENCE, self.rng)
            booking_status = weighted_choice(EXPERIENCE_BOOKING_STATUSES, self.rng)

            booking_ref = self._next_booking_id(date_str, "EXP")
            h, m, s = self.rng.randint(0, 23), self.rng.randint(0, 59), self.rng.randint(0, 59)
            booking_ts = f"{date_str}T{h:02d}:{m:02d}:{s:02d}+07:00"

            if self.rng.random() < self.config['error_rate']:
                amount = self._mess_up_amount(amount)

            self.world.update_lifetime_value(cust['id'], amount)

            cur = self.vendor_conn.cursor()
            cur.execute("""
                INSERT INTO experience_bookings
                (booking_ref, email, experience_name, city, category,
                 activity_date, participants, amount_idr, payment_method,
                 booking_status, booking_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking_ref, email, exp['experience_name'], exp['city'],
                exp['category'], activity_date, participants, amount,
                payment_method, booking_status, booking_ts,
            ))

            if self.rng.random() < self.config['dupe_rate']:
                dupe_amount = amount + self.rng.choice([-100, -50, -1, 1, 50, 100])
                dupe_ref = self._next_booking_id(date_str, "EXP")
                cur.execute("""
                    INSERT INTO experience_bookings
                    (booking_ref, email, experience_name, city, category,
                     activity_date, participants, amount_idr, payment_method,
                     booking_status, booking_ts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dupe_ref, email, exp['experience_name'], exp['city'],
                    exp['category'], activity_date, participants,
                    max(1000, dupe_amount), payment_method,
                    booking_status, booking_ts,
                ))

        self.vendor_conn.commit()

    # ── CRM Tickets (SFTP upload) ───────────────────────────────

    def _generate_crm_tickets(self, date_str, count):
        if count <= 0:
            return

        tickets = []
        for i in range(count):
            is_new = self.rng.random() < 0.25
            if is_new:
                cust = self.world.get_or_create_customer(source='crm')
            else:
                # Shared customer base: pick any prior customer (incl. app, vendor)
                # so the CRM ticket's customer_phone overlaps customers.phone in
                # app OLTP — the phone bridge that downstream identity resolution
                # relies on.
                existings = self.world.get_random_existing_customers(1, source=None)
                if existings and len(existings) > 0:
                    cust = existings[0]
                    self.world.set_source_flag(cust['id'], 'crm')
                else:
                    cust = self.world.get_or_create_customer(source='crm')

            email = cust.get('email') or self.fake.email()
            if self.rng.random() < 0.25 and cust.get('alternate_email') and cust['alternate_email'].strip():
                email = cust['alternate_email']
            elif self.rng.random() < 0.05:
                email = self.fake.email()

            phone = cust.get('phone') or generate_indonesian_phone(self.rng)
            use_alt_phone = self.rng.random() < 0.20 and cust.get('alternate_phone') and cust['alternate_phone'].strip()
            if use_alt_phone:
                phone = cust['alternate_phone']

            customer_name = cust.get('canonical_name') or self.fake.name()
            if self.rng.random() < self.config['error_rate']:
                customer_name = self._mess_up_name(customer_name)

            if self.rng.random() < self.config['error_rate']:
                email = self._mess_up_email(email)
            if self.rng.random() < self.config['error_rate']:
                phone = self._mess_up_phone(phone)

            category = weighted_choice(CRM_TICKET_CATEGORY_WEIGHTS, self.rng)

            subject = self.rng.choice(CRM_TICKET_SUBJECTS)
            body_template = self.rng.choice(CRM_TICKET_BODIES)

            body = self._fill_ticket_body(body_template, cust, date_str)

            status = self.rng.choices(
                ['open', 'in_progress', 'resolved', 'closed'],
                weights=[0.40, 0.30, 0.20, 0.10],
            )[0]
            priority = self.rng.choices(
                ['low', 'medium', 'high', 'critical'],
                weights=[0.20, 0.50, 0.25, 0.05],
            )[0]
            channel = self.rng.choices(
                ['email', 'phone', 'whatsapp', 'app_chat'],
                weights=[0.60, 0.25, 0.10, 0.05],
            )[0]

            from datetime import datetime, timedelta
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            h, m, s = self.rng.randint(6, 23), self.rng.randint(0, 59), self.rng.randint(0, 59)
            created_at = f"{date_str}T{h:02d}:{m:02d}:{s:02d}+07:00"

            resolved_at = None
            if status in ('resolved', 'closed'):
                resolve_offset = self.rng.randint(1, 72)
                resolved_dt = datetime.strptime(created_at[:19], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=resolve_offset)
                resolved_at = resolved_dt.strftime('%Y-%m-%dT%H:%M:%S+07:00')

            agent_name = self.rng.choice(CRM_AGENT_NAMES)
            ticket_id = self._next_booking_id(date_str, "TKT")

            ticket = {
                "ticket_id": ticket_id,
                "customer_email": email,
                "customer_phone": phone,
                "customer_name": customer_name,
                "subject": subject,
                "body": body,
                "status": status,
                "priority": priority,
                "channel": channel,
                "created_at": created_at,
                "resolved_at": resolved_at,
                "category": category,
                "agent_name": agent_name,
            }
            tickets.append(ticket)

        payload = json.dumps(tickets, ensure_ascii=False, indent=2)
        filename = f"tickets_{_date_ymd_no_sep(date_str)}.json"

        tpt = paramiko.Transport((self.sftp_host, self.sftp_port))
        tpt.connect(username=self.sftp_user, password=self.sftp_password)
        sftp = paramiko.SFTPClient.from_transport(tpt)
        sftp.chdir(self.sftp_path)
        with sftp.file(filename, 'w') as f:
            f.write(payload)
        sftp.close()
        tpt.close()

    def _fill_ticket_body(self, body_template, cust, date_str):
        from datetime import datetime, timedelta
        airline_name = self.rng.choice([a[0] for a in AIRLINES if a[3] == 1])
        origin = self.rng.choice(DOMESTIC_ROUTES)[0]
        destination = self.rng.choice(DOMESTIC_ROUTES)[1]
        hotel_name = self.rng.choice([h[0] for h in HOTEL_NAMES])
        room_type = self.rng.choice(ROOM_TYPES)
        experience_name = self.rng.choice([e[0] for e in EXPERIENCE_CATALOG])
        amount = self.rng.randint(150000, 5000000)
        hours = self.rng.randint(1, 12)
        booking_ref = f"HTL-{_date_ymd_no_sep(date_str)}-{self.rng.randint(1000, 9999):06d}"
        old_date_dt = datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=self.rng.randint(1, 30))
        old_date = old_date_dt.strftime('%Y-%m-%d')

        body = body_template
        body = body.replace("{airline}", airline_name)
        body = body.replace("{origin}", origin)
        body = body.replace("{destination}", destination)
        body = body.replace("{date}", date_str)
        body = body.replace("{hours}", str(hours))
        body = body.replace("{hotel}", hotel_name)
        body = body.replace("{amount_idr}", _idr_fmt(amount))
        body = body.replace("{old_date}", old_date)
        body = body.replace("{booking_ref}", booking_ref)
        body = body.replace("{room_type}", room_type)
        body = body.replace("{experience_name}", experience_name)

        return body

    # ── messiness helpers ───────────────────────────────────────

    def _mess_up_phone(self, phone_str):
        if not phone_str or len(str(phone_str)) < 3:
            return phone_str
        phone = str(phone_str).strip()
        roll = self.rng.random()
        if roll < 0.02:
            return '000-000-0000'
        if roll < 0.04:
            return 'TIDAK ADA'
        if roll < 0.06:
            return ''
        if roll < 0.50:
            cleaned = phone.replace(' ', '').replace('-', '').replace('+', '')
            if cleaned.startswith('62'):
                cleaned = '0' + cleaned[2:]
            elif not cleaned.startswith('0'):
                cleaned = '0' + cleaned
            if self.rng.random() < 0.5:
                return cleaned[:4] + '-' + cleaned[4:8] + '-' + cleaned[8:]
            return cleaned
        if roll < 0.75:
            cleaned = phone.replace(' ', '').replace('-', '').replace('+', '')
            if cleaned.startswith('62'):
                cleaned = '0' + cleaned[2:]
            return cleaned[:4] + '-' + cleaned[4:8] + ' ' + cleaned[8:]
        if roll < 0.88:
            cleaned = phone.replace(' ', '').replace('-', '')
            if cleaned.startswith('+62'):
                cleaned = cleaned[3:]
            elif cleaned.startswith('0'):
                cleaned = cleaned[1:]
            return cleaned
        return phone

    def _mess_up_email(self, email_str):
        if not email_str or '@' not in str(email_str):
            return email_str
        email = str(email_str).strip()
        local, domain = email.split('@', 1)
        roll = self.rng.random()
        if roll < 0.05:
            local = local.upper()
        elif roll < 0.10:
            domain = domain.upper()
        elif roll < 0.12:
            local = local.lower()
            domain = domain.lower()
        if self.rng.random() < 0.10:
            if 'gmail.com' in domain.lower():
                domain = self.rng.choice(['gnail.com', 'gmaill.com', 'gmail.com'])
            elif 'yahoo.co.id' in domain.lower():
                domain = 'yaho.co.id'
        if self.rng.random() < 0.05:
            local = local + '+' + self.fake.word()
        if self.rng.random() < 0.10:
            local = ' ' + local
        if self.rng.random() < 0.10:
            domain = domain + ' '
        return local + '@' + domain

    def _mess_up_name(self, name_str):
        if not name_str or len(str(name_str).strip()) == 0:
            return name_str
        name = str(name_str).strip()
        roll = self.rng.random()
        if roll < 0.05:
            return name.upper()
        if roll < 0.10:
            return name.lower()
        if roll < 0.13:
            parts = name.split(None, 1)
            return parts[0] if parts else name
        if roll < 0.28:
            prefix = self.rng.choice(['Bpk. ', 'Ibu ', 'Sdr. '])
            return prefix + name
        return name

    def _mess_up_amount(self, amount):
        roll = self.rng.random()
        if roll < 0.2:
            return amount + self.rng.choice([-100, -50, 50, 100])
        if roll < 0.3:
            return amount + 1
        if roll < 0.35:
            return amount - 1
        if roll < 0.40:
            return amount + self.rng.randint(10, 99)
        return amount

    def _random_idr_amount(self, base_price, noise_pct=0.1):
        noise = 1.0 + self.rng.uniform(-noise_pct, noise_pct)
        raw = base_price * noise
        return max(100, int(round(raw / 100.0) * 100))
