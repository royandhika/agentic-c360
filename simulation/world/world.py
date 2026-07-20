import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PARENT, 'lib'))
from id_locales import (
    PROVINCES, INDONESIAN_CITIES, POSTAL_PREFIXES,
    PHONE_MOBILE_PREFIXES, LANDLINE_AREA_CODES,
    HOTEL_NAMES, AIRLINES, AIRPORTS, DOMESTIC_ROUTES,
    INTERNATIONAL_ROUTES, EXPERIENCE_CATALOG, LOYALTY_TIERS,
    LOYALTY_TIER_WEIGHTS, TOURIST_CITIES, TOURIST_CITY_WEIGHTS,
    weighted_choice, generate_indonesian_phone, generate_mobile_phone,
)

_FAKE = Faker('id_ID')
_WORLD_RNG = random.Random(4242)


def _now_iso():
    return datetime.now().isoformat()


def _parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d')


class WorldState:

    def __init__(self, db_path):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                alternate_email TEXT,
                alternate_phone TEXT,
                address TEXT,
                city TEXT,
                province TEXT,
                postal_code TEXT,
                created_at TEXT,
                is_app_customer INTEGER DEFAULT 0,
                is_vendor_customer INTEGER DEFAULT 0,
                is_crm_customer INTEGER DEFAULT 0,
                loyalty_tier TEXT DEFAULT NULL,
                lifetime_value_idr INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS hotels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_name TEXT,
                city TEXT,
                province TEXT,
                star_rating INTEGER,
                base_price_per_night_idr INTEGER,
                chain_name TEXT
            );

            CREATE TABLE IF NOT EXISTS airlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                airline_name TEXT,
                iata_code TEXT UNIQUE,
                is_lcc INTEGER DEFAULT 0,
                is_domestic INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS airports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                airport_name TEXT,
                iata_code TEXT UNIQUE,
                city TEXT,
                province TEXT
            );

            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experience_name TEXT,
                city TEXT,
                category TEXT,
                base_price_per_person_idr INTEGER
            );

            CREATE TABLE IF NOT EXISTS generation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                total_rows INTEGER,
                hotel_rows INTEGER,
                flight_rows INTEGER,
                experience_rows INTEGER,
                crm_rows INTEGER,
                is_holiday INTEGER DEFAULT 0
            );
        """)
        self._conn.commit()

    def seed_data(self):
        cur = self._conn.cursor()

        cur.execute("SELECT COUNT(*) FROM hotels")
        if cur.fetchone()[0] > 0:
            return

        for hotel_name, city, star_rating, base_price, chain in HOTEL_NAMES:
            province = self._resolve_province(city)
            cur.execute(
                "INSERT OR IGNORE INTO hotels (hotel_name, city, province, star_rating, base_price_per_night_idr, chain_name) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (hotel_name, city, province, star_rating, base_price, chain),
            )

        seen_iata = set()
        for airline_name, iata_code, is_lcc, is_domestic in AIRLINES:
            pair = (airline_name, iata_code)
            if pair in seen_iata:
                continue
            seen_iata.add(pair)
            cur.execute(
                "INSERT OR IGNORE INTO airlines (airline_name, iata_code, is_lcc, is_domestic) "
                "VALUES (?, ?, ?, ?)",
                (airline_name, iata_code, is_lcc, is_domestic),
            )

        for airport_name, iata_code, city, province in AIRPORTS:
            cur.execute(
                "INSERT OR IGNORE INTO airports (airport_name, iata_code, city, province) "
                "VALUES (?, ?, ?, ?)",
                (airport_name, iata_code, city, province),
            )

        for exp_name, category, city, base_price in EXPERIENCE_CATALOG:
            cur.execute(
                "INSERT OR IGNORE INTO experiences (experience_name, city, category, base_price_per_person_idr) "
                "VALUES (?, ?, ?, ?)",
                (exp_name, city, category, base_price),
            )

        self._conn.commit()

    def _resolve_province(self, city_or_region):
        for prov_name, cities in INDONESIAN_CITIES.items():
            for cname, _ in cities:
                if cname.lower() in city_or_region.lower() or city_or_region.lower() in cname.lower():
                    return prov_name

        city_province_map = {
            "Jakarta": "DKI Jakarta",
            "Bali": "Bali", "Kuta": "Bali", "Seminyak": "Bali",
            "Ubud": "Bali", "Canggu": "Bali", "Nusa Dua": "Bali",
            "Sanur": "Bali", "Jimbaran": "Bali",
            "Yogyakarta": "Daerah Istimewa Yogyakarta",
            "Bandung": "Jawa Barat", "Lembang": "Jawa Barat",
            "Lombok": "Nusa Tenggara Barat", "Senggigi": "Nusa Tenggara Barat",
            "Gili Trawangan": "Nusa Tenggara Barat",
            "Labuan Bajo": "Nusa Tenggara Timur",
            "Surabaya": "Jawa Timur", "Malang": "Jawa Timur",
            "Banyuwangi": "Jawa Timur", "Probolinggo": "Jawa Timur",
            "Batu": "Jawa Timur",
            "Semarang": "Jawa Tengah",
            "Medan": "Sumatera Utara",
            "Makassar": "Sulawesi Selatan",
            "Manado": "Sulawesi Utara",
            "Padang": "Sumatera Barat",
            "Palembang": "Sumatera Selatan",
            "Bogor": "Jawa Barat",
            "Banjarmasin": "Kalimantan Selatan",
            "Balikpapan": "Kalimantan Timur",
            "Raja Ampat": "Papua Barat Daya",
            "Bukit Lawang": "Sumatera Utara",
            "Tana Toraja": "Sulawesi Selatan",
            "Tanjung Puting": "Kalimantan Tengah",
            "Derawan": "Kalimantan Timur",
            "Magelang": "Jawa Tengah",
        }
        return city_province_map.get(city_or_region, "DKI Jakarta")

    def get_or_create_customer(self, email=None, phone=None, name=None, source='app'):
        cur = self._conn.cursor()

        existing = self._lookup_customer(cur, email, phone)

        if existing is not None:
            cust = dict(existing)
            self._set_source_flag(cur, cust, source)
            self._conn.commit()
            return cust

        return self._create_customer(cur, email, phone, name, source)

    def get_or_create_customer_for_source(self, email=None, phone=None, name=None, source='vendor'):
        cur = self._conn.cursor()

        if source == 'vendor':
            existing = self._lookup_customer(cur, email, phone)
        elif source == 'crm':
            existing = self._lookup_customer(cur, email, phone)
        else:
            existing = self._lookup_customer(cur, email, phone)

        if existing is not None:
            cust = dict(existing)
            self._set_source_flag(cur, cust, source)
            self._conn.commit()
            return cust

        return self._create_customer(cur, email, phone, name, source)

    def _lookup_customer(self, cur, email, phone):
        if phone is not None and str(phone).strip():
            p = str(phone).strip()
            cur.execute(
                "SELECT * FROM customers WHERE phone = ? OR alternate_phone = ?",
                (p, p),
            )
            row = cur.fetchone()
            if row:
                return row

        if email is not None and str(email).strip():
            e = str(email).strip()
            cur.execute(
                "SELECT * FROM customers WHERE lower(email) = lower(?) OR lower(alternate_email) = lower(?)",
                (e, e),
            )
            row = cur.fetchone()
            if row:
                return row

        return None

    def _set_source_flag(self, cur, cust, source):
        cid = cust['id']
        if source == 'app':
            cur.execute("UPDATE customers SET is_app_customer = 1 WHERE id = ?", (cid,))
            cust['is_app_customer'] = 1
        elif source == 'vendor':
            cur.execute("UPDATE customers SET is_vendor_customer = 1 WHERE id = ?", (cid,))
            cust['is_vendor_customer'] = 1
        elif source == 'crm':
            cur.execute("UPDATE customers SET is_crm_customer = 1 WHERE id = ?", (cid,))
            cust['is_crm_customer'] = 1

    def _create_customer(self, cur, email, phone, name, source):
        canonical_name = name if name else _FAKE.name()
        email = email if email else _FAKE.email()
        phone = phone if phone else generate_indonesian_phone(_WORLD_RNG)

        # Identity-fragmentation: same human keeps separate personal/work emails
        # and an occasional alternate number across sources — this is the
        # raw material that downstream entity resolution has to stitch together.
        alternate_email = self._alternate_email(email)
        alternate_phone = generate_mobile_phone(_WORLD_RNG)

        province_name = random.choice(PROVINCES)[0]
        city_info = self._random_city_for_province(province_name)
        city = city_info if city_info else _FAKE.city()

        postcode_prefix = random.choice(POSTAL_PREFIXES.get(province_name, ["10"]))
        postal_code = postcode_prefix + str(random.randint(100, 999))

        address = self._generate_indonesian_address(city, province_name)

        now = _FAKE.date_time_this_decade().isoformat()

        loyalty = random.choices(
            LOYALTY_TIERS,
            weights=[LOYALTY_TIER_WEIGHTS.get(t, 0.1) for t in LOYALTY_TIERS],
        )[0]

        is_app = 1 if source == 'app' else 0
        is_vendor = 1 if source == 'vendor' else 0
        is_crm = 1 if source == 'crm' else 0

        cur.execute("""
            INSERT INTO customers
            (canonical_name, email, phone, alternate_email, alternate_phone,
             address, city, province, postal_code,
             created_at, is_app_customer, is_vendor_customer, is_crm_customer,
             loyalty_tier, lifetime_value_idr)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            canonical_name, email, phone, alternate_email, alternate_phone,
            address, city, province_name, postal_code,
            now, is_app, is_vendor, is_crm, loyalty, 0,
        ))
        self._conn.commit()

        cur.execute("SELECT * FROM customers WHERE id = ?", (cur.lastrowid,))
        return dict(cur.fetchone())

    def _alternate_email(self, primary_email):
        """Personal vs work email drift across sources — base on same local name."""
        if not primary_email or '@' not in primary_email:
            return _FAKE.email()
        local, _ = primary_email.split('@', 1)
        domain = _WORLD_RNG.choice([
            'gmail.com', 'yahoo.co.id', 'outlook.com', 'hotmail.com',
            'yahoo.com', 'protonmail.com',
        ])
        suffix = _WORLD_RNG.choice(['', '', '.id', str(_WORLD_RNG.randint(1, 99))])
        return f"{local}{suffix}@{domain}"

    def set_source_flag(self, customer_id, source):
        """Mark a reused world customer as also belonging to `source`."""
        field = {'app': 'is_app_customer',
                 'vendor': 'is_vendor_customer',
                 'crm': 'is_crm_customer'}.get(source)
        if not field:
            return
        cur = self._conn.cursor()
        cur.execute(f"UPDATE customers SET {field} = 1 WHERE id = ?", (customer_id,))
        self._conn.commit()

    def _random_city_for_province(self, province_name):
        cities = INDONESIAN_CITIES.get(province_name, [])
        if cities:
            return random.choice(cities)[0]
        return None

    def _generate_indonesian_address(self, city, province):
        rt = str(random.randint(1, 20)).zfill(2)
        rw = str(random.randint(1, 20)).zfill(2)

        street_names = [
            "Jl. Merdeka", "Jl. Sudirman", "Jl. Gatot Subroto", "Jl. Ahmad Yani",
            "Jl. Diponegoro", "Jl. Thamrin", "Jl. Imam Bonjol", "Jl. Kartini",
            "Jl. Raya", "Jl. Pahlawan", "Jl. Veteran", "Jl. Pemuda",
            "Jl. MH Thamrin", "Jl. Cendrawasih", "Jl. Melati", "Jl. Anggrek",
        ]
        street = random.choice(street_names)
        no = random.randint(1, 200)

        rtrw_format = random.choice([
            f"RT {rt}/RW {rw}",
            f"RT {rt} RW {rw}",
            f"RT.{rt}/RW.{rw}",
            f"RT {rt}/RW {rw}",
        ])

        kel_names = [
            "Menteng", "Cibodas", "Sukamaju", "Mekarsari", "Cipayung",
            "Kebon Jeruk", "Tebet", "Mampang", "Gondangdia", "Tanjung",
        ]
        kec_names = [
            "Menteng", "Cibodas", "Sukamaju", "Cipayung", "Kebon Jeruk",
            "Tebet", "Mampang", "Gondangdia",
        ]
        kel = random.choice(kel_names)
        kec = random.choice(kec_names)

        return f"{street} No. {no}, {rtrw_format}, Kel. {kel}, Kec. {kec}, {city}, {province}"

    def get_random_existing_customers(self, n, source=None):
        cur = self._conn.cursor()
        if source == 'app':
            where = "WHERE is_app_customer = 1"
        elif source == 'vendor':
            where = "WHERE is_vendor_customer = 1"
        elif source == 'crm':
            where = "WHERE is_crm_customer = 1"
        else:
            where = ""
        cur.execute(f"SELECT * FROM customers {where} ORDER BY RANDOM() LIMIT ?", (n,))
        return [dict(row) for row in cur.fetchall()]

    def get_random_hotel(self, city=None):
        cur = self._conn.cursor()
        if city:
            cur.execute(
                "SELECT * FROM hotels WHERE city LIKE ? ORDER BY RANDOM() LIMIT 1",
                (f"%{city}%",),
            )
        else:
            cur.execute("SELECT * FROM hotels ORDER BY RANDOM() LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else None

    def get_random_airline(self, domestic=True):
        cur = self._conn.cursor()
        dom_val = 1 if domestic else 0
        cur.execute(
            "SELECT * FROM airlines WHERE is_domestic = ? ORDER BY RANDOM() LIMIT 1",
            (dom_val,),
        )
        row = cur.fetchone()
        if row is None and not domestic:
            cur.execute("SELECT * FROM airlines ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
        return dict(row) if row else None

    def get_random_route(self, domestic=True):
        if domestic or random.random() < 0.70:
            return random.choice(DOMESTIC_ROUTES)
        return random.choice(INTERNATIONAL_ROUTES)

    def get_random_experience(self, city=None):
        cur = self._conn.cursor()
        if city:
            cur.execute(
                "SELECT * FROM experiences WHERE city LIKE ? ORDER BY RANDOM() LIMIT 1",
                (f"%{city}%",),
            )
        else:
            cur.execute("SELECT * FROM experiences ORDER BY RANDOM() LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else None

    def get_random_itinerary_hotel_city(self):
        cities = list(TOURIST_CITY_WEIGHTS.keys())
        weights = list(TOURIST_CITY_WEIGHTS.values())
        return random.choices(cities, weights=weights, k=1)[0]

    def update_lifetime_value(self, customer_id, amount_idr):
        cur = self._conn.cursor()
        cur.execute(
            "UPDATE customers SET lifetime_value_idr = lifetime_value_idr + ? WHERE id = ?",
            (amount_idr, customer_id),
        )

        cur.execute("SELECT lifetime_value_idr FROM customers WHERE id = ?", (customer_id,))
        row = cur.fetchone()
        if row:
            ltv = row[0]
            if ltv >= 10000000:
                tier = "gold"
            elif ltv >= 2000000:
                tier = "silver"
            else:
                tier = "basic"
            cur.execute("UPDATE customers SET loyalty_tier = ? WHERE id = ?", (tier, customer_id))

        self._conn.commit()

    def log_day(self, date_str, total_rows, hotel_rows, flight_rows, experience_rows, crm_rows, is_holiday):
        cur = self._conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO generation_log "
            "(date, total_rows, hotel_rows, flight_rows, experience_rows, crm_rows, is_holiday) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date_str, total_rows, hotel_rows, flight_rows, experience_rows, crm_rows, int(is_holiday)),
        )
        self._conn.commit()

    def was_generated(self, date_str):
        cur = self._conn.cursor()
        cur.execute("SELECT 1 FROM generation_log WHERE date = ?", (date_str,))
        return cur.fetchone() is not None

    def close(self):
        self._conn.commit()
        self._conn.close()
