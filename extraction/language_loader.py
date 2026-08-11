import json

def load_languages(
    lang_path="data/languages.json",
    family_path="data/language_families.json"
):
    # Load main ISO language list
    with open(lang_path, encoding="utf-8") as f:
        languages = json.load(f)

    # Load language families and OED-specific extras
    try:
        with open(family_path, encoding="utf-8") as f:
            families = json.load(f)
        # Families go first so they're matched preferentially
        languages = families + languages
    except FileNotFoundError:
        print("Warning: language_families.json not found, using ISO list only")

    # Deduplicate preserving order
    seen = set()
    unique = []
    for lang in languages:
        if lang not in seen:
            seen.add(lang)
            unique.append(lang)

    # Sort longest first — critical for regex alternation to work correctly
    return sorted(unique, key=len, reverse=True)