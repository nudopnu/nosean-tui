import os
from pathlib import Path
from dataclasses import dataclass
from typing import Any

import yaml

@dataclass
class Entry:
    name: str
    content: str
    metadata: Any

class Vault:

    def __init__(self, path):
        self.path = path
    
    def get_entries(self) -> list[Entry]:
        result: list[Entry] = []
        for file in Path(self.path).glob("**/*.md"):
            name = os.path.splitext(file.name)[0]
            content = file.read_text(encoding="utf8")
            metadata = None
            lines = content.splitlines()
            if lines and lines[0].strip() == "---":
                for idx, line in enumerate(lines[1:]):
                    if not line.strip() == "---":
                        continue
                    metadata = yaml.safe_load("\n".join(lines[1:idx]))
                    content = "\n".join(lines[idx + 2:])
                    break
            result.append(Entry(name, content, metadata))
        return result

# for testing only
if __name__ == "__main__":
    VAULT_PATH = r"C:\Users\peter\code\work\hst2\terminology"
    vault = Vault(path=VAULT_PATH)
    entries = vault.get_entries()
    for e in entries:
        print(e.name)

