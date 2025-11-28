import pathlib
from typing import TypedDict

import mistune
from mistletoe import Document
from mistletoe.token import Token
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.block_token import Paragraph, Heading, CodeFence, List, BlockCode
from mistletoe.span_token import RawText, InlineCode
from bs4 import BeautifulSoup

# renderer = MarkdownRenderer()

heading: dict[int, str] = { 1: "Docker" }
sections: dict[str, list[Token]] = {}
current_level = 1

def parse(token: Token):
    global current_level
    key = ".".join(heading[i + 1] for i in range(current_level))
    tokens = sections.get(key, [])
    match(token):
        case Paragraph():
            for child in token.children:
                parse(child)
        case Heading():
            current_level = token.level
            title = ''.join(c.content for c in token.children if hasattr(c, 'content'))
            heading[current_level] = title
        case _:
            tokens.append(token)
            sections[key] = tokens

if __name__ == "__main__":
    content = pathlib.Path("./data/docker.md").read_text(encoding="utf8")
    parser = mistune.create_markdown(renderer="ast", escape=True)
    for token in Document(content).children:
        parse(token)
    renderer = MarkdownRenderer()

    typed_sections: dict[str, dict] = {}
    for section_name, tokens in sections.items():
        # print(f"![{section_name}]!")

        content = ""
        code_placeholders = {}
        i = 0
        for token in tokens:
            render = renderer.render(token)
            match(token):
                case CodeFence():
                    key = f"p{i}"
                    code_placeholders[key] = render
                    content += f"${{{key}}}\n"
                    i += 1
                case BlockCode():
                    key = f"p{i}"
                    code_placeholders[key] = render
                    content += f"${{{key}}}\n"
                    i += 1
                case List():
                    key = f"p{i}"
                    code_placeholders[key] = render
                    content += f"${{{key}}}\n"
                    i += 1
                case InlineCode():
                    key = f"p{i}"
                    code_placeholders[key] = render
                    content = f"{content[:-1]}{{{key}}}"
                    i += 1
                case _:
                    content += render

        # post-processing
        bs = BeautifulSoup(f"<root>{content}</root>", "html.parser")
        result = []
        for node in bs.root.contents:
            if node.name == "details":
                summary = node.summary.get_text(strip=True)
                summary = summary.format(**code_placeholders).strip().replace("\n", "")
                body = "".join(str(c) for c in node.contents if c.name != "summary")
                result.append({"type": "details", "summary": summary, "body": body})
                key = f"{section_name}.{summary}"
                typed_sections[key] = body
            else:
                text = str(node).strip().format(**code_placeholders)
                if text:
                    result.append({"type": "text", "body": text})
                typed_sections[section_name] = typed_sections.get(section_name, "") + text
                
    for k in typed_sections:
        print(k)