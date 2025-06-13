import json
import logging
import os
import subprocess
import sys
import webbrowser
from os import environ
from pathlib import Path

import click
import pyperclip
from rich.console import Console
from rich.markdown import Markdown

from llm.client import get_llm_client, apply_profile
from llm.conversation import Conversation
from llm.prompts import (
    build_command_generation_prompt,
    build_emoji_generation_prompt,
    build_link_generation_prompt,
    build_generic_prompt,
    build_text_enhancement_prompt,
)
from utils.config import read_config
from utils.helper import (
    get_shell_and_rc,
    read_file,
    sanitize_shell_command,
    maybe_load_content,
    ContentLoadType,
)
from utils.input import user_input

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

brand_emoji = "🧐"

last_conversation_path = "/tmp/smart-conversation.json"
system_prompt_files_key = "system_prompt_files"


@click.group()
@click.option(
    "-s",
    "--system-prompt-file",
    type=str,
    default=[],
    multiple=True,
    help="Path to the system prompt file",
)
@click.option("-p", "--profile", type=str, help="Profile to apply", default=None)
@click.pass_context
def cli(ctx, system_prompt_file, profile):
    ctx.ensure_object(dict)
    ctx.obj[system_prompt_files_key] = system_prompt_file
    if profile:
        if apply_profile(profile):
            console.print(f"[bold green]Profile applied: {profile}[/bold green]")
        else:
            console.print(f"[red]Profile not found: {profile}, using default[/red]")


# New chat command with continuous loop
@cli.command()
@click.option(
    "-i",
    "--instruction",
    type=str,
    multiple=True,
    help="Provide the initial instruction for chat. Can be text or image file path (prefixed with file://)",
)
@click.pass_context
def chat(ctx, instruction):
    conversation = Conversation()
    conversation.add_system_message(load_system_prompt(ctx, build_generic_prompt()))

    def handle_instruction(input_instruction):
        current_content = []
        for instr in input_instruction:
            load_type, processed_instr = maybe_load_content(instr)
            if processed_instr:
                if load_type == ContentLoadType.IMAGE:
                    # Add image to current content array
                    current_content.append(processed_instr)
                else:
                    # If we have accumulated content, add it first
                    if current_content:
                        # Always wrap image content in an array
                        conversation.add_user_message(current_content)
                        current_content = []
                    conversation.add_user_message(processed_instr)
                if load_type == ContentLoadType.PRELOAD:
                    conversation.add_assistant_message("Okay.")

    # If there are initial instructions, collect them all first
    if instruction:
        handle_instruction(instruction)
        # Run LLM streaming if the last message wasn't from assistant
        if conversation.messages[-1]["role"] != "assistant":
            run_llm_streaming(conversation)
        else:
            console.print(
                f"[bold blue]Loaded {len(instruction)} instruction(s)![/bold blue]"
            )

    # Start continuous loop for follow-up instructions
    while True:
        instruction = user_input(
            f"\n{brand_emoji} What would you like to chat about? Type /q to quit: "
        )
        instruction = handle_commands(conversation, instruction)
        if not instruction:
            continue
        handle_instruction([instruction])
        run_llm_streaming(conversation)


@cli.command()
@click.option(
    "-i",
    "--instruction",
    type=str,
    multiple=True,
    help="Provide the instruction for chat completion",
)
@click.pass_context
def complete(ctx, instruction):
    conversation = Conversation()
    conversation.add_system_message(load_system_prompt(ctx, build_generic_prompt()))

    if instruction:
        for instr in instruction:
            _, processed_instr = maybe_load_content(instr)
            if processed_instr:
                processed_instr = handle_commands(conversation, processed_instr)
                if processed_instr:
                    conversation.add_user_message(processed_instr)
    else:
        instruction = user_input(f"\n{brand_emoji} What would you like to ask about?")
        instruction = handle_commands(conversation, instruction)
        if instruction:
            conversation.add_user_message(instruction)

    if conversation.messages:
        content = run_llm(conversation)
        # Print the markdown to terminal using rich
        console.print(Markdown(content))


