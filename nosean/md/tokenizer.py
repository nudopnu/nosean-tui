from typing import TypedDict

from .token import Token, ContainerToken


class TokenDict(TypedDict):
    token: str


class ContainerTokenDict(TokenDict):
    container_id: int
    start: bool


class Tokenizer:

    def __init__(self, allowed_tokens_by_pattern="*"):
        self.allowed_tokens_by_pattern = allowed_tokens_by_pattern
        self._setup()

    def _setup(self):
        self.result = []
        self.allowed_tokens = Token.by_pattern(self.allowed_tokens_by_pattern)
        self.open_container_tokens: list[TokenDict] = []
        self.cid = 0
        self.offset = 0
        self.current_literal: str = ""

    def tok(self, text: str):
        self._setup()
        lines = iter(text.splitlines())
        line = next(lines)
        while line is not None:
            stripped = line[self.offset:].rstrip()
            tokens = self._get_token_starts(stripped) | self._get_token_ends(stripped)
            if tokens:
                start = min(s for s in tokens)
                end, token = tokens[start]
                if "container_id" in token:
                    if token["start"]:
                        self.open_container_tokens.append(token)
                        self.allowed_tokens = Token.by_name(token["token"]).inner_tokens()
                    else:
                        self.open_container_tokens.pop()
                        if self.open_container_tokens:
                            name = self.open_container_tokens[-1]["token"]
                            self.allowed_tokens = Token.by_name(name).inner_tokens()
                        else:
                            self.allowed_tokens = Token.by_pattern(self.allowed_tokens_by_pattern)
                if start > 0:
                    self.current_literal += stripped[:start]
                self._add(token)
                self.offset += end
            else:
                self.current_literal += f"{stripped}\n"
                self.offset += len(stripped)
            self.offset %= len(line.rstrip()) or 1
            if self.offset:
                continue
            try:
                line = next(lines)
            except StopIteration:
                break
        self._add(None)
        return self.result
    
    def _get_token_starts(self, line: str) -> dict[int, tuple[int, TokenDict]]:
        tokens_by_start: dict[int, tuple[int, dict]] = {}
        for Token in self.allowed_tokens:
            token_name = Token._token_name
            result = Token.start(line)
            if result:
                start, end, attrs = result
                token: TokenDict = {"token": token_name} | (attrs or {})
                if issubclass(Token, ContainerToken):
                    self.cid += 1
                    token |= {"container_id": self.cid, "start": True}
                tokens_by_start[start] = end, token
        return tokens_by_start

    def _get_token_ends(self, line: str) -> dict[int, tuple[int, TokenDict]]:
        tokens_by_start: dict[int, tuple[int, TokenDict]] = {}
        for token_dict in self.open_container_tokens:
            token_name = token_dict["token"]
            TokenType: type[ContainerToken] = Token.by_name(token_name)
            if TokenType not in self.allowed_tokens:
                continue
            result = TokenType.end(line)
            if result:
                cid = token_dict["container_id"]
                start, end, attrs = result
                token: ContainerTokenDict = {"token": token_name, "container_id": cid, "start": False} | (attrs or {})
                tokens_by_start[start] = end, token
        return tokens_by_start
    
    def _add(self, thing: Token):
        if self.current_literal:
            self.result.append({"token": "literal", "raw": self.current_literal})
            self.current_literal = ""
        if thing is not None:
            self.result.append(thing)


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
    for tok in tokens:
        print(tok)
