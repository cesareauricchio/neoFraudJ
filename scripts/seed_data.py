"""
seed_data.py — Deterministic data pool shared by bulk_seed.py and stream_seed.py.

All IDs are stable strings derived from real names so the graph is readable.
"""

from __future__ import annotations

# ─── Users ────────────────────────────────────────────────────────────────────

USERS: list[dict] = [
    {"user_id": "usr_emma_johnson",    "name": "Emma Johnson",    "email": "emma.johnson@nfj.example"},
    {"user_id": "usr_luca_ferrari",    "name": "Luca Ferrari",    "email": "luca.ferrari@nfj.example"},
    {"user_id": "usr_sofia_garcia",    "name": "Sofia Garcia",    "email": "sofia.garcia@nfj.example"},
    {"user_id": "usr_james_miller",    "name": "James Miller",    "email": "james.miller@nfj.example"},
    {"user_id": "usr_amina_diallo",    "name": "Amina Diallo",    "email": "amina.diallo@nfj.example"},
    {"user_id": "usr_noah_kim",        "name": "Noah Kim",        "email": "noah.kim@nfj.example"},
    {"user_id": "usr_chloe_martin",    "name": "Chloé Martin",    "email": "chloe.martin@nfj.example"},
    {"user_id": "usr_rafael_silva",    "name": "Rafael Silva",    "email": "rafael.silva@nfj.example"},
    {"user_id": "usr_yuki_tanaka",     "name": "Yuki Tanaka",     "email": "yuki.tanaka@nfj.example"},
    {"user_id": "usr_oliver_schmidt",  "name": "Oliver Schmidt",  "email": "oliver.schmidt@nfj.example"},
    {"user_id": "usr_fatima_hassan",   "name": "Fatima Hassan",   "email": "fatima.hassan@nfj.example"},
    {"user_id": "usr_ethan_brown",     "name": "Ethan Brown",     "email": "ethan.brown@nfj.example"},
    {"user_id": "usr_ines_dupont",     "name": "Inès Dupont",     "email": "ines.dupont@nfj.example"},
    {"user_id": "usr_carlos_mendez",   "name": "Carlos Méndez",   "email": "carlos.mendez@nfj.example"},
    {"user_id": "usr_priya_patel",     "name": "Priya Patel",     "email": "priya.patel@nfj.example"},
    {"user_id": "usr_max_weber",       "name": "Max Weber",       "email": "max.weber@nfj.example"},
    {"user_id": "usr_aisha_okonkwo",   "name": "Aisha Okonkwo",   "email": "aisha.okonkwo@nfj.example"},
    {"user_id": "usr_tom_anderson",    "name": "Tom Anderson",    "email": "tom.anderson@nfj.example"},
    {"user_id": "usr_mei_chen",        "name": "Mei Chen",        "email": "mei.chen@nfj.example"},
    {"user_id": "usr_ivan_petrov",     "name": "Ivan Petrov",     "email": "ivan.petrov@nfj.example"},
]

# ─── Accounts (1–2 per user, deterministic) ───────────────────────────────────

