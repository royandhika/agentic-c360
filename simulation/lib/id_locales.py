"""Indonesian travel-domain locale reference data for the WanderFuel simulator.

Use ``Faker('id_ID')`` separately for name, address and phone string generation;
this module supplies static lookup tables that Faker does not expose:
province/city lists, postcode prefixes, hotel/airline/airport catalogues,
domestic flight routes, experience catalogue, travel-domain payment methods,
seasonal holidays with uplift factors, CRM ticket templates in Bahasa Indonesia,
and support agent names.
"""

# ──────────────────────────────────────────────────────────────────────
# PROVINCES
# ──────────────────────────────────────────────────────────────────────
PROVINCES = [
    ("Nanggroe Aceh Darussalam", "AC", "Banda Aceh"),
    ("Sumatera Utara", "SU", "Medan"),
    ("Sumatera Barat", "SB", "Padang"),
    ("Riau", "RI", "Pekanbaru"),
    ("Jambi", "JA", "Jambi"),
    ("Sumatera Selatan", "SS", "Palembang"),
    ("Bengkulu", "BE", "Bengkulu"),
    ("Lampung", "LA", "Bandar Lampung"),
    ("Kepulauan Bangka Belitung", "BB", "Pangkalpinang"),
    ("Kepulauan Riau", "KR", "Tanjungpinang"),
    ("DKI Jakarta", "JK", "Jakarta"),
    ("Jawa Barat", "JB", "Bandung"),
    ("Jawa Tengah", "JT", "Semarang"),
    ("Daerah Istimewa Yogyakarta", "YO", "Yogyakarta"),
    ("Jawa Timur", "JI", "Surabaya"),
    ("Banten", "BT", "Serang"),
    ("Bali", "BA", "Denpasar"),
    ("Nusa Tenggara Barat", "NB", "Mataram"),
    ("Nusa Tenggara Timur", "NT", "Kupang"),
    ("Kalimantan Barat", "KB", "Pontianak"),
    ("Kalimantan Tengah", "KT", "Palangkaraya"),
    ("Kalimantan Selatan", "KS", "Banjarmasin"),
    ("Kalimantan Timur", "KI", "Samarinda"),
    ("Kalimantan Utara", "KU", "Tanjung Selor"),
    ("Sulawesi Utara", "SA", "Manado"),
    ("Sulawesi Tengah", "ST", "Palu"),
    ("Sulawesi Selatan", "SN", "Makassar"),
    ("Sulawesi Tenggara", "SG", "Kendari"),
    ("Gorontalo", "GO", "Gorontalo"),
    ("Sulawesi Barat", "SR", "Mamuju"),
    ("Maluku", "MA", "Ambon"),
    ("Maluku Utara", "MU", "Sofifi"),
    ("Papua", "PA", "Jayapura"),
    ("Papua Barat", "PB", "Manokwari"),
    ("Papua Selatan", "PS", "Merauke"),
    ("Papua Tengah", "PT", "Nabire"),
    ("Papua Pegunungan", "PP", "Wamena"),
    ("Papua Barat Daya", "PD", "Sorong"),
]

# ──────────────────────────────────────────────────────────────────────
# INDONESIAN_CITIES  (travel-relevant cities per province)
# ──────────────────────────────────────────────────────────────────────
INDONESIAN_CITIES = {
    "Nanggroe Aceh Darussalam": [("Banda Aceh", "Kota"), ("Lhokseumawe", "Kota"), ("Sabang", "Kota")],
    "Sumatera Utara": [("Medan", "Kota"), ("Pematangsiantar", "Kota"), ("Berastagi", "Kota"),
                       ("Parapat", "Kota"), ("Samosir", "Kabupaten")],
    "Sumatera Barat": [("Padang", "Kota"), ("Bukittinggi", "Kota"), ("Payakumbuh", "Kota"),
                       ("Mentawai", "Kabupaten")],
    "Riau": [("Pekanbaru", "Kota"), ("Dumai", "Kota")],
    "Jambi": [("Jambi", "Kota")],
    "Sumatera Selatan": [("Palembang", "Kota"), ("Prabumulih", "Kota")],
    "Bengkulu": [("Bengkulu", "Kota")],
    "Lampung": [("Bandar Lampung", "Kota"), ("Metro", "Kota"), ("Kalianda", "Kabupaten")],
    "Kepulauan Bangka Belitung": [("Pangkalpinang", "Kota"), ("Tanjung Pandan", "Kota")],
    "Kepulauan Riau": [("Tanjungpinang", "Kota"), ("Batam", "Kota"), ("Bintan", "Kabupaten")],
    "DKI Jakarta": [
        ("Jakarta Pusat", "Kota"), ("Jakarta Selatan", "Kota"),
        ("Jakarta Barat", "Kota"), ("Jakarta Timur", "Kota"),
        ("Jakarta Utara", "Kota"),
    ],
    "Jawa Barat": [
        ("Bandung", "Kota"), ("Bogor", "Kota"), ("Bekasi", "Kota"),
        ("Cimahi", "Kota"), ("Depok", "Kota"), ("Lembang", "Kota"),
        ("Puncak", "Kota"), ("Ciwidey", "Kota"),
    ],
    "Jawa Tengah": [
        ("Semarang", "Kota"), ("Surakarta", "Kota"), ("Magelang", "Kota"),
        ("Tegal", "Kota"), ("Pekalongan", "Kota"), ("Salatiga", "Kota"),
    ],
    "Daerah Istimewa Yogyakarta": [
        ("Yogyakarta", "Kota"), ("Sleman", "Kabupaten"),
        ("Bantul", "Kabupaten"), ("Kulon Progo", "Kabupaten"),
    ],
    "Jawa Timur": [
        ("Surabaya", "Kota"), ("Malang", "Kota"), ("Batu", "Kota"),
        ("Kediri", "Kota"), ("Banyuwangi", "Kota"), ("Probolinggo", "Kota"),
    ],
    "Banten": [
        ("Tangerang", "Kota"), ("Tangerang Selatan", "Kota"),
        ("Serang", "Kota"), ("Cilegon", "Kota"), ("Anyer", "Kota"),
    ],
    "Bali": [
        ("Denpasar", "Kota"), ("Kuta", "Kota"), ("Seminyak", "Kota"),
        ("Ubud", "Kota"), ("Canggu", "Kota"), ("Nusa Dua", "Kota"),
        ("Sanur", "Kota"), ("Jimbaran", "Kota"), ("Uluwatu", "Kota"),
        ("Amed", "Kota"), ("Lovina", "Kota"), ("Sukawati", "Kabupaten"),
    ],
    "Nusa Tenggara Barat": [
        ("Mataram", "Kota"), ("Lombok Barat", "Kabupaten"),
        ("Lombok Tengah", "Kabupaten"), ("Senggigi", "Kota"),
        ("Gili Trawangan", "Kota"), ("Kuta Lombok", "Kota"),
    ],
    "Nusa Tenggara Timur": [
        ("Kupang", "Kota"), ("Labuan Bajo", "Kota"),
        ("Ende", "Kabupaten"), ("Maumere", "Kota"), ("Ruteng", "Kabupaten"),
        ("Waingapu", "Kota"), ("Komodo", "Kabupaten"),
    ],
    "Kalimantan Barat": [("Pontianak", "Kota"), ("Singkawang", "Kota")],
    "Kalimantan Tengah": [("Palangkaraya", "Kota"), ("Tanjung Puting", "Kabupaten")],
    "Kalimantan Selatan": [("Banjarmasin", "Kota"), ("Banjarbaru", "Kota")],
    "Kalimantan Timur": [("Samarinda", "Kota"), ("Balikpapan", "Kota"), ("Derawan", "Kabupaten")],
    "Kalimantan Utara": [("Tarakan", "Kota"), ("Malinau", "Kabupaten")],
    "Sulawesi Utara": [("Manado", "Kota"), ("Bunaken", "Kabupaten"), ("Tomohon", "Kota")],
    "Sulawesi Tengah": [("Palu", "Kota"), ("Tentena", "Kota"), ("Luwuk", "Kabupaten")],
    "Sulawesi Selatan": [("Makassar", "Kota"), ("Parepare", "Kota"), ("Tana Toraja", "Kabupaten")],
    "Sulawesi Tenggara": [("Kendari", "Kota"), ("Wakatobi", "Kabupaten")],
    "Gorontalo": [("Gorontalo", "Kota")],
    "Sulawesi Barat": [("Mamuju", "Kabupaten")],
    "Maluku": [("Ambon", "Kota"), ("Tual", "Kota"), ("Banda Neira", "Kota")],
    "Maluku Utara": [("Ternate", "Kota"), ("Tidore", "Kota"), ("Morotai", "Kabupaten")],
    "Papua": [("Jayapura", "Kota"), ("Wamena", "Kota"), ("Sentani", "Kota")],
    "Papua Barat": [("Manokwari", "Kabupaten"), ("Raja Ampat", "Kabupaten")],
    "Papua Selatan": [("Merauke", "Kabupaten")],
    "Papua Tengah": [("Nabire", "Kabupaten"), ("Timika", "Kota")],
    "Papua Pegunungan": [("Jayawijaya", "Kabupaten")],
    "Papua Barat Daya": [("Sorong", "Kota"), ("Waisai", "Kota")],
}

