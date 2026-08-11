import json
from collections import defaultdict


def build_json(relations, lemma, output_file="data/data.json"):

    tree = defaultdict(list)
    children_set = set()

    for parent, child, relation in relations:
        tree[parent].append({
            "name": child,
            "relation": relation
        })
        children_set.add(child)

    root_candidates = list(set(tree.keys()) - children_set)

    if len(root_candidates) != 1:
        raise ValueError(
            f"Expected one root, found {len(root_candidates)}: {root_candidates}"
        )

    root = root_candidates[0]

    def build_tree(node):
        result = {"name": node}

        children = tree.get(node, [])

        if children:
            children_list = []

            for child in children:
                child_tree = build_tree(child["name"])
                child_tree["relation"] = child["relation"]
                children_list.append(child_tree)

            result["children"] = children_list

        return result

    json_tree = {
        "lemma": lemma,
        **build_tree(root)
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_tree, f, indent=2, ensure_ascii=False)

    return json_tree