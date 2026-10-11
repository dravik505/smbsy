import re
import time
from pathlib import Path
from typing import Optional

import smbclient
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel

from .session import S
from .errors import report

CONSOLE = Console()


def _norm(p: str) -> str:
    return p.strip().strip("\\")


def _join(a: str, b: str) -> str:
    if not b:
        return a
    if b.startswith("\\") or b.startswith("/"):
        return _norm(b)
    return _norm(f"{a}\\{b}" if a else b)


def _size(n: int) -> str:
    for u in ("B", "K", "M", "G", "T"):
        if n < 1024:
            return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}P"


def _ts(t) -> str:
    if t is None:
        return "—"
    if hasattr(t, "timestamp"):
        t = t.timestamp()
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(t))


def cmd_ls(args):
    target = _join(S.cwd, args[0]) if args else S.cwd
    unc = S.unc(target)
    try:
        entries = list(smbclient.scandir(unc))
    except Exception as e:
        report("ls", e)
        return
    t = Table(show_header=True, header_style="bold cyan")
    t.add_column("Mode")
    t.add_column("Size", justify="right")
    t.add_column("Modified")
    t.add_column("Name")
    for e in sorted(entries, key=lambda x: (not x.is_dir(), x.name.lower())):
        mode = "[bold blue]DIR[/]" if e.is_dir() else "FILE"
        try:
            st = e.stat()
            size = "" if e.is_dir() else _size(st.st_size)
            mtime = _ts(st.st_mtime)
        except Exception:
            size, mtime = "", "—"
        t.add_row(mode, size, mtime, e.name)
        S.manifest.append({"name": e.name, "dir": e.is_dir(), "path": _join(target, e.name)})
    CONSOLE.print(t)


def cmd_cd(args):
    if not args:
        S.cwd = ""
        return
    if args[0] == "..":
        S.cwd = "\\".join(S.cwd.split("\\")[:-1])
        return
    tgt = _join(S.cwd, args[0])
    try:
        smbclient.listdir(S.unc(tgt))
    except Exception as e:
        report("cd", e)
        return
    S.cwd = tgt
    S.save()


def cmd_pwd(args):
    CONSOLE.print(f"\\\\{S.host}\\{S.share}\\{S.cwd}")