@cli.command()
@click.option(
    "-i",
    "--instruction",
    type=str,
    multiple=True,
    help="Use natural language to describe what you want to do",
)
@click.argument("extra_args", nargs=-1)
@click.option("--kb", type=str, default="", help="Knowledge base file path")
@click.pass_context
def run(ctx, instruction, extra_args, kb):
    conversation = Conversation()
    kb_content = read_file(kb)
    system_prompt = build_command_generation_prompt(kb_content)
    conversation.add_system_message(load_system_prompt(ctx, system_prompt))
    conversation.add_user_message(
        f'Current directory: "{Path.cwd()}"\n'
        f"Current shell: \"{environ.get('SHELL')}\"\n"
        f"Current user: \"{environ.get('USER')}\""
    )
    if extra_args:
        conversation.add_user_message(
            f"Here are the file arguments user provided: {extra_args}"
        )

    if instruction:
        for instr in instruction:
            _, processed_instr = maybe_load_content(instr)
            if processed_instr:
                processed_instr = handle_commands(conversation, processed_instr)
                if processed_instr:
                    run_action(processed_instr, conversation)
    else:
        instruction = user_input(f"\n{brand_emoji} What shall I run, your highness:")
        instruction = handle_commands(conversation, instruction)
        if instruction:
            run_action(instruction, conversation)

    while True:
        instruction = user_input(f"\n{brand_emoji} What else do you need? /q to quit:")
        instruction = handle_commands(conversation, instruction)
        if instruction:
            run_action(instruction, conversation)


@cli.command()
@click.option(
    "-i",
    "--instruction",
    type=str,
    multiple=True,
    help="Use natural language to describe what you want to do",
)
@click.option("--kb", type=str, default="", help="Knowledge base file path")
@click.pass_context
def goto(ctx, instruction, kb):
    conversation = Conversation()
    kb_content = read_file(kb)
    system_prompt = build_link_generation_prompt(kb_content)
    conversation.add_system_message(load_system_prompt(ctx, system_prompt))

    if instruction:
        for instr in instruction:
            _, processed_instr = maybe_load_content(instr)
            if processed_instr:
                processed_instr = handle_commands(conversation, processed_instr)
                if processed_instr:
                    conversation.add_user_message(
                        f"Here is the user input: {processed_instr}"
                    )
                    for _ in range(3):
                        link = run_llm(conversation)
                        if not link or not link.startswith("https://"):
                            conversation.add_user_message(
                                f"Invalid link. It should start with 'https://'. Please regenerate!"
                            )
                        else:
                            break
                    console.print(
                        f"[bold blue]Opening link:[/bold blue] [underline]{link}[/underline]"
                    )
                    webbrowser.open(link)
    else:
        instruction = user_input(f"\n{brand_emoji} Describe your link:")
        instruction = handle_commands(conversation, instruction)
        if instruction:
            goto_link(ctx, instruction, kb, conversation)


@cli.command()
@click.option(
    "-i",
    "--instruction",
    type=str,
    multiple=True,
    help="Use natural language to describe what you want to do",
)
@click.pass_context
def emoji(ctx, instruction):
    conversation = Conversation()
    system_prompt = build_emoji_generation_prompt()
    conversation.add_system_message(load_system_prompt(ctx, system_prompt))

    if instruction:
        for instr in instruction:
            _, processed_instr = maybe_load_content(instr)
            if processed_instr:
                processed_instr = handle_commands(conversation, processed_instr)
                if processed_instr:
                    conversation.add_user_message(
                        f"Here is the user input: {processed_instr}"
                    )
                    content = run_llm(conversation)
                    console.print(
                        f"[bold green]Here is your emoji:[/bold green] {content}"
                    )
                    # Copy the emoji to clipboard
                    pyperclip.copy(content)
                    console.print("[bold blue]Emoji copied to clipboard![/bold blue]")
    else:
        instruction = user_input(f"\n{brand_emoji} Describe your emoji:")
        instruction = handle_commands(conversation, instruction)
        if instruction:
            content = get_emoji(ctx, instruction, conversation)
            # Copy the emoji to clipboard
            pyperclip.copy(content)
            console.print("[bold blue]Emoji copied to clipboard![/bold blue]")


