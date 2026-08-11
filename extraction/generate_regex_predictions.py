import json
from pathlib import Path

from extraction.parser_extractor import extract


PROJECT_DIR = Path(__file__).resolve().parent.parent

ETYMOLOGY_PATH = PROJECT_DIR / "data" / "etymologies.json"
OUTPUT_PATH = PROJECT_DIR / "extraction" / "regex_predictions.json"


def load_etymologies():
    with open(ETYMOLOGY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    entries = load_etymologies()
    predictions = []

    print(f"Total words loaded: {len(entries)}")

    for i, entry in enumerate(entries, start=1):
        word = entry["word"]
        origin = entry.get("origin", "")
        etymology = entry.get("etymology", "")

        try:
            relations = extract(origin, etymology, word.capitalize())

            predictions.append({
                "word": word,
                "predicted_relations": relations
            })

            print(f"[{i}/{len(entries)}] Processed: {word}")

        except Exception as e:
            predictions.append({
                "word": word,
                "predicted_relations": [],
                "error": str(e)
            })

            print(f"[{i}/{len(entries)}] Failed: {word} | {e}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False)

    print("\nSaved regex predictions to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()