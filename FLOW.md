# Flow

When the user request that the agent complete some code several steps need to take place in a loop until the agent has enough context to complete the task.

The desired end state is a code patch that can be sucessfully applied to the code base.

The flow is as follows:

- The bot checks out the repo with a shallow copy of depth=1
- The initial prompt is created that:
  - tells the LLM it is a coding agent that generates patches related to tasks on a repo
  - tells the LLM about the repo including file structure and then the issue it needs to fix
  - search for AGENTS.md and send that through by default
  - tells the LLM that it should call tools to get context until it can generate a patch
- Then the list of tools is sent as part of the API body that seems to be part of model /chat endpoint now
- Basically just keep calling the LLM and if it responds with a tool call then add the response to the list of messages and call it again
- You need limits e.g. no more than 50 calls or something, no more than X lines per file read (it can request more), no more than X matches for a regex search

Use ChatGPT to help craft the propmts to send.

This should produce an initial MR then......

- You can leave MR comments to make the model change it to your liking
- You could have another LLM run once per topic in which you are interested e.g. performance and make the first model be better
