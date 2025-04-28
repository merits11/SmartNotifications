## Smart Local Automations with AI

### Overview

This project aims to simplify the automation of local tasks by leveraging AI and messaging capabilities. Users can perform actions without needing to memorize complex commands; they simply describe what they want to achieve.

### Key Features

- **Natural Language Processing**: Interact using plain language to specify tasks
- **User-Friendly Interface**: Intuitive design that minimizes the learning curve
- **Multiple AI Models**: Support for different LLM models through profiles
- **Conversation Management**: Save, view, and manage conversations
- **Clipboard Integration**: Easy copy/paste functionality
- **Command History**: Access and reuse previous commands
- **HTML View**: View conversations in a browser
- **Profile System**: Switch between different AI configurations

### How It Works

1. **Input**: Users provide a description of the task they want to automate
2. **Processing**: The system interprets the input using AI to determine the appropriate action
3. **Execution**: The specified task is executed seamlessly
4. **Feedback**: Results are displayed in a user-friendly format

### Usage

```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  -s, --system-prompt-file TEXT  Path to the system prompt file
  -p, --profile TEXT            Profile to apply
  --help                        Show this message and exit.

Commands:
  chat      Start an interactive chat session
  complete  Get a single completion for a prompt
  emoji     Generate an emoji based on description
  goto      Generate and open a URL based on description
  run       Execute shell commands based on natural language
  enhance   Enhance or modify text based on instructions
```

### Special Commands

During chat or command execution, you can use these special commands:

- `/q` - Quit the current session
- `/pb` or `/paste` - Paste clipboard content as context
- `/cp` or `/copy` - Copy message to clipboard
- `/del` or `/delete` - Delete a message
- `/save` - Save the current conversation
- `/profile` - View or change the current profile
- `/model` - View or change the current model
- `/view` - View conversation in browser
- `/last` or `:last` - Run the last command
- `/regenerate` - Regenerate the last command

### Examples

#### Run command

```bash
$ poetry run python main.py run
🧐 What shall I run, your highness: show all git remotes
Running this command?
git remote -v
github  git@github.com:merits11/SmartNotifications.git (fetch)
github  git@github.com:merits11/SmartNotifications.git (push)
origin  git@gitlab.com:merits/smartnotifications.git (fetch)
origin  git@gitlab.com:merits/smartnotifications.git (push)

Command returned status: 0
```

#### Chat command

```bash
$ poetry run python main.py chat
🧐 What would you like to chat about? Type /q to quit: hi
Hello! How can I assist you today? Whether you have questions about the command line, coding, or macOS in general, I'm here to help!
```

#### Emoji generation

```bash
$ poetry run python main.py emoji
🧐 Describe your emoji: happy face
😊
```

#### Text enhancement

```bash
$ poetry run python main.py enhance
🧐 Any specific instruction: Make it more professional
🧐 What text would you like to enhance: hello world
[Enhanced text will be copied to clipboard]
```

### Setup

1. Install dependencies:

```bash
poetry install
```

2. Configure your environment:

   - Create a config file with your API keys and settings
   - Set up profiles for different AI models
   - Configure system prompts if needed

3. Run the application:

```bash
poetry run python main.py [command]
```

### Configuration

The application uses a profile-based configuration system. You can:

- Switch between different AI models
- Configure API keys and endpoints
- Set up custom system prompts
- Manage different profiles for different use cases

