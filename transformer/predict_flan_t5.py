import json
import re
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# -------------------------------------------------
# PATHS
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = BASE_DIR / "final_model"
DATA_DIR = BASE_DIR / "data"

TRAIN_PATH = DATA_DIR / "train.json"
VALID_PATH = DATA_DIR / "valid.json"
TEST_PATH  = DATA_DIR / "test.json"

OUTPUT_PATH = DATA_DIR / "flan_predictions.json"


# -------------------------------------------------
# DEVICE SETUP
# -------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# -------------------------------------------------
# LOAD MODEL
# -------------------------------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR)

model.to(device)
model.eval()


# -------------------------------------------------
# LOAD FULL DATASET (ALL WORDS)
# -------------------------------------------------
def load_all_data():
    with open(TRAIN_PATH, "r", encoding="utf-8") as f:
        train = json.load(f)

    with open(VALID_PATH, "r", encoding="utf-8") as f:
        valid = json.load(f)

    with open(TEST_PATH, "r", encoding="utf-8") as f:
        test = json.load(f)

    return train + valid + test


# -------------------------------------------------
# ROBUST PARSER (FINAL FIX)
# -------------------------------------------------
def parse_output(text):
    relations = []
    allowed = {"ancestor", "descendant", "language_ancestor"}

    tokens = text.replace("\n", " ").split("|")

    i = 0
    while i + 2 < len(tokens):
        parent = tokens[i].strip()
        child = tokens[i + 1].strip()
        relation_chunk = tokens[i + 2].strip()

        relation_words = relation_chunk.split()

        if not relation_words:
            i += 1
            continue

        relation = relation_words[0]

        if relation in allowed:
            relations.append([parent, child, relation])

            remaining = " ".join(relation_words[1:]).strip()

            if remaining:
                tokens[i + 2] = remaining
                i += 2
            else:
                i += 3
        else:
            i += 1

    # remove duplicate relations
    seen = set()
    deduped = []

    for rel in relations:
        key = tuple(rel)

        if key not in seen:
            seen.add(key)
            deduped.append(rel)

    return deduped

# -------------------------------------------------
# PREDICTION FUNCTION
# -------------------------------------------------
def predict(example):

    inputs = tokenizer(
        example["input"],
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            num_beams=5
        )

    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return {
        "word": example["word"],
        "predicted_relations": parse_output(decoded),
        "raw_output": decoded
    }


# -------------------------------------------------
# MAIN PIPELINE
# -------------------------------------------------
def main():

    data = load_all_data()

    print(f"Total words loaded: {len(data)}")

    results = []

    for i, ex in enumerate(data):
        pred = predict(ex)
        results.append(pred)

        print(f"[{i+1}/{len(data)}] {ex['word']} processed")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nSaved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()