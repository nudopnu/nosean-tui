import re
import fnmatch
from functools import cache
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Occurence:
    line_idx: int
    start: int
    end: int


class Token(ABC):

    _token_name = "None"
    """The name that gets assigned by the @token decorator"""

    _allowed_inner_token = "*"
    """A pattern to match against all token 
    names that gets assigned by the @token decorator"""

    _token_registry: dict[str, type["Token"]] = {}
    """The registry of all tokens that get registered by the @token decorator"""

    def __init__(self, name: str, occurence: Occurence, attributes: dict=None):
        """When the start class method returns an Occurence, a Token instance will be created"""
        self.name = name
        self.occurence = occurence
        self.attributes = attributes or {}

    @classmethod
    @abstractmethod
    def start(cls, line_idx: int, line: str) -> tuple[Occurence, dict] | None:
        ...
    
    @classmethod
    def by_name(cls, name: str):
        return cls._token_registry[name]
    
    @classmethod
    @cache
    def by_pattern(cls, pattern: str):
        result: list[type[Token]] = []
        if not pattern:
            return result
        for key, TokenClass in cls._token_registry.items():
            if fnmatch.fnmatch(key, cls._allowed_inner_token):
                result.append(TokenClass)
        return result

    @classmethod
    @cache
    def inner_tokens(cls) -> list[type["Token"]]:
        return cls.by_pattern(cls._allowed_inner_token)


class ContainerToken(Token):

    def __init__(self, name: str, occurence: Occurence, attributes: dict, container_id: str, is_start=True):
        super().__init__(name, occurence, attributes)
        self.container_id = container_id
        self.is_start = is_start

    @classmethod
    @abstractmethod
    def end(cls, line_idx: int, line: str) -> tuple[Occurence, dict] | None:
        ...


def token(name: str, inner_tokens="*"):
    """A decorator for classes derived from Token class to add to the registry"""

    def cls_decorator(cls: type[Token]):
        Token._token_registry[name] = cls
        cls._token_name = name
        cls._allowed_inner_token = inner_tokens
        return cls

    return cls_decorator

@token("literal")
class Literal(Token):

    @classmethod
    def start(cls, line_idx, line):
        ...

@token("heading")
class Heading(Token):

    pattern = re.compile(r"#{1,4}")

    @classmethod
    def start(cls, line_idx, line):
        match = cls.pattern.match(line)
        if match:
            start, end = match.span(0)
            attrs = {
                "title": line[end:].strip(),
                "level": end - start,
                "raw": line
            }
            return Occurence(line_idx, 0, 0), attrs


@token("html")
class HtmlBlock(ContainerToken):

    start_pattern = re.compile(r"<([^/]*?)>")
    end_pattern = re.compile(r"</(.*?)>")
    
    @classmethod
    def start(cls, line_idx, line):
        match = cls.start_pattern.search(line)
        if match:
            tagname = match.group(0)[1:-1]
            start, end = match.span(0)
            attrs = {
                "tagname": tagname,
                "raw": line[start:end],
            }
            return Occurence(line_idx, start, end), attrs

    @classmethod
    def end(cls, line_idx, line):
        match = cls.end_pattern.search(line)
        if match:
            tagname = match.group(0)[2:-1]
            start, end = match.span(0)
            attrs = {
                "tagname": tagname,
                "raw": line[start:end],
            }
            return Occurence(line_idx, start, end), attrs


@token("code", inner_tokens="code")
class CodeStart(ContainerToken):

    start_pattern = re.compile(r"```(.*)")
    end_pattern = re.compile(r"```.*")

    @classmethod
    def start(cls, line_idx, line):
        match = cls.start_pattern.match(line)
        if match:
            language = match.group(1)
            attrs = {
                "language": language,
                "raw": line,
            }
            return Occurence(line_idx, 0, 0), attrs

    @classmethod
    def end(cls, line_idx, line):
        match = cls.end_pattern.match(line)
        if match:
            attrs = {"raw": line}
            return Occurence(line_idx, 0, 0), attrs