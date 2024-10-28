import json
import logging
import subprocess
import webbrowser
from os import environ
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown

from llm.client import get_llm_client
from llm.conversation import Conversation
from llm.prompts import build_command_generation_prompt, build_emoji_generation_prompt, build_link_generation_prompt, \
    build_generic_prompt, build_text_enhancement_prompt
from utils.input import user_input
import pyperclip

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

brand_emoji = "🧐"


@click.group()
@click.option('-s', '--system-prompt-file', type=str, default=None,
              help='Path to the system prompt file')
@click.pass_context
def cli(ctx, system_prompt_file):
    ctx.ensure_object(dict)
    ctx.obj['system_prompt_file'] = system_prompt_file


# New chat command with continuous loop
@cli.command()
@click.option('-i', '--instruction', type=str, help='Provide the initial instruction for chat')
@click.pass_context
def chat(ctx, instruction):
    conversation = Conversation()
    conversation.add_system_message(build_generic_prompt())

    # If there's an initial instruction, run it
    if instruction:
        conversation.add_user_message(instruction)
        run_llm_streaming(conversation)

    # Start continuous loop for follow-up instructions
    while True:
        instruction = user_input(f"\n{brand_emoji} What would you like to chat about? Type /q to quit: ")

        if instruction.strip().lower() == "/q":
            console.print("[red]Goodbye![/red] Exiting chat.")
            break

        # Add the user instruction to the conversation
        conversation.add_user_message(instruction)

        # Process the user's instruction with the LLM
        run_llm_streaming(conversation)


@cli.command()
@click.option('-i', '--instruction', type=str, help='Provide the instruction for chat completion')
@click.pass_context
def complete(ctx, instruction):
    if not instruction:
        instruction = user_input(f"\n{brand_emoji} What would you like to ask about?")
    conversation = Conversation()
    conversation.add_system_message(build_generic_prompt())
    conversation.add_user_message(instruction)
    content = run_llm(conversation)

    # Print the markdown to terminal using rich
    console.print(Markdown(content))


@cli.command()
@click.option('-i', '--instruction', type=str, help='Use natural language to describe what you want to do')
@click.argument('extra_args', nargs=-1)
@click.option('--kb', type=str, default=lambda: str(Path(__file__).resolve().parent / 'knowledge/private_kb.md'),
              help='Knowledge base file path')
@click.pass_context
def run(ctx, instruction, extra_args, kb):
    if not instruction:
        instruction = user_input(f"\n{brand_emoji} What shall I run, your highness:")
    conversation = Conversation()
    kb_content = Path(kb).read_text()
    system_prompt = build_command_generation_prompt(kb_content)
    conversation.add_system_message(load_system_prompt(ctx, system_prompt))
    if extra_args:
        conversation.add_user_message(f"Here are the file arguments user provided: {extra_args}")
    while instruction != '/q':
        run_action(instruction, conversation)
        instruction = user_input(f"\n{brand_emoji} What else do you need? /q to quit:")


@cli.command()
@click.option('-i', '--instruction', type=str, help='Use natural language to describe what you want to do')
@click.option('--kb', type=str, default=lambda: str(Path(__file__).resolve().parent / 'knowledge/private_ddlol.md'),
              help='Knowledge base file path')
@click.pass_context
def goto(ctx, instruction, kb):
    if not instruction:
        instruction = user_input(f"\n{brand_emoji} Describe your link:")
    conversation = Conversation()
    goto_link(ctx, instruction, kb, conversation)


@cli.command()
@click.option('-i', '--instruction', type=str, help='Use natural language to describe what you want to do')
@click.pass_context
def emoji(ctx, instruction):
    if not instruction:
        instruction = user_input(f"\n{brand_emoji} Describe your emoji:")
    conversation = Conversation()
    content = get_emoji(ctx, instruction, conversation)
    # Copy the enhanced text to clipboard
    pyperclip.copy(content)  # Copying the content to clipboard
    console.print("[bold blue]Emoji copied to clipboard![/bold blue]")


