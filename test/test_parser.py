from pathlib import Path

from nosean.parse_md import MarkdownParser


def test_data_dir():
    files = Path("data").glob("**/*.md")
    for file in files:
        parser = MarkdownParser(file)
        parser.parse()
    assert False
