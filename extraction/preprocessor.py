import re
import unicodedata


def preprocess_text(text):

    # Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Normalize quotes
    text = (
        text
        .replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    # Normalize dashes
    text = (
        text
        .replace("–", "-")
        .replace("—", "-")
    )

    # Remove editorial markers
    # Keep * because reconstructed forms
    # such as *Proto-Germanic carry meaning
    text = re.sub(r"[†‡]", "", text)

    # Normalize line endings
    text = re.sub(r"\r\n?", "\n", text)

    # Collapse spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()