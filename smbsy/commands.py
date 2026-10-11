from rich.console import Console
from rich.table import Table

from .shares import cmd_shares, cmd_use
from .fs import (
    cmd_ls, cmd_cd, cmd_pwd, cmd_get, cmd_mget, cmd_put,
    cmd_rm, cmd_mkdir, cmd_rmdir, cmd_find, cmd_info,
    cmd_recurse, cmd_whoami, cmd_save,
)
from .manifest import cmd_loot, cmd_manifest

CONSOLE = Console()


def cmd_help(args=None):
    rows = [
        ("use <share>", "select share"),
        ("shares", "re-enumerate shares"),
        ("ls [path]", "list directory"),
        ("cd <path|..>", "change directory"),
        ("pwd", "print current UNC"),
        ("get <remote> [local]", "download one file"),
        ("mget <regex>", "download matching files in cwd"),
        ("put <local> [remote]", "upload file"),
        ("rm <name...>", "delete files"),
        ("mkdir <name...>", "create directory"),
        ("rmdir <name...>", "remove directory"),
        ("find <regex> [depth]", "recursive search"),
        ("info <remote>", "stat metadata"),
        ("recurse [on|off]", "toggle recursion flag"),
        ("loot [clear]", "loot dir / manifest"),
        ("manifest [file]", "dump manifest JSON"),
        ("whoami", "current session"),
        ("save", "persist session"),
        ("help", "this"),
        ("exit | quit", "leave"),
    ]
    t = Table(show_header=True, header_style="bold magenta")
    t.add_column("command", style="cyan", no_wrap=True)
    t.add_column("description")
    for c, d in rows:
        t.add_row(c, d)
    CONSOLE.print(t)


COMMANDS = {
    "use": cmd_use, "shares": cmd_shares,
    "ls": cmd_ls, "dir": cmd_ls,
    "cd": cmd_cd, "pwd": cmd_pwd,
    "get": cmd_get, "mget": cmd_mget, "put": cmd_put,
    "rm": cmd_rm, "del": cmd_rm,
    "mkdir": cmd_mkdir, "rmdir": cmd_rmdir,
    "find": cmd_find, "info": cmd_info, "stat": cmd_info,
    "recurse": cmd_recurse, "loot": cmd_loot, "manifest": cmd_manifest,
    "whoami": cmd_whoami, "save": cmd_save,
    "help": cmd_help, "?": cmd_help,
}
