import argparse

from nosean.app import MyApp
from nosean.notion import NotionVault
from nosean.vault import Entry

VAULT_PATH = "data/"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("vault_path", nargs="?", default=VAULT_PATH)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    vault = NotionVault(path=args.vault_path)
    entries = vault.get_entries()
    entries = [Entry(name, value["body"], {}) for name, value in entries.items()]
    app = MyApp(entries=entries)
    app.run()
