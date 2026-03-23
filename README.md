# Coding Agent

I need to lean into LLM agents coding for me or leave the industry.

If I don't enjoy this experience then I should quit tech.

### Commands

#### /agent-implement

The `/agent-implement` command triggers the coding agent to implement an issue. To use it, leave a comment on an issue with the following format:

```
/agent-implement please implement the above issue
```

The agent will:
- Checkout the issue repository
- Read information about the repository and the issue
- Gather context using tools about the files in the repository
- Generate a code patch that can be applied to the repository that addresses the issue

#### /agent-ask

The `/agent-ask` command triggers the agent to answer questions about the codebase. To use it, leave a comment on a PR (review comment or regular comment) with the following format:

```
/agent-ask what does the handle() method do in base_handler.py?
```

The agent will:
- Checkout the PR branch
- Read information about the repository structure and AGENTS.md if present
- Use tools to search files, list directories, and read file contents
- Respond with an answer to the question

This is useful for asking questions about code context during code review without needing to manually explore the repository.

#### /agent-update

The `/agent-update` command triggers the coding agent to make changes to an existing PR. To use it, leave a comment on a PR (review comment or regular comment) with the following format:

```
/agent-update fix the typo in the function name
```

The agent will:
- Checkout the PR branch
- Read information about the repository and the code context from the review comment
- Gather context using tools about the files in the repository
- Generate a code patch and commit it directly to the existing PR branch

### Modalities

This agent supports the following input modalities:

#### Text

Text messages are the primary input method. The agent processes text-based commands and questions through the various `/agent-*` commands documented above.

#### Audio

The agent can also process audio file attachments with the following constraints:

- **Single file limit**: Only 1 audio file can be processed at a time. If multiple files are attached, the agent will request that files be sent one at a time.
- **Allowed MIME types**: Currently only `mp3` or `wav` file types are supported.
  - `audio/mpeg` (MP3)
  - `audio/mp3` (MP3)
  - `audio/wav` (WAV)
- **Non-audio files**: Other file types (images, documents, etc.) are not currently supported.

Audio files are transcribed and processed as text input alongside any accompanying message text.

### Slack Integration

This coding agent integrates with Slack for notifications and interactions. Slack configuration is required for the application to function. See the "Environment Variables" section for configuration details.

### Database (CouchDB)

CouchDB is the required database for this application. The following environment variables must be configured: `DB_URL`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`. See the "Environment Variables" section for CouchDB configuration details.

### Configuring Git Webhooks

The Git webhook must include the Slack workspace ID in the path: `/{workspace_id}/gitea/events`.

For example, if your Slack workspace ID is `T123456`, the webhook URL becomes `https://your-domain.com/T123456/gitea/events`.

This is required for Slack integration to work properly.

### Environment Variables

| Name | Where it's used | Purpose / description |
| :-- | :-- | :-- |
| `REPO_BASE_URL` | `handlers/planning_handler.py:443,451` | Base URL for the Git repository. Used to build clone URLs and repository API endpoints. |
| `AGENT_TOKEN` | `utils/repo.py:23` | Git authentication token used in clone URLs. |
| `AGENT_SECRET` | `main.py:40,48,53,56,70` | Bearer token used to authenticate incoming webhook requests. |
| `AGENT_USERNAME` | `utils/repo.py:23` | Git username used in clone URLs with `AGENT_TOKEN`. |
| `OPEN_ROUTER_API_KEY` | `utils/transcribe.py:27`, `flows/run_planning_compaction.py:47`, `data/open_router.py:33`, `flows/agent_ask.py:67`, `flows/agent_implement.py:111`, `handlers/planning_handler.py:188` | API key used to authenticate requests to OpenRouter for chat and transcription calls. |
| `AGENT_MODELS` | `data/open_router.py:20` | Comma-separated list of available agent/coding models. |
| `PLANNING_MODELS` | `data/open_router.py:14` | Comma-separated list of available planning models. |
| `AUDIO_MODELS` | `data/open_router.py:26` | Comma-separated list of available audio transcription models. |
| `DB_URL` | `data/db_handler.py:239` | CouchDB host and port used to construct the database base URL. |
| `DB_USER` | `data/db_handler.py:243` | CouchDB username used for database authentication. |
| `DB_PASSWORD` | `data/db_handler.py:243` | CouchDB password used for database authentication. |
| `DB_NAME` | `data/db_handler.py:47,64,81,102,130,168,196` | CouchDB database name used for storing workspace, channel, and message data. |
| `SLACK_SIGNING_SECRET` | `utils/slack.py:16` | Slack signing secret used to verify Slack event request signatures. |
| `SLACK_CLIENT_ID` | `main.py:157` | Slack OAuth client ID used during workspace installation. |
| `SLACK_CLIENT_SECRET` | `main.py:158` | Slack OAuth client secret used during workspace installation. |
| `ADMIN_SECRET` | `main.py:179,182,196` | Bearer token used to protect admin endpoints. |
| `COMPACT_ON_POST` | `handlers/planning_handler.py:420` | Enables automatic compaction after a successful post when set to `true`. |

Slack configuration is required: `SLACK_SIGNING_SECRET`, `SLACK_CLIENT_ID`, and `SLACK_CLIENT_SECRET` must be set for the application to function.

### Environment Variables

| Name | Description | Required |
| :------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------- | :------- |
| `REPO_BASE_URL` | The base URL for the Git repository (e.g., `github.com` or `gitea.example.com`). Used to construct clone URLs and API endpoints. | Yes |
| `AGENT_TOKEN` | The authentication token for the agent to access repositories. Used with `AGENT_USERNAME` for Git operations. | Yes |
| `AGENT_USERNAME` | The username for the agent to access repositories. Used with `AGENT_TOKEN` for Git operations. | Yes |
| `AGENT_SECRET` | The secret token for webhook authentication. Used to verify incoming webhook requests. | Yes |
| `OPEN_ROUTER_API_KEY` | The API key for OpenRouter (LLM API provider). Used to authenticate with the OpenRouter API for model inference. | Yes |
| `AGENT_MODEL` | The model to use for coding tasks. | Yes |
| `PLANNING_MODEL` | The model to use for planning tasks. | Yes |
| `ADMIN_SECRET` | The secret token for admin endpoints. Used to verify admin API requests. | No |
| `SLACK_SIGNING_SECRET` | The signing secret for Slack API requests. | No |
| `SLACK_CLIENT_ID` | The client ID for your Slack app. | No |
| `SLACK_CLIENT_SECRET` | The client secret for your Slack app. | No |
| `DB_URL` | The URL for the CouchDB instance (e.g., `main-db:5984`). | Yes |
| `DB_USER` | The username for CouchDB authentication. | Yes |
| `DB_PASSWORD` | The password for CouchDB authentication. | Yes |
| `DB_NAME` | The name of the database to use within CouchDB. | Yes |

### Future Features

- If you want to naturally chat with the agent then `openai/gpt-audio` is the way forward. However, it is verrrryy expensive.
- Run tests function (will need a run_tests.sh file, or Makefile command) -> return is success or failure with a message
- Run linting function (will need a run_lint.sh file, or Makefile command) -> return is success or failure with a message
- If performance is not 100% then try the planner/coder model where 1 model (maybe a thinking one) plans the approach to the solution and another model (a coding specific one) calls the replace, insert and delete functions
- Add guardrails in the form of another LLM that checks output and provides feedback before the patch is accepted
- Add benchmarks for code complexity, performance e.t.c and ask the model to optimise for it
