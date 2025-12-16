from pathlib import Path
import re
from abc import ABC, abstractmethod
from functools import cache
import fnmatch
from typing import Callable


class Token(ABC):

    @classmethod
    @abstractmethod
    def start(cls, line: str) -> tuple[int, int, dict] | None:
        ...
    
tokens: dict[str, type[Token]] = {}
allowed_inner_tokens: dict[type[Token], str] = {}
restrictions: dict[type[Token], Callable[[list[str]], bool]] = {}

def token(name: str, inner_tokens="*", only_after=None):
    def cls_decorator(cls: type):
        tokens[name] = cls
        allowed_inner_tokens[cls] = inner_tokens
        # TODO: find a solution
        if only_after:
            restrictions[cls] = lambda tokens: only_after in tokens
        return cls
    return cls_decorator

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

@token("html_start")
class HtmlBlockStart(Token):

    pattern = re.compile(r"<([^/]*?)>")
    
    @classmethod
    def start(cls, line):
        match = cls.pattern.search(line)
        if match:
            tagname = match.group(0)[1:-1]
            start, end = match.span(0)
            raw = line[start:end]
            attrs = {
                "tagname": tagname,
                "raw": raw,
            }
            return start, end, attrs
    
@token("html_end", only_after="html_start")
class HtmlBlockEnd(Token):

    pattern = re.compile(r"</(.*?)>")

    @classmethod
    def start(cls, line):
        match = cls.pattern.search(line)
        if match:
            tagname = match.group(0)[2:-1]
            start, end = match.span(0)
            raw = line[start:end]
            attrs = {
                "tagname": tagname,
                "raw": raw,
            }
            return start, end, attrs

@token("code_start")
class CodeStart(Token):

    pattern = re.compile(r"```(.*)")

    @classmethod
    def start(cls, line):
        match = cls.pattern.match(line)
        if match:
            language = match.group(1)
            attrs = {
                "language": language,
                "raw": line,
            }
            return 0, 0, attrs

@token("code_end")
class CodeEnd(Token):

    pattern = re.compile(r"```.?")

    @classmethod
    def start(cls, line):
        match = cls.pattern.match(line)
        attrs = {"raw": line}
        if match:
            return 0, 0, attrs

class Tokenizer:

    def __init__(self):
        self._setup()

    def _setup(self):
        self.result = []
        self.allowed_tokens = self.get_allowed_tokens("*")
        self.current_literal: str = ""

    def tok(self, text: str):
        self._setup()
        lines = iter(text.splitlines())
        line = next(lines)
        self.offset = 0
        while line is not None:
            stripped = line[self.offset:].rstrip()
            result = self.try_detect_token_start(stripped)
            if result:
                start, end, token = result
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
    
    def try_detect_token_start(self, line: str):
        possible_tokens_by_start: dict[int, tuple[int, dict]] = {}
        for name, Tokenizer in self.allowed_tokens:
            result = Tokenizer.start(line)
            if result:
                self.allowed_tokens = self.get_allowed_tokens_by_class(Tokenizer)
                start, end, attrs = result
                token = {"token": name} | (attrs or {})
                possible_tokens_by_start[start] = end, token
        if possible_tokens_by_start:
            min_offset = min(k for k in possible_tokens_by_start)
            return min_offset, *possible_tokens_by_start[min_offset]
    
    def _add(self, thing: Token):
        if self.current_literal:
            self.result.append({"token": "literal", "raw": self.current_literal})
            self.current_literal = ""
        if thing is not None:
            self.result.append(thing)
    @cache
    def get_allowed_tokens(self, pattern: str):
        result: list[tuple[str, type[Token]]] = []
        for key in tokens:
            if fnmatch.fnmatch(key, pattern):
                result.append((key, tokens[key]))
        return result

    @cache
    def get_allowed_tokens_by_class(self, cls: type[Token]):
        return self.get_allowed_tokens(allowed_inner_tokens[cls])

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
    for tokens in tokens:
        print(tokens)
