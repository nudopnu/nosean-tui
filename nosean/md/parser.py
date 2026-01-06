from pathlib import Path
from functools import cache
from typing import TypedDict
from dataclasses import dataclass, field

from .tokenizer import Tokenizer, Token, ContainerToken
from .token import Heading, Literal

@dataclass
class TokenNode:
    token: Token | None
    children: list["TokenNode"] = field(default_factory=list)

    def get_raw(self):
        raw = self.token.attributes["raw"]
        if not isinstance(self.token, ContainerToken):
            return raw
        for child in self.children:
            raw += child.get_raw()
        return raw
        
@dataclass
class KnowledgeItem:
    title: str
    content: str
    path: str

class Parser:

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
    
    @cache
    def ast(self):
        root = TokenNode(None)
        parents = []
        tmp: list = root.children
        for tok in self.tokens:
            token_node = TokenNode(tok)
            if not isinstance(tok, ContainerToken):
                tmp.append(token_node)
                continue
            if not tok.is_start:
                tmp = parents.pop()
                continue
            tmp.append(token_node)
            parents.append(tmp)
            tmp = token_node.children
        return root
    
    def knowledge_items(self):
        root = self.ast()
        path: list[str] = []
        result: dict[str, KnowledgeItem] = {}
        
        def is_node_tag(node: TokenNode, tag: str):
            return node.token.name == "html" and node.token.attributes["tagname"] == tag
        
        def traverse(token: TokenNode):
            nonlocal path
            for child in token.children:
                if child.token.name == "heading":
                    level = child.token.attributes["level"]
                    title = child.token.attributes["title"]
                    path = ["" if idx >= len(path) else path[idx] for idx in range(level + 1)]
                    path[level] = title
                    print(path)
                elif is_node_tag(child, "details"):
                    content = ""
                    title = "?"
                    for sub_child in child.children:
                        if is_node_tag(sub_child, "summary"):
                            title = "".join(x.get_raw() for x in sub_child.children).strip()
                        else:
                            content += sub_child.get_raw().strip()
                    path_str = ".".join(path)
                    result[title] = KnowledgeItem(title, content, path_str)
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
    sample = Path("data/schematherapie.md").read_text(encoding="utf8")
    tokens = Tokenizer().tok(sample)
    p = Parser(tokens)
    import json
    tree = p.ast()
    path = {}
    current = {}

    def traverse(node: TokenNode):
        global current
        match token := node.token:
            case Heading(attributes=attributes):
                level = attributes["level"]
                title = attributes["title"]
                path[level] = title
                path_str = ".".join(path[i] if i in path else "" for i in range(max(path)))
                current = {
                    "path": path_str,
                    "name": title,
                }
            case Literal():
                current["content"] = token.attributes["raw"]
                print(current)
            case _:
                current = {}
        for child in node.children:
            traverse(child)

    traverse(tree)
    # for title, item in p.knowledge_items().items(): print(f"{item.path:<30}: {title}")
