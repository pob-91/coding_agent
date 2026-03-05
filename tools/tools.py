from typing import Any, Iterable

tools: Iterable[Any] = [
    {
        "type": "function",
        "name": "search",
        "description": "Search repository using regex.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Regex pattern to use for search.",
                },
                "sub_path": {
                    "type": "string",
                    "description": "Optional sub-path to limit the search location relative to the repo root.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_files",
        "description": "List files and directories at a given path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to repo root.",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Read a portion of a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to repo root.",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Line from which to read. Cannot be < 1. Defaults to 1.",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Line at which to stop reading. Defaults to start_line + 50.",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "submit_patch",
        "description": "Submit a code patch to resolve the issue.",
        "parameters": {
            "type": "object",
            "properties": {
                "patch": {
                    "type": "string",
                    "description": "A valid git patch to apply to the repo that implements the issue.",
                },
                "commit_message": {
                    "type": "string",
                    "description": "An optional commit message to add when committing the patch.",
                },
            },
            "required": ["patch"],
            "additionalProperties": False,
        },
    },
]
