import os
import pathlib
from typing import TypedDict, Optional, Literal

from mistletoe import Document
from mistletoe.token import Token
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.block_token import Paragraph, Heading, CodeFence, List, BlockCode, Table
from mistletoe.span_token import InlineCode
from bs4 import BeautifulSoup


class Section(TypedDict):
    type: Literal["text", "summary"]
    body: str


class MarkdownParser:

    def __init__(self, path: str):
        p = pathlib.Path(path)
        name = os.path.splitext(p.name)[0].title()
        self.content = p.read_text(encoding="utf8")
        self.heading: dict[int, str] = { 1: name }
        self.sections: dict[str, list[Token]] = {}
        self.current_level = 1

    def __search_sections_rescursive(self, token: Token):
        key = ".".join(self.heading[i + 1] for i in range(self.current_level) if (i + 1) in self.heading)
        tokens = self.sections.get(key, [])
        match(token):
            case Paragraph():
                for child in token.children:
                    self.__search_sections_rescursive(child)
            case Heading():
                self.current_level = token.level
                title = ''.join(c.content for c in token.children if hasattr(c, 'content'))
                self.heading[token.level] = title
            case _:
                tokens.append(token)
                self.sections[key] = tokens

    def parse(self) -> dict[str, Section]:
        for token in Document(self.content).children:
            self.__search_sections_rescursive(token)
        renderer = MarkdownRenderer()

        typed_sections: dict[str, Section] = {}
        for section_name, tokens in self.sections.items():

            # Put placeholders before parsing html
            content = ""
            code_placeholders = {}
            i = 0
            for token in tokens:
                render = renderer.render(token)
                match(token):
                    case CodeFence():
                        key = f"p{i}"
                        code_placeholders[key] = render
                        content += f"{{{key}}}\n"
                        i += 1
                    case BlockCode():
                        key = f"p{i}"
                        code_placeholders[key] = render
                        content += f"{{{key}}}\n"
                        i += 1
                    case List():
                        key = f"p{i}"
                        code_placeholders[key] = render
                        content += f"{{{key}}}\n"
                        i += 1
                    case Table():
                        key = f"p{i}"
                        code_placeholders[key] = render
                        content += f"{{{key}}}\n"
                        i += 1
                    case InlineCode():
                        key = f"p{i}"
                        code_placeholders[key] = render
                        content = f"{content[:-1]}{{{key}}}"
                        i += 1
                    case _:
                        content += render

            # parsing html
            bs = BeautifulSoup(f"<root>{content}</root>", "html.parser")
            for node in bs.root.contents:
                if node.name == "details":
                    summary = node.summary.get_text(strip=True)
                    summary = summary.format(**code_placeholders).strip().replace("\n", "")
                    body = "".join(str(c) for c in node.contents if c.name != "summary")
                    body = body.format(**code_placeholders)
                    key = f"{section_name}.{summary}"
                    typed_sections[key] = {"type": "details", "body": body}
                else:
                    text = str(node).strip().format(**code_placeholders)
                    if section_name in typed_sections:
                        typed_sections[section_name]["body"] += text
                    else:
                        typed_sections[section_name] = {"type": "text", "body": text}
        return typed_sections

if __name__ == "__main__":
    parser = MarkdownParser("./data/python.md")
    typed_sections = parser.parse()
                
    for k in typed_sections:
        print(k)
    
    print(typed_sections["Python.PyQT6"]["body"])