# ──────────────────────────────────────────────────────────────────────
# POSTAL_PREFIXES
# ──────────────────────────────────────────────────────────────────────
POSTAL_PREFIXES = {
    "Nanggroe Aceh Darussalam": ["23", "24"],
    "Sumatera Utara": ["20", "21", "22"],
    "Sumatera Barat": ["25", "26", "27"],
    "Riau": ["28"],
    "Jambi": ["36", "37"],
    "Sumatera Selatan": ["30", "31", "32", "33"],
    "Bengkulu": ["38"],
    "Lampung": ["34", "35"],
    "Kepulauan Bangka Belitung": ["33"],
    "Kepulauan Riau": ["29"],
    "DKI Jakarta": ["10", "11", "12", "13"],
    "Jawa Barat": ["16", "40", "41", "42", "43", "45", "46"],
    "Jawa Tengah": ["50", "51", "52", "53", "56", "57", "58", "59"],
    "Daerah Istimewa Yogyakarta": ["55"],
    "Jawa Timur": ["60", "61", "62", "63", "64", "67", "68", "69"],
    "Banten": ["15", "17"],
    "Bali": ["80", "82"],
    "Nusa Tenggara Barat": ["83"],
    "Nusa Tenggara Timur": ["85", "86"],
    "Kalimantan Barat": ["78", "79"],
    "Kalimantan Tengah": ["73"],
    "Kalimantan Selatan": ["70", "71", "72"],
    "Kalimantan Timur": ["75", "76"],
    "Kalimantan Utara": ["77"],
    "Sulawesi Utara": ["95"],
    "Sulawesi Tengah": ["94"],
    "Sulawesi Selatan": ["90", "91", "92"],
    "Sulawesi Tenggara": ["93"],
    "Gorontalo": ["96"],
    "Sulawesi Barat": ["91"],
    "Maluku": ["97"],
    "Maluku Utara": ["97"],
    "Papua": ["99"],
    "Papua Barat": ["98"],
    "Papua Selatan": ["99"],
    "Papua Tengah": ["98"],
    "Papua Pegunungan": ["99"],
    "Papua Barat Daya": ["98"],
}

# ──────────────────────────────────────────────────────────────────────
# PHONE_MOBILE_PREFIXES
# ──────────────────────────────────────────────────────────────────────
PHONE_MOBILE_PREFIXES = [
    "0811", "0812", "0813", "0821", "0822", "0823",
    "0852", "0853", "0854", "0855", "0856", "0857", "0858", "0859",
    "0814", "0815", "0816",
    "0817", "0818", "0819",
    "0831", "0832", "0833", "0834", "0835", "0836", "0837", "0838",
    "0881", "0882", "0883", "0884", "0885", "0886", "0887", "0888", "0889",
    "0894", "0895", "0896", "0897", "0898", "0899",
]

MOBILE_PREFIXES_BY_CARRIER = {
    "Telkomsel": ["0811", "0812", "0813", "0821", "0822", "0823",
                  "0852", "0853", "0854", "0855", "0856", "0857", "0858", "0859"],
    "Indosat": ["0814", "0815", "0816", "0855", "0858"],
    "XL": ["0817", "0818", "0819"],
    "Axis": ["0831", "0832", "0833", "0834", "0835", "0836", "0837", "0838"],
    "Smartfren": ["0881", "0882", "0883", "0884", "0885", "0886", "0887", "0888", "0889"],
    "Three": ["0894", "0895", "0896", "0897", "0898", "0899"],
}

