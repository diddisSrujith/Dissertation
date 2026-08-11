import json
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

ETYMOLOGIES_PATH = BASE_DIR / "data" / "etymologies.json"
GOLD_PATH = BASE_DIR / "evaluation" / "gold_dataset.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "data"

RANDOM_SEED = 42


def make_input(entry):
    return (
        "Extract etymological relations.\n"
        "Return only triples in this exact format:\n"
        "Parent|Child|Relation\n"
        "Allowed relations: ancestor, descendant, language_ancestor.\n"
        "No explanations. No extra text.\n\n"
        f"Word: {entry['word']}\n"
        f"Origin: {entry.get('origin', '').strip()}\n"
        f"Etymology: {entry.get('etymology', '').strip()}"
    )


def make_target(gold_relations):
    cleaned = []

    for parent, child, relation in gold_relations:
        relation = relation.strip().split()[0]

        if relation not in {"ancestor", "descendant", "language_ancestor"}:
            continue

        cleaned.append(f"{parent.strip()}|{child.strip()}|{relation}")

    return "\n".join(cleaned)

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(ETYMOLOGIES_PATH, "r", encoding="utf-8") as f:
        etymologies = json.load(f)

    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    gold_map = {
        item["word"].lower(): item["gold_relations"]
        for item in gold_data
        if "word" in item and "gold_relations" in item
    }

    examples = []

    for entry in etymologies:
        word = entry["word"].lower()

        if word not in gold_map:
            continue

        gold_relations = gold_map[word]

        if not isinstance(gold_relations, list):
            continue

        examples.append({
            "word": word,
            "input": make_input(entry),
            "target": make_target(gold_relations)
        })

    random.seed(RANDOM_SEED)
    random.shuffle(examples)

    n = len(examples)
    train_end = int(n * 0.8)
    valid_end = int(n * 0.9)

    splits = {
        "train.json": examples[:train_end],
        "valid.json": examples[train_end:valid_end],
        "test.json": examples[valid_end:]
    }

    for filename, data in splits.items():
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Total examples: {n}")
    print(f"Train: {len(splits['train.json'])}")
    print(f"Valid: {len(splits['valid.json'])}")
    print(f"Test: {len(splits['test.json'])}")


if __name__ == "__main__":
    main()