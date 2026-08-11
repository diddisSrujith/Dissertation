import requests
from bs4 import BeautifulSoup

URL = "https://en.wiktionary.org/w/api.php"

params = {
    "action": "parse",
    "page": "Wiktionary:List_of_languages,_csv_format",
    "prop": "text",
    "format": "json"
}

headers = {
    "User-Agent": "OED-Etymology-Dissertation/1.0"
}

response = requests.get(
    URL,
    params=params,
    headers=headers
)

print("STATUS:", response.status_code)

data = response.json()

html = data["parse"]["text"]["*"]

soup = BeautifulSoup(html, "html.parser")

# CSV is inside <pre>
pre = soup.find("pre")

if not pre:
    print("No CSV block found")
    exit()

csv_text = pre.get_text()

with open(
    "data/languages.csv",
    "w",
    encoding="utf-8"
) as f:

    f.write(csv_text)

print("CSV downloaded successfully")