from pathlib import Path
import re
from abc import ABC, abstractmethod
from functools import cache
from typing import TypedDict
import fnmatch

class TokenDict(TypedDict):
    token: str

class ContainerTokenDict(TokenDict):
    container_id: int
    start: bool

class Token(ABC):

    _token_name = "None"
    """The name that gets assigned by the @token decorator"""

    @classmethod
    @abstractmethod
    def start(cls, line: str) -> tuple[int, int, dict] | None:
        ...
    
class ContainerToken(Token):

    @classmethod
    @abstractmethod
    def end(cls, line: str) -> tuple[int, int, dict] | None:
        ...

token_classes: dict[str, type[Token]] = {}
allowed_inner_tokens: dict[type[Token], str] = {}

def token(name: str, inner_tokens="*"):
    def cls_decorator(cls: type[Token]):
        token_classes[name] = cls
        allowed_inner_tokens[cls] = inner_tokens
        cls._token_name = name
        return cls
    return cls_decorator

def get_token_by_name(name: str) -> type[Token]:
    return token_classes[name]

@token("heading")
class Heading(Token):

    pattern = re.compile(r"#{1,4}")

    @classmethod
    def start(cls, line):
        match = cls.pattern.match(line)
        if match:
            start, end = match.span(0)
            attrs = {
                "title": line[end:].strip(),
                "level": end - start,
                "raw": line
            }
            return 0, 0, attrs

@token("html")
class HtmlBlock(ContainerToken):

    start_pattern = re.compile(r"<([^/]*?)>")
    end_pattern = re.compile(r"</(.*?)>")
    
    @classmethod
    def start(cls, line):
        match = cls.start_pattern.search(line)
        if match:
            tagname = match.group(0)[1:-1]
            start, end = match.span(0)
            raw = line[start:end]
            attrs = {
                "tagname": tagname,
                "raw": raw,
            }
            return start, end, attrs

    @classmethod
    def end(cls, line):
        match = cls.end_pattern.search(line)
        if match:
            tagname = match.group(0)[2:-1]
            start, end = match.span(0)
            raw = line[start:end]
            attrs = {
                "tagname": tagname,
                "raw": raw,
            }
            return start, end, attrs

@token("code", inner_tokens="code")
class CodeStart(ContainerToken):

    start_pattern = re.compile(r"```(.*)")
    end_pattern = re.compile(r"```.?")

    @classmethod
    def start(cls, line):
        match = cls.start_pattern.match(line)
        if match:
            language = match.group(1)
            attrs = {
                "language": language,
                "raw": line,
            }
            return 0, 0, attrs

    @classmethod
    def end(cls, line):
        match = cls.end_pattern.match(line)
        if match:
            attrs = {"raw": line}
            return 0, 0, attrs

class Tokenizer:

    def __init__(self):
        self._setup()

    def _setup(self):
        self.result = []
        self.allowed_tokens = self.get_allowed_tokens("*")
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
            tokens = self.get_token_starts(stripped) | self.get_token_ends(stripped)
            if tokens:
                start = min(s for s in tokens)
                end, token = tokens[start]
                if "container_id" in token:
                    if token["start"]:
                        self.open_container_tokens.append(token)
                        self.allowed_tokens = self.get_allowed_tokens(allowed_inner_tokens[get_token_by_name(token["token"])])
                    else:
                        self.open_container_tokens.pop()
                        if self.open_container_tokens:
                            name = self.open_container_tokens[-1]["token"]
                            self.allowed_tokens = self.get_allowed_tokens(allowed_inner_tokens[get_token_by_name(name)])
                        else:
                            self.allowed_tokens = self.get_allowed_tokens("*")
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
    
    def get_token_starts(self, line: str) -> dict[int, tuple[int, TokenDict]]:
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

    def get_token_ends(self, line: str) -> dict[int, tuple[int, TokenDict]]:
        tokens_by_start: dict[int, tuple[int, TokenDict]] = {}
        for token_dict in self.open_container_tokens:
            token_name = token_dict["token"]
            Token: type[ContainerToken] = get_token_by_name(token_name)
            if Token not in self.allowed_tokens:
                continue
            result = Token.end(line)
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

    @cache
    def get_allowed_tokens(self, pattern: str | None) -> list[type[Token]]:
        if not pattern:
            return []
        result: list[type[Token]] = []
        for key in token_classes:
            if fnmatch.fnmatch(key, pattern):
                result.append(token_classes[key])
        return result

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

if __name__ == "__main__":
    # sample = Path("data/bash.md").read_text(encoding="utf8")
    tokens = Tokenizer().tok(sample)
    for tok in tokens:
        print(tok)
