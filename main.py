import argparse
import logging
import os.path
import subprocess
from os import environ
from pathlib import Path

from llm.client import get_llm_client
from llm.prompts import build_command_find_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="CLI tool for processing input strings.")
    # Add an argument for the action
    parser.add_argument('--action', type=str, help='Use natural language to describe what you want to do')
    repo_dir = Path(__file__).resolve().parent
    default_kb = os.path.join(repo_dir, 'knowledge/private_kb.md')
    parser.add_argument('--kb', type=str, default=default_kb, help='Knowledge base file path')

    # Parse the arguments
    args = parser.parse_args()

    # Implement your logic based on the action argument
    if not args.action:
        args.action = input("What shall I run, your highness? 🧐")
    process_action(args)


def sanitize_command(content: str) -> str:
    lines = content.split('\n')
    if len(lines) == 1:
        return content
    elif len(lines) == 3:
        return lines[1]
    else:
        raise ValueError(f"response is not parsable: {content}")


def get_shell_and_rc():
    shell = environ.get("SHELL", '/bin/zsh')
    if 'zsh' in shell:
        return shell, f"{environ.get('HOME')}/.zshrc"
    raise ValueError(f'Not yet implemented for shell {shell}')


def process_action(args):
    action = args.action
    client = get_llm_client()
    kb = Path(args.kb).read_text()
    system_prompt = build_command_find_prompt(kb)
    response = client.get_chat_completion(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": f"Here is the user input: {action}"}, ])
    content = response.choices[0].message.content
    command_from_llm = sanitize_command(content)
    shell, rc = get_shell_and_rc()
    input(f"Running: `{command_from_llm}` with {shell}?")
    final_command = f'source {rc} && {command_from_llm}'
    subprocess.run(final_command, shell=True, check=True, executable=shell)


if __name__ == "__main__":
    main()