ACCOUNTS: list[dict] = [
    # Emma Johnson
    {"account_id": "acc_emma_checking",   "user_id": "usr_emma_johnson",   "account_type": "checking"},
    {"account_id": "acc_emma_savings",    "user_id": "usr_emma_johnson",   "account_type": "savings"},
    # Luca Ferrari
    {"account_id": "acc_luca_checking",   "user_id": "usr_luca_ferrari",   "account_type": "checking"},
    # Sofia Garcia
    {"account_id": "acc_sofia_checking",  "user_id": "usr_sofia_garcia",   "account_type": "checking"},
    {"account_id": "acc_sofia_business",  "user_id": "usr_sofia_garcia",   "account_type": "business"},
    # James Miller
    {"account_id": "acc_james_checking",  "user_id": "usr_james_miller",   "account_type": "checking"},
    # Amina Diallo
    {"account_id": "acc_amina_checking",  "user_id": "usr_amina_diallo",   "account_type": "checking"},
    {"account_id": "acc_amina_savings",   "user_id": "usr_amina_diallo",   "account_type": "savings"},
    # Noah Kim
    {"account_id": "acc_noah_checking",   "user_id": "usr_noah_kim",       "account_type": "checking"},
    # Chloé Martin
    {"account_id": "acc_chloe_checking",  "user_id": "usr_chloe_martin",   "account_type": "checking"},
    # Rafael Silva
    {"account_id": "acc_rafael_checking", "user_id": "usr_rafael_silva",   "account_type": "checking"},
    {"account_id": "acc_rafael_savings",  "user_id": "usr_rafael_silva",   "account_type": "savings"},
    # Yuki Tanaka
    {"account_id": "acc_yuki_checking",   "user_id": "usr_yuki_tanaka",    "account_type": "checking"},
    # Oliver Schmidt
    {"account_id": "acc_oliver_checking", "user_id": "usr_oliver_schmidt", "account_type": "checking"},
    # Fatima Hassan
    {"account_id": "acc_fatima_checking", "user_id": "usr_fatima_hassan",  "account_type": "checking"},
    {"account_id": "acc_fatima_savings",  "user_id": "usr_fatima_hassan",  "account_type": "savings"},
    # Ethan Brown
    {"account_id": "acc_ethan_checking",  "user_id": "usr_ethan_brown",    "account_type": "checking"},
    # Inès Dupont
    {"account_id": "acc_ines_checking",   "user_id": "usr_ines_dupont",    "account_type": "checking"},
    # Carlos Méndez
    {"account_id": "acc_carlos_checking", "user_id": "usr_carlos_mendez",  "account_type": "checking"},
    {"account_id": "acc_carlos_business", "user_id": "usr_carlos_mendez",  "account_type": "business"},
    # Priya Patel
    {"account_id": "acc_priya_checking",  "user_id": "usr_priya_patel",    "account_type": "checking"},
    # Max Weber
    {"account_id": "acc_max_checking",    "user_id": "usr_max_weber",      "account_type": "checking"},
    # Aisha Okonkwo
    {"account_id": "acc_aisha_checking",  "user_id": "usr_aisha_okonkwo",  "account_type": "checking"},
    {"account_id": "acc_aisha_savings",   "user_id": "usr_aisha_okonkwo",  "account_type": "savings"},
    # Tom Anderson
    {"account_id": "acc_tom_checking",    "user_id": "usr_tom_anderson",   "account_type": "checking"},
    # Mei Chen
    {"account_id": "acc_mei_checking",    "user_id": "usr_mei_chen",       "account_type": "checking"},
    # Ivan Petrov
    {"account_id": "acc_ivan_checking",   "user_id": "usr_ivan_petrov",    "account_type": "checking"},
    {"account_id": "acc_ivan_savings",    "user_id": "usr_ivan_petrov",    "account_type": "savings"},
]

# ─── Cards (1–2 per account, deterministic) ───────────────────────────────────

