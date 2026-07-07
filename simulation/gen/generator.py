import os
import sys
import random
import json
import csv
import hashlib
import sqlite3

import yaml
import psycopg2
from faker import Faker

_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJ = os.path.dirname(_PARENT)
sys.path.insert(0, os.path.join(_PARENT, 'src'))
sys.path.insert(0, _PARENT)
from world.world import WorldState
from src.id_locales import (
    PROVINCES, CITIES, PAYMENT_METHODS, HOLIDAYS_SEASONAL,
    PHONE_MOBILE_PREFIXES, LANDLINE_AREA_CODES, ID_MONTH_ABBR,
    STORE_NAME_PREFIXES,
)


def _idr_fmt(val):
    """Format integer as Indonesian dot-thousands: 1500000 -> '1.500.000'."""
    s = str(val)
    parts = []
    while len(s) > 3:
        parts.insert(0, s[-3:])
        s = s[:-3]
    parts.insert(0, s)
    return '.'.join(parts)


def _date_dmy(date_str):
    """Convert YYYY-MM-DD to DD/MM/YYYY."""
    y, m, d = date_str.split('-')
    return f"{d}/{m}/{y}"


def _date_ymd_no_sep(date_str):
    """Convert YYYY-MM-DD to YYYYMMDD."""
    return date_str.replace('-', '')


