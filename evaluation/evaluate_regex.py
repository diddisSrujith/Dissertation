import json
import re
from pathlib import Path
from collections import defaultdict


# -------------------------------------------------
# PATHS
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

GOLD_PATH = BASE_DIR / "gold_dataset.json"
PRED_PATH = PROJECT_DIR / "extraction" / "regex_predictions.json"
ETYMOLOGY_PATH = PROJECT_DIR / "data" / "etymologies.json"

RESULTS_DIR = PROJECT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

REPORT_JSON = RESULTS_DIR / "regex_eval_report.json"

ALLOWED_RELATIONS = {
    "ancestor",
    "descendant",
    "language_ancestor",
}


# -------------------------------------------------
# NORMALISATION
# -------------------------------------------------
def clean_text(text):
    text = str(text).strip()
    return re.sub(r"\s+", " ", text)


def language_from_node(name):
    """
    Old Saxon (thorn) -> Old Saxon
    Germanic -> Germanic
    """
    name = clean_text(name)
    return re.sub(r"\s*\(.*?\)\s*", "", name).strip()


def form_from_node(name):
    """
    Old Saxon (thorn) -> thorn
    Germanic -> None
    """
    match = re.search(r"\((.*?)\)", clean_text(name))

    if match:
        return clean_text(match.group(1))

    return None


def normalize_strict_relation(relation):
    """
    Keeps the full parent node, full child node and relation type.

    Example:
    Old Saxon (thorn) | Dutch (doorn) | descendant
    """
    if not isinstance(relation, list) or len(relation) != 3:
        return None

    parent = clean_text(relation[0])
    child = clean_text(relation[1])
    relation_type = clean_text(relation[2])

    if relation_type not in ALLOWED_RELATIONS:
        return None

    return parent, child, relation_type


def normalize_language_relation(relation):
    """
    Removes lexical forms but keeps the languages and relation type.

    Example:
    Old Saxon | Dutch | descendant
    """
    strict_relation = normalize_strict_relation(relation)

    if not strict_relation:
        return None

    parent, child, relation_type = strict_relation

    return (
        language_from_node(parent),
        language_from_node(child),
        relation_type,
    )


def to_set(relations, normalizer):
    output = set()

    for relation in relations:
        normalized = normalizer(relation)

        if normalized:
            output.add(normalized)

    return output


# -------------------------------------------------
# ENTITY EXTRACTION
# -------------------------------------------------
def extract_language_nodes(strict_relations):
    """
    Extracts language names only.

    Old Saxon (thorn) -> Old Saxon
    """
    nodes = set()

    for parent, child, _ in strict_relations:
        nodes.add(language_from_node(parent))
        nodes.add(language_from_node(child))

    return nodes


def extract_full_nodes(strict_relations):
    """
    Extracts complete language-form nodes.

    Old Saxon (thorn) -> Old Saxon (thorn)
    """
    nodes = set()

    for parent, child, _ in strict_relations:
        nodes.add(clean_text(parent))
        nodes.add(clean_text(child))

    return nodes


def extract_word_forms(strict_relations):
    """
    Extracts lexical forms only.

    Old Saxon (thorn) -> thorn
    """
    forms = set()

    for parent, child, _ in strict_relations:
        parent_form = form_from_node(parent)
        child_form = form_from_node(child)

        if parent_form:
            forms.add(parent_form)

        if child_form:
            forms.add(child_form)

    return forms


# -------------------------------------------------
# METRICS
# -------------------------------------------------
def compute_counts(gold_set, predicted_set):
    true_positive = len(gold_set & predicted_set)
    false_positive = len(predicted_set - gold_set)
    false_negative = len(gold_set - predicted_set)

    return true_positive, false_positive, false_negative


def compute_scores(true_positive, false_positive, false_negative):
    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive)
        else 0
    )

    recall = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative)
        else 0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


def add_counts(total, counts):
    total[0] += counts[0]
    total[1] += counts[1]
    total[2] += counts[2]