# ──────────────────────────────────────────────────────────────────────
# LANDLINE_AREA_CODES
# ──────────────────────────────────────────────────────────────────────
LANDLINE_AREA_CODES = {
    "21": "Jakarta",
    "22": "Bandung",
    "231": "Medan",
    "31": "Surabaya",
    "32": "Malang",
    "24": "Padang",
    "25": "Bogor",
    "26": "Bekasi",
    "29": "Tangerang",
    "34": "Yogyakarta",
    "35": "Madiun/Kediri",
    "40": "Palembang",
    "41": "Bengkulu",
    "42": "Bandar Lampung",
    "48": "Jambi",
    "49": "Pekanbaru",
    "50": "Semarang",
    "53": "Manado",
    "61": "Pontianak",
    "62": "Banjarmasin",
    "63": "Samarinda",
    "65": "Makassar",
    "70": "Kendari",
    "71": "Palu",
    "72": "Gorontalo",
    "361": "Denpasar",
    "271": "Solo",
    "511": "Banjarmasin",
    "543": "Balikpapan",
    "370": "Mataram",
    "380": "Kupang",
    "411": "Makassar kode lama",
}

# ──────────────────────────────────────────────────────────────────────
# HOTEL_NAMES  (hotel_name, city, star_rating, base_price_per_night_idr, chain_name)
# ──────────────────────────────────────────────────────────────────────
HOTEL_NAMES = [
    ("Grand Hyatt Jakarta", "Jakarta", 5, 3200000, "Hyatt"),
    ("Hotel Indonesia Kempinski", "Jakarta", 5, 4500000, "Kempinski"),
    ("The Ritz-Carlton Jakarta", "Jakarta", 5, 3800000, "Ritz-Carlton"),
    ("Aryaduta Jakarta", "Jakarta", 4, 950000, "Aryaduta"),
    ("Hotel Santika Premiere Jakarta", "Jakarta", 4, 850000, "Santika"),
    ("Ibis Jakarta Tamarin", "Jakarta", 3, 450000, "Ibis"),
    ("Favehotel LTC Glodok", "Jakarta", 3, 350000, "Favehotel"),

    ("Padma Resort Legian", "Bali", 5, 3500000, "Padma"),
    ("Alila Ubud", "Bali", 5, 4200000, "Alila"),
    ("The Mulia Bali", "Bali", 5, 5000000, "Mulia"),
    ("Ayana Resort Jimbaran", "Bali", 5, 4800000, "Ayana"),
    ("Grand Hyatt Bali", "Bali", 5, 2800000, "Hyatt"),
    ("Hard Rock Hotel Bali", "Bali", 4, 1500000, "Hard Rock"),
    ("Swiss-Belhotel Rainforest Kuta", "Bali", 4, 650000, "Swiss-Belhotel"),
    ("Aston Kuta Hotel", "Bali", 4, 700000, "Aston"),
    ("KU DE TA Suites Seminyak", "Bali", 5, 3800000, "Independent"),
    ("Amnaya Resort Kuta", "Bali", 4, 900000, "Independent"),
    ("The Jayakarta Bali", "Bali", 3, 500000, "Jayakarta"),

    ("Hotel Tentrem Yogyakarta", "Yogyakarta", 5, 2200000, "Independent"),
    ("Royal Ambarrukmo Yogyakarta", "Yogyakarta", 5, 1800000, "Independent"),
    ("Melia Purosani Yogyakarta", "Yogyakarta", 4, 800000, "Melia"),
    ("Novotel Yogyakarta", "Yogyakarta", 4, 750000, "Novotel"),
    ("Grand Aston Yogyakarta", "Yogyakarta", 4, 700000, "Aston"),
    ("Ibis Styles Yogyakarta", "Yogyakarta", 3, 400000, "Ibis"),

    ("Hotel Santika Premiere Surabaya", "Surabaya", 4, 800000, "Santika"),
    ("JW Marriott Surabaya", "Surabaya", 5, 2000000, "Marriott"),
    ("Sheraton Surabaya", "Surabaya", 5, 1800000, "Sheraton"),
    ("Hotel Majapahit Surabaya", "Surabaya", 4, 900000, "Independent"),
    ("Ibis Surabaya City Center", "Surabaya", 3, 380000, "Ibis"),

    ("Swiss-Belhotel Bandung", "Bandung", 4, 750000, "Swiss-Belhotel"),
    ("GH Universal Hotel Bandung", "Bandung", 4, 850000, "Independent"),
    ("Padma Hotel Bandung", "Bandung", 5, 2500000, "Padma"),
    ("Hilton Bandung", "Bandung", 5, 2200000, "Hilton"),
    ("Zodiak Bandung", "Bandung", 3, 350000, "Independent"),
    ("Ibis Bandung Trans Studio", "Bandung", 3, 420000, "Ibis"),

    ("The Jayakarta Lombok", "Lombok", 4, 750000, "Jayakarta"),
    ("Katamaran Hotel Senggigi", "Lombok", 5, 2000000, "Independent"),
    ("Novotel Lombok Resort", "Lombok", 4, 1200000, "Novotel"),
    ("Jeeva Klui Resort", "Lombok", 4, 950000, "Independent"),
    ("Pearl of Trawangan", "Lombok", 3, 500000, "Independent"),

    ("Bintang Flores Hotel Labuan Bajo", "Labuan Bajo", 4, 1100000, "Independent"),
    ("Plataran Komodo Resort", "Labuan Bajo", 5, 4500000, "Plataran"),
    ("Loccal Collection Hotel Labuan Bajo", "Labuan Bajo", 3, 600000, "Independent"),
    ("Ayana Komodo Waecicu", "Labuan Bajo", 5, 4800000, "Ayana"),

    ("Aston Makassar", "Makassar", 4, 700000, "Aston"),
    ("Hotel Santika Makassar", "Makassar", 4, 650000, "Santika"),
    ("Swiss-Belinn Panakkukang", "Makassar", 3, 400000, "Swiss-Belhotel"),

    ("Novotel Manado", "Manado", 4, 800000, "Novotel"),
    ("Aston Manado", "Manado", 4, 650000, "Aston"),

    ("Grand Mercure Medan Angkasa", "Medan", 5, 1200000, "Mercure"),
    ("Hotel Santika Premiere Medan", "Medan", 4, 700000, "Santika"),
    ("Aryaduta Medan", "Medan", 4, 750000, "Aryaduta"),

    ("Hotel Santika Premiere Semarang", "Semarang", 4, 650000, "Santika"),
    ("Novotel Semarang", "Semarang", 4, 700000, "Novotel"),
]

