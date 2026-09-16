# Productivity MCP Server

An MCP (Model Context Protocol) server for the **Personal Productivity** domain. It lets an MCP client (e.g. Claude Desktop) manage a local task list and send email summaries on the user's behalf.

## Features

### Tools

| Tool | Description |
|---|---|
| `ping` | Simple health-check tool that confirms the server is running. |
| `add_task(title, due_date)` | Adds a new task to the local SQLite task list. |
| `list_tasks()` | Returns all tasks currently stored. |
| `delete_task(task_id)` | Deletes a task by its numeric id. |
| `send_email(to, subject, body)` | Sends an email from the configured Gmail account via SMTP. |

### Prompt

| Prompt | Description |
|---|---|
| `plan_my_day(recipient_email)` | Generates instructions for the model to summarize all current tasks (ordered by due date) and email them to the given recipient. |

## Security Best Practices Implemented

**1. Input Sanitization** — All SQL queries (`add_task`, `list_tasks`, `delete_task`) use parameterized queries (`?` placeholders) instead of string formatting/concatenation. This prevents SQL injection, since user-supplied values are always passed as data, never as part of the query text.

**2. Error Disclosure** — `send_email` never returns raw exception details (SMTP server responses, stack traces, credentials, etc.) to the caller. The real exception is logged only to the server's own stderr (for developer debugging), while the caller receives a generic, safe error message.

Both are demonstrated with working exploit/verification tests in [`security_tests.py`](./security_tests.py). Run them with:

```bash
python security_tests.py
```

This prints both the "safe" behavior of our implementation and, for comparison, what an unsafe/naive implementation would have leaked.

## Prerequisites

- Python 3.11+
- A Gmail account with [2-Step Verification](https://myaccount.google.com/security) enabled and an [App Password](https://myaccount.google.com/apppasswords) generated for this project

## Setup

### Option A: using `uv` (recommended)

```bash
git clone https://github.com/XinruiXu729/productivity-mcp-server.git
cd productivity-mcp-server
uv venv
source .venv/bin/activate
uv sync
```

### Option B: using `pip`

```bash
git clone https://github.com/XinruiXu729/productivity-mcp-server.git
cd productivity-mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy the example environment file and fill in your own Gmail credentials:

```bash
cp .env.example .env
```

Edit `.env`:

GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_character_app_password


`.env` is git-ignored and must never be committed. The database file (`tasks.db`) is created automatically on first run and is also git-ignored.

## Running the Server Standalone (for testing)

Use the official MCP Inspector to test tools and the prompt without connecting a real LLM client:

```bash
mcp dev server.py
```

This opens a local web UI where each tool and the prompt can be called directly.

## Connecting to Claude Desktop

1. Locate your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Open [`claude_desktop_config.example.json`](./claude_desktop_config.example.json) in this repo and copy its `productivity-assistant` entry into the `mcpServers` object of your own config file (merge it in — do not overwrite any existing servers already listed there).
3. Replace the placeholder paths with the absolute paths on your own machine, e.g.:
```json
   "command": "/Users/<you>/path/to/productivity-mcp-server/.venv/bin/python",
   "args": ["/Users/<you>/path/to/productivity-mcp-server/server.py"]
```
4. Fully quit Claude Desktop (Cmd+Q) and reopen it.
5. Start a new chat and ask something like "What tasks do I have?" — Claude should call the `list_tasks` tool automatically.

## Project Structure

productivity-mcp-server/
├── server.py # MCP server: tools + prompt
├── security_tests.py # Exploit/verification tests for both best practices
├── requirements.txt # pip-compatible dependency list
├── pyproject.toml / uv.lock # uv-managed dependency files
├── .env.example # Template for required environment variables
├── claude_desktop_config.example.json # Example MCP config for Claude Desktop
└── README.md


## Author

Xu Xinrui (XinruiXu729)