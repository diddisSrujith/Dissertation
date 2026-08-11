# Portrayal of OED etymologies

An MSc research project for automatically extracting etymological relationships from unstructured dictionary entries and representing them as interactive etymology trees.

The project implements and compares two approaches:

* **Rule-based extraction using Regex**
* **Fine-tuned FLAN-T5 transformer model**

The extracted relationships are evaluated against a manually annotated gold-standard dataset and visualised through an interactive web application.

---

## Project Overview

The system processes etymological descriptions and extracts relationships in the following form:

```text
(parent, child, relation type)
```

Each node represents a **language and its associated word/form**.

The extraction process works sentence-by-sentence. Languages are identified using the available language resources, after which predefined relationship patterns are applied to extract flat relationships.

The flat relationships are then converted into tree structures for visualisation.

```text
Etymology Text
      ↓
Preprocessing
      ↓
Language Detection
      ↓
Relationship Pattern Detection
      ↓
Flat Relations
      ↓
Tree Construction
      ↓
Interactive Visualisation
```

For detailed documentation of the individual files, extraction rules, and implementation, see:

**[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.txt)**

---

# Dataset

The project uses **102 etymology entries collected from the Oxford English Dictionary (OED)**.

### `data/etymologies.json`

Contains the manually collected origin and etymology text for the 102 words.

The words are categorised as:

* `simple`
* `complex`
* `very_complex`

based on the complexity of their textual etymological descriptions.

### `evaluation/gold_dataset.json`

Contains manually annotated etymological relationships for the same 102 words.

The gold dataset is used for:

* Training the FLAN-T5 model
* Evaluating the Regex extraction system
* Evaluating the FLAN-T5 system
* Measuring average tree completeness

---

# Running the Application

## Install dependencies

From the project root:

```bash
pip install -r requirements.txt
```

## Start the application

```bash
python -m app
```

Then open:

**http://127.0.0.1:5000/**

The application provides an interactive interface for exploring the extracted etymology trees.

---

# Application Pipeline

When the application is started, the backend runs the extraction and tree-building pipeline.

The main components are:

| File                    | Purpose                                                 |
| ----------------------- | ------------------------------------------------------- |
| `preprocessor.py`       | Preprocesses etymology text before extraction           |
| `language_loader.py`    | Loads language and language-family resources at runtime |
| `parser_extractor.py`   | Main extraction system for the primary etymology tree   |
| `parallel_extractor.py` | Extracts parallel cognate relationships                 |
| `tree_builder.py`       | Converts flat relationships into a tree structure       |

The application generates:

```text
relations.json
parallel.json
data.json
```

* `relations.json` — extracted flat relationships
* `parallel.json` — parallel cognate tree structure
* `data.json` — main tree structure used by the visualiser

The generated structures are consumed by the frontend and rendered using D3.js.

---

# Language Resources

The language resources can be generated using:

```bash
python -m extraction.fetch_languages
```

This creates:

```text
languages.csv
```

The CSV can then be converted into JSON using:

```bash
python -m extraction.parse_languages
```

This creates:

```text
languages.json
```

The application loads the language and language-family resources at runtime.

---

# Regex Evaluation

The Regex system can be evaluated independently against the manually annotated gold dataset.

## Generate Regex predictions

```bash
python -m extraction.generate_regex_predictions
```

This processes the etymology entries and generates:

```text
regex_predictions.json
```

The predictions contain the extracted relationships for all 102 words.

## Evaluate Regex

```bash
python -m evaluation.evaluate_regex
```

This compares:

```text
regex_predictions.json
        ↓
gold_dataset.json
```

and generates:

```text
results/regex_eval_report.json
```

The evaluation includes:

* Strict relation extraction
* Language-only relation extraction
* Node detection
* Word-form detection
* Precision
* Recall
* F1-score

---

# FLAN-T5 Transformer

The project also uses a pretrained **FLAN-T5** sequence-to-sequence transformer that is fine-tuned on the project's annotated etymology data.

