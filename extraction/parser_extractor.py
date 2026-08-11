import re
import json
from pprint import pprint

from .tree_builder import build_json
from .language_loader import load_languages
from .preprocessor import preprocess_text


def load_etymology(word):
    with open("data/etymologies.json", "r", encoding="utf-8") as f:
        entries = json.load(f)

    for entry in entries:
        if entry["word"].lower() == word.lower():
            return entry["origin"], entry["etymology"]

    raise ValueError(f"{word} not found")


def make_language_pattern():
    languages = [
        lang for lang in load_languages()
        if len(lang) > 2
    ]

    languages = sorted(languages, key=len, reverse=True)
    return r"(?<![A-Za-z])(?:{})(?![A-Za-z])".format(
        "|".join(map(re.escape, languages))
    )


def add_relation(relations, parent, child, relation_type):
    edge = [parent.strip(), child.strip(), relation_type]
    if edge not in relations:
        relations.append(edge)


def clean_forms(forms):
    forms = re.sub(r"\([^()]*\)", "", forms)
    forms = re.sub(r"\s+", " ", forms).strip(" ,.;:")

    if not forms:
        return ""

    first_part = forms.split(",")[0].strip()
    tokens = first_part.split()

    if not tokens:
        return ""

    token = tokens[0].strip(" ,.;:")

    if token.lower() in {"base", "root", "word"}:
        return ""

    return token

def make_node(language, forms):
    return f"{language.strip()} ({clean_forms(forms)})"


def get_node_language(node):
    return node.split("(", 1)[0].strip()


def find_root_language(origin, etymology, language_pattern):
    text = preprocess_text(f"{origin} {etymology}")

    patterns = [
        rf"(?:inherited|borrowing|borrowed|derived|adopted)\s+from\s+({language_pattern})",
        rf"(?:A\s+)?Common\s+({language_pattern})",
        rf"same\s+({language_pattern})\s+base",
        rf"<\s*({language_pattern})"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def extract_language_ancestor_from_base(text, root_language, relations, language_pattern):
    pattern = rf"same\s+({language_pattern})\s+base\s+as"

    for match in re.finditer(pattern, text, re.IGNORECASE):
        parent_language = match.group(1).strip()

        if parent_language != root_language:
            add_relation(relations, parent_language, root_language, "language_ancestor")


def get_main_etymology_section(text):
    text = re.sub(
        r"^Origin:.*?Etymology:\s*",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    stop_patterns = [
        r"\band further with\b",
        r"\ball ultimately\b",
        r"\bfurther etymology\b",
        r"\boutside germanic\b",
        r"\boutside the germanic\b",
        r"\bthe usual word\b",
        r"\bsemantic developments\b",
        r"\bthe word was also borrowed\b"
    ]

    for stop in stop_patterns:
        match = re.search(stop, text, re.IGNORECASE)
        if match:
            return text[:match.start()].strip()

    return text.strip()


def find_parenthetical_blocks(section, language_pattern):
    header_pattern = re.compile(
        rf"({language_pattern})\s+([^()<>;]+?)\s*\(",
        re.IGNORECASE
    )

    blocks = []

    for match in header_pattern.finditer(section):
        parent_lang = match.group(1).strip()
        parent_form = clean_forms(match.group(2))

        if not parent_form:
            continue

        start = match.end()
        depth = 1
        i = start

        while i < len(section):
            if section[i] == "(":
                depth += 1
            elif section[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1

        if depth != 0:
            continue

        blocks.append({
            "parent_lang": parent_lang,
            "parent_form": parent_form,
            "inner": section[start:i]
        })

    return blocks


def extract_language_form_pairs(text, language_pattern):
    pair_pattern = re.compile(
        rf"({language_pattern})\s+([^,;()]+(?:,\s*(?!{language_pattern}\b)[^,;()]+)*)",
        re.IGNORECASE
    )

    pairs = []

    for match in pair_pattern.finditer(text):
        lang = match.group(1).strip()
        form = clean_forms(match.group(2))

        if form:
            pairs.append(make_node(lang, form))

    return pairs


def extract_parenthetical_descendants(section, relations, language_pattern):
    blocks = find_parenthetical_blocks(section, language_pattern)

    for block in blocks:
        parent_node = make_node(block["parent_lang"], block["parent_form"])
        children = extract_language_form_pairs(block["inner"], language_pattern)

        if not children:
            continue

        previous = parent_node

        for child in children:
            if child == previous:
                continue

            if "(base)" in previous.lower() or "(base)" in child.lower():
                continue

            add_relation(relations, previous, child, "descendant")
            previous = child


def extract_ancestor_forms(section, root_language, relations, language_pattern):
    section_without_parentheses = re.sub(r"\([^()]*\)", "", section)

    descendant_parent_languages = {
        get_node_language(parent)
        for parent, _, rel in relations
        if rel == "descendant" and "(" in parent
    }

    descendant_children = {
        child
        for _, child, rel in relations
        if rel == "descendant"
    }

    pattern = rf"({language_pattern})\s+([^,;()<>]+)"

    ignore = {
        "base", "word", "words", "language", "languages",
        "strong", "weak", "masculine", "feminine", "neuter",
        "regional", "modern", "rare", "only", "also",
        "probably", "perhaps", "apparently", "same",
        "further", "compare", "see", "from", "with",
        "and", "or", "in", "of", "as", "root"
    }

    for match in re.finditer(pattern, section_without_parentheses, re.IGNORECASE):
        lang = match.group(1).strip()
        form = clean_forms(match.group(2))

        if not form:
            continue

        if lang in descendant_parent_languages:
            continue

        first = form.split()[0].lower().strip(" ,.;:")
        if first in ignore:
            continue

        if lang == root_language:
            continue

        node = make_node(lang, form)

        if node in descendant_children:
            continue

        add_relation(relations, root_language, node, "ancestor")


def ensure_descendant_parents_attached(relations, root_language):
    existing_children = {
        child
        for _, child, rel in relations
        if rel in {"ancestor", "language_ancestor"}
    }

    descendant_parents = {
        parent
        for parent, _, rel in relations
        if rel == "descendant" and "(" in parent
    }

    descendant_children = {
        child
        for _, child, rel in relations
        if rel == "descendant" and "(" in child
    }

    top_level_descendant_parents = descendant_parents - descendant_children

    for parent in top_level_descendant_parents:
        if parent not in existing_children:
            add_relation(relations, root_language, parent, "ancestor")


def extract(origin, etymology, lemma):
    text = preprocess_text(
        f"Origin: {origin}\nEtymology: {etymology}"
    )

    language_pattern = make_language_pattern()
    relations = []

    root_language = find_root_language(origin, etymology, language_pattern)

    if not root_language:
        raise ValueError("Unable to determine root language.")

    extract_language_ancestor_from_base(text, root_language, relations, language_pattern)

    main_section = get_main_etymology_section(text)

    extract_parenthetical_descendants(main_section, relations, language_pattern)
    extract_ancestor_forms(main_section, root_language, relations, language_pattern)
    ensure_descendant_parents_attached(relations, root_language)

    with open("data/relations.json", "w", encoding="utf-8") as f:
        json.dump(relations, f, indent=2, ensure_ascii=False)

    build_json(relations, lemma)

    print("\nRELATIONS")
    pprint(relations)

    return relations