CARDS: list[dict] = [
    # Emma Johnson
    {"card_id": "crd_emma_visa",       "card_last_four": "4821", "card_type": "VISA",       "account_id": "acc_emma_checking",   "user_id": "usr_emma_johnson"},
    {"card_id": "crd_emma_mc",         "card_last_four": "9034", "card_type": "MASTERCARD", "account_id": "acc_emma_savings",    "user_id": "usr_emma_johnson"},
    # Luca Ferrari
    {"card_id": "crd_luca_visa",       "card_last_four": "1573", "card_type": "VISA",       "account_id": "acc_luca_checking",   "user_id": "usr_luca_ferrari"},
    {"card_id": "crd_luca_amex",       "card_last_four": "6609", "card_type": "AMEX",       "account_id": "acc_luca_checking",   "user_id": "usr_luca_ferrari"},
    # Sofia Garcia
    {"card_id": "crd_sofia_visa",      "card_last_four": "2290", "card_type": "VISA",       "account_id": "acc_sofia_checking",  "user_id": "usr_sofia_garcia"},
    {"card_id": "crd_sofia_biz_mc",    "card_last_four": "8847", "card_type": "MASTERCARD", "account_id": "acc_sofia_business",  "user_id": "usr_sofia_garcia"},
    # James Miller
    {"card_id": "crd_james_mc",        "card_last_four": "3312", "card_type": "MASTERCARD", "account_id": "acc_james_checking",  "user_id": "usr_james_miller"},
    # Amina Diallo
    {"card_id": "crd_amina_visa",      "card_last_four": "7765", "card_type": "VISA",       "account_id": "acc_amina_checking",  "user_id": "usr_amina_diallo"},
    {"card_id": "crd_amina_mc",        "card_last_four": "4401", "card_type": "MASTERCARD", "account_id": "acc_amina_savings",   "user_id": "usr_amina_diallo"},
    # Noah Kim
    {"card_id": "crd_noah_visa",       "card_last_four": "5538", "card_type": "VISA",       "account_id": "acc_noah_checking",   "user_id": "usr_noah_kim"},
    # Chloé Martin
    {"card_id": "crd_chloe_visa",      "card_last_four": "0192", "card_type": "VISA",       "account_id": "acc_chloe_checking",  "user_id": "usr_chloe_martin"},
    {"card_id": "crd_chloe_amex",      "card_last_four": "7723", "card_type": "AMEX",       "account_id": "acc_chloe_checking",  "user_id": "usr_chloe_martin"},
    # Rafael Silva
    {"card_id": "crd_rafael_mc",       "card_last_four": "6684", "card_type": "MASTERCARD", "account_id": "acc_rafael_checking", "user_id": "usr_rafael_silva"},
    {"card_id": "crd_rafael_visa",     "card_last_four": "3359", "card_type": "VISA",       "account_id": "acc_rafael_savings",  "user_id": "usr_rafael_silva"},
    # Yuki Tanaka
    {"card_id": "crd_yuki_visa",       "card_last_four": "9901", "card_type": "VISA",       "account_id": "acc_yuki_checking",   "user_id": "usr_yuki_tanaka"},
    # Oliver Schmidt
    {"card_id": "crd_oliver_mc",       "card_last_four": "2267", "card_type": "MASTERCARD", "account_id": "acc_oliver_checking", "user_id": "usr_oliver_schmidt"},
    {"card_id": "crd_oliver_visa",     "card_last_four": "8814", "card_type": "VISA",       "account_id": "acc_oliver_checking", "user_id": "usr_oliver_schmidt"},
    # Fatima Hassan
    {"card_id": "crd_fatima_visa",     "card_last_four": "5576", "card_type": "VISA",       "account_id": "acc_fatima_checking", "user_id": "usr_fatima_hassan"},
    {"card_id": "crd_fatima_mc",       "card_last_four": "1143", "card_type": "MASTERCARD", "account_id": "acc_fatima_savings",  "user_id": "usr_fatima_hassan"},
    # Ethan Brown
    {"card_id": "crd_ethan_visa",      "card_last_four": "4498", "card_type": "VISA",       "account_id": "acc_ethan_checking",  "user_id": "usr_ethan_brown"},
    # Inès Dupont
    {"card_id": "crd_ines_mc",         "card_last_four": "7730", "card_type": "MASTERCARD", "account_id": "acc_ines_checking",   "user_id": "usr_ines_dupont"},
    # Carlos Méndez
    {"card_id": "crd_carlos_visa",     "card_last_four": "2285", "card_type": "VISA",       "account_id": "acc_carlos_checking", "user_id": "usr_carlos_mendez"},
    {"card_id": "crd_carlos_biz_amex", "card_last_four": "9962", "card_type": "AMEX",       "account_id": "acc_carlos_business", "user_id": "usr_carlos_mendez"},
    # Priya Patel
    {"card_id": "crd_priya_mc",        "card_last_four": "6617", "card_type": "MASTERCARD", "account_id": "acc_priya_checking",  "user_id": "usr_priya_patel"},
    # Max Weber
    {"card_id": "crd_max_visa",        "card_last_four": "3374", "card_type": "VISA",       "account_id": "acc_max_checking",    "user_id": "usr_max_weber"},
    {"card_id": "crd_max_mc",          "card_last_four": "0051", "card_type": "MASTERCARD", "account_id": "acc_max_checking",    "user_id": "usr_max_weber"},
    # Aisha Okonkwo
    {"card_id": "crd_aisha_visa",      "card_last_four": "8829", "card_type": "VISA",       "account_id": "acc_aisha_checking",  "user_id": "usr_aisha_okonkwo"},
    {"card_id": "crd_aisha_mc",        "card_last_four": "5506", "card_type": "MASTERCARD", "account_id": "acc_aisha_savings",   "user_id": "usr_aisha_okonkwo"},
    # Tom Anderson
    {"card_id": "crd_tom_visa",        "card_last_four": "1163", "card_type": "VISA",       "account_id": "acc_tom_checking",    "user_id": "usr_tom_anderson"},
    # Mei Chen
    {"card_id": "crd_mei_mc",          "card_last_four": "4420", "card_type": "MASTERCARD", "account_id": "acc_mei_checking",    "user_id": "usr_mei_chen"},
    {"card_id": "crd_mei_visa",        "card_last_four": "7797", "card_type": "VISA",       "account_id": "acc_mei_checking",    "user_id": "usr_mei_chen"},
    # Ivan Petrov
    {"card_id": "crd_ivan_mc",         "card_last_four": "2254", "card_type": "MASTERCARD", "account_id": "acc_ivan_checking",   "user_id": "usr_ivan_petrov"},
    {"card_id": "crd_ivan_visa",       "card_last_four": "9931", "card_type": "VISA",       "account_id": "acc_ivan_savings",    "user_id": "usr_ivan_petrov"},
]

# ─── Merchants ────────────────────────────────────────────────────────────────

MERCHANTS: list[dict] = [
    {"merchant_id": "mrc_amazon",      "merchant_name": "Amazon",         "merchant_category": "5999", "merchant_country": "US"},
    {"merchant_id": "mrc_starbucks",   "merchant_name": "Starbucks",      "merchant_category": "5812", "merchant_country": "US"},
    {"merchant_id": "mrc_uber",        "merchant_name": "Uber",           "merchant_category": "4121", "merchant_country": "US"},
    {"merchant_id": "mrc_netflix",     "merchant_name": "Netflix",        "merchant_category": "7841", "merchant_country": "US"},
    {"merchant_id": "mrc_tesco",       "merchant_name": "Tesco",          "merchant_category": "5411", "merchant_country": "GB"},
    {"merchant_id": "mrc_ikea",        "merchant_name": "IKEA",           "merchant_category": "5712", "merchant_country": "SE"},
    {"merchant_id": "mrc_shell",       "merchant_name": "Shell",          "merchant_category": "5541", "merchant_country": "NL"},
    {"merchant_id": "mrc_apple",       "merchant_name": "Apple Store",    "merchant_category": "5734", "merchant_country": "US"},
    {"merchant_id": "mrc_booking",     "merchant_name": "Booking.com",    "merchant_category": "7011", "merchant_country": "NL"},
    {"merchant_id": "mrc_steam",       "merchant_name": "Steam",          "merchant_category": "7994", "merchant_country": "US"},
    {"merchant_id": "mrc_carrefour",   "merchant_name": "Carrefour",      "merchant_category": "5411", "merchant_country": "FR"},
    {"merchant_id": "mrc_zalando",     "merchant_name": "Zalando",        "merchant_category": "5691", "merchant_country": "DE"},
    {"merchant_id": "mrc_spotify",     "merchant_name": "Spotify",        "merchant_category": "7929", "merchant_country": "SE"},
    {"merchant_id": "mrc_airbnb",      "merchant_name": "Airbnb",         "merchant_category": "7011", "merchant_country": "US"},
    {"merchant_id": "mrc_paypal",      "merchant_name": "PayPal",         "merchant_category": "6012", "merchant_country": "US"},
    {"merchant_id": "mrc_lidl",        "merchant_name": "Lidl",           "merchant_category": "5411", "merchant_country": "DE"},
    {"merchant_id": "mrc_trainline",   "merchant_name": "Trainline",      "merchant_category": "4112", "merchant_country": "GB"},
    {"merchant_id": "mrc_deliveroo",   "merchant_name": "Deliveroo",      "merchant_category": "5812", "merchant_country": "GB"},
    {"merchant_id": "mrc_h_and_m",     "merchant_name": "H&M",            "merchant_category": "5691", "merchant_country": "SE"},
    {"merchant_id": "mrc_mediamarkt",  "merchant_name": "MediaMarkt",     "merchant_category": "5734", "merchant_country": "DE"},
]

# ─── Devices ──────────────────────────────────────────────────────────────────

DEVICES: list[dict] = [
    {"device_id": "dev_emma_iphone",    "device_type": "mobile",  "device_fingerprint": "a1b2c3d4e5f60001"},
    {"device_id": "dev_luca_android",   "device_type": "mobile",  "device_fingerprint": "a1b2c3d4e5f60002"},
    {"device_id": "dev_sofia_macbook",  "device_type": "desktop", "device_fingerprint": "a1b2c3d4e5f60003"},
    {"device_id": "dev_james_ipad",     "device_type": "tablet",  "device_fingerprint": "a1b2c3d4e5f60004"},
    {"device_id": "dev_amina_iphone",   "device_type": "mobile",  "device_fingerprint": "a1b2c3d4e5f60005"},
    {"device_id": "dev_noah_galaxy",    "device_type": "mobile",  "device_fingerprint": "a1b2c3d4e5f60006"},
    {"device_id": "dev_chloe_laptop",   "device_type": "desktop", "device_fingerprint": "a1b2c3d4e5f60007"},
    {"device_id": "dev_rafael_android", "device_type": "mobile",  "device_fingerprint": "a1b2c3d4e5f60008"},
    {"device_id": "dev_yuki_iphone",    "device_type": "mobile",  "device_fingerprint": "a1b2c3d4e5f60009"},
    {"device_id": "dev_oliver_pc",      "device_type": "desktop", "device_fingerprint": "a1b2c3d4e5f60010"},
    {"device_id": "dev_fatima_iphone",  "device_type": "mobile",  "device_fingerprint": "a1b2c3d4e5f60011"},
    {"device_id": "dev_shared_pos",     "device_type": "pos",     "device_fingerprint": "a1b2c3d4e5f60012"},
]

# ─── IP Pool ──────────────────────────────────────────────────────────────────

IP_POOL: list[dict] = [
    {"ip_address": "203.0.113.10",  "ip_country": "US"},
    {"ip_address": "203.0.113.11",  "ip_country": "US"},
    {"ip_address": "203.0.113.12",  "ip_country": "US"},
    {"ip_address": "198.51.100.10", "ip_country": "GB"},
    {"ip_address": "198.51.100.11", "ip_country": "GB"},
    {"ip_address": "192.0.2.10",    "ip_country": "DE"},
    {"ip_address": "192.0.2.11",    "ip_country": "DE"},
    {"ip_address": "192.0.2.50",    "ip_country": "FR"},
    {"ip_address": "192.0.2.51",    "ip_country": "FR"},
    {"ip_address": "192.0.2.100",   "ip_country": "NL"},
    {"ip_address": "10.0.1.10",     "ip_country": "SE"},
    {"ip_address": "10.0.2.10",     "ip_country": "IT"},
    {"ip_address": "100.64.1.10",   "ip_country": "ES"},
    {"ip_address": "100.64.2.10",   "ip_country": "CA"},
    {"ip_address": "100.64.3.10",   "ip_country": "JP"},
]
