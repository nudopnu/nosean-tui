import tomllib

from notion_client import Client
from notion_to_md import NotionToMarkdown

def load_env(path: str):
    with open(path, "rb") as file:
        env = tomllib.load(file)
    return {k.lower(): v for k, v in env.items()}

if __name__ == "__main__":
    env = load_env(".env")
    auth = env["notion_api_key"]
    page_ids = env["page_ids"]
    client = Client(auth=auth)
    converter = NotionToMarkdown(client)
    for page_id in page_ids:
        md_blocks = converter.page_to_markdown(page_id)
        md_str = converter.to_markdown_string(md_blocks).get("parent")
        with open(f"{page_id}.md", "w", encoding="utf8") as file:
            file.write(md_str)
