import sys

from prompt_toolkit import prompt


def user_input(hint, default=""):
    if sys.stdin.isatty():
        final_value = prompt(hint, default=default).strip()
    else:
        default_output= f' (defaults to  `{default}`)' if default else ""
        final_value = input(f"{hint}{default_output}:").strip()
        if not final_value:
            final_value = default
    return final_value
