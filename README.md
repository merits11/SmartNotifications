## Smart Local Automations with AI

### Overview
This project aims to simplify the automation of local tasks by leveraging AI and messaging capabilities. Users can perform actions without needing to memorize complex commands; they simply describe what they want to achieve.

### Key Features
- **Natural Language Processing**: Interact using plain language to specify tasks.
- **User-Friendly Interface**: Intuitive design that minimizes the learning curve.

### How It Works
1. **Input**: Users provide a description of the task they want to automate.
2. **Processing**: The system interprets the input using AI to determine the appropriate action.
3. **Execution**: The specified task is executed seamlessly.


### Usage

```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  chat
  complete
  emoji
  goto
  run
```

### Examples

#### Run command
```
$poetry run python main.py run                                                                                                                       [13:46:31]
 
🧐 What shall I run, your highness:show all git remotes
Running this command?
git remote -v
github  git@github.com:merits11/SmartNotifications.git (fetch)
github  git@github.com:merits11/SmartNotifications.git (push)
origin  git@gitlab.com:merits/smartnotifications.git (fetch)
origin  git@gitlab.com:merits/smartnotifications.git (push)

Command returned status: 0
 
🧐 What else do you need? /q to quit:
```

#### Chat command
```commandline
 $poetry run python main.py chat                                                                                                                      [13:51:45]
 
🧐 What would you like to chat about? Type /q to quit: hi
Hello! How can I assist you today? Whether you have questions about the command line, coding, or macOS in general, I'm here to help!
Stream complete.

🧐 What would you like to chat about? Type /q to quit:
```
### Setup
TBD