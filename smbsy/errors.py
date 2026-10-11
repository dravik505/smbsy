"""Unified SMB error formatting."""
from rich.console import Console

CONSOLE = Console()

FRIENDLY = {
    "STATUS_ACCESS_DENIED": "access denied",
    "STATUS_INVALID_INFO_CLASS": "not a filesystem share (ipc/print)",
    "STATUS_OBJECT_NAME_NOT_FOUND": "path not found",
    "STATUS_OBJECT_PATH_NOT_FOUND": "parent path not found",
    "STATUS_NOT_A_DIRECTORY": "not a directory",
    "STATUS_FILE_IS_A_DIRECTORY": "is a directory",
    "STATUS_USER_SESSION_DELETED": "session was dropped by server",
    "STATUS_LOGON_FAILURE": "bad credentials",
    "STATUS_ACCOUNT_DISABLED": "account disabled",
    "STATUS_PASSWORD_EXPIRED": "password expired",
    "STATUS_NETWORK_SESSION_EXPIRED": "session expired",
    "STATUS_SHARING_VIOLATION": "file in use",
    "STATUS_DISK_FULL": "disk full",
    "SMBResponseException": "smb protocol error",
    "SessionError": "smb session error",
    "ConnectionError": "connection lost",
    "OSError": "os error",
}

def fmt(e: Exception) -> str:
    name = type(e).__name__
    msg = str(e)
    for key, nice in FRIENDLY.items():
        if key in msg or key == name:
            return f"{nice} ({msg.splitlines()[0][:120]})"
    return msg.splitlines()[0][:160]

def report(prefix: str, e: Exception):
    CONSOLE.print(f"[red]{prefix}:[/] {fmt(e)}")
