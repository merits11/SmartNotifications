# Template with placeholders for user_input and knowledge_file_content
from typing import Dict

command_find_prompt_template = """
You are an assistant that maps user input to predefined shell function calls.

Your task is to identify the most appropriate function from the list below. If no predefined function applies, suggest a valid Mac OS shell command. 
Return a fully executable shell command, including any required arguments, compatible with the Mac OS environment.

Functions and descriptions:
<<<knowledge_file>>>
{knowledge_file_content}
<<<end_knowledge_file>>>

Respond only with the complete shell command.
"""


def build_command_find_prompt(knowledge_file_content: str) -> str:
    args = { 'knowledge_file_content': knowledge_file_content}
    return build_prompt(command_find_prompt_template, args)


def build_prompt(template: str, args: Dict) -> str:
    return template.format(**args)
