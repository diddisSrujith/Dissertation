import json
from pathlib import Path

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments
)

MODEL_NAME = "google/flan-t5-small"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
FINAL_MODEL_DIR = BASE_DIR / "final_model"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():

    train_data = load_json(DATA_DIR / "train.json")
    valid_data = load_json(DATA_DIR / "valid.json")

    print(f"\nTrain examples: {len(train_data)}")
    print(f"Validation examples: {len(valid_data)}")

    print("\n=== SAMPLE TRAINING EXAMPLE ===\n")
    print(train_data[0]["input"][:500])
    print("\nTARGET:\n")
    print(train_data[0]["target"])
    print("\n===============================\n")

    train_dataset = Dataset.from_list(train_data)
    valid_dataset = Dataset.from_list(valid_data)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    def preprocess(example):
        model_inputs = tokenizer(
            example["input"],
            truncation=True,
            max_length=512
        )

        labels = tokenizer(
            text_target=example["target"],
            truncation=True,
            max_length=256
        )

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    train_dataset = train_dataset.map(
        preprocess,
        remove_columns=train_dataset.column_names
    )

    valid_dataset = valid_dataset.map(
        preprocess,
        remove_columns=valid_dataset.column_names
    )

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        label_pad_token_id=-100
    )

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(CHECKPOINT_DIR),

        num_train_epochs=50,
        learning_rate=5e-5,

        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,

        weight_decay=0.01,
        max_grad_norm=1.0,

        eval_strategy="epoch",
        save_strategy="epoch",

        logging_steps=10,

        predict_with_generate=True,
        generation_max_length=256,

        load_best_model_at_end=True,
        save_total_limit=2,

        fp16=False
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        processing_class=tokenizer,
        data_collator=data_collator
    )

    trainer.train()

    trainer.save_model(str(FINAL_MODEL_DIR))
    tokenizer.save_pretrained(str(FINAL_MODEL_DIR))

    print("\nTraining complete.")
    print(f"Final model saved to: {FINAL_MODEL_DIR}")


if __name__ == "__main__":
    main()