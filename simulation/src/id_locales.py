"""Indonesian geographic / locale reference data for the simulation generator.

Use ``Faker('id_ID')`` separately for name, address and phone string generation;
this module supplies static lookup tables that Faker does not expose:
province/city lists, postcode prefixes, kelurahan samples, mobile/landline
prefixes by carrier, Indonesian month abbreviations, seasonal holidays,
payment methods and store-name prefixes. All data reflects Indonesian retail
reality (see ``plan.md``) and is kept dependency-free so the generator can
import it without pulling Faker.
"""

# --- PROVINCES ---
# (full_name, iso_code, capital_city). The four post-2022 Papua splits
# (Papua Selatan/Tengah/Pegunungan/Barat Daya) were carved from Papua and
# Papua Barat; their ISO codes here are placeholders (not yet standardized).
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

# --- CITIES ---
# province full_name -> list of (city_or_kabupaten_name, type)
# type is "Kota" (administrative city) or "Kabupaten" (regency).
CITIES = {
    "Nanggroe Aceh Darussalam": [("Banda Aceh", "Kota"), ("Lhokseumawe", "Kota"), ("Aceh Utara", "Kabupaten")],
    "Sumatera Utara": [("Medan", "Kota"), ("Pematangsiantar", "Kota"), ("Deliserdang", "Kabupaten")],
    "Sumatera Barat": [("Padang", "Kota"), ("Bukittinggi", "Kota"), ("Padang Panjang", "Kota")],
    "Riau": [("Pekanbaru", "Kota"), ("Dumai", "Kota"), ("Bengkalis", "Kabupaten")],
    "Jambi": [("Jambi", "Kota"), ("Muara Bulian", "Kabupaten")],
    "Sumatera Selatan": [("Palembang", "Kota"), ("Prabumulih", "Kota"), ("Banyuasin", "Kabupaten")],
    "Bengkulu": [("Bengkulu", "Kota"), ("Arga Makmur", "Kabupaten")],
    "Lampung": [("Bandar Lampung", "Kota"), ("Metro", "Kota"), ("Pringsewu", "Kabupaten")],
    "Kepulauan Bangka Belitung": [("Pangkalpinang", "Kota"), ("Sungailiat", "Kabupaten")],
    "Kepulauan Riau": [("Tanjungpinang", "Kota"), ("Batam", "Kota")],
    "DKI Jakarta": [
        ("Jakarta Pusat", "Kota"),
        ("Jakarta Selatan", "Kota"),
        ("Jakarta Barat", "Kota"),
        ("Jakarta Timur", "Kota"),
        ("Jakarta Utara", "Kota"),
        ("Kepulauan Seribu", "Kabupaten"),
    ],
    "Jawa Barat": [
        ("Bandung", "Kota"),
        ("Bekasi", "Kota"),
        ("Depok", "Kota"),
        ("Bogor", "Kota"),
        ("Cimahi", "Kota"),
        ("Bandung", "Kabupaten"),
        ("Bekasi", "Kabupaten"),
    ],
    "Jawa Tengah": [
        ("Semarang", "Kota"),
        ("Surakarta", "Kota"),
        ("Tegal", "Kota"),
        ("Semarang", "Kabupaten"),
        ("Kudus", "Kabupaten"),
    ],
    "Daerah Istimewa Yogyakarta": [
        ("Yogyakarta", "Kota"),
        ("Sleman", "Kabupaten"),
        ("Bantul", "Kabupaten"),
        ("Kulon Progo", "Kabupaten"),
    ],
    "Jawa Timur": [
        ("Surabaya", "Kota"),
        ("Malang", "Kota"),
        ("Sidoarjo", "Kabupaten"),
        ("Gresik", "Kabupaten"),
    ],
    "Banten": [("Tangerang", "Kota"), ("Tangerang Selatan", "Kota"), ("Serang", "Kota"), ("Tangerang", "Kabupaten")],
    "Bali": [("Denpasar", "Kota"), ("Badung", "Kabupaten"), ("Gianyar", "Kabupaten")],
    "Nusa Tenggara Barat": [("Mataram", "Kota"), ("Bima", "Kota"), ("Lombok Barat", "Kabupaten")],
    "Nusa Tenggara Timur": [("Kupang", "Kota"), ("Ende", "Kabupaten")],
    "Kalimantan Barat": [("Pontianak", "Kota"), ("Singkawang", "Kota")],
    "Kalimantan Tengah": [("Palangkaraya", "Kota")],
    "Kalimantan Selatan": [("Banjarmasin", "Kota"), ("Banjarbaru", "Kota")],
    "Kalimantan Timur": [("Samarinda", "Kota"), ("Balikpapan", "Kota")],
    "Kalimantan Utara": [("Tarakan", "Kota")],
    "Sulawesi Utara": [("Manado", "Kota")],
    "Sulawesi Tengah": [("Palu", "Kota")],
    "Sulawesi Selatan": [("Makassar", "Kota"), ("Parepare", "Kota")],
    "Sulawesi Tenggara": [("Kendari", "Kota")],
    "Gorontalo": [("Gorontalo", "Kota")],
    "Sulawesi Barat": [("Mamuju", "Kabupaten")],
    "Maluku": [("Ambon", "Kota")],
    "Maluku Utara": [("Ternate", "Kota")],
    "Papua": [("Jayapura", "Kota")],
    "Papua Barat": [("Manokwari", "Kabupaten")],
    "Papua Selatan": [("Merauke", "Kabupaten")],
    "Papua Tengah": [("Nabire", "Kabupaten")],
    "Papua Pegunungan": [("Jayawijaya", "Kabupaten")],
    "Papua Barat Daya": [("Sorong", "Kota")],
}