@cli.command()
@click.option('-i', '--instruction', type=str, default="", help='Specific instruction for the text enhancement')
@click.option('-t', '--text', type=str, help='Text to enhance')
@click.pass_context
def enhance(ctx, instruction, text):
    if not instruction:
        instruction = user_input(f"\n{brand_emoji} Any specific instruction:").strip()
    if not text:
        text = user_input(f"\n{brand_emoji} What text would you like to enhance:")
    conversation = Conversation()
    content = enhance_text(ctx, instruction, text, conversation)
    # Copy the enhanced text to clipboard
    pyperclip.copy(content)  # Copying the content to clipboard
    console.print("[bold blue]Enhanced text copied to clipboard![/bold blue]")


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


def enhance_text(ctx, instruction, text_input, conversation):
    system_prompt = build_text_enhancement_prompt()
    conversation.add_system_message(load_system_prompt(ctx, system_prompt))
    if instruction:
        conversation.add_user_message(f"Here is the user instruction:\n\n{instruction}")
    conversation.add_user_message(f"Here is the user input: \n\n{text_input}")
    content = run_llm(conversation)
    console.print(f"[bold green]Here is enhanced text:[/bold green]\n\n{content}")
    return content


def get_emoji(ctx, instruction, conversation):
    system_prompt = build_emoji_generation_prompt()
    conversation.add_system_message(load_system_prompt(ctx, system_prompt))
    conversation.add_user_message(f"Here is the user input: {instruction}")
    content = run_llm(conversation)
    console.print(f"[bold green]Here is your emoji:[/bold green] {content}")
    return content


def goto_link(ctx, instruction, kb, conversation):
    kb_content = Path(kb).read_text()
    system_prompt = build_link_generation_prompt(kb_content)
    conversation.add_system_message(load_system_prompt(ctx, system_prompt))
    conversation.add_user_message(f"Here is the user input: {instruction}")
    link = run_llm(conversation)
    console.print(f"[bold blue]Opening link:[/bold blue] [underline]{link}[/underline]")
    webbrowser.open(link)


def run_action(action, conversation):
    if action == "/regenerate":
        conversation.add_user_message(f"User does not like the command, regenerate!")
    else:
        conversation.add_user_message(f"User follows up: {action}")
    content = run_llm(conversation)
    command_from_llm = sanitize_shell_command(content)
    shell, rc = get_shell_and_rc()
    edited_command = user_input(f"Running this command?\n", default=command_from_llm)
    # regenerating the final command
    if edited_command.endswith("!"):
        return run_action("/regenerate", conversation)
    elif edited_command.endswith("~") or edited_command.endswith("/q"):
        conversation.add_user_message("User aborted the command.")
        return
    else:
        final_command = f'source {rc} && {edited_command}'
        result = subprocess.run(final_command, shell=True, executable=shell)
        status_color = "green" if result.returncode == 0 else "red"
        console.print(
            f"\n[bold cyan]Command returned status:[/bold cyan] [bold {status_color}]{result.returncode}[/bold {status_color}]")
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


def run_llm_streaming(conversation):
    """
    This function calls the LLM in streaming mode and prints the response as it comes in.
    """
    client = get_llm_client()
    response_stream = client.converse_stream(conversation)  # Assuming 'converse_stream' for streaming

    # Iterate over the streaming response
    for chunk in response_stream:
        content_chunk = chunk.content
        if content_chunk:
            console.print(content_chunk, end='', markup=True)  # Print each part of the response as it's received

    # Final message after the stream ends
    console.print("\n[green]Stream complete.[/green]")  # Just a fun end message


def load_system_prompt(ctx, default_system_prompt):
    system_prompt_file = ctx.obj.get('system_prompt_file')
    if system_prompt_file and Path(system_prompt_file).exists():
        return Path(system_prompt_file).read_text()
    else:
        return default_system_prompt


if __name__ == "__main__":
    cli()
