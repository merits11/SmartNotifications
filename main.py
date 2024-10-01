import logging
import subprocess
from os import environ
from pathlib import Path

import click

from llm.client import get_llm_client
from llm.prompts import build_command_find_prompt
from utils.input import user_input

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)


@click.group()
def cli():
    pass


@cli.command()
@click.option('-i', '--instruction', type=str, help='Use natural language to describe what you want to do')
@click.argument('extra_args', nargs=-1)
@click.option('--kb', type=str, default=lambda: str(Path(__file__).resolve().parent / 'knowledge/private_kb.md'),
              help='Knowledge base file path')
def run(instruction, extra_args, kb):
    if not instruction:
        instruction = user_input("What shall I run, your highness? 🧐")
    while instruction != '/q':
        process_action(instruction, extra_args, kb)
        instruction = user_input("What else do you need? /q to quit:")


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


def process_action(action, extra_args, kb):
    client = get_llm_client()
    kb_content = Path(kb).read_text()
    system_prompt = build_command_find_prompt(kb_content)
    chat_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is the user input: {action}"}
    ]
    if extra_args:
        chat_messages.append({"role": "user", "content": f"Here are the file arguments to the command: {extra_args}"})
    response = client.get_chat_completion(chat_messages)
    content = response.choices[0].message.content
    command_from_llm = sanitize_command(content)
    shell, rc = get_shell_and_rc()
    edited_command = user_input(f"Running command with {shell}?\n", default=command_from_llm)
    final_command = f'source {rc} && {edited_command}'
    result = subprocess.run(final_command, shell=True, executable=shell)
    logging.info(f"Command returned status {result.returncode}")


if __name__ == "__main__":
    cli()
