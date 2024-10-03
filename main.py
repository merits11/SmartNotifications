import json
import logging
import subprocess
import webbrowser
from os import environ
from pathlib import Path

import click

from llm.client import get_llm_client
from llm.conversation import Conversation
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
    conversation = Conversation()
    while instruction != '/q':
        run_action(instruction, extra_args, kb, conversation)
        instruction = user_input("What else do you need? /q to quit:")


@cli.command()
@click.option('-i', '--instruction', type=str, help='Use natural language to describe what you want to do')
@click.option('--kb', type=str, default=lambda: str(Path(__file__).resolve().parent / 'knowledge/private_ddlol.md'),
              help='Knowledge base file path')
def goto(instruction, kb):
    if not instruction:
        instruction = user_input("🧐Describe your link:")
    conversation = Conversation()
    goto_link(instruction, kb, conversation)


@cli.command()
@click.option('-i', '--instruction', type=str, help='Use natural language to describe what you want to do')
def emoji(instruction):
    if not instruction:
        instruction = user_input("Describe your emoji:")
    conversation = Conversation()
    get_emoji(instruction, conversation)


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


def get_emoji(instruction, conversation):
    system_prompt = build_emoji_generation_prompt()
    conversation.add_system_message(system_prompt)
    conversation.add_user_message(f"Here is the user input: {instruction}")
    content = run_llm(conversation)
    print(f"Here is your emoji: {content}")


def goto_link(instruction, kb, conversation):
    kb_content = Path(kb).read_text()
    system_prompt = build_link_generation_prompt(kb_content)
    conversation.add_system_message(system_prompt)
    conversation.add_user_message(f"Here is the user input: {instruction}")
    link = run_llm(conversation)
    print(f"Opening link {link}")
    webbrowser.open(link)


def run_action(action, extra_args, kb, conversation):
    if not conversation.messages:
        kb_content = Path(kb).read_text()
        system_prompt = build_command_generation_prompt(kb_content)
        conversation.add_system_message(system_prompt)
        conversation.add_user_message(f"Here is the user input: {action}")
        if extra_args:
            conversation.add_user_message(f"Here are the file arguments user provided: {extra_args}")
    else:
        conversation.add_user_message(f"User follows up: {action}")
    content = run_llm(conversation)
    command_from_llm = sanitize_shell_command(content)
    shell, rc = get_shell_and_rc()
    edited_command = user_input(f"Running command with {shell}?\n", default=command_from_llm)
    final_command = f'source {rc} && {edited_command}'
    result = subprocess.run(final_command, shell=True, executable=shell)
    print(f"Command returned status {result.returncode}")
    conversation.add_user_message(f"User ran `{edited_command}`, exited with code {result.returncode}")


def run_llm(conversation):
    client = get_llm_client()
    response = client.converse(conversation)
    # Write to JSON file TODO: organize better
    output_path = '/tmp/smart-conversation.json'
    try:
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(conversation.messages, json_file, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error writing to file: {e}")
    return response.choices[0].message.content


if __name__ == "__main__":
    cli()
