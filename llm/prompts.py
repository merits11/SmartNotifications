from typing import Dict

# Template with placeholders for user_input and knowledge_file_content


generic_system_prompt = """
You are a helpful AI assistant designed to support software engineers working on MacOS in a CLI environment.

Your goal is to provide accurate, concise, and relevant information, code snippets, or suggestions for terminal-based tasks.

Respond in Markdown format with appropriate code blocks, lists, and headings.
You can also assist with a wide range of other topics—feel free to make things fun and enjoyable when appropriate!
"""

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
If no rules apply, return a legit URL based on your best knowledge.

Knowledge file content:
<<<knowledge_file>>>
{knowledge_file_content}
<<<end_knowledge_file>>>

Respond only with the complete link or URL.
"""

text_enhancement_prompt = """
You are a text enhancement assistant. Your task is to enhance the provided user input by optimizing its grammar and making it more understandable.

1. Correct any grammatical errors.
2. Improve sentence structure for clarity.
3. Ensure the content is easy to read and understand.
4. Perform any other enhancements that you think are necessary or requested by the user.

Respond only with the enhanced text.
"""


def build_generic_prompt() -> str:
    return generic_system_prompt


def build_link_generation_prompt(knowledge_file_content: str) -> str:
    args = {'knowledge_file_content': knowledge_file_content}
    return build_prompt(generate_link_prompt_template, args)


def build_command_generation_prompt(knowledge_file_content: str) -> str:
    args = {'knowledge_file_content': knowledge_file_content}
    return build_prompt(generate_command_prompt_template, args)


def build_emoji_generation_prompt() -> str:
    return build_prompt(generate_emoji_prompt_template, {})


def build_text_enhancement_prompt() -> str:
    return text_enhancement_prompt


def build_prompt(template: str, args: Dict) -> str:
    return template.format(**args)