@cli.command()
@click.option(
    "-i",
    "--instruction",
    type=str,
    multiple=True,
    default=[],
    help="Specific instruction for the text enhancement",
)
@click.option("-t", "--text", type=str, help="Text to enhance")
@click.pass_context
def enhance(ctx, instruction, text):
    conversation = Conversation()
    system_prompt = build_text_enhancement_prompt()
    conversation.add_system_message(load_system_prompt(ctx, system_prompt))

    if not text:
        text = user_input(f"\n{brand_emoji} What text would you like to enhance:")

    if instruction:
        for instr in instruction:
            _, processed_instr = maybe_load_content(instr)
            if processed_instr:
                processed_instr = handle_commands(conversation, processed_instr)
                if processed_instr:
                    conversation.add_user_message(
                        f"Here is the user instruction:\n\n{processed_instr}"
                    )
                    conversation.add_user_message(f"Here is the user input: \n\n{text}")
                    content = run_llm(conversation)
                    console.print(
                        f"[bold green]Here is enhanced text:[/bold green]\n\n{content}"
                    )
                    # Copy the enhanced text to clipboard
                    pyperclip.copy(content)
                    console.print(
                        "[bold blue]Enhanced text copied to clipboard![/bold blue]"
                    )
    else:
        instruction = user_input(f"\n{brand_emoji} Any specific instruction:").strip()
        instruction = handle_commands(conversation, instruction)
        if instruction:
            content = enhance_text(ctx, instruction, text, conversation)
            # Copy the enhanced text to clipboard
            pyperclip.copy(content)
            console.print("[bold blue]Enhanced text copied to clipboard![/bold blue]")


def handle_commands(conversation, instruction) -> str:
    if not instruction:
        return instruction

    parts = instruction.split(" ")

    # Handle special commands
    if parts[0].strip().lower() == "/q":
        console.print("[red]Goodbye![/red] Exiting chat.")
        sys.exit(0)

    if parts[0] in ["/pb", "/paste"]:
        content = pyperclip.paste()
        if not content:
            console.print("[red]No content in clipboard![/red]")
            return True
        conversation.add_user_message("Save this for context:\n\n" + content)
        conversation.add_assistant_message("Okay.")
        console.print(
            f"[bold blue]{len(content)} characters saved for context![/bold blue]"
        )
        return ""

    if parts[0] in ["/cp", "/copy"]:
        if len(parts) > 1:
            if parts[1].isdigit() and -len(conversation.messages) <= int(
                    parts[1]
            ) < len(conversation.messages):
                index = int(parts[1])
                pyperclip.copy(conversation.messages[index]["content"])
                console.print(
                    f"[bold blue]Message at index {index} copied to clipboard![/bold blue]"
                )
            else:
                console.print("[red]Invalid index![/red]")
        else:
            pyperclip.copy(conversation.messages[-1]["content"])
            console.print("[bold blue]Last message copied to clipboard![/bold blue]")
        return ""

    if parts[0] in ["/del", "/delete"]:
        if len(parts) > 1:
            if parts[1].isdigit() and 0 <= int(parts[1]) < len(conversation.messages):
                index = int(parts[1])
                conversation.delete_message(index)
                console.print(
                    f"[bold blue]Message at index {index} deleted![/bold blue]"
                )
            else:
                console.print(
                    f"[red]Invalid index, allowed range [0, {len(conversation.messages) - 1}]![/red]"
                )
        else:
            conversation.delete_message(len(conversation.messages) - 1)
            console.print("[bold blue]Last message deleted![/bold blue]")
        return ""

    if parts[0] == "/save":
        save_path = Path(os.getenv("HOME")) / "Documents" / "Smart" / "Conversations"
        save_path.mkdir(parents=True, exist_ok=True)
        file_name = f"{conversation.started_at.strftime('%Y-%m-%d-%H-%M-%S')}.json"
        save_conversation(conversation, save_path / file_name)
        console.print(
            f"[bold blue]Conversation saved to:[/bold blue] {save_path / file_name}"
        )
        return ""

    if parts[0].startswith("/profile"):
        if len(parts) > 1:
            profile = parts[1]
            if apply_profile(profile):
                conversation.model = read_config().model
                console.print(
                    f"[bold blue]Profile set to:[/bold blue] {profile}, model: {conversation.model}"
                )
            else:
                console.print(f"[red]Profile not found: {profile}[/red]")
        else:
            console.print(
                f"[bold blue]You are currently using profile:[/bold blue] {read_config().get_current_profile()}"
            )
        return ""

    if parts[0].startswith("/model"):
        if len(parts) > 1:
            model = parts[1]
            conversation.model = model
            console.print(f"[bold blue]Model set to:[/bold blue] {model}")
        else:
            console.print(
                f"[bold blue]You are currently using model:[/bold blue] {conversation.model}"
            )
        return ""

    if parts[0] == "/copy":
        if conversation.messages:
            last_message = conversation.messages[-1]["content"]
            pyperclip.copy(last_message)
            console.print("[bold blue]Last message copied to clipboard![/bold blue]")
        else:
            console.print("[red]No messages to copy![/red]")
        return ""

    if parts[0] == "/view":
        save_path = Path(os.getenv("HOME")) / "Documents" / "Smart" / "Temp"
        save_path.mkdir(parents=True, exist_ok=True)
        file_path = (
                save_path / f"{conversation.started_at.strftime('%Y-%m-%d-%H-%M-%S')}.html"
        )
        last_n = 2  # 1 Q/A pair
        if len(parts) > 1:
            if parts[1] == "all":
                last_n = len(conversation.messages)
            elif parts[1].isdigit():
                last_n = int(parts[1])
        with open(file_path, "w") as file:
            file.write(conversation.as_html(last_n=last_n))
        console.print(f"Opening file: file://{file_path}")
        webbrowser.open(f"file://{file_path}")
        return ""

    return instruction


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
    kb_content = read_file(kb)
    system_prompt = build_link_generation_prompt(kb_content)
    conversation.add_system_message(load_system_prompt(ctx, system_prompt))
    conversation.add_user_message(f"Here is the user input: {instruction}")
    for _ in range(3):
        link = run_llm(conversation)
        if not link or not link.startswith("https://"):
            conversation.add_user_message(
                f"Invalid link. It should start with 'https://'. Please regenerate!"
            )
        else:
            break
    console.print(f"[bold blue]Opening link:[/bold blue] [underline]{link}[/underline]")
    webbrowser.open(link)


