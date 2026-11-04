import re


def slugify(text: str) -> str:
    """'FastAPI Basics!' -> 'fastapi-basics'"""
    return "-".join(re.findall(r"[a-z0-9]+", text.lower()))
