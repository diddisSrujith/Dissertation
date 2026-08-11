import re
import json

from .language_loader import load_languages
from .preprocessor import preprocess_text


def load_etymology(word):
    with open("data/etymologies.json", "r", encoding="utf-8") as f:
        entries = json.load(f)

    for entry in entries:
        if entry["word"].lower() == word.lower():
            return (
                entry.get("origin", "").strip(),
                entry.get("etymology", "").strip()
            )

    raise ValueError(f"Word '{word}' not found in etymologies.json")


def make_language_pattern():
    languages = [
        lang for lang in load_languages()
        if len(lang) > 2
    ]

    languages = sorted(languages, key=len, reverse=True)

    return r"(?<![A-Za-z])(?:{})(?![A-Za-z])".format(
        "|".join(map(re.escape, languages))
    )


def clean_form(form):
    form = re.sub(r"\([^()]*\)", "", form)
    form = re.sub(r"\s+", " ", form).strip(" ,.;:")

    if not form:
        return ""

    first_part = form.split(",")[0].strip()
    tokens = first_part.split()

    if not tokens:
        return ""

    token = tokens[0].strip(" ,.;:")

    if token.lower() in {"base", "root", "word"}:
        return ""

    return token


def make_node(language, form):
    form = clean_form(form)

    if not form:
        return None

    return {
        "name": f"{language.strip()} ({form})"
    }


def empty_parallel(lemma, output_file="data/parallel.json"):
    parallel_json = {
        "lemma": lemma,
        "name": "No parallel cognates",
        "children": []
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(parallel_json, f, indent=2, ensure_ascii=False)

    return parallel_json


def find_inherited_language(origin, language_pattern):
    origin = preprocess_text(origin)

    match = re.search(
        rf"(?:inherited|borrowed|derived|adopted)\s+from\s+({language_pattern})",
        origin,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


def extract_parallel_section(text, language_pattern):
    root = None
    section = None

    base_match = re.search(
        rf"same\s+({language_pattern})\s+base\s+as\s+(.*)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if base_match:
        root = base_match.group(1).strip()
        section = base_match.group(2)

    else:
        further_match = re.search(
            r"(?:and\s+)?further\s+with\s+(.*)",
            text,
            re.IGNORECASE | re.DOTALL
        )

        if further_match:
            root = "Parallel cognates"
            section = further_match.group(1)

        else:
            perhaps_match = re.search(
                r"perhaps\s+<\s+(.*)",
                text,
                re.IGNORECASE | re.DOTALL
            )

            if perhaps_match:
                root = "Possible parallel cognates"
                section = perhaps_match.group(1)

    if not root or not section:
        return None, None

    stop_patterns = [
        r"\bfurther etymology\b",
        r"\balthough\b",
        r"\bhowever\b",
        r"\bsee\b",
        r"\bthe exact\b",
        r"\bsemantic\b",
        r"\bcompare\b"
    ]

    for stop in stop_patterns:
        stop_match = re.search(stop, section, re.IGNORECASE)
        if stop_match:
            section = section[:stop_match.start()]
            break

    return root, section.strip()


def extract_language_forms(section, language_pattern):
    pattern = rf"({language_pattern})\s+([^,;()<>]+)"

    children = []

    for match in re.finditer(pattern, section, re.IGNORECASE):
        lang = match.group(1).strip()
        form = match.group(2).strip()

        node = make_node(lang, form)

        if node and node not in children:
            children.append(node)

    return children


def add_inherited_branch(children, inherited_language):
    if not inherited_language:
        return children

    inherited_node = {
        "name": inherited_language
    }

    if inherited_node not in children:
        children.insert(0, inherited_node)

    return children


def extract(origin, etymology, lemma):
    text = preprocess_text(
        f"Origin: {origin}\nEtymology: {etymology}"
    )

    language_pattern = make_language_pattern()

    root, section = extract_parallel_section(
        text,
        language_pattern
    )

    if not root or not section:
        return empty_parallel(lemma)

    children = extract_language_forms(
        section,
        language_pattern
    )

    inherited_language = find_inherited_language(
        origin,
        language_pattern
    )

    children = add_inherited_branch(
        children,
        inherited_language
    )

    parallel_json = {
        "lemma": lemma,
        "name": root,
        "children": children
    }

    with open("data/parallel.json", "w", encoding="utf-8") as f:
        json.dump(parallel_json, f, indent=2, ensure_ascii=False)

    return parallel_json