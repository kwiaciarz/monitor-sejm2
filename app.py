from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

KOMISJE = ["OSZ", "GOR", "CNT", "DER", "GOR01S", "GOR02S", "GOR03S", "OSZ01S", "OSZ03S"]
KADENCJA = 10

HTML_TEMPLATE = """
# Posiedzenia komisji Sejmu RP
## Monitor posiedzeń komisji Sejmu RP
{% for komisja, posiedzenia in dane.items() %}
### {{ komisja }}

{% if posiedzenia %}
{% for p in posiedzenia %}
{{ p.get('date') }} – {{ p.get('title') }}
{% endfor %}
{% else %}
Brak zaplanowanych posiedzeń.
{% endif %}

{% endfor %}
"""

def pobierz_posiedzenia_api(kod):
    url = f"https://api.sejm.gov.pl/sejm/term/{KADENCJA}/committees/{kod}/sittings"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            dane = res.json()
            print(f"API ({kod}): znaleziono {len(dane)} posiedzeń.")
            return [{"date": p.get("date"), "title": p.get("title")} for p in dane]
        else:
            print(f"API ({kod}): kod odpowiedzi {res.status_code}")
    except Exception as e:
        print(f"Błąd API dla {kod}: {e}")
    return []

def pobierz_posiedzenia_html(kod):
    url = f"https://www.sejm.gov.pl/Sejm10.nsf/PlanPosKom.xsp?view=2&komisja={kod}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            print(f"HTML ({kod}): kod odpowiedzi {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select("table tr")[1:]  # pomijamy nagłówek
        posiedzenia = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                date = cols[0].get_text(strip=True)
                title = cols[1].get_text(strip=True)
                posiedzenia.append({"date": date, "title": title})

        print(f"HTML ({kod}): znaleziono {len(posiedzenia)} posiedzeń.")
        return posiedzenia

    except Exception as e:
        print(f"Błąd HTML dla {kod}: {e}")
        return []

@app.route("/")
def index():
    dane = {}
    for kod in KOMISJE:
        z_api = pobierz_posiedzenia_api(kod)
        z_html = pobierz_posiedzenia_html(kod)
        dane[kod] = z_api + z_html
    return render_template_string(HTML_TEMPLATE, dane=dane)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
