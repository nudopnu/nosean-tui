import argparse

from nosean.app import MyApp
from nosean.vault import Vault

VAULT_PATH = r"C:\Users\peter\code\work\hst2\terminology"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("vault_path", nargs="?", default=VAULT_PATH)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    vault = Vault(path=args.vault_path)
    app = MyApp(entries=vault.get_entries())
    app.run()