# -------------------------------------------------
# DATA LOADING
# -------------------------------------------------
def load_categories():
    with open(ETYMOLOGY_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        item["word"].lower(): item.get("category", "unknown")
        for item in data
    }


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    with open(GOLD_PATH, "r", encoding="utf-8") as file:
        gold_data = json.load(file)

    with open(PRED_PATH, "r", encoding="utf-8") as file:
        prediction_data = json.load(file)

    category_map = load_categories()

    gold_map = {
        item["word"].lower(): item["gold_relations"]
        for item in gold_data
    }

    prediction_map = {
        item["word"].lower(): item.get("predicted_relations", [])
        for item in prediction_data
    }

    metric_keys = [
        "strict_relation_extraction",
        "language_only_relation_extraction",
        "language_detection",
        "word_form_detection",
        "full_node_detection",
    ]

    overall = {
        key: [0, 0, 0]
        for key in metric_keys
    }

    by_category = defaultdict(
        lambda: {
            "words": 0,
            **{
                key: [0, 0, 0]
                for key in metric_keys
            },
        }
    )

    for word, gold_relations_raw in gold_map.items():
        predicted_relations_raw = prediction_map.get(word, [])
        category = category_map.get(word, "unknown")

        gold_strict = to_set(
            gold_relations_raw,
            normalize_strict_relation,
        )

        predicted_strict = to_set(
            predicted_relations_raw,
            normalize_strict_relation,
        )

        gold_language_relations = to_set(
            gold_relations_raw,
            normalize_language_relation,
        )

        predicted_language_relations = to_set(
            predicted_relations_raw,
            normalize_language_relation,
        )

        gold_language_nodes = extract_language_nodes(gold_strict)
        predicted_language_nodes = extract_language_nodes(predicted_strict)

        gold_full_nodes = extract_full_nodes(gold_strict)
        predicted_full_nodes = extract_full_nodes(predicted_strict)

        gold_forms = extract_word_forms(gold_strict)
        predicted_forms = extract_word_forms(predicted_strict)

        metric_sets = {
            "strict_relation_extraction": (
                gold_strict,
                predicted_strict,
            ),
            "language_only_relation_extraction": (
                gold_language_relations,
                predicted_language_relations,
            ),
            "language_detection": (
                gold_language_nodes,
                predicted_language_nodes,
            ),
            "word_form_detection": (
                gold_forms,
                predicted_forms,
            ),
            "full_node_detection": (
                gold_full_nodes,
                predicted_full_nodes,
            ),
        }

        by_category[category]["words"] += 1

        for key, (gold_set, predicted_set) in metric_sets.items():
            counts = compute_counts(gold_set, predicted_set)

            add_counts(overall[key], counts)
            add_counts(by_category[category][key], counts)

    report = {
        "system": "Regex",
        "total_words": len(gold_map),
        "overall": {
            key: compute_scores(*counts)
            for key, counts in overall.items()
        },
        "by_category": {},
    }

    for category, category_data in by_category.items():
        report["by_category"][category] = {
            "words": category_data["words"],
            **{
                key: compute_scores(*category_data[key])
                for key in metric_keys
            },
        }

    with open(REPORT_JSON, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n=== REGEX EVALUATION ===")
    print(f"Words evaluated: {report['total_words']}")

    print("\nOverall:")

    for key, values in report["overall"].items():
        print(
            f"{key}: "
            f"P={values['precision']} "
            f"R={values['recall']} "
            f"F1={values['f1']}"
        )

    print("\nBy Category:")

    for category, values in report["by_category"].items():
        print(f"\n{category} | words={values['words']}")

        for key in metric_keys:
            score = values[key]

            print(
                f"{key}: "
                f"P={score['precision']} "
                f"R={score['recall']} "
                f"F1={score['f1']}"
            )

    print("\nSaved:")
    print(REPORT_JSON)


if __name__ == "__main__":
    main()