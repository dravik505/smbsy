import shlex
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from rich.console import Console as RichConsole

from .session import S
from .commands import COMMANDS, cmd_help
from .errors import report

CONSOLE = RichConsole()
HISTORY_FILE = Path.home() / ".smbsy_history"


def dispatch(line: str):
    try:
        parts = shlex.split(line)
    except ValueError as e:
        CONSOLE.print(f"[red]parse:[/] {e}")
        return
    if not parts:
        return
    cmd, rest = parts[0].lower(), parts[1:]
    if cmd in ("exit", "quit", "q"):
        raise SystemExit(0)
    fn = COMMANDS.get(cmd)
    if not fn:
        CONSOLE.print(f"[red]unknown:[/] {cmd}  ([cyan]help[/])")
        return
    try:
        fn(rest)
    except SystemExit:
        raise
    except Exception as e:
        report(cmd, e)


def interactive():
    cmd_help()
    session = PromptSession(
        history=FileHistory(str(HISTORY_FILE)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter(list(COMMANDS.keys()), ignore_case=True),
    )
    while True:
        try:
            line = session.prompt(f"smbsy:{S.share or '-'}:{S.cwd or chr(92)}> ")
        except (EOFError, KeyboardInterrupt):
            break
        try:
            dispatch(line)
        except SystemExit:
            break
