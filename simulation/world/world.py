import os
import sys
import sqlite3
import random
from faker import Faker

_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PARENT, 'src'))
from id_locales import PROVINCES, CITIES, STORE_NAME_PREFIXES

_FAKE = Faker('id_ID')


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
                name TEXT,
                email TEXT,
                alternate_email TEXT,
                phone TEXT,
                alternate_phone TEXT,
                address TEXT,
                city_prov TEXT,
                is_online_customer INTEGER DEFAULT 0,
                is_pos_customer INTEGER DEFAULT 0,
                is_crm_customer INTEGER DEFAULT 0,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE,
                name TEXT,
                category TEXT,
                base_price_idr INTEGER,
                ecom_sku TEXT
            );

            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT UNIQUE,
                store_name TEXT,
                city TEXT,
                prov TEXT
            );

            CREATE TABLE IF NOT EXISTS generation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                total_rows INTEGER,
                ecom_rows INTEGER,
                pos_rows INTEGER,
                crm_rows INTEGER,
                is_holiday INTEGER DEFAULT 0
            );
        """)
        self._conn.commit()

    def seed_data(self):
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] > 0:
            return
        cur.execute("SELECT COUNT(*) FROM stores")
        if cur.fetchone()[0] > 0:
            return

        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            products = [
                ("Kopi Arabika 250g", "Kopi & Teh", 78000, "SKU-KOP-001"),
                ("Gula Aren 500g", "Sembako", 25000, "SKU-SEM-001"),
                ("Beras Ramos 5kg", "Sembako", 68500, "SKU-SEM-002"),
                ("Minyak Goreng Bimoli 2L", "Sembako", 38000, "SKU-SEM-003"),
                ("Mie Instan Indomie Goreng", "Sembako", 3500, "SKU-SEM-004"),
                ("Kecap Bango 275ml", "Sembako", 12000, "SKU-SEM-005"),
                ("Sikat Gigi Formula", "Perlengkapan Rumah", 8500, "SKU-PRL-001"),
                ("Kue Lebaran Nastar", "Kue & Roti", 45000, "SKU-KUR-001"),
                ("Sarung Wadimor Premium", "Pakaian", 95000, "SKU-PAK-001"),
                ("Mukena Travel", "Pakaian", 120000, "SKU-PAK-002"),
                ("Baju Koko Anak", "Pakaian", 65000, "SKU-PAK-003"),
                ("Peci Songkok Hitam", "Pakaian", 35000, "SKU-PAK-004"),
                ("Lilin Aromaterapi", "Perlengkapan Rumah", 18000, "SKU-PRL-002"),
                ("Teh Celup Sariwangi", "Kopi & Teh", 8000, "SKU-KOP-002"),
                ("Kopi Kapal Api Spc Mix", "Kopi & Teh", 3000, "SKU-KOP-003"),
                ("Sabun Mandi Lifebuoy", "Perlengkapan Rumah", 5500, "SKU-PRL-003"),
                ("Shampoo Sunsilk 170ml", "Perlengkapan Rumah", 12500, "SKU-PRL-004"),
                ("Rinso Deterjen 1.8kg", "Perlengkapan Rumah", 23000, "SKU-PRL-005"),
                ("Paracetamol 500mg Strip", "Obat-obatan", 3000, "SKU-OBT-001"),
                ("Flashdisk 32GB Sandisk", "Elektronik", 55000, "SKU-ELK-001"),
            ]
            for name, cat, price, sku in products:
                ecom_sku = sku + '-EC' if cat not in ('Sembako', 'Kopi & Teh', 'Obat-obatan') else sku
                cur.execute(
                    "INSERT INTO products (sku, name, category, base_price_idr, ecom_sku) VALUES (?, ?, ?, ?, ?)",
                    (sku, name, cat, price, ecom_sku),
                )

        cur.execute("SELECT COUNT(*) FROM stores")
        if cur.fetchone()[0] == 0:
            stores = [
                ("TKJ-CGR-01", "Toko Sejahtera Ceger", "Jakarta Timur", "DKI Jakarta"),
                ("BDG-CBL-01", "Toko Keluarga Cimahi", "Cimahi", "Jawa Barat"),
                ("SBY-RGK-01", "CV Makmur Jaya", "Surabaya", "Jawa Timur"),
                ("MDN-KSN-01", "Warung Bu Endang", "Medan", "Sumatera Utara"),
                ("DPS-KTA-01", "UD Karya Abadi", "Badung", "Bali"),
                ("YGY-DNJ-01", "Toko Sidomuncul", "Yogyakarta", "Daerah Istimewa Yogyakarta"),
                ("SMG-GAJ-01", "Kios Barokah", "Semarang", "Jawa Tengah"),
                ("TGR-CBD-01", "Toko Bangunan Jaya", "Tangerang", "Banten"),
                ("MKS-PNJ-01", "CV Sumber Rezeki", "Makassar", "Sulawesi Selatan"),
                ("BLP-DAM-01", "Warung Sederhana", "Balikpapan", "Kalimantan Timur"),
            ]
            for sid, name, city, prov in stores:
                cur.execute(
                    "INSERT INTO stores (store_id, store_name, city, prov) VALUES (?, ?, ?, ?)",
                    (sid, name, city, prov),
                )

        self._conn.commit()

    def get_random_product(self):
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM products ORDER BY RANDOM() LIMIT 1")
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)

    def get_random_products(self, n):
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM products ORDER BY RANDOM() LIMIT ?", (n,))
        return [dict(row) for row in cur.fetchall()]

    def get_or_create_customer(self, phone=None, email=None, name=None, address=None, city_prov=None, source='pos'):
        cur = self._conn.cursor()

        existing = None
        if phone is not None and phone.strip():
            cur.execute("SELECT * FROM customers WHERE phone = ? OR alternate_phone = ?", (phone, phone))
            existing = cur.fetchone()
        if existing is None and email is not None and email.strip():
            cur.execute(
                "SELECT * FROM customers WHERE email = ? OR alternate_email = ? COLLATE NOCASE",
                (email, email),
            )
            existing = cur.fetchone()

        if existing is not None:
            cust = dict(existing)
            if source == 'pos':
                cur.execute("UPDATE customers SET is_pos_customer = 1 WHERE id = ?", (cust['id'],))
                cust['is_pos_customer'] = 1
            elif source == 'ecom':
                cur.execute("UPDATE customers SET is_online_customer = 1 WHERE id = ?", (cust['id'],))
                cust['is_online_customer'] = 1
            elif source == 'crm':
                cur.execute("UPDATE customers SET is_crm_customer = 1 WHERE id = ?", (cust['id'],))
                cust['is_crm_customer'] = 1
            self._conn.commit()
            return cust

        if name is None:
            name = _FAKE.name()
        if phone is None:
            phone = _FAKE.phone_number()
        if email is None:
            email = _FAKE.email()
        if address is None:
            address = _FAKE.address()
        if city_prov is None:
            city_prov = _FAKE.city()

        now = _FAKE.date_time_this_decade().isoformat()

        is_pos = 1 if source == 'pos' else 0
        is_ecom = 1 if source == 'ecom' else 0
        is_crm = 1 if source == 'crm' else 0

        cur.execute(
            """INSERT INTO customers
               (canonical_name, name, email, phone, address, city_prov,
                is_online_customer, is_pos_customer, is_crm_customer, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, name, email, phone, address, city_prov, is_ecom, is_pos, is_crm, now),
        )
        self._conn.commit()

        cur.execute("SELECT * FROM customers WHERE id = ?", (cur.lastrowid,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_random_existing_customers(self, n, source=None):
        cur = self._conn.cursor()
        if source == 'online':
            where = "WHERE is_online_customer = 1"
        elif source == 'pos':
            where = "WHERE is_pos_customer = 1"
        else:
            where = ""
        cur.execute(f"SELECT * FROM customers {where} ORDER BY RANDOM() LIMIT ?", (n,))
        return [dict(row) for row in cur.fetchall()]

    def get_random_store(self):
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM stores ORDER BY RANDOM() LIMIT 1")
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)

    def log_day(self, date_str, total, ecom, pos, crm, is_holiday):
        cur = self._conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO generation_log (date, total_rows, ecom_rows, pos_rows, crm_rows, is_holiday) VALUES (?, ?, ?, ?, ?, ?)",
            (date_str, total, ecom, pos, crm, int(is_holiday)),
        )
        self._conn.commit()

    def was_generated(self, date_str):
        cur = self._conn.cursor()
        cur.execute("SELECT 1 FROM generation_log WHERE date = ?", (date_str,))
        return cur.fetchone() is not None

    def close(self):
        self._conn.commit()
        self._conn.close()
