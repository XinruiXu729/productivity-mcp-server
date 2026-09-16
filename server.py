import os
import sys
import sqlite3
import smtplib
from pathlib import Path
from email.mime.text import MIMEText

from dotenv import load_dotenv
from mcp.server import MCPServer

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

DB_PATH = str(BASE_DIR / "tasks.db")

mcp = MCPServer("Productivity Assistant")


def init_db() -> None:
    """Create the tasks table if it doesn't exist yet."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


init_db()


@mcp.tool()
def ping() -> str:
    """A simple test tool that confirms the MCP server is running."""
    return "pong! MCP server is running."


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email from the user's Gmail account to a recipient.

    Args:
        to: recipient email address
        subject: the email subject line
        body: the plain text email body
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return "Error: email credentials are not configured on the server."

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = GMAIL_ADDRESS
    message["To"] = to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(message)
        return f"Email sent to {to}."
    except Exception as exc:
        # Error Disclosure best practice: 详细的真实错误只打印到 server 自己的
        # 控制台(给开发者自己排查用),返回给调用者(Claude/用户)的永远是
        # 一句不含任何敏感细节的通用提示。
        print(f"[send_email] internal error: {exc}", file=sys.stderr)
        return "Error: failed to send the email. Please check the recipient address and try again."
@mcp.tool()
def add_task(title: str, due_date: str = "") -> str:
    """Add a new task to the user's task list.

    Args:
        title: what the task is
        due_date: optional due date, as free text (e.g. "2026-09-20")
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            (title, due_date),
        )
    return f"Task added with id {cursor.lastrowid}: {title}"

@mcp.tool()
def delete_task(task_id: int) -> str:
    """Delete a task from the user's task list by its id.

    Args:
        task_id: the numeric id of the task to delete (use list_tasks to find it)
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if cursor.rowcount == 0:
        return f"No task found with id {task_id}."
    return f"Task {task_id} deleted."
    
@mcp.prompt()
def plan_my_day(recipient_email: str) -> str:
    """Generate a daily summary email of all current tasks."""
    return (
        f"Please look at all of my current tasks using the list_tasks tool, "
        f"organize them by due date (soonest first), and then use the send_email "
        f"tool to send a friendly daily summary email to {recipient_email}. "
        f"Use the subject 'Your Daily Task Summary', and list each task with its "
        f"due date in a clear, encouraging tone."
    )

@mcp.tool()
def list_tasks() -> list[dict]:
    """List all tasks currently in the user's task list."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, title, due_date, created_at FROM tasks ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    mcp.run()