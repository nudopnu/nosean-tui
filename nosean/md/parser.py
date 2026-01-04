from pathlib import Path
from functools import cache
from typing import TypedDict

from .tokenizer import Tokenizer, Token, ContainerToken

class TokenNode(TypedDict):
    token: str
    children: list["TokenNode"]

class KnowledgeItem(TypedDict):
    title: str
    content: str
    metadata: dict

class Parser:

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
    
    @cache
    def ast(self):
        root: TokenNode = {"token": "root", "children": []}
        parents = []
        tmp: list = root["children"]
        for tok in tokens:
            if "container_id" not in tok:
                tmp.append(tok)
                continue
            tok: ContainerToken = tok
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
        result: dict[str, KnowledgeItem] = {}
        
        def is_node_tag(node: TokenNode, tag: str):
            return node["token"] == "html" and node["tagname"] == tag
        
        def get_raw(node: TokenNode):
            raw: str = node["raw"]
            if "children" not in node:
                return raw
            for child in node["children"]:
                raw += get_raw(child)
            return raw

        def traverse(token: TokenNode):
            nonlocal path
            for child in token["children"]:
                if child["token"] == "heading":
                    level = child["level"]
                    title = child["title"]
                    path = ["" if idx >= len(path) else path[idx] for idx in range(level + 1)]
                    path[level] = title
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
    sample = Path("data/bash.md").read_text(encoding="utf8")
    tokens = Tokenizer().tok(sample)
    p = Parser(tokens)
    # print(json.dumps(p.ast()))
    for title, content in p.knowledge_items().items():
        print(title)
