import argparse

from nosean.app import MyApp
from nosean.vault import Vault

VAULT_PATH = r"C:\Users\Peter\code\work\xr-lab\terminology"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("vault_path", nargs="?", default=VAULT_PATH)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    vault_path = args.vault_path
    vault = Vault(path=vault_path)
    options = vault.get_entries()
    app = MyApp(entries=options)
    app.run()
