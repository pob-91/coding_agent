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
        "name": "replace_text",
        "description": "Replace a piece of text in a given file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the file to modify.",
                },
                "search": {
                    "type": "string",
                    "description": "The block of text to replace in the file.",
                },
                "replacement": {
                    "type": "string",
                    "description": "The replacement block of text to add.",
                },
            },
            "required": ["path", "search", "replacement"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "insert_after",
        "description": "Add new text after a given search phrase in a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the file to modify.",
                },
                "search": {
                    "type": "string",
                    "description": "The block to insert after i.e. the search phrase. This should be a small but unique snippet.",
                },
                "text": {
                    "type": "string",
                    "description": "The new block of text to add after the search phrase.",
                },
            },
            "required": ["path", "search", "text"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "create_file",
        "description": "Create a new file at the given path. Optionally provide initial text content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to repo root.",
                },
                "text": {
                    "type": "string",
                    "description": "Optional initial text content for the file.",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "delete_text",
        "description": "Deletes a block of text in a given file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the file to modify.",
                },
                "search": {
                    "type": "string",
                    "description": "The block to delete.",
                },
            },
            "required": ["path", "search"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "commit",
        "description": "Commit the changes and complete the task. ONLY CALL THIS ONCE THE TASK IS COMPLETE.",
        "parameters": {
            "type": "object",
            "properties": {
                "commit_message": {
                    "type": "string",
                    "description": "A very brief commit message that provides an overview of the changes.",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
]
