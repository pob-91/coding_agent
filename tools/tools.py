from typing import Any, Iterable

issue_tools: Iterable[Any] = [
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
        "description": "Create a new file at the given path. Automatically creates any necessary subdirectories. Optionally provide initial text content.",
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

ask_tools: Iterable[Any] = [
    {
        "type": "function",
        "name": "search",
        "description": "Search repository using regex.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Regex pattern to search."},
                "sub_path": {
                    "type": "string",
                    "description": "Optional sub-path relative to repo root.",
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
                },
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
                    "description": "Line to start reading from. Defaults to 1.",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Line to stop reading. Defaults to start_line + 50.",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "respond",
        "description": "Submit your final answer. Call this once you have sufficient context to answer the question.",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The answer to post as a comment on the pull request.",
                },
            },
            "required": ["answer"],
            "additionalProperties": False,
        },
    },
]

planning_tools: Iterable[Any] = [
    {
        "type": "function",
        "name": "channel_config",
        "description": "Set the config for a channel so we know how to respond.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "The name of the repo that is associated with the channel.",
                },
            },
            "required": ["repo_name"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search",
        "description": "Search repository using regex.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Regex pattern to search."},
                "sub_path": {
                    "type": "string",
                    "description": "Optional sub-path relative to repo root.",
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
                },
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
                    "description": "Line to start reading from. Defaults to 1.",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Line to stop reading. Defaults to start_line + 50.",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "checkout_branch",
        "description": "Checkout a specific branch in the current repository.",
        "parameters": {
            "type": "object",
            "properties": {
                "branch_name": {
                    "type": "string",
                    "description": "The name of the branch to checkout.",
                },
            },
            "required": ["branch_name"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_branches",
        "description": "List all available branches in the current repo.",
        "parameters": {},
    },
    {
        "type": "function",
        "name": "web_search",
        "description": "Get web search results for a specific search phrase.",
        "parameters": {
            "type": "object",
            "properties": {
                "phrase": {
                    "type": "string",
                    "description": "The web search phrase.",
                },
            },
            "required": ["phrase"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "visit_site",
        "description": "Get the full contents of a webpage.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "A fully qualified web url e.g. https://google.com",
                },
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "post_issue",
        "description": "Post an issue that triggers the coding agent to implement the described change.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title of the issue. This should be brief as it becomes the branch and PR name, try to keep it to no more than 4 words.",
                },
                "body": {
                    "type": "string",
                    "description": "The description of the issue. This should be aimed at the coding agent and include very specific instructions on what to implement.",
                },
            },
            "required": ["title", "body"],
            "additionalProperties": False,
        },
    },
]