class DailyGenerator:

    def __init__(self, config):
        self.config = config
        world_path = os.path.join(_PROJ, config['world_db_path'])
        self.world = WorldState(world_path)
        self.world.seed_data()
        self.rng = random.Random(config['seed'])
        self.fake = Faker(['id_ID'])
        self.ecom_db_path = os.path.join(_PROJ, config['ecom_db_path'])
        self.pos_csv_dir = os.path.join(_PROJ, config['pos_csv_dir'])

        os.makedirs(self.pos_csv_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.ecom_db_path), exist_ok=True)

        crm_cfg = config['crm_db']
        self.crm_conn = psycopg2.connect(
            host=crm_cfg['host'],
            port=crm_cfg['port'],
            dbname=crm_cfg['db_name'],
            user=crm_cfg['user'],
            password=crm_cfg['password'],
        )
        self.crm_conn.autocommit = False

        self._ecom_db_initialized = False
        self._crm_initialized = False

    # ── public API ──────────────────────────────────────────────

    def generate(self, date_str, holiday_mode=False):
        if self.world.was_generated(date_str):
            return

        seed = self.config['seed'] + int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16) % 999983
        self.rng.seed(seed)
        self.fake.seed_instance(seed)

        volume = self.rng.randint(
            self.config['daily_volume_min'],
            self.config['daily_volume_max'],
        )

        if holiday_mode:
            ecom_count = self.config['ecom_cap']
            pos_count = self.config['pos_cap']
            crm_count = self.config['crm_cap']
        else:
            remaining = volume
            ecom_count = self.rng.randint(0, min(remaining, self.config['ecom_cap']))
            remaining -= ecom_count
            pos_count = self.rng.randint(0, min(remaining, self.config['pos_cap']))
            remaining -= pos_count
            crm_count = self.rng.randint(0, min(remaining, self.config['crm_cap']))

        self._generate_ecom_orders(date_str, ecom_count)
        self._generate_pos_transactions(date_str, pos_count)
        self._generate_crm_data(date_str, crm_count)

        self.world.log_day(date_str, volume, ecom_count, pos_count, crm_count, holiday_mode)

    def close(self):
        self.world.close()
        if hasattr(self, 'crm_conn') and self.crm_conn and not self.crm_conn.closed:
            self.crm_conn.commit()
            self.crm_conn.close()

    # ── e-commerce SQLite ───────────────────────────────────────

    def _init_ecom_db(self):
        if self._ecom_db_initialized:
            return
        self.ecom_conn = sqlite3.connect(self.ecom_db_path)
        self.ecom_conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                order_ts TEXT,
                channel TEXT,
                status TEXT,
                payment_method TEXT,
                currency TEXT DEFAULT 'IDR',
                grand_total_idr INTEGER,
                shipping_fee_idr INTEGER,
                discount_idr INTEGER,
                customer_email TEXT,
                customer_phone TEXT,
                customer_name TEXT,
                customer_address TEXT,
                customer_city_prov TEXT,
                line_items_json TEXT
            )
        """)
        self.ecom_conn.commit()
        self._ecom_db_initialized = True

    def _generate_ecom_orders(self, date_str, count):
        if count <= 0:
            return
        self._init_ecom_db()

        rows = []
        for i in range(count):
            if self.rng.random() < 0.7:
                existings = self.world.get_random_existing_customers(1, source='online')
                if existings and len(existings) > 0:
                    customer = existings[0]
                else:
                    customer = self.world.get_or_create_customer(source='ecom')
            else:
                customer = self.world.get_or_create_customer(source='ecom')

            email = customer.get('email') or ''
            if not email.strip():
                email = self.fake.email()
                email = self._mess_up_email(email) if self.rng.random() < self.config['error_rate'] else email

            phone = customer.get('phone') or self.fake.phone_number()
            if self.rng.random() < self.config['error_rate']:
                phone = self._mess_up_phone(phone)

            name = customer.get('name') or self.fake.name()
            if self.rng.random() < self.config['error_rate']:
                name = self._mess_up_name(name)

            address = customer.get('address') or self.fake.address()
            city_prov = customer.get('city_prov') or self.fake.city()

            order_id = "ORD-{}-{:06d}".format(_date_ymd_no_sep(date_str), i)
            h, m, s = self.rng.randint(6, 23), self.rng.randint(0, 59), self.rng.randint(0, 59)
            order_ts = "{}T{:02d}:{:02d}:{:02d}+07:00".format(date_str, h, m, s)
            channel = self.rng.choice(['web', 'android', 'ios', 'marketplace'])
            status = self.rng.choices(
                ['paid', 'shipped', 'delivered', 'cancelled', 'refunded'],
                weights=[0.1, 0.25, 0.55, 0.05, 0.05],
            )[0]
            payment_method = self.rng.choice([
                'QRIS', 'GoPay', 'OVO', 'DANA', 'ShopeePay', 'LinkAja',
                'BCA', 'Mandiri', 'BNI', 'BRI', 'COD',
            ])

            n_items = self.rng.randint(1, 4)
            products = self.world.get_random_products(n_items)
            line_items = []
            line_sum = 0
            for prod in products:
                qty = self.rng.randint(1, 5)
                unit_price = self._random_idr_amount(prod['base_price_idr'])
                line_items.append({
                    'sku': prod['ecom_sku'] if prod.get('ecom_sku') and prod['ecom_sku'] != prod['sku'] else prod['sku'],
                    'name': prod['name'],
                    'qty': qty,
                    'unit_price_idr': unit_price,
                })
                line_sum += qty * unit_price

            shipping_options = [0, 0, 0, 0, 10000, 15000, 25000, 35000, 50000]
            shipping_fee = self.rng.choice(shipping_options)
            discount = 0 if self.rng.random() < 0.85 else self.rng.randint(5000, 50000)
            grand_total = line_sum + shipping_fee - discount

            if self.rng.random() < 0.001:
                grand_total += self.rng.choice([-100, 100, -50, 50])

            if not email.strip():
                email = 'unknown@unknown.com'

            rows.append((
                order_id, order_ts, channel, status, payment_method, 'IDR',
                max(0, int(grand_total)), shipping_fee, discount,
                email, phone, name, address, city_prov,
                json.dumps(line_items, ensure_ascii=False),
            ))

        cur = self.ecom_conn.cursor()
        cur.executemany("""
            INSERT OR REPLACE INTO orders
            (order_id, order_ts, channel, status, payment_method, currency,
             grand_total_idr, shipping_fee_idr, discount_idr,
             customer_email, customer_phone, customer_name,
             customer_address, customer_city_prov, line_items_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        self.ecom_conn.commit()

    # ── POS CSV ─────────────────────────────────────────────────

    def _build_pos_columns(self):
        drift = int(self.config.get('drift_year', 2024))
        base = ['receipt_no', 'txn_date', 'txn_time']

        if drift >= 2023:
            base.extend(['store_id'])
        base.append('store_name')

        if drift >= 2023:
            base.extend(['kasir_id'])
        base.extend(['customer_phone', 'customer_name', 'customer_address'])

        base.extend(['product_code', 'product_name', 'qty',
                      'unit_price_idr', 'line_total_idr', 'payment_method'])

        if drift >= 2024:
            base.extend(['cashier_shift', 'void_flag'])

        return base

    def _generate_pos_transactions(self, date_str, count):
        if count <= 0:
            return

        cols = self._build_pos_columns()
        date_dmy = _date_dmy(date_str)
        rows = []

        pos_txn_count = count

        for txn_i in range(pos_txn_count):
            store = self.world.get_random_store()
            store_id = store['store_id']
            store_name = store['store_name']

            if self.rng.random() < 0.5:
                existings = self.world.get_random_existing_customers(1, source='pos')
                if existings and len(existings) > 0:
                    customer = existings[0]
                else:
                    customer = self.world.get_or_create_customer(source='pos')
            else:
                customer = self.world.get_or_create_customer(source='pos')

            receipt_no = "REC-{}-{}".format(store_id, self.rng.randint(1000000, 9999999))
            h, m, s = self.rng.randint(6, 23), self.rng.randint(0, 59), self.rng.randint(0, 59)
            txn_time = "{:02d}:{:02d}:{:02d}".format(h, m, s)

            phone = customer.get('phone') or self.fake.phone_number()
            name = customer.get('name') or self.fake.name()
            address = customer.get('address') or ''
            if not address.strip():
                address = self.fake.address()

            if self.rng.random() < self.config['error_rate']:
                phone = self._mess_up_phone(phone)
            if self.rng.random() < self.config['error_rate']:
                name = self._mess_up_name(name)

            payment_method = self.rng.choices(
                ['Cash', 'QRIS', 'Debit BCA', 'Kredit Mandiri', 'GoPay',
                 'DANA', 'ShopeePay', 'OVO'],
                weights=[0.50, 0.20, 0.10, 0.05, 0.05, 0.04, 0.03, 0.03],
            )[0]

            cashier_shift = self.rng.choice(['Pagi', 'Siang', 'Malam'])
            void_roll = self.rng.random()
            if void_roll < 0.95:
                void_flag = 'N'
            elif void_roll < 0.99:
                void_flag = 'TIDAK ADA'
            else:
                void_flag = 'Y'

            n_items = self.rng.randint(1, 3)
            products = self.world.get_random_products(n_items)
            for prod in products:
                qty = self.rng.randint(1, 5)
                unit_price = self._random_idr_amount(prod['base_price_idr'])
                line_total = qty * unit_price

                if self.rng.random() < 0.001:
                    line_total += self.rng.choice([-100, -50, 50, 100])

                unit_price_str = str(unit_price)
                line_total_str = str(max(0, line_total))
                if self.rng.random() < self.config['error_rate']:
                    variant = self.rng.random()
                    if variant < 0.3:
                        unit_price_str = "Rp " + _idr_fmt(int(unit_price))
                        line_total_str = "Rp " + _idr_fmt(int(max(0, line_total)))
                    elif variant < 0.5:
                        unit_price_str = "{},00".format(_idr_fmt(int(unit_price)))
                        line_total_str = "{},00".format(_idr_fmt(int(max(0, line_total))))

                row = {
                    'receipt_no': receipt_no,
                    'txn_date': date_dmy,
                    'txn_time': txn_time,
                    'store_id': store_id,
                    'store_name': store_name,
                    'kasir_id': '',
                    'customer_phone': phone,
                    'customer_name': name,
                    'customer_address': address,
                    'product_code': prod['sku'],
                    'product_name': prod['name'],
                    'qty': qty,
                    'unit_price_idr': unit_price_str,
                    'line_total_idr': line_total_str,
                    'payment_method': payment_method,
                    'cashier_shift': cashier_shift,
                    'void_flag': void_flag,
                }

                if self.rng.random() < self.config['error_rate']:
                    sentinel_types = ['TIDAK ADA', 'N/A', '000-000-0000', '']
                    target_field = self.rng.choice(
                        ['customer_phone', 'customer_name', 'customer_address', 'product_name']
                    )
                    row[target_field] = self.rng.choice(sentinel_types)
                    if target_field == 'customer_phone':
                        phone = row['customer_phone']
                    if target_field == 'customer_name':
                        name = row['customer_name']

                rows.append(row)

                if self.rng.random() < self.config['dupe_rate']:
                    dupe = dict(row)
                    dupe['line_total_idr'] = str(max(0, int(line_total) + self.rng.choice(
                        [-100, -50, -30, -10, -1, 1, 10, 30, 50, 100]
                    )))
                    rows.append(dupe)

        csv_path = os.path.join(self.pos_csv_dir,
                                "sales_{}.csv".format(_date_ymd_no_sep(date_str)))

        with open(csv_path, 'w', encoding='iso-8859-1', newline='') as f:
            header = cols
            header_line = ','.join(header) + '\n'
            f.write(header_line)

            for row_dict in rows:
                vals = [str(row_dict.get(c, '')) for c in cols]

                inject_comma = self.rng.random() < 0.005
                if inject_comma and 'customer_address' in cols:
                    addr_idx = cols.index('customer_address')
                    orig = vals[addr_idx]
                    if ',' not in orig and len(orig) > 10:
                        vals[addr_idx] = orig.replace(' ', ', ', 2)

                    safe = all(',' not in str(v) for v in vals)
                    if safe or inject_comma:
                        f.write(','.join(str(v) for v in vals) + '\n')
                        continue

                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                writer.writerow(vals)

    # ── CRM Postgres ────────────────────────────────────────────

    def _init_crm(self):
        if self._crm_initialized:
            return
        cur = self.crm_conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id BIGSERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                preferred_contact TEXT DEFAULT 'email',
                lifetime_value_idr BIGINT DEFAULT 0,
                address TEXT,
                city_prov TEXT,
                is_vip BOOLEAN DEFAULT FALSE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
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
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                interaction_id BIGSERIAL PRIMARY KEY,
                ticket_id BIGINT REFERENCES tickets(ticket_id),
                agent_id TEXT,
                agent_name TEXT,
                ts TIMESTAMP DEFAULT NOW(),
                direction TEXT,
                channel TEXT,
                note TEXT
            )
        """)
        self.crm_conn.commit()
        self._crm_initialized = True

    def _upsert_crm_customer(self, world_customer):
        cur = self.crm_conn.cursor()
        email = world_customer.get('email') or self.fake.email()
        phone = world_customer.get('phone') or self.fake.phone_number()
        name = world_customer.get('name') or self.fake.name()
        address = world_customer.get('address') or self.fake.address()
        city_prov = world_customer.get('city_prov') or self.fake.city()

        cur.execute(
            "SELECT customer_id FROM customers WHERE email = %s OR phone = %s",
            (email, phone),
        )
        row = cur.fetchone()

        if row:
            cid = row[0]
            cur.execute(
                "UPDATE customers SET full_name=%s, address=%s, city_prov=%s, updated_at=NOW() WHERE customer_id=%s",
                (name, address, city_prov, cid),
            )
        else:
            cur.execute(
                "INSERT INTO customers (email, phone, full_name, address, city_prov) VALUES (%s, %s, %s, %s, %s) RETURNING customer_id",
                (email, phone, name, address, city_prov),
            )
            cid = cur.fetchone()[0]

        self.crm_conn.commit()
        return cid, email, phone, name

    _TICKET_SUBJECTS = [
        "Paket belum sampai",
        "Permintaan pengembalian dana",
        "Barang rusak - mohon ganti rugi",
        "Ongkir terlalu mahal",
        "Status pesanan tidak update",
        "Pembayaran gagal",
        "Salah kirim produk",
        "Akun tidak bisa login",
        "Voucher tidak berlaku",
    ]

    _TICKET_BODIES = [
        "Tolong dicek ya mob, udah 2 hari paketnya ga sampe",
        "dt-05-rt-10 jalan kelapa dua no 17",
        "Barangnya beda sama yang difoto. Saya mau refund",
        "Sudah transfer tapi status masih pending",
        "Kak vouchernya gabisa dipake katanya expired",
        "Paket saya diterima sudah dalam keadaan rusak. Minta ganti rugi",
        "Kenapa ongkirnya mahal banget? Padahal masih satu kota",
        "Tolong bantu lacak paket saya, nomor resi katanya ga valid",
        "Saya salah alamat waktu checkout, bisa diubah?",
    ]

    _TICKET_STATUSES = ['open', 'pending_cust', 'waiting_3rd_party', 'resolved', 'closed', 'escalated']

    _INTERACTION_NOTES = [
        "sudah dijelaskan via email",
        "menunggu respon dari customer",
        "produk dikirim ulang 3 Juli",
        "customer minta nomor resi",
        "dijadwalkan pengambilan barang besok",
        "menunggu konfirmasi dari gudang",
        "sudah kirim link refund",
        "customer sudah konfirmasi terima barang",
        "voucher sudah dikirim ulang via email",
        "eskalasi ke supervisor",
    ]

    def _generate_crm_data(self, date_str, ticket_count):
        if ticket_count <= 0:
            return
        self._init_crm()

        for _ in range(ticket_count):
            if self.rng.random() < 0.7:
                existings = self.world.get_random_existing_customers(1, source='crm')
                if existings and len(existings) > 0:
                    customer = existings[0]
                else:
                    customer = self.world.get_or_create_customer(source='crm')
            else:
                customer = self.world.get_or_create_customer(source='crm')

            cid, c_email, c_phone, c_name = self._upsert_crm_customer(customer)

            subject = self.rng.choice(self._TICKET_SUBJECTS)
            body = self.rng.choice(self._TICKET_BODIES)
            t_status = self.rng.choices(self._TICKET_STATUSES,
                                        weights=[0.3, 0.2, 0.1, 0.25, 0.1, 0.05])[0]
            priority = self.rng.choices(
                ['normal', 'high', 'low', 'urgent'],
                weights=[0.70, 0.20, 0.05, 0.05],
            )[0]
            channel = self.rng.choices(
                ['email', 'whatsapp', 'phone', 'web_form', 'instagram', 'twitter'],
                weights=[0.40, 0.30, 0.20, 0.05, 0.03, 0.02],
            )[0]
            category = self.rng.choices(
                ['shipping', 'refund', 'product_quality', 'payment', 'account', 'other'],
                weights=[0.30, 0.20, 0.15, 0.15, 0.10, 0.10],
            )[0]

            snapshot = c_email
            if self.rng.random() < 0.15:
                if customer.get('alternate_email') and customer['alternate_email'].strip():
                    snapshot = customer['alternate_email']
                else:
                    snapshot = self.fake.email()

            cur = self.crm_conn.cursor()
            h, m, s = self.rng.randint(8, 21), self.rng.randint(0, 59), self.rng.randint(0, 59)
            created_ts = "{} {:02d}:{:02d}:{:02d}".format(date_str, h, m, s)

            cur.execute("""
                INSERT INTO tickets
                (customer_id, subject, body, status, priority, channel,
                 created_at, category, contact_email_snapshot)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING ticket_id
            """, (cid, subject, body, t_status, priority, channel,
                  created_ts, category, snapshot))
            ticket_id = cur.fetchone()[0]
            self.crm_conn.commit()

            n_interactions = self.rng.randint(1, 3)
            for ix in range(n_interactions):
                direction = 'inbound' if ix == 0 else 'outbound'
                if ix > 0 and self.rng.random() < 0.3:
                    direction = 'inbound'
                agent_name = self.fake.name()
                agent_id = "AGT-{:04d}".format(self.rng.randint(1, 9999))
                note = self.rng.choice(self._INTERACTION_NOTES)

                h2, m2, s2 = self.rng.randint(0, 23), self.rng.randint(0, 59), self.rng.randint(0, 59)
                int_ts = "{} {:02d}:{:02d}:{:02d}".format(date_str, h2, m2, s2)
                int_channel = channel if self.rng.random() < 0.6 else self.rng.choice(
                    ['email', 'whatsapp', 'phone', 'chat']
                )

                cur.execute("""
                    INSERT INTO interactions
                    (ticket_id, agent_id, agent_name, ts, direction, channel, note)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (ticket_id, agent_id, agent_name, int_ts, direction, int_channel, note))
            self.crm_conn.commit()

    # ── messiness helpers ───────────────────────────────────────

    def _mess_up_phone(self, phone_str):
        if not phone_str or len(str(phone_str)) < 3:
            return phone_str
        phone = str(phone_str).strip()
        roll = self.rng.random()
        if roll < 0.02:
            return '000-000-0000'
        if roll < 0.04:
            return ''
        if roll < 0.50:
            cleaned = phone.replace(' ', '').replace('-', '').replace('+', '')
            if cleaned.startswith('62'):
                cleaned = '0' + cleaned[2:]
            elif not cleaned.startswith('0'):
                cleaned = '0' + cleaned
            if self.rng.random() < 0.5:
                return cleaned[:4] + '-' + cleaned[4:8] + '-' + cleaned[8:]
            else:
                return cleaned
        if roll < 0.75:
            cleaned = phone.replace(' ', '').replace('-', '').replace('+', '')
            if cleaned.startswith('62'):
                cleaned = '0' + cleaned[2:]
            if self.rng.random() < 0.5:
                return cleaned[:4] + '-' + cleaned[4:8] + ' ' + cleaned[8:]
            return cleaned
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
            if 'gmail.com' in domain:
                domain = self.rng.choice(['gnail.com', 'gmaill.com', 'gmail.com'])
            elif 'yahoo.co.id' in domain:
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

    def _random_idr_amount(self, base_price, noise_pct=0.1):
        noise = 1.0 + self.rng.uniform(-noise_pct, noise_pct)
        raw = base_price * noise
        return max(100, int(round(raw / 100.0) * 100))