# ──────────────────────────────────────────────────────────────────────
# HOTEL_CHAINS  chain_name -> list of hotel names
# ──────────────────────────────────────────────────────────────────────
HOTEL_CHAINS = {
    "Santika": ["Hotel Santika Premiere Jakarta", "Hotel Santika Premiere Surabaya",
                "Hotel Santika Makassar", "Hotel Santika Premiere Medan",
                "Hotel Santika Premiere Semarang"],
    "Swiss-Belhotel": ["Swiss-Belhotel Rainforest Kuta", "Swiss-Belhotel Bandung",
                       "Swiss-Belinn Panakkukang"],
    "Aston": ["Aston Kuta Hotel", "Grand Aston Yogyakarta", "Aston Makassar",
              "Aston Manado"],
    "Novotel": ["Novotel Yogyakarta", "Novotel Lombok Resort", "Novotel Manado",
                "Novotel Semarang"],
    "Padma": ["Padma Resort Legian", "Padma Hotel Bandung"],
    "Ibis": ["Ibis Jakarta Tamarin", "Ibis Styles Yogyakarta", "Ibis Surabaya City Center",
             "Ibis Bandung Trans Studio"],
    "Ayana": ["Ayana Resort Jimbaran", "Ayana Komodo Waecicu"],
    "Hyatt": ["Grand Hyatt Jakarta", "Grand Hyatt Bali"],
    "Aryaduta": ["Aryaduta Jakarta", "Aryaduta Medan"],
    "Jayakarta": ["The Jayakarta Bali", "The Jayakarta Lombok"],
}

# ──────────────────────────────────────────────────────────────────────
# AIRLINES  (airline_name, iata_code, is_lcc, is_domestic)
# ──────────────────────────────────────────────────────────────────────
AIRLINES = [
    ("Garuda Indonesia", "GA", 0, 1),
    ("Lion Air", "JT", 1, 1),
    ("Citilink", "QG", 1, 1),
    ("Batik Air", "ID", 0, 1),
    ("AirAsia Indonesia", "QZ", 1, 1),
    ("Sriwijaya Air", "SJ", 0, 1),
    ("Pelita Air", "IP", 0, 1),
    ("Wings Air", "IW", 1, 1),
    ("Super Air Jet", "IU", 1, 1),
    ("TransNusa", "8B", 1, 1),

    ("Singapore Airlines", "SQ", 0, 0),
    ("AirAsia", "AK", 1, 0),
    ("Malaysia Airlines", "MH", 0, 0),
    ("Scoot", "TR", 1, 0),
    ("Jetstar Asia", "3K", 1, 0),
    ("Thai Airways", "TG", 0, 0),
    ("Garuda Indonesia", "GA", 0, 0),
    ("All Nippon Airways", "NH", 0, 0),
    ("Korean Air", "KE", 0, 0),
    ("Emirates", "EK", 0, 0),
]

# ──────────────────────────────────────────────────────────────────────
# AIRPORTS  (airport_name, iata_code, city, province)
# ──────────────────────────────────────────────────────────────────────
AIRPORTS = [
    ("Bandara Soekarno-Hatta", "CGK", "Jakarta", "DKI Jakarta"),
    ("Bandara Halim Perdanakusuma", "HLP", "Jakarta", "DKI Jakarta"),
    ("Bandara I Gusti Ngurah Rai", "DPS", "Denpasar", "Bali"),
    ("Bandara Juanda", "SUB", "Surabaya", "Jawa Timur"),
    ("Bandara Kualanamu", "KNO", "Medan", "Sumatera Utara"),
    ("Bandara Sultan Hasanuddin", "UPG", "Makassar", "Sulawesi Selatan"),
    ("Bandara Adisutjipto", "JOG", "Yogyakarta", "Daerah Istimewa Yogyakarta"),
    ("Bandara Internasional Yogyakarta", "YIA", "Yogyakarta", "Daerah Istimewa Yogyakarta"),
    ("Bandara Husein Sastranegara", "BDO", "Bandung", "Jawa Barat"),
    ("Bandara Ahmad Yani", "SRG", "Semarang", "Jawa Tengah"),
    ("Bandara Lombok Praya", "LOP", "Lombok", "Nusa Tenggara Barat"),
    ("Bandara Komodo", "LBJ", "Labuan Bajo", "Nusa Tenggara Timur"),
    ("Bandara Sultan Aji Muhammad Sulaiman", "BPN", "Balikpapan", "Kalimantan Timur"),
    ("Bandara Minangkabau", "PDG", "Padang", "Sumatera Barat"),
    ("Bandara Sultan Syarif Kasim II", "PKU", "Pekanbaru", "Riau"),
    ("Bandara Sultan Mahmud Badaruddin II", "PLM", "Palembang", "Sumatera Selatan"),
    ("Bandara Syamsudin Noor", "BDJ", "Banjarmasin", "Kalimantan Selatan"),
    ("Bandara Sam Ratulangi", "MDC", "Manado", "Sulawesi Utara"),
    ("Bandara El Tari", "KOE", "Kupang", "Nusa Tenggara Timur"),
    ("Bandara Pattimura", "AMQ", "Ambon", "Maluku"),
    ("Bandara Sentani", "DJJ", "Jayapura", "Papua"),
    ("Bandara Supadio", "PNK", "Pontianak", "Kalimantan Barat"),
    ("Bandara Radin Inten II", "TKG", "Bandar Lampung", "Lampung"),
    ("Bandara Sultan Iskandar Muda", "BTJ", "Banda Aceh", "Nanggroe Aceh Darussalam"),
    ("Bandara Depati Amir", "PGK", "Pangkalpinang", "Kepulauan Bangka Belitung"),
    ("Bandara Hang Nadim", "BTH", "Batam", "Kepulauan Riau"),

    ("Bandara Changi Singapura", "SIN", "Singapore", "International"),
    ("Bandara Internasional Kuala Lumpur", "KUL", "Kuala Lumpur", "International"),
    ("Bandara Suvarnabhumi", "BKK", "Bangkok", "International"),
    ("Bandara Narita", "NRT", "Tokyo", "International"),
    ("Bandara Incheon", "ICN", "Seoul", "International"),
    ("Bandara Perth", "PER", "Perth", "International"),
    ("Bandara Sydney Kingsford Smith", "SYD", "Sydney", "International"),
    ("Bandara Internasional Dubai", "DXB", "Dubai", "International"),
]