def run_action(action, conversation):
    if not action:
        return
    # If the action starts with '!', it's a direct command to run
    if action.startswith("!"):
        edited_command = action[1:]
        conversation.add_user_message(f"User directly ran `{edited_command}`")
    elif action.strip() in ["/last", ":last"]:
        last_command = conversation.get_metadata("last_command")
        edited_command = user_input(f"Running this command?\n", default=last_command)
    else:
        if action == "/regenerate":
            conversation.add_user_message(
                f"User does not like the command, regenerate!"
            )
        else:
            conversation.add_user_message(f"User follows up: {action}")
        content = run_llm(conversation)
        command_from_llm = sanitize_shell_command(content)
        edited_command = user_input(
            f"Running this command?\n", default=command_from_llm
        )
    if not edited_command:
        console.print("[red]No command to run![/red]")
        return
        # regenerating the final command
    if edited_command.endswith("!"):
        return run_action("/regenerate", conversation)
    elif edited_command.endswith("~") or edited_command.endswith("/q"):
        conversation.add_user_message("User aborted the command.")
        return
    else:
        shell, rc = get_shell_and_rc()
        final_command = f"source {rc} && {edited_command}"
        result = subprocess.run(final_command, shell=True, executable=shell)
        conversation.add_metadata("last_command", edited_command)
        status_color = "green" if result.returncode == 0 else "red"
        console.print(
            f"\n[bold cyan]Command returned status:[/bold cyan] [bold {status_color}]{result.returncode}[/bold {status_color}]"
        )
        conversation.add_user_message(
            f"User ran `{edited_command}`, exited with code {result.returncode}"
        )


def run_llm(conversation):
    client = get_llm_client()
    response = client.converse(conversation)
    save_conversation(conversation, last_conversation_path)
    return response.choices[0].message.content


def run_llm_streaming(conversation):
    """
    This function calls the LLM in streaming mode and prints the response as it comes in.
    """
    client = get_llm_client()
    response_stream = client.converse_stream(
        conversation
    )  # Assuming 'converse_stream' for streaming

    # Iterate over the streaming response
    for chunk in response_stream:
        content_chunk = chunk.content
        if content_chunk:
            console.print(
                content_chunk, end="", markup=True
            )  # Print each part of the response as it's received

    save_conversation(
        conversation, last_conversation_path
    )  # Save the conversation to a file
    # Final message after the stream ends
    console.print(
        f"\n[green]Stream complete. Index: {len(conversation.messages) - 1} Tokens: {conversation.get_token_usage()}[/green]"
    )


def save_conversation(conversation, file_path):
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(conversation.to_dict(), json_file, ensure_ascii=False, indent=4)
    except IOError as e:
        console.print(f"[red]Error writing conversation to file: {e}[/red]")


def load_system_prompt(ctx, default_system_prompt):
    system_prompt_files = ctx.obj.get(system_prompt_files_key)
    system_prompts = []
    for system_prompt_file in system_prompt_files:
        if system_prompt_file:
            if Path(system_prompt_file).exists():
                system_prompts.append(Path(system_prompt_file).read_text())
            else:
                console.print(
                    f"[red]System prompt file not found at path: {system_prompt_file}[/red]"
                )
                continue
    return [default_system_prompt] if not system_prompts else system_prompts


if __name__ == "__main__":
    cli()
