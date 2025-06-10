from __future__ import annotations

from enum import Enum
from os import environ
from pathlib import Path
import base64
import mimetypes


class ContentLoadType(Enum):
    NORMAL = "normal"
    PRELOAD = "preload"
    FILE = "file"
    IMAGE = "image"


def get_shell_and_rc():
    shell = environ.get("SHELL", "/bin/zsh")
    if "zsh" in shell:
        return shell, f"{environ.get('HOME')}/.zshrc"
    raise ValueError(f"Not yet implemented for shell {shell}")


def read_file(file_path: str | Path, default: str = "") -> str:
    if not file_path:
        return default
    file_content = default
    if isinstance(file_path, str):
        kb_path = Path(file_path)
    else:
        kb_path = file_path
    if kb_path.exists():
        file_content = kb_path.read_text()
    return file_content


def sanitize_shell_command(content: str) -> str:
    lines = content.split("\n")
    if len(lines) == 1:
        return content
    elif len(lines) == 3:
        return lines[1]
    else:
        raise ValueError(f"response is not parsable: {content}")


def _load_image_file(path: str) -> dict:
    """Helper function to load and encode an image file.

    Args:
        path: Path to the image file

    Returns:
        A dictionary containing the image data in OpenAI API format
    """
    mime_type, _ = mimetypes.guess_type(path)
    if not mime_type or not mime_type.startswith("image/"):
        return None

    # Read image file and encode as base64
    with open(path, "rb") as img_file:
        base64_image = base64.b64encode(img_file.read()).decode("utf-8")
        # Format exactly as OpenAI API expects
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_image}",
                "detail":"auto"
            },
        }


def maybe_load_content(
        file_path_or_str: str | None,
) -> tuple[ContentLoadType, str | dict]:
    if not file_path_or_str:
        return ContentLoadType.NORMAL, ""

    # Handle preload URLs
    if file_path_or_str.startswith("preload:file://"):
        path = file_path_or_str[15:]  # Remove "preload:file://" prefix
        image_content = _load_image_file(path)
        if image_content:
            return ContentLoadType.PRELOAD, image_content
        return ContentLoadType.PRELOAD, read_file(path)

    # Handle regular file URLs
    if file_path_or_str.startswith("file://"):
        path = file_path_or_str[7:]  # Remove "file://" prefix
        image_content = _load_image_file(path)
        if image_content:
            return ContentLoadType.IMAGE, image_content
        return ContentLoadType.FILE, read_file(path)

    return ContentLoadType.NORMAL, file_path_or_str