# ──────────────────────────────────────────────────────────────────────
# DOMESTIC_ROUTES  (origin_iata, destination_iata, typical_fare_idr)
# ──────────────────────────────────────────────────────────────────────
DOMESTIC_ROUTES = [
    ("CGK", "DPS", 1200000),
    ("CGK", "SUB", 850000),
    ("CGK", "KNO", 1100000),
    ("CGK", "UPG", 1500000),
    ("CGK", "JOG", 650000),
    ("CGK", "YIA", 700000),
    ("CGK", "BDO", 450000),
    ("CGK", "SRG", 600000),
    ("CGK", "LOP", 1100000),
    ("CGK", "LBJ", 1800000),
    ("CGK", "BPN", 1300000),
    ("CGK", "PDG", 900000),
    ("CGK", "PKU", 800000),
    ("CGK", "PLM", 600000),
    ("CGK", "BDJ", 900000),
    ("CGK", "MDC", 1800000),
    ("CGK", "PNK", 700000),
    ("CGK", "BTJ", 1200000),
    ("CGK", "BTH", 500000),
    ("CGK", "DJJ", 3500000),

    ("DPS", "SUB", 500000),
    ("DPS", "LOP", 350000),
    ("DPS", "LBJ", 600000),
    ("DPS", "JOG", 700000),
    ("DPS", "UPG", 1100000),
    ("DPS", "CGK", 1200000),
    ("DPS", "BDO", 850000),

    ("SUB", "CGK", 850000),
    ("SUB", "DPS", 500000),
    ("SUB", "BPN", 800000),
    ("SUB", "UPG", 900000),
    ("SUB", "LOP", 500000),

    ("KNO", "CGK", 1100000),
    ("KNO", "BTH", 450000),
    ("KNO", "PDG", 500000),
    ("KNO", "DPS", 1800000),

    ("UPG", "CGK", 1500000),
    ("UPG", "DPS", 1100000),
    ("UPG", "SUB", 900000),
    ("UPG", "DJJ", 1200000),
    ("UPG", "SOQ", 800000),

    ("JOG", "CGK", 650000),
    ("JOG", "DPS", 700000),
    ("YIA", "CGK", 700000),
    ("YIA", "DPS", 750000),
    ("YIA", "LOP", 500000),

    ("BDO", "CGK", 450000),
    ("BDO", "DPS", 850000),

    ("LOP", "CGK", 1100000),
    ("LOP", "DPS", 350000),
    ("LOP", "YIA", 500000),
    ("LOP", "SUB", 500000),

    ("BPN", "CGK", 1300000),
    ("BPN", "SUB", 800000),
    ("BPN", "UPG", 700000),
]

# ──────────────────────────────────────────────────────────────────────
# INTERNATIONAL_ROUTES  (origin_iata, destination_iata, typical_fare_idr)
# ──────────────────────────────────────────────────────────────────────
INTERNATIONAL_ROUTES = [
    ("CGK", "SIN", 1800000),
    ("CGK", "KUL", 1500000),
    ("CGK", "BKK", 3000000),
    ("CGK", "NRT", 6000000),
    ("CGK", "ICN", 5500000),
    ("CGK", "PER", 4500000),
    ("CGK", "SYD", 7000000),
    ("CGK", "DXB", 9000000),
    ("DPS", "SIN", 2000000),
    ("DPS", "KUL", 1800000),
    ("DPS", "PER", 4000000),
    ("DPS", "SYD", 6000000),
    ("DPS", "NRT", 7000000),
    ("DPS", "DXB", 10000000),
    ("SUB", "KUL", 2500000),
    ("SUB", "SIN", 2200000),
    ("KNO", "KUL", 1200000),
    ("KNO", "SIN", 1300000),
    ("UPG", "KUL", 3500000),
    ("BDO", "SIN", 1500000),
]