def _download(remote: str, local: Path):
    unc = S.unc(remote)
    local.parent.mkdir(parents=True, exist_ok=True)
    size = smbclient.stat(unc).st_size
    with Progress(
        TextColumn("[cyan]{task.fields[name]}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
    ) as prog:
        task = prog.add_task("dl", total=size or 1, name=local.name)
        with smbclient.open_file(unc, mode="rb") as rf, open(local, "wb") as lf:
            while True:
                chunk = rf.read(262144)
                if not chunk:
                    break
                lf.write(chunk)
                prog.advance(task, len(chunk))
    CONSOLE.print(f"[green][+][/] {local}  ({_size(size)})")


def cmd_get(args):
    if not args:
        CONSOLE.print("[yellow]get <remote> [local][/]")
        return
    remote = _join(S.cwd, args[0])
    local = Path(args[1]) if len(args) > 1 else S.loot / Path(remote).name
    try:
        _download(remote, local)
    except Exception as e:
        report("get", e)


def cmd_mget(args):
    if not args:
        CONSOLE.print("[yellow]mget <regex>[/]")
        return
    try:
        rx = re.compile(args[0])
    except re.error as e:
        CONSOLE.print(f"[red]regex:[/] {e}")
        return
    S.loot.mkdir(parents=True, exist_ok=True)
    try:
        entries = list(smbclient.scandir(S.unc(S.cwd)))
    except Exception as e:
        report("mget", e)
        return
    for e in entries:
        if e.is_file() and rx.search(e.name):
            try:
                _download(_join(S.cwd, e.name), S.loot / e.name)
            except Exception as ex:
                report(f"mget {e.name}", ex)


def cmd_put(args):
    if len(args) < 1:
        CONSOLE.print("[yellow]put <local> [remote][/]")
        return
    local = Path(args[0])
    if not local.exists():
        CONSOLE.print(f"[red]no such file:[/] {local}")
        return
    remote = _join(S.cwd, args[1]) if len(args) > 1 else _join(S.cwd, local.name)
    try:
        with open(local, "rb") as lf, smbclient.open_file(S.unc(remote), mode="wb") as rf:
            while True:
                chunk = lf.read(262144)
                if not chunk:
                    break
                rf.write(chunk)
        CONSOLE.print(f"[green][+][/] uploaded → {remote}")
    except Exception as e:
        report("put", e)


def cmd_rm(args):
    for pat in args:
        try:
            smbclient.remove(S.unc(_join(S.cwd, pat)))
            CONSOLE.print(f"[green]rm[/] {pat}")
        except Exception as e:
            report(f"rm {pat}", e)


def cmd_mkdir(args):
    for d in args:
        try:
            smbclient.mkdir(S.unc(_join(S.cwd, d)))
            CONSOLE.print(f"[green]mkdir[/] {d}")
        except Exception as e:
            report(f"mkdir {d}", e)


def cmd_rmdir(args):
    for d in args:
        try:
            smbclient.rmdir(S.unc(_join(S.cwd, d)))
            CONSOLE.print(f"[green]rmdir[/] {d}")
        except Exception as e:
            report(f"rmdir {d}", e)


def _walk(unc: str, depth: int, max_depth: int, rx: Optional[re.Pattern]):
    if depth > max_depth:
        return
    try:
        entries = list(smbclient.scandir(unc))
    except Exception:
        return
    for e in entries:
        if e.is_dir():
            yield from _walk(f"{unc}\\{e.name}", depth + 1, max_depth, rx)
        else:
            if rx is None or rx.search(e.name):
                yield e, unc


def cmd_find(args):
    if not args:
        CONSOLE.print("[yellow]find <regex> [maxdepth][/]")
        return
    rx = re.compile(args[0])
    maxd = int(args[1]) if len(args) > 1 else 4
    hits = 0
    for e, parent in _walk(S.unc(), 0, maxd, rx):
        try:
            sz = _size(e.stat().st_size)
        except Exception:
            sz = "?"
        CONSOLE.print(f"{sz:>8}  {parent}\\{e.name}")
        hits += 1
    CONSOLE.print(f"[cyan]{hits} hits[/]")


def cmd_recurse(args):
    S.recurse = (not S.recurse) if not args else args[0].lower() in ("on", "1", "true")
    CONSOLE.print(f"recurse → {S.recurse}")


def cmd_info(args):
    if not args:
        CONSOLE.print("[yellow]info <remote>[/]")
        return
    unc = S.unc(_join(S.cwd, args[0]))
    try:
        st = smbclient.stat(unc)
    except Exception as e:
        report("info", e)
        return
    d = {
        "name": Path(args[0]).name,
        "size": st.st_size,
        "size_h": _size(st.st_size),
        "created": _ts(st.st_ctime),
        "modified": _ts(st.st_mtime),
        "accessed": _ts(st.st_atime),
        "mode": oct(st.st_mode),
    }
    CONSOLE.print(Panel.fit("\n".join(f"{k:>10}: {v}" for k, v in d.items()), title="stat"))


def cmd_whoami(args):
    kind = "(hash)" if S.nthash else "(password)" if S.password else "(null)"
    CONSOLE.print(
        f"{S.domain + chr(92) if S.domain else ''}{S.username or '<null>'}@{S.host}:{S.port} "
        f"{kind} encrypt={S.encrypt} share={S.share or '-'}"
    )


def cmd_save(args):
    S.save()
    CONSOLE.print(f"[green]state → ~/.smbsy_state.json[/]")
