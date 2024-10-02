from typing import Dict
# Template with placeholders for user_input and knowledge_file_content

generate_command_prompt_template = """
You are an assistant that maps user input to predefined shell function calls.

Your task is to identify the most appropriate function from the list below. If no predefined function applies, suggest a valid Mac OS shell command. 
Return a fully executable shell command, including any required arguments, compatible with the Mac OS environment.

Functions and descriptions:
<<<knowledge_file>>>
{knowledge_file_content}
<<<end_knowledge_file>>>

Respond only with the complete shell command.
"""

# Template for generating emoji representation
generate_emoji_prompt_template = """
You are an assistant that converts user input into an emoji representation.

Your task is to analyze the input and return the most appropriate emoji that represents it. 
Respond only with the emoji.
"""


generate_link_prompt_template = """
You are an assistant that generates a single link based on user input.

Your task is to analyze the input and check for applicable rules in the knowledge file. 
If a relevant rule is found, generate one link based on that rule. 
If no rules apply, return a single Google search query URL for the input.

Knowledge file content:
<<<knowledge_file>>>
{knowledge_file_content}
<<<end_knowledge_file>>>

Respond only with the complete link or URL.
"""

def build_link_generation_prompt(knowledge_file_content: str) -> str:
    args = { 'knowledge_file_content': knowledge_file_content }
    return build_prompt(generate_link_prompt_template, args)


def build_command_generation_prompt(knowledge_file_content: str) -> str:
    args = { 'knowledge_file_content': knowledge_file_content}
    return build_prompt(generate_command_prompt_template, args)


def build_emoji_generation_prompt() -> str:
    return build_prompt(generate_emoji_prompt_template, {})

def build_prompt(template: str, args: Dict) -> str:
    return template.format(**args)
