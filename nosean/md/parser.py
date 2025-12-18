import json

from .tokenizer import Tokenizer, TokenDict, ContainerTokenDict


class Parser:

    def __init__(self, tokens: list[TokenDict]):
        root = {"token": "root", "children": []}

        parents = []
        tmp = root["children"]
        for tok in tokens:
            
            if "container_id" in tok:
                tok: ContainerTokenDict = tok
                if tok["start"]:
                    tmp.append(tok)
                    parents.append(tmp)
                    tok["children"] = []
                    tmp = tok["children"]
                else:
                    tmp = parents.pop()
                del tok["container_id"]
                del tok["start"]
            else:
                tmp.append(tok)
        print(json.dumps(root))


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
