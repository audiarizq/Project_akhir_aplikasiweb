import csv
import json
import sqlite3
from pathlib import Path
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "badmimate-development-key"
DATABASE = Path(__file__).with_name("badmimate.db")
DATA_DIR = Path(__file__).with_name("data")


def _number(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _format_price(value):
    amount = _number(value)
    return f"Rp{amount:,.0f}".replace(",", ".") if amount is not None else ""


def _price_label(lapangan):
    minimum = _format_price(lapangan.get("harga_per_jam_min"))
    maximum = _format_price(lapangan.get("harga_per_jam_max"))
    if minimum and maximum and minimum != maximum:
        return f"{minimum}–{maximum}"
    return minimum or maximum or "Hubungi pengelola"


def _time_label(value):
    value = (value or "").strip()
    return value[:5] if len(value) >= 5 and value[2] == ":" else value


def load_courts():
    """Combine venue data with individual court data using id_gor."""
    venue_paths = (
        DATA_DIR / "data_gor_sleman-v3.csv",
    )
    venue_path = next((path for path in venue_paths if path.exists()), None)
    court_path = DATA_DIR / "data_lapangan_gor_sleman-v3.csv"
    if not venue_path or not court_path.exists():
        return None

    with venue_path.open(newline="", encoding="utf-8-sig") as file:
        venue_rows = list(csv.DictReader(file))
    with court_path.open(newline="", encoding="utf-8-sig") as file:
        court_rows = list(csv.DictReader(file))

    courts_by_gor = {}
    for row in court_rows:
        courts_by_gor.setdefault(row.get("id_gor", "").strip(), []).append({
            "id": row.get("id_lapangan", "").strip(),
            "name": row.get("nama_lapangan", "").strip(),
            "floor": row.get("jenis_lantai", "").strip() or "Belum tersedia",
            "price": _price_label(row),
            "price_min": row.get("harga_per_jam_min", "").strip(),
            "price_max": row.get("harga_per_jam_max", "").strip(),
            "package": row.get("harga_paket", "").strip(),
            "package_hours": row.get("durasi_paket_jam", "").strip(),
            "note": row.get("catatan_tarif", "").strip(),
            "status": row.get("status_lapangan", "").strip() or "Belum tersedia",
        })

    tones = ("purple", "green", "orange", "blue")
    result = []
    for index, row in enumerate(venue_rows, start=1):
        venue_id = (row.get("id_gor") or f"GOR-SLM-{index:03d}").strip()
        individual_courts = courts_by_gor.get(venue_id, [])
        if not individual_courts:
            continue
        location_parts = [row.get("kecamatan", "").strip(), row.get("kabupaten", "").strip()]
        location = ", ".join(part for part in location_parts if part)
        hours = "–".join(filter(None, [_time_label(row.get("jam_buka")), _time_label(row.get("jam_tutup"))])) or "Informasi belum tersedia"
        priced_court = next((court for court in individual_courts if court["price"] != "Hubungi pengelola"), individual_courts[0])
        result.append({
            "id": venue_id,
            "name": row.get("nama_gor", "").strip(),
            "location": location or row.get("kabupaten", "").strip(),
            "address": row.get("alamat", "").strip(),
            "latitude": _number(row.get("latitude")),
            "longitude": _number(row.get("longitude")),
            "price": priced_court["price"],
            "tone": tones[(index - 1) % len(tones)],
            "description": row.get("deskripsi", "").strip() or "Informasi deskripsi venue belum tersedia.",
            "hours": hours,
            "facilities": row.get("fasilitas", "").strip() or "Informasi fasilitas belum tersedia.",
            "courts": f"{len(individual_courts)} lapangan",
            "court_details": individual_courts,
            "google_maps": row.get("link_google_maps", "").strip(),
            "contact": row.get("kontak", "").strip(),
            "verification": row.get("status_verifikasi", "").strip(),
            "photo_url": row.get("foto_url", "").strip(),
        })
    return result


def fallback_courts():
    return [
        {"name": "GOR Cempaka Badminton", "location": "Bandung", "price": "Rp80.000", "tone": "purple", "description": "Lapangan badminton nyaman untuk bermain santai, latihan rutin, dan sparring bersama komunitas.", "hours": "07.00–22.00", "facilities": "Parkir, kamar mandi, kantin, dan ruang tunggu", "courts": "1 lapangan", "court_details": []},
        {"name": "Arena Smash Jakarta", "location": "Jakarta Selatan", "price": "Rp95.000", "tone": "green", "description": "Venue badminton strategis dengan suasana nyaman untuk bermain bersama teman.", "hours": "06.00–23.00", "facilities": "Parkir, kamar mandi, mushola, dan kantin", "courts": "3 lapangan", "court_details": []},
        {"name": "Prima Badminton Center", "location": "Depok", "price": "Rp70.000", "tone": "orange", "description": "Lapangan pilihan untuk latihan dan pertandingan badminton komunitas.", "hours": "07.00–22.00", "facilities": "Parkir, kamar mandi, dan ruang tunggu", "courts": "2 lapangan", "court_details": []},
        {"name": "GOR Satria Mandala", "location": "Bekasi", "price": "Rp65.000", "tone": "blue", "description": "GOR badminton dengan akses mudah dan area bermain yang luas.", "hours": "08.00–22.00", "facilities": "Parkir, kamar mandi, dan kantin", "courts": "4 lapangan", "court_details": []},
        {"name": "Nusantara Badminton Hall", "location": "Tangerang", "price": "Rp85.000", "tone": "purple", "description": "Venue indoor untuk bermain badminton dengan keluarga, teman, atau komunitas.", "hours": "06.00–22.00", "facilities": "Parkir, kamar mandi, mushola, dan ruang tunggu", "courts": "3 lapangan", "court_details": []},
        {"name": "Victory Badminton Arena", "location": "Bogor", "price": "Rp75.000", "tone": "green", "description": "Lapangan badminton dengan suasana asri dan fasilitas yang mendukung permainan.", "hours": "07.00–21.00", "facilities": "Parkir, kamar mandi, dan kantin", "courts": "2 lapangan", "court_details": []},
    ]


def init_database():
    with sqlite3.connect(DATABASE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                level TEXT NOT NULL,
                score REAL NOT NULL,
                assessment TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS match_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                opponent TEXT NOT NULL,
                venue TEXT NOT NULL,
                played_at TEXT NOT NULL,
                result TEXT NOT NULL,
                score TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS received_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reviewer TEXT NOT NULL,
                aspect TEXT NOT NULL,
                stars INTEGER NOT NULL,
                review TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


init_database()


@app.route("/")
def index():
    rooms = [
        {"title": "Fun Match Jumat Malam", "place": "GOR Cempaka, Bandung", "date": "Jumat, 21 Nov", "date_value": "2026-11-21", "time": "19.00–21.00", "level": "Menengah", "price": "Rp35k", "slots": "2 slot tersisa", "tone": "purple"},
        {"title": "Belajar Bareng Pemula", "place": "Arena Smash, Jakarta", "date": "Sabtu, 22 Nov", "date_value": "2026-11-22", "time": "08.00–10.00", "level": "Pemula", "price": "Rp25k", "slots": "4 slot tersisa", "tone": "green"},
        {"title": "Sparring Kompetitif", "place": "Prima Badminton, Depok", "date": "Minggu, 23 Nov", "date_value": "2026-11-23", "time": "16.00–18.00", "level": "Jago", "price": "Rp45k", "slots": "1 slot tersisa", "tone": "orange"},
    ]
    courts = load_courts() or fallback_courts()
    return render_template("index.html", rooms=rooms, courts=courts)


@app.post("/register")
def register():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "")

    if not all((full_name, email, phone, password, confirmation)):
        flash("Semua data pendaftaran wajib diisi.", "error")
    elif password != confirmation:
        flash("Konfirmasi password tidak sama.", "error")
    else:
        try:
            with sqlite3.connect(DATABASE) as connection:
                connection.execute(
                    "INSERT INTO users (full_name, email, phone, password) VALUES (?, ?, ?, ?)",
                    (full_name, email, phone, password),
                )
            flash("Pendaftaran berhasil. Silakan masuk dengan akun Anda.", "success")
        except sqlite3.IntegrityError:
            flash("Email tersebut sudah terdaftar.", "error")

    return redirect(url_for("index") + "#login")


@app.post("/login")
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    with sqlite3.connect(DATABASE) as connection:
        user = connection.execute(
            "SELECT id, full_name, password FROM users WHERE email = ?", (email,)
        ).fetchone()

    if user and user[2] == password:
        session["user_id"] = user[0]
        session["user_name"] = user[1]
        flash(f"Selamat datang, {user[1]}!", "success")
        return redirect(url_for("profile"))

    flash("Email atau password salah.", "error")
    return redirect(url_for("index") + "#login")


def logged_in_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with sqlite3.connect(DATABASE) as connection:
        return connection.execute(
            "SELECT id, full_name, email, phone FROM users WHERE id = ?", (user_id,)
        ).fetchone()


@app.route("/profile")
def profile():
    user = logged_in_user()
    if not user:
        flash("Silakan masuk terlebih dahulu.", "error")
        return redirect(url_for("index") + "#login")

    with sqlite3.connect(DATABASE) as connection:
        profile_data = connection.execute(
            "SELECT level, score, assessment, completed_at FROM profiles WHERE user_id = ?",
            (user[0],),
        ).fetchone()
        matches = connection.execute(
            "SELECT opponent, venue, played_at, result, score FROM match_history "
            "WHERE user_id = ? ORDER BY id DESC", (user[0],)
        ).fetchall()
        ratings = connection.execute(
            "SELECT reviewer, aspect, stars, review, created_at FROM received_ratings "
            "WHERE user_id = ? ORDER BY id DESC", (user[0],)
        ).fetchall()

    assessment = json.loads(profile_data[2]) if profile_data else None
    wins = sum(1 for match in matches if match[3] == "Menang")
    losses = sum(1 for match in matches if match[3] == "Kalah")
    return render_template(
        "profile.html", user=user, profile_data=profile_data,
        assessment=assessment, matches=matches, ratings=ratings,
        wins=wins, losses=losses, section=request.args.get("section", "home"),
    )


@app.post("/profile/assessment")
def save_assessment():
    user = logged_in_user()
    if not user:
        return redirect(url_for("index") + "#login")

    fields = [
        "serve", "clear", "drop", "smash", "netting", "drive", "backhand",
        "return_service", "footwork", "stamina", "agility", "experience",
        "tactics", "sportsmanship", "enjoyment",
    ]
    try:
        assessment = {field: int(request.form[field]) for field in fields}
        if any(value < 1 or value > 5 for value in assessment.values()):
            raise ValueError
    except (KeyError, ValueError):
        flash("Lengkapi semua penilaian dengan pilihan yang tersedia.", "error")
        return redirect(url_for("profile"))

    technique = sum(assessment[field] for field in fields[:8]) / 8
    groups = {
        "Teknik pukulan": technique,
        "Footwork": assessment["footwork"],
        "Kondisi fisik": (assessment["stamina"] + assessment["agility"]) / 2,
        "Pengalaman bermain": assessment["experience"],
        "Taktik": assessment["tactics"],
        "Sikap di lapangan": (assessment["sportsmanship"] + assessment["enjoyment"]) / 2,
    }
    weights = {
        "Teknik pukulan": 0.35, "Footwork": 0.15, "Kondisi fisik": 0.15,
        "Pengalaman bermain": 0.15, "Taktik": 0.15, "Sikap di lapangan": 0.05,
    }
    score = round(sum(groups[name] * weights[name] for name in groups), 2)
    level = "Pemula" if score < 2.5 else "Menengah" if score < 3.75 else "Jago"
    saved_data = {"answers": assessment, "groups": groups, "weights": weights}

    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO profiles "
            "(user_id, level, score, assessment, completed_at) VALUES (?, ?, ?, ?, ?)",
            (user[0], level, score, json.dumps(saved_data), datetime.now().isoformat()),
        )
    flash("Penilaian awal berhasil disimpan. Selamat datang di profilmu!", "success")
    return redirect(url_for("profile"))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
