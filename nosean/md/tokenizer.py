from .token import Token, ContainerToken, Occurence, Literal


class Tokenizer:

    def __init__(self, allowed_tokens_by_pattern="*"):
        self.allowed_tokens_by_pattern = allowed_tokens_by_pattern
        self._setup()

    def _setup(self):
        self.result = []
        self.allowed_tokens = Token.by_pattern(self.allowed_tokens_by_pattern)
        self.open_container_tokens: list[ContainerToken] = []
        self.cid = 0
        self.offset = 0
        self.current_literal = ""

    def tok(self, text: str):
        self._setup()
        lines = enumerate(text.splitlines())
        idx, line = next(lines)
        while line is not None:
            stripped = line[self.offset:].rstrip()
            tokens = self._get_token_starts(idx, stripped) | self._get_token_ends(idx, stripped)
            if tokens:
                start = min(s for s in tokens)
                token = tokens[start]
                if isinstance(token, ContainerToken):
                    if token.is_start:
                        self.open_container_tokens.append(token)
                        self.allowed_tokens = token.__class__.inner_tokens()
                    else:
                        self.open_container_tokens.pop()
                        if self.open_container_tokens:
                            previous_container_token = self.open_container_tokens[-1]
                            self.allowed_tokens = previous_container_token.__class__.inner_tokens()
                        else:
                            self.allowed_tokens = Token.by_pattern(self.allowed_tokens_by_pattern)
                if start > 0:
                    self.current_literal += stripped[:start]
                self._add(token, token.occurence)
                self.offset += token.occurence.end
            else:
                self.current_literal += f"{stripped}\n"
                self.offset += len(stripped)
            self.offset %= len(line.rstrip()) or 1
            if self.offset:
                continue
            try:
                idx, line = next(lines)
            except StopIteration:
                break
        self._add(None, Occurence(idx, 0, self.offset))
        return self.result
    
    def _get_token_starts(self, idx: int, line: str) -> dict[int, Token]:
        tokens_by_start: dict[int, Token] = {}
        for Tok in self.allowed_tokens:
            token_name = Tok._token_name
            result = Tok.start(idx, line)
            if result:
                occurence, attrs = result
                if issubclass(Tok, ContainerToken):
                    self.cid += 1
                    token = Tok(token_name, occurence, attrs, self.cid)
                else:
                    token = Tok(token_name, occurence, attrs)
                tokens_by_start[occurence.start] = token
        return tokens_by_start

    def _get_token_ends(self, idx: int, line: str) -> dict[int, Token]:
        tokens_by_start: dict[int, Token] = {}
        for start_token in self.open_container_tokens:
            token_name = start_token.name
            Tok: type[ContainerToken] = Token.by_name(token_name)
            if Tok not in self.allowed_tokens:
                continue
            result = Tok.end(idx, line)
            if result:
                cid = start_token.container_id
                occurence, attrs = result
                end_token = Tok(token_name, occurence, attrs, cid, False)
                tokens_by_start[occurence.start] = end_token
        return tokens_by_start
    
    def _add(self, thing: Token, occurence: Occurence):
        if self.current_literal:
            attrs = {"raw": self.current_literal}
            self.result.append(Literal("literal", occurence, attrs))
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
    # from pathlib import Path
    # sample = Path("data/bash.md").read_text(encoding="utf8")
    tokens = Tokenizer().tok(sample)
    for tok in tokens:
        print(tok)
