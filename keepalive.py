"""
Optional keepalive placeholder.
Intentionally minimal because this bot is designed to run as a worker process.
"""


def ping() -> str:
    return "ok"
