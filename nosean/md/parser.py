import json
from functools import cache
from typing import TypedDict

from .tokenizer import Tokenizer, TokenDict, ContainerTokenDict

class TokenNodeDict(TypedDict):
    token: str
    children: list["TokenNodeDict"]

class KnowledgeItemDict(TypedDict):
    title: str
    content: str

class Parser:

    def __init__(self, tokens: list[TokenDict]):
        self.tokens = tokens
    
    @cache
    def ast(self):
        root: TokenNodeDict = {"token": "root", "children": []}
        parents = []
        tmp: list = root["children"]
        for tok in tokens:
            if "container_id" not in tok:
                tmp.append(tok)
                continue
            tok: ContainerTokenDict = tok
            if not tok["start"]:
                tmp = parents.pop()
                continue
            tmp.append(tok)
            parents.append(tmp)
            tok["children"] = []
            del tok["container_id"]
            del tok["start"]
            tmp = tok["children"]
        return root
    
    def knowledge_items(self):
        root = self.ast()
        path: list[str] = []
        result: dict[str, KnowledgeItemDict] = {}
        
        def is_node_tag(node: TokenNodeDict, tag: str):
            return node["token"] == "html" and node["tagname"] == tag
        
        def get_raw(node: TokenNodeDict):
            raw: str = node["raw"]
            if "children" not in node:
                return raw
            for child in node["children"]:
                raw += get_raw(child)
            return raw

        def traverse(token: TokenNodeDict):
            nonlocal path
            for child in token["children"]:
                if child["token"] == "heading":
                    level = child["level"]
                    title = child["title"]
                    path = ["" if idx >= len(path) else path[idx] for idx in range(level + 1)]
                    path[level] = title
                    print(path)
                elif is_node_tag(child, "details"):
                    content = ""
                    title = "?"
                    for sub_child in child["children"]:
                        if is_node_tag(sub_child, "summary"):
                            title = "".join(get_raw(x) for x in sub_child["children"]).strip()
                        else:
                            content += get_raw(sub_child).strip()
                    result[title] = content
        traverse(root)
        return result

if __name__ == "__main__":
    sample = """
abc
## Various snippets
<details><summary>Something interesting?</summary>
```bash
<html>
</html>
```
</details> 

# test
    """
    # sample = Path("data/bash.md").read_text(encoding="utf8")
    tokens = Tokenizer().tok(sample)
    p = Parser(tokens)
    # print(json.dumps(p.ast()))
    print(p.knowledge_items())
