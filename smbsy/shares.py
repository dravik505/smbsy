import re
import subprocess
import smbclient
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from .session import S
from .errors import report
from .acl import probe_access, access_label

CONSOLE = Console()

NON_FS = {"IPC$", "print$", "NETLOGON", "SYSVOL"}


def enum_shares() -> list:
    """Use smbclient CLI -L to enumerate shares. Works regardless of signing/guest."""
    args = ["smbclient", "-L", f"//{S.host}/", "-U", f"{S.username}%{S.password}", "-p", str(S.port)]
    if S.domain:
        args += ["-W", S.domain]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=20)
    except Exception as e:
        report("smbclient -L", e)
        return []

    out = []
    for line in r.stdout.splitlines():
        m = re.match(r"^\s+(\S+)\s+(Disk|IPC|Printer)\s*(.*)$", line)
        if m:
            name = m.group(1)
            kind = {"Disk": "disk", "IPC": "ipc", "Printer": "print"}[m.group(2)]
            comment = m.group(3).strip()
            out.append({"name": name, "type": kind, "comment": comment})
    return out


def pick_share():
    shares = enum_shares()
    if not shares:
        CONSOLE.print("[red]no shares found[/]")
        return None
    fs = [s for s in shares if s["type"] == "disk"]
    if not fs:
        fs = shares

    t = Table(show_header=True, header_style="bold magenta")
    t.add_column("#", style="cyan", justify="right")
    t.add_column("name", style="bold")
    t.add_column("type")
    t.add_column("access", style="green")
    t.add_column("comment", style="dim")

    with CONSOLE.status("[dim]probing share access…[/]"):
        for i, s in enumerate(fs, 1):
            a = probe_access(S.host, s["name"], S.username, S.password, S.domain, S.port) if s["type"] == "disk" else {"list": False}
            s["access"] = a if s["type"] == "disk" else {}
            label = access_label(a) if s["type"] == "disk" else "—"
            t.add_row(str(i), s["name"], s["type"], label, s["comment"])

    CONSOLE.print(t)
    CONSOLE.print("[dim]legend: R=read W=write L=list-only D=delete M=mkdir[/]")
    sel = Prompt.ask("[bold]choose share[/] (number or name)", default=fs[0]["name"])
    if sel.isdigit() and 1 <= int(sel) <= len(fs):
        return fs[int(sel) - 1]["name"]
    return sel


def cmd_shares(args):
    for s in enum_shares():
        if s["type"] == "disk":
            a = probe_access(S.host, s["name"], S.username, S.password, S.domain, S.port)
            label = access_label(a)
        else:
            label = "—"
        CONSOLE.print(f"  [bold]{s['name']:<16}[/]  [dim]{s['type']:<6}[/]  [green]{label:<6}[/]  {s['comment']}")


def cmd_use(args):
    if not args:
        CONSOLE.print("[yellow]use <share>[/]")
        return
    name = args[0]
    if name in NON_FS:
        CONSOLE.print(f"[yellow]{name} is not a filesystem share — choose another[/]")
        return
    try:
        smbclient.listdir(rf"\\{S.host}\{name}")
    except Exception as e:
        report(f"use {name}", e)
        return
    S.share = name
    S.cwd = ""
    S.save()
    CONSOLE.print(f"[green]share →[/] {S.share}")
