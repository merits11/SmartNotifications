import logging
import subprocess
import webbrowser
from os import environ
from pathlib import Path

import click

from llm.client import get_llm_client
from llm.prompts import build_command_generation_prompt, build_emoji_generation_prompt, build_link_generation_prompt
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
        instruction = user_input("🧐What shall I run, your highness:")
    while instruction != '/q':
        run_action(instruction, extra_args, kb)
        instruction = user_input("What else do you need? /q to quit:")


@cli.command()
@click.option('-i', '--instruction', type=str, help='Use natural language to describe what you want to do')
@click.option('--kb', type=str, default=lambda: str(Path(__file__).resolve().parent / 'knowledge/private_ddlol.md'),
              help='Knowledge base file path')
def goto(instruction, kb):
    if not instruction:
        instruction = user_input("🧐Describe your link:")
    goto_link(instruction, kb)


@cli.command()
@click.option('-i', '--instruction', type=str, help='Use natural language to describe what you want to do')
def emoji(instruction):
    if not instruction:
        instruction = user_input("Describe your emoji:")
    get_emoji(instruction)


def sanitize_shell_command(content: str) -> str:
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


def get_emoji(instruction):
    system_prompt = build_emoji_generation_prompt()
    chat_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is the user input: {instruction}"}
    ]
    content = run_llm(chat_messages)
    print(f"Here is your emoji: {content}")


def goto_link(instruction, kb):
    kb_content = Path(kb).read_text()
    system_prompt = build_link_generation_prompt(kb_content)
    chat_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is the user input: {instruction}"}
    ]
    link = run_llm(chat_messages)
    print(f"Opening link {link}")
    webbrowser.open(link)


def run_action(action, extra_args, kb):
    kb_content = Path(kb).read_text()
    system_prompt = build_command_generation_prompt(kb_content)
    chat_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is the user input: {action}"}
    ]
    if extra_args:
        chat_messages.append({"role": "user", "content": f"Here are the file arguments to the command: {extra_args}"})
    content = run_llm(chat_messages)
    command_from_llm = sanitize_shell_command(content)
    shell, rc = get_shell_and_rc()
    edited_command = user_input(f"Running command with {shell}?\n", default=command_from_llm)
    final_command = f'source {rc} && {edited_command}'
    result = subprocess.run(final_command, shell=True, executable=shell)
    print(f"Command returned status {result.returncode}")


def run_llm(chat_messages):
    client = get_llm_client()
    response = client.get_chat_completion(chat_messages)
    return response.choices[0].message.content


if __name__ == "__main__":
    cli()
