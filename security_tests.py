"""
security_tests.py

Demonstrates and verifies the two best practices implemented in server.py:
1. Input Sanitization — SQL injection defense in add_task / list_tasks
2. Error Disclosure — safe error messages from send_email

Run with: python security_tests.py
"""

import os
import sqlite3
import smtplib

import server  # our actual MCP server module


def test_sql_injection_blocked():
    print("\n=== Test 1: SQL Injection (Input Sanitization) ===")

    server.DB_PATH = "test_tasks.db"
    if os.path.exists(server.DB_PATH):
        os.remove(server.DB_PATH)
    server.init_db()

    server.add_task("Buy groceries", "2026-09-20")

    # --- The attack payload ---
    malicious_title = "hacked'); DROP TABLE tasks; --"
    server.add_task(malicious_title, "2026-01-01")

    # If the injection had worked, this call would error out
    # ("no such table: tasks") instead of returning results.
    tasks = server.list_tasks()

    table_survived = any(t["title"] == "Buy groceries" for t in tasks)
    payload_stored_as_text = any(t["title"] == malicious_title for t in tasks)

    print(f"Tasks after attack: {tasks}")
    assert table_survived, "FAILED: the tasks table was destroyed by the injection!"
    assert payload_stored_as_text, "FAILED: malicious input was not stored safely."
    print("PASSED: parameterized queries blocked the SQL injection attempt.")

    os.remove(server.DB_PATH)


def demonstrate_vulnerable_sql():
    """For comparison only — NOT used anywhere in server.py.
    Shows what would happen with an unsafe, string-formatted query."""
    print("\n=== For comparison: an UNSAFE version (not used in our server) ===")

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT)")
    conn.execute("INSERT INTO tasks (title) VALUES ('Buy groceries')")

    malicious_title = "hacked'); DROP TABLE tasks; --"
    unsafe_query = f"INSERT INTO tasks (title) VALUES ('{malicious_title}')"
    print(f"Unsafe query that would run: {unsafe_query}")

    conn.executescript(unsafe_query)
    remaining = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    print(f"Tables remaining after attack: {remaining}")
    if not remaining:
        print("CONFIRMED: without parameterized queries, the attacker deleted the entire table.")
    conn.close()


def test_error_disclosure_safe():
    print("\n=== Test 2: Error Disclosure ===")

    original_password = server.GMAIL_APP_PASSWORD
    server.GMAIL_APP_PASSWORD = "definitely-wrong-password"

    result = server.send_email("someone@example.com", "Test", "This should fail safely.")
    print(f"Message returned to the caller: {result}")

    leaks_password = original_password is not None and original_password in result
    leaks_details = "smtp.gmail.com" in result.lower() or "traceback" in result.lower()

    assert not leaks_password, "FAILED: the real password leaked into the error message!"
    assert not leaks_details, "FAILED: internal server details leaked into the error message!"
    print("PASSED: no sensitive details reached the caller.")

    server.GMAIL_APP_PASSWORD = original_password


def demonstrate_vulnerable_error_disclosure():
    """For comparison only — shows what a naive tool would have returned."""
    print("\n=== For comparison: an UNSAFE version (not used in our server) ===")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(server.GMAIL_ADDRESS, "definitely-wrong-password")
    except Exception as exc:
        print(f"What an unsafe tool would have returned: Error: {exc}")


if __name__ == "__main__":
    test_sql_injection_blocked()
    demonstrate_vulnerable_sql()
    test_error_disclosure_safe()
    demonstrate_vulnerable_error_disclosure()