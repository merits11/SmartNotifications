

AWESOME_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open an application on Mac",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the app",
                    },
                },
                "required": ["app_name"],
            },
        },
    },
]