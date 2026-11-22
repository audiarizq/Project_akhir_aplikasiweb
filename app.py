from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    rooms = [
        {"title": "Fun Match Jumat Malam", "place": "GOR Cempaka, Bandung", "date": "Jumat, 21 Nov", "time": "19.00–21.00", "level": "Menengah", "price": "Rp35k", "slots": "2 slot tersisa", "tone": "purple"},
        {"title": "Belajar Bareng Pemula", "place": "Arena Smash, Jakarta", "date": "Sabtu, 22 Nov", "time": "08.00–10.00", "level": "Pemula", "price": "Rp25k", "slots": "4 slot tersisa", "tone": "green"},
        {"title": "Sparring Kompetitif", "place": "Prima Badminton, Depok", "date": "Minggu, 23 Nov", "time": "16.00–18.00", "level": "Jago", "price": "Rp45k", "slots": "1 slot tersisa", "tone": "orange"},
    ]
    return render_template("index.html", rooms=rooms)


if __name__ == "__main__":
    app.run(debug=True)