# --- POSTAL_PREFIXES ---
# province name -> list of 2-3 digit postcode prefixes (string, leading zeros kept).
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

# --- MAJOR_KELURAHAN_SAMPLES ---
# (kelurahan_name, kecamatan_name, kota_name, provinsi_name)
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
    ("Gondokusuman", "Mantrijeron", "Yogyakarta", "Daerah Istimewa Yogyakarta"),
    ("Danurejan", "Danurejan", "Yogyakarta", "Daerah Istimewa Yogyakarta"),
    ("Kesawan", "Medan Barat", "Medan", "Sumatera Utara"),
    ("Polonia", "Medan Polonia", "Medan", "Sumatera Utara"),
]

# --- PHONE_MOBILE_PREFIXES ---
# Telkomsel 0852/0853/0854 also overlap with Indosat in some allocations;
# 0855/0856/0857/0858 are shared between Telkomsel and Indosat depending on
# the HLR of the number block.
PHONE_MOBILE_PREFIXES = [
    "0811", "0812", "0813", "0821", "0822", "0823",
    "0852", "0853", "0854", "0855", "0856", "0857", "0858", "0859",
    "0814", "0815", "0816",
    "0817", "0818", "0819",
    "0831", "0832", "0833", "0834", "0835", "0836", "0837", "0838",
    "0881", "0882", "0883", "0884", "0885", "0886", "0887", "0888", "0889",
    "0894", "0895", "0896", "0897", "0898", "0899",
]

# --- MOBILE_PREFIXES_BY_CARRIER ---
# See overlap note on PHONE_MOBILE_PREFIXES: 0853-0855/0858 are reused across
# Telkomsel/Indosat/Smartfren allocations depending on the number series.
MOBILE_PREFIXES_BY_CARRIER = {
    "Telkomsel": ["0811", "0812", "0813", "0821", "0822", "0823",
                  "0852", "0853", "0854", "0855", "0856", "0857", "0858", "0859"],
    "Indosat": ["0814", "0815", "0816", "0855", "0858"],
    "XL": ["0817", "0818", "0819"],
    "Axis": ["0831", "0832", "0833", "0834", "0835", "0836", "0837", "0838"],
    "Smartfren": ["0881", "0882", "0883", "0884", "0885", "0886", "0887", "0888", "0889"],
    "Three": ["0894", "0895", "0896", "0897", "0898", "0899"],
}

# --- LANDLINE_AREA_CODES ---
# area code (string, no leading 0) -> major city name.
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
}

# --- ID_MONTH_ABBR ---
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

# --- HOLIDAYS_SEASONAL ---
# Lebaran (Idul Fitri) follows the Hijri calendar and shifts roughly 11 days
# earlier each Gregorian year; the month_range below is an approximation for
# Indonesian retail uplift around the main Lebaran season.
HOLIDAYS_SEASONAL = [
    {
        "name": "Lebaran / Idul Fitri",
        "month_range": [3, 4, 5],
        "uplift_factor": 2.8,
        "typical_products": ["sarung", "mukena", "baju kurung", "kue lebaran", "sirup", "ketupat"],
    },
    {
        "name": "Natal",
        "month_range": [12],
        "uplift_factor": 2.0,
        "typical_products": ["kado", "pohon natal", "dekorasi", "kue kering"],
    },
    {
        "name": "Imlek",
        "month_range": [1, 2],
        "uplift_factor": 1.8,
        "typical_products": ["angpau", "dekor merah", "kue keranjang", "jeruk"],
    },
    {
        "name": "Tahun Baru",
        "month_range": [1],
        "uplift_factor": 1.5,
        "typical_products": ["kembang api", "kado", "minuman"],
    },
    {
        "name": "Waisak",
        "month_range": [5],
        "uplift_factor": 1.3,
        "typical_products": ["lilin", "dupa", "sesaji"],
    },
    {
        "name": "Kemerdekaan RI",
        "month_range": [8],
        "uplift_factor": 1.2,
        "typical_products": ["bendera merah putih", "atribut kemerdekaan", "snack"],
    },
]

# --- PAYMENT_METHODS ---
PAYMENT_METHODS = [
    {"name": "QRIS", "channel": ["in-store", "online"], "region_affinity": "nationwide"},
    {"name": "COD", "channel": ["delivery"], "region_affinity": "outside-jabodetabek-heavy"},
    {"name": "GoPay", "channel": ["online"], "region_affinity": "jabodetabek"},
    {"name": "OVO", "channel": ["online"], "region_affinity": "jabodetabek"},
    {"name": "DANA", "channel": ["online"], "region_affinity": "nationwide"},
    {"name": "ShopeePay", "channel": ["online"], "region_affinity": "nationwide"},
    {"name": "LinkAja", "channel": ["online"], "region_affinity": "nationwide"},
    {"name": "Bank Transfer", "channel": ["online"], "region_affinity": "nationwide",
     "banks": ["BCA", "Mandiri", "BNI", "BRI"]},
    {"name": "Cash", "channel": ["in-store"], "region_affinity": "nationwide"},
]

# --- STORE_NAME_PREFIXES ---
STORE_NAME_PREFIXES = ["Toko", "CV", "UD", "Warung", "Toko Bangunan", "Kios"]


def get_province(name):
    return next((p for p in PROVINCES if p[0] == name), None)