# ──────────────────────────────────────────────────────────────────────
# EXPERIENCE_CATALOG  (experience_name, category, city, base_price_per_person_idr)
# ──────────────────────────────────────────────────────────────────────
EXPERIENCE_CATALOG = [
    ("Sunrise Trek Gunung Bromo", "adventure", "Probolinggo", 750000),
    ("Pendakian Gunung Rinjani 3 Hari", "adventure", "Lombok", 2500000),
    ("Pendakian Gunung Ijen Blue Fire", "adventure", "Banyuwangi", 650000),
    ("Trekking Gunung Agung Sunrise", "adventure", "Bali", 900000),
    ("Ekspedisi Pendakian Puncak Jaya", "adventure", "Papua", 15000000),

    ("Cooking Class Masakan Bali Ubud", "culinary", "Ubud", 450000),
    ("Wisata Kuliner Malam Surabaya", "culinary", "Surabaya", 300000),
    ("Kursus Memasak Rendang Padang", "culinary", "Padang", 350000),
    ("Tur Kuliner Jalanan Bandung", "culinary", "Bandung", 250000),

    ("Tur Candi Borobudur Sunrise", "cultural", "Magelang", 550000),
    ("Tur Candi Prambanan Sunset", "cultural", "Yogyakarta", 450000),
    ("Jalan Kaki Heritage Kota Tua Jakarta", "cultural", "Jakarta", 200000),
    ("Pertunjukan Tari Kecak Uluwatu", "cultural", "Bali", 350000),
    ("Mengunjungi Desa Adat Tana Toraja", "cultural", "Tana Toraja", 1200000),
    ("Tur Kuil Tanah Lot & Uluwatu", "cultural", "Bali", 400000),

    ("Snorkeling Raja Ampat", "water_sports", "Raja Ampat", 1500000),
    ("Selam Scuba Nusa Penida", "water_sports", "Bali", 1200000),
    ("Snorkeling dengan Hiu Paus Derawan", "water_sports", "Derawan", 2000000),
    ("Selam Scuba Pulau Bunaken", "water_sports", "Manado", 950000),
    ("Arung Jeram Sungai Ayung Ubud", "water_sports", "Bali", 500000),
    ("Snorkeling Gili Trawangan", "water_sports", "Lombok", 300000),

    ("Kursus Selancar Pantai Kuta", "water_sports", "Bali", 350000),
    ("Kursus Selancar Pantai Canggu", "water_sports", "Bali", 400000),
    ("Safari Komodo Tour 2 Hari 1 Malam", "nature", "Labuan Bajo", 2500000),
    ("Susur Hutan Hujan Bukit Lawang", "nature", "Bukit Lawang", 600000),
    ("Tur Melihat Orangutan Tanjung Puting", "nature", "Tanjung Puting", 2500000),
    ("Tur Kebun Teh Ciwidey & Kawah Putih", "nature", "Bandung", 350000),
    ("Kemping di Kawah Ijen", "nature", "Banyuwangi", 700000),

    ("Spa & Pijat Tradisional Bali", "wellness", "Bali", 500000),
    ("Retret Meditasi & Yoga Ubud", "wellness", "Ubud", 800000),
    ("Paket Spa Pasangan Seminyak", "wellness", "Bali", 1200000),
    ("Spa Air Panas Ciater", "wellness", "Bandung", 300000),

    ("Tur Eksplorasi Kota Jakarta", "city_tour", "Jakarta", 250000),
    ("Tur Wisata Sejarah Surabaya", "city_tour", "Surabaya", 200000),
    ("Tur Museum & Galeri Yogyakarta", "city_tour", "Yogyakarta", 200000),
    ("Tur Arsitektur Kolonial Bandung", "city_tour", "Bandung", 250000),
    ("Tur Kuliner & Sejarah Makassar", "city_tour", "Makassar", 300000),
]

# ──────────────────────────────────────────────────────────────────────
# CATEGORIES
# ──────────────────────────────────────────────────────────────────────
CATEGORIES = [
    "adventure", "cultural", "culinary", "wellness",
    "water_sports", "nature", "city_tour",
]

# ──────────────────────────────────────────────────────────────────────
# ROOM_TYPES
# ──────────────────────────────────────────────────────────────────────
ROOM_TYPES = [
    "Standard", "Deluxe", "Suite", "Family Room",
    "Villa", "Superior", "Executive", "Presidential Suite",
]

ROOM_TYPE_MULTIPLIERS = {
    "Standard": 1.0,
    "Deluxe": 1.5,
    "Suite": 2.5,
    "Family Room": 1.8,
    "Villa": 3.0,
    "Superior": 1.2,
    "Executive": 2.0,
    "Presidential Suite": 5.0,
}

# ──────────────────────────────────────────────────────────────────────
# PAYMENT_METHODS (travel-domain with hotel/flight/experience weights)
# ──────────────────────────────────────────────────────────────────────
PAYMENT_METHODS_HOTEL = {
    "Bank Transfer (BCA)": 0.15,
    "Bank Transfer (Mandiri)": 0.10,
    "Bank Transfer (BRI)": 0.05,
    "QRIS": 0.15,
    "GoPay": 0.12,
    "OVO": 0.10,
    "DANA": 0.08,
    "ShopeePay": 0.05,
    "LinkAja": 0.05,
    "COD": 0.15,
}

PAYMENT_METHODS_FLIGHT = {
    "Bank Transfer (BCA)": 0.20,
    "Bank Transfer (Mandiri)": 0.12,
    "Bank Transfer (BRI)": 0.08,
    "QRIS": 0.10,
    "GoPay": 0.10,
    "OVO": 0.08,
    "DANA": 0.10,
    "ShopeePay": 0.07,
    "LinkAja": 0.05,
    "Kartu Kredit": 0.10,
}

PAYMENT_METHODS_EXPERIENCE = {
    "QRIS": 0.20,
    "GoPay": 0.18,
    "OVO": 0.12,
    "DANA": 0.15,
    "ShopeePay": 0.10,
    "Bank Transfer (BCA)": 0.10,
    "Bank Transfer (Mandiri)": 0.08,
    "Kartu Kredit": 0.07,
}

PAYMENT_METHODS_ALL = [
    "QRIS", "GoPay", "OVO", "DANA", "ShopeePay", "LinkAja",
    "Bank Transfer (BCA)", "Bank Transfer (Mandiri)",
    "Bank Transfer (BRI)", "Bank Transfer (BNI)",
    "Kartu Kredit", "COD",
]

# ──────────────────────────────────────────────────────────────────────
# HOLIDAYS_SEASONAL (travel-domain, uplift factors for Indonesian travel)
# ──────────────────────────────────────────────────────────────────────
HOLIDAYS_SEASONAL = [
    {
        "name": "Lebaran / Idul Fitri",
        "month_range": [3, 4, 5],
        "uplift_factor": 3.0,
        "travel_pattern": "mudik",
    },
    {
        "name": "Natal / Tahun Baru",
        "month_range": [12, 1],
        "uplift_factor": 2.5,
        "travel_pattern": "holiday",
    },
    {
        "name": "Imlek",
        "month_range": [1, 2],
        "uplift_factor": 1.8,
        "travel_pattern": "getaway",
    },
    {
        "name": "Libur Sekolah (Juni-Juli)",
        "month_range": [6, 7],
        "uplift_factor": 2.0,
        "travel_pattern": "family",
    },
    {
        "name": "Libur Sekolah (Desember)",
        "month_range": [12],
        "uplift_factor": 2.2,
        "travel_pattern": "family",
    },
    {
        "name": "Kemerdekaan RI",
        "month_range": [8],
        "uplift_factor": 1.3,
        "travel_pattern": "long_weekend",
    },
    {
        "name": "Waisak / Nyepi",
        "month_range": [3, 4, 5],
        "uplift_factor": 1.4,
        "travel_pattern": "cultural",
    },
]

# ──────────────────────────────────────────────────────────────────────
# ID_MONTH_ABBR
# ──────────────────────────────────────────────────────────────────────
ID_MONTH_ABBR = [
    ("Jan", "Jan", "Januari"),
    ("Feb", "Feb", "Februari"),
    ("Mar", "Mar", "Maret"),
    ("Apr", "Apr", "April"),
    ("May", "Mei", "Mei"),
    ("Jun", "Jun", "Juni"),
    ("Jul", "Jul", "Juli"),
    ("Aug", "Agt", "Agustus"),
    ("Sep", "Sep", "September"),
    ("Oct", "Okt", "Oktober"),
    ("Nov", "Nov", "November"),
    ("Dec", "Des", "Desember"),
]

# ──────────────────────────────────────────────────────────────────────
# CRM_TICKET_CATEGORIES
# ──────────────────────────────────────────────────────────────────────
CRM_TICKET_CATEGORIES = [
    "penerbangan", "hotel", "refund", "pembatalan",
    "ubah_jadwal", "bagasi", "pengalaman", "pembayaran", "lainnya",
]

CRM_TICKET_CATEGORY_WEIGHTS = {
    "penerbangan": 0.25,
    "hotel": 0.25,
    "refund": 0.12,
    "pembatalan": 0.10,
    "ubah_jadwal": 0.08,
    "bagasi": 0.07,
    "pengalaman": 0.06,
    "pembayaran": 0.04,
    "lainnya": 0.03,
}

# ──────────────────────────────────────────────────────────────────────
# CRM_TICKET_SUBJECTS (Bahasa Indonesia)
# ──────────────────────────────────────────────────────────────────────
CRM_TICKET_SUBJECTS = [
    "penerbangan ditunda",
    "refund hotel",
    "ubah jadwal check-in",
    "bagasi hilang",
    "kamar hotel tidak sesuai",
    "keluhan kebersihan kamar",
    "pengalaman dibatalkan karena cuaca",
    "refund penerbangan",
    "penumpang tidak bisa terbang",
    "komplain pelayanan",
    "perubahan tanggal penerbangan",
    "perubahan nama tamu hotel",
    "kursi penerbangan tidak sesuai",
    "pembayaran ganda",
    "tidak menerima konfirmasi booking",
    "tiket pesawat salah nama",
    "hotel overbooked",
    "fasilitas hotel tidak berfungsi",
    "makanan pesawat tidak sesuai pesanan",
    "aplikasi error saat booking",
]

# ──────────────────────────────────────────────────────────────────────
# CRM_TICKET_BODIES (Bahasa Indonesia, with {placeholders})
# ──────────────────────────────────────────────────────────────────────
CRM_TICKET_BODIES = [
    "Selamat pagi, saya ingin komplain mengenai penerbangan {airline} saya dari {origin} ke {destination} pada tanggal {date}. Penerbangan ditunda selama {hours} jam tanpa pemberitahuan sebelumnya. Saya minta kompensasi atas ketidaknyamanan ini. Terima kasih.",

    "Mohon bantuannya, saya ingin refund hotel {hotel} untuk check-in tanggal {date}. Saya sudah membatalkan booking melalui aplikasi tetapi dana belum kembali. Total pembayaran saya Rp {amount_idr}. Terima kasih.",

    "Halo, saya ingin mengubah jadwal check-in hotel {hotel} menjadi tanggal {date}. Sebelumnya saya booking untuk tanggal {old_date}. Mohon dikonfirmasi apakah ada biaya perubahan. Terima kasih.",

    "Saya melaporkan kehilangan bagasi pada penerbangan {airline} dengan kode booking {booking_ref}. Bagasi saya berisi pakaian dan barang pribadi. Saya sudah menunggu di baggage claim selama 2 jam. Tolong segera ditindaklanjuti.",

    "Kamar hotel {hotel} yang saya booking tidak sesuai dengan deskripsi di aplikasi. Saya booking tipe kamar {room_type}, tapi diberikan tipe yang berbeda. Pihak hotel tidak membantu dan meminta biaya tambahan. Saya minta refund selisih harga.",

    "Kebersihan kamar di hotel {hotel} sangat buruk. Lantai kotor, sprei ada noda, dan kamar mandi bau. Saya sudah meminta housekeeping tapi tidak ada tindak lanjut. Booking ID saya {booking_ref}.",

    "Pengalaman {experience_name} yang saya booking untuk tanggal {date} dibatalkan oleh operator karena cuaca buruk. Saya sudah mencoba menghubungi operator tapi tidak ada respons. Tolong bantu proses refund. Total pembayaran Rp {amount_idr}.",

    "Saya ingin refund penerbangan {airline} rute {origin}-{destination} karena ada keadaan darurat keluarga. Saya tidak bisa terbang pada tanggal {date}. Booking reference saya {booking_ref}.",

    "Mohon maaf, saya tidak bisa melakukan check-in online untuk penerbangan {airline} besok. Sistem mengatakan data penumpang tidak ditemukan. Nomor booking {booking_ref}. Tolong diperiksa.",

    "Pelayanan staf hotel {hotel} sangat tidak memuaskan. Saya sudah komplain ke front desk tapi tidak digubris. Saya terpaksa pindah hotel dan minta refund penuh. Check-in seharusnya tanggal {date}.",

    "Halo tim WanderFuel, saya sudah transfer pembayaran untuk booking hotel {hotel} sebesar Rp {amount_idr} tetapi di aplikasi masih pending. Mohon konfirmasinya. Bukti transfer sudah saya lampirkan. Booking ID {booking_ref}.",

    "Saya ingin membatalkan pengalaman {experience_name} yang dijadwalkan tanggal {date}. Ada perubahan rencana perjalanan. Mohon informasikan kebijakan pembatalan. Booking ID: {booking_ref}.",

    "Terkait penerbangan {airline} saya tanggal {date}, saya ingin upgrade kursi dari ekonomi ke bisnis. Apakah bisa dilakukan sekarang? Berapa biaya tambahannya? Kode booking: {booking_ref}.",

    "Saya tidak menerima email konfirmasi untuk booking hotel {hotel}. Tapi saldo saya sudah terpotong. Tolong kirimkan konfirmasi booking. Total Rp {amount_idr}, tanggal check-in {date}.",

    "Aplikasi WanderFuel error saat saya mencoba booking penerbangan. Beberapa kali transaksi gagal tapi tetap muncul di mutasi rekening. Saya khawatir terjadi pembayaran ganda. Tolong diperiksa. Terima kasih.",
]

# ──────────────────────────────────────────────────────────────────────
# CRM_AGENT_NAMES
# ──────────────────────────────────────────────────────────────────────
CRM_AGENT_NAMES = [
    "Rina Anggraini", "Bambang Sulistyo", "Dewi Kartika",
    "Agus Setiawan", "Fitriani Hasan", "Irfan Malik", "Lina Permata",
    "Hendra Gunawan", "Sari Nirmala", "Adi Pramono",
    "Nia Kurniawati", "Wahyudi Saputra",
]

# ──────────────────────────────────────────────────────────────────────
# SEAT_CLASSES
# ──────────────────────────────────────────────────────────────────────
SEAT_CLASSES = ["economy", "business", "first"]

SEAT_CLASS_WEIGHTS = {
    "economy": 0.80,
    "business": 0.18,
    "first": 0.02,
}

SEAT_CLASS_MULTIPLIERS = {
    "economy": 1.0,
    "business": 3.0,
    "first": 8.0,
}

# ──────────────────────────────────────────────────────────────────────
# LOYALTY_TIERS
# ──────────────────────────────────────────────────────────────────────
LOYALTY_TIERS = ["gold", "silver", "basic"]

LOYALTY_TIER_WEIGHTS = {
    "gold": 0.10,
    "silver": 0.30,
    "basic": 0.60,
}

LOYALTY_TIER_THRESHOLDS_IDR = {
    "gold": 10000000,
    "silver": 2000000,
}

# ──────────────────────────────────────────────────────────────────────
# TOURIST_CITIES (popular travel destinations in Indonesia)
# ──────────────────────────────────────────────────────────────────────
TOURIST_CITIES = [
    "Bali", "Yogyakarta", "Bandung", "Lombok", "Labuan Bajo",
    "Jakarta", "Surabaya", "Malang", "Semarang", "Medan",
    "Makassar", "Manado", "Padang", "Palembang", "Banyuwangi",
    "Bogor", "Raja Ampat",
]

TOURIST_CITY_WEIGHTS = {
    "Bali": 0.30,
    "Yogyakarta": 0.15,
    "Bandung": 0.10,
    "Lombok": 0.08,
    "Labuan Bajo": 0.07,
    "Jakarta": 0.07,
    "Surabaya": 0.05,
    "Malang": 0.03,
    "Semarang": 0.02,
    "Medan": 0.02,
    "Makassar": 0.03,
    "Manado": 0.02,
    "Banyuwangi": 0.02,
    "Padang": 0.01,
    "Palembang": 0.01,
    "Bogor": 0.01,
    "Raja Ampat": 0.01,
}

# ──────────────────────────────────────────────────────────────────────
# BOOKING_STATUSES
# ──────────────────────────────────────────────────────────────────────
HOTEL_BOOKING_STATUSES = {
    "confirmed": 0.75,
    "completed": 0.15,
    "cancelled": 0.05,
    "no_show": 0.05,
}

FLIGHT_BOOKING_STATUSES = {
    "confirmed": 0.70,
    "completed": 0.15,
    "cancelled": 0.10,
    "no_show": 0.05,
}

EXPERIENCE_BOOKING_STATUSES = {
    "confirmed": 0.80,
    "cancelled": 0.15,
    "completed": 0.05,
}

# ──────────────────────────────────────────────────────────────────────
# MAJOR_KELURAHAN_SAMPLES
# ──────────────────────────────────────────────────────────────────────
MAJOR_KELURAHAN_SAMPLES = [
    ("Menteng", "Menteng", "Jakarta Pusat", "DKI Jakarta"),
    ("Kebon Jeruk", "Kebon Jeruk", "Jakarta Barat", "DKI Jakarta"),
    ("Tebet Barat", "Tebet", "Jakarta Selatan", "DKI Jakarta"),
    ("Kelapa Gading Barat", "Kelapa Gading", "Jakarta Utara", "DKI Jakarta"),
    ("Cipayung", "Cipayung", "Jakarta Timur", "DKI Jakarta"),
    ("Coblong", "Coblong", "Bandung", "Jawa Barat"),
    ("Cidadap", "Cidadap", "Bandung", "Jawa Barat"),
    ("Sukajadi", "Sukajadi", "Bandung", "Jawa Barat"),
    ("Gubeng", "Gubeng", "Surabaya", "Jawa Timur"),
    ("Tegalsari", "Tegalsari", "Surabaya", "Jawa Timur"),
    ("Rungkut Kidul", "Rungkut", "Surabaya", "Jawa Timur"),
    ("Sanur Kaja", "South Denpasar", "Badung", "Bali"),
    ("Kuta", "Kuta", "Badung", "Bali"),
    ("Seminyak", "Kuta", "Badung", "Bali"),
    ("Ubud", "Ubud", "Gianyar", "Bali"),
    ("Gondokusuman", "Mantrijeron", "Yogyakarta", "Daerah Istimewa Yogyakarta"),
    ("Danurejan", "Danurejan", "Yogyakarta", "Daerah Istimewa Yogyakarta"),
    ("Kesawan", "Medan Barat", "Medan", "Sumatera Utara"),
    ("Polonia", "Medan Polonia", "Medan", "Sumatera Utara"),
    ("Tanjung Bunga", "Tamalate", "Makassar", "Sulawesi Selatan"),
]

# ──────────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────────

def get_province(name):
    return next((p for p in PROVINCES if p[0] == name), None)


def get_airport_by_iata(iata):
    for apt in AIRPORTS:
        if apt[1] == iata:
            return apt
    return None


def get_airport_city(iata):
    apt = get_airport_by_iata(iata)
    if apt:
        return apt[2]
    return iata


def get_cities_for_province(province_name):
    return INDONESIAN_CITIES.get(province_name, [])


def weighted_choice(weights_dict, rng=None):
    import random
    _rng = rng if rng else random
    items = list(weights_dict.keys())
    w = list(weights_dict.values())
    return _rng.choices(items, weights=w)[0]
