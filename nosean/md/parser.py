import json

from .tokenizer import Tokenizer, TokenDict, ContainerTokenDict


class Parser:

    def __init__(self, tokens: list[TokenDict]):
        self.tokens = tokens
    
    def ast(self):
        root = {"token": "root", "children": []}
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
    print(json.dumps(p.ast()))
