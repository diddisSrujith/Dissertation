import csv
import json

languages = []

with open("data/languages.csv", encoding="utf-8") as f:

    reader = csv.DictReader(
        f,
        delimiter=";"
    )

    for row in reader:

        name = row["canonical name"]

        if name:
            languages.append(name.strip())

languages = sorted(
    set(languages),
    key=len,
    reverse=True
)

print("TOTAL:", len(languages))

with open(
    "data/languages.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        languages,
        f,
        indent=2,
        ensure_ascii=False
    )

print("Saved languages.json")