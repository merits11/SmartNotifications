from os import environ
from pathlib import Path


def get_shell_and_rc():
    shell = environ.get("SHELL", '/bin/zsh')
    if 'zsh' in shell:
        return shell, f"{environ.get('HOME')}/.zshrc"
    raise ValueError(f'Not yet implemented for shell {shell}')


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
    lines = content.split('\n')
    if len(lines) == 1:
        return content
    elif len(lines) == 3:
        return lines[1]
    else:
        raise ValueError(f"response is not parsable: {content}")
