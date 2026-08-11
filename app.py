from flask import Flask, render_template, request, jsonify
import json

from extraction.parser_extractor import (
    extract,
    load_etymology
)

from extraction.parallel_extractor import (
    extract as extract_parallel
)

app = Flask(__name__)


def load_words():
    with open(
        "data/etymologies.json",
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def load_generated_json():
    with open(
        "data/data.json",
        "r",
        encoding="utf-8"
    ) as f:
        tree = json.load(f)

    with open(
        "data/parallel.json",
        "r",
        encoding="utf-8"
    ) as f:
        parallel = json.load(f)

    return tree, parallel


@app.route("/")
def index():
    return render_template(
        "index.html",
        words=load_words()
    )


@app.route("/words")
def words():
    return jsonify(load_words())


@app.route("/extract/<word>")
def extract_dataset(word):

    origin, etymology = load_etymology(word)

    extract(
        origin,
        etymology,
        word.capitalize()
    )

    extract_parallel(
        origin,
        etymology,
        word.capitalize()
    )

    tree, parallel = load_generated_json()

    return jsonify({
        "tree": tree,
        "parallel": parallel
    })


@app.route("/extract", methods=["POST"])
def extract_custom():

    data = request.json

    word = data["word"]
    origin = data["origin"]
    etymology = data["etymology"]

    extract(
        origin,
        etymology,
        word.capitalize()
    )

    extract_parallel(
        origin,
        etymology,
        word.capitalize()
    )

    tree, parallel = load_generated_json()

    return jsonify({
        "tree": tree,
        "parallel": parallel
    })


if __name__ == "__main__":
    app.run(debug=True)