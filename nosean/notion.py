from pathlib import Path

from nosean.parse_md import MarkdownParser, Section


class NotionVault:

    def __init__(self, path):
        self.path = path
    
    def get_entries(self):
        result: dict[str, Section] = {}
        for file in Path(self.path).glob("**/*.md"):
            parser = MarkdownParser(file)
            result = parser.try_parse()
            for k, v in result.items():
                result[k] = v
        return result