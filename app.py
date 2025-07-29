from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

KOMISJE = ["OSZ", "GOR", "CNT", "DER", "GOR01S", "GOR02S", "GOR03S", "OSZ01S", "OSZ03S"]
KADENCJA = 10

HTML_TEMPLATE = """
<!doctype html>
<html lang="pl">
<head>
    <meta charset="utf-8">
    <title>Posiedzenia komisji Sejmu RP</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        h1 { color: #003366; }
        .komisja { margin-bottom: 2em; }
        .posiedzenie { margin-left: 1em; }
    </style>
</head>
<body>
    <h1>Monitor posiedzeń komisji Sejmu RP</h1>
    {% for komisja, posiedzenia in dane.items() %}
        <div class="komisja">
            <h2>{{ komisja }}</h2>
            {% if posiedzenia %}
                {% for p in posiedzenia %}
                    <div class="posiedzenie">
                        <strong>{{ p.get('date') }}</strong> – {{ p.get('title') }}
                    </div>
                {% endfor %}
            {% else %}
                <p>Brak zaplanowanych posiedzeń.</p>
            {% endif %}
        </div>
    {% endfor %}
</body>
</html>
"""

def pobierz_posiedzenia_api(kod):
    url = f"https://api.sejm.gov.pl/sejm/term/{KADENCJA}/committees/{kod}/sittings"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Błąd API dla {kod}: {e}")
    return []

def pobierz_posiedzenia_html(komisja_kod="DER"):
    url = f"https://www.sejm.gov.pl/Sejm10.nsf/PlanPosKom.xsp?view=2&komisja={komisja_kod}"
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        tabela = soup.find("table", class_="tab_pos")
        if not tabela:
            return []
        posiedzenia = []
        for wiersz in tabela.find_all("tr")[1:]:
            komorki = wiersz.find_all("td")
            if len(komorki) >= 2:
                data = komorki[0].get_text(strip=True)
                tytul = komorki[1].get_text(strip=True)
                posiedzenia.append({"date": data, "title": tytul})
        return posiedzenia
    except Exception as e:
        print(f"Błąd HTML dla {komisja_kod}: {e}")
        return []

@app.route("/")
def index():
    dane = {}
    for kod in KOMISJE:
        z_api = pobierz_posiedzenia_api(kod)
        z_html = pobierz_posiedzenia_html(kod) if kod == "DER" else []
        dane[kod] = z_api + z_html
    return render_template_string(HTML_TEMPLATE, dane=dane)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