## 1. Prepare training data

```bash
python -m extraction.prepare_flan_data
```

This uses:

```text
etymologies.json
gold_dataset.json
```

to create the training, validation, and test datasets.

The model receives the etymology text as input and learns to generate the corresponding structured relationship sequence.

## 2. Fine-tune FLAN-T5

```bash
python -m extraction.train_flan_t5
```

This fine-tunes the pretrained FLAN-T5 model using the prepared training data.

## 3. Generate predictions

```bash
python -m extraction.predict_flan_t5
```

This uses the trained model to generate predictions for the etymology entries and saves:

```text
flan_predictions.json
```

## 4. Evaluate FLAN-T5

```bash
python -m evaluation.evaluate_flan
```

This compares the FLAN-T5 predictions against the gold dataset and generates:

```text
results/flan_eval_report.json
```

---

# Tree Completeness Evaluation

In addition to relation-level Precision, Recall and F1-score, the project measures **Average Tree Completeness**.

The metric measures how much of each word's gold etymological tree was reconstructed:

```text
Tree Completeness =
Correct gold relations reconstructed
-------------------------------------
Total gold relations
```

The score is calculated for each word and then averaged across the corpus.

Run:

```bash
python -m evaluation.evaluate_tree_completeness
```

This generates:

```text
results/tree_completeness_report.json
```

The report contains separate results for:

* Regex
* FLAN-T5

and results by etymology complexity category.

---

# Frontend

The user interface consists of:

| File         | Purpose                                                 |
| ------------ | ------------------------------------------------------- |
| `index.html` | Defines the application interface                       |
| `styles.css` | Defines the visual styling                              |
| `script.js`  | Handles client-side interaction and D3.js visualisation |

The interface supports:

* Interactive etymology trees
* Expand/collapse tree nodes
* Combined language + word view
* Language-only view
* Word/form-only view
* Parallel cognate tree
* Manual etymology input
* Word search

---

# Technology Stack

### Frontend

* HTML
* CSS
* JavaScript
* D3.js

### Backend

* Python
* Flask
* Regex-based NLP

### Machine Learning

* PyTorch
* Hugging Face Transformers
* FLAN-T5

### Data

* JSON
* CSV

---

# Comparative Study

A major component of the project is the comparison between a deterministic rule-based approach and a transformer-based approach.

Both systems are evaluated against the same manually annotated gold-standard dataset.

The comparison considers:

* Relation extraction accuracy
* Node detection
* Word-form detection
* Language-aware relation extraction
* Precision
* Recall
* F1-score
* Average Tree Completeness

This allows the strengths and limitations of both approaches to be analysed across different levels of etymological complexity.

---

# Detailed Documentation

For detailed information about the project implementation, individual Python files, extraction rules, data flow, and processing logic, see:

**[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)**

---

# Project Structure

```text
project/
│
├── app.py
├── requirements.txt
├── README.md
├── PROJECT_DOCUMENTATION.md
│
├── data/
│   └── etymologies.json
│
├── extraction/
│   ├── preprocessor.py
│   ├── language_loader.py
│   ├── parser_extractor.py
│   ├── parallel_extractor.py
│   ├── tree_builder.py
│   ├── fetch_languages.py
│   ├── parse_languages.py
│   ├── generate_regex_predictions.py
│   ├── prepare_flan_data.py
│   ├── train_flan_t5.py
│   └── predict_flan_t5.py
│
├── evaluation/
│   ├── gold_dataset.json
│   ├── evaluate_regex.py
│   ├── evaluate_flan.py
│   └── evaluate_tree_completeness.py
│
├── results/
│
└── templates/
    └── index.html
```

---

## Research Project

**Automated Etymology Relation Extraction using Rule-Based NLP and Fine-Tuned FLAN-T5**

This project was developed as part of an MSc research dissertation investigating automated extraction and visualisation of etymological relationships from dictionary text.
