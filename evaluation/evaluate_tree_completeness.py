import json
import re
from pathlib import Path
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

GOLD_PATH = BASE_DIR / "gold_dataset.json"
ETYMOLOGY_PATH = PROJECT_DIR / "data" / "etymologies.json"

REGEX_PRED_PATH = PROJECT_DIR / "extraction" / "regex_predictions.json"
FLAN_PRED_PATH = PROJECT_DIR / "transformer" / "data" / "flan_predictions.json"

RESULTS_DIR = PROJECT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

OUTPUT_PATH = RESULTS_DIR / "tree_completeness_report.json"

ALLOWED_RELATIONS = {"ancestor", "descendant", "language_ancestor"}


def clean_text(text):
    return re.sub(r"\s+", " ", str(text).strip())


def normalize_relation(rel):
    if not isinstance(rel, list) or len(rel) != 3:
        return None

    parent = clean_text(rel[0])
    child = clean_text(rel[1])
    relation = clean_text(rel[2])

    if relation not in ALLOWED_RELATIONS:
        return None

    return parent, child, relation


def to_relation_set(relations):
    output = set()

    for rel in relations:
        normalized = normalize_relation(rel)
        if normalized:
            output.add(normalized)

    return output


def load_categories():
    with open(ETYMOLOGY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        item["word"].lower(): item.get("category", "unknown")
        for item in data
    }


def load_gold():
    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        item["word"].lower(): to_relation_set(item["gold_relations"])
        for item in data
    }


def load_predictions(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        item["word"].lower(): to_relation_set(item["predicted_relations"])
        for item in data
    }


def evaluate_system(system_name, pred_path, gold_map, category_map):
    pred_map = load_predictions(pred_path)

    overall_scores = []
    by_category = defaultdict(list)

    for word, gold_relations in gold_map.items():
        pred_relations = pred_map.get(word, set())
        category = category_map.get(word, "unknown")

        if len(gold_relations) == 0:
            score = 0
        else:
            correct = len(gold_relations & pred_relations)
            score = correct / len(gold_relations)

        overall_scores.append(score)
        by_category[category].append(score)

    overall_avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0

    category_results = {}

    for category, scores in by_category.items():
        category_results[category] = {
            "words": len(scores),
            "average_tree_completeness": round(sum(scores) / len(scores), 4)
        }

    return {
        "system": system_name,
        "total_words": len(overall_scores),
        "average_tree_completeness": round(overall_avg, 4),
        "by_category": category_results
    }


def main():
    gold_map = load_gold()
    category_map = load_categories()

    report = {
        "metric": "Average Tree Completeness",
        "definition": "For each word, correct gold relations divided by total gold relations, then averaged across words.",
        "systems": {
            "regex": evaluate_system(
                "Regex",
                REGEX_PRED_PATH,
                gold_map,
                category_map
            ),
            "flan_t5": evaluate_system(
                "FLAN-T5",
                FLAN_PRED_PATH,
                gold_map,
                category_map
            )
        }
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n=== TREE COMPLETENESS EVALUATION ===")

    for key, result in report["systems"].items():
        print(f"\n{result['system']}")
        print(f"Average Tree Completeness: {result['average_tree_completeness']}")

        for category, values in result["by_category"].items():
            print(
                f"  {category}: "
                f"{values['average_tree_completeness']} "
                f"({values['words']} words)"
            )

    print("\nSaved:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()