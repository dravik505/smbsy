#!/usr/bin/env python3
"""
smbsy — SMB operator console
dev: Dravik   TG: @x_tcp
"""
import argparse
import sys
from pathlib import Path

from rich.console import Console

from smbsy.session import S, connect
from smbsy.shares import pick_share, enum_shares
from smbsy.console import dispatch, interactive

VERSION = "0.2"

BANNER = """
  Dev: Dravik
  TG: @x_tcp"""

CONSOLE = Console()



def cli():
    p = argparse.ArgumentParser(
        prog="smb-sy.py",
        description="smbsy — SMB operator console",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example:  smb-sy.py -ip 10.0.0.5 -u administrator -p ''",
    )
    p.add_argument("-ip", required=True)
    p.add_argument("-u", "--user", default="")
    p.add_argument("-p", "--password", default="")
    p.add_argument("-d", "--domain", default="")
    p.add_argument("-P", "--port", type=int, default=445)
    p.add_argument("-hash", "--nthash", default="")
    p.add_argument("-lmhash", default="")
    p.add_argument("-encrypt", action="store_true")
    p.add_argument("-share", default="")
    p.add_argument("-o", "--loot", default="./loot")
    p.add_argument("-c", "--command", action="append", default=[])
    p.add_argument("-v", "--version", action="version", version=f"smbsy {VERSION}")
    args = p.parse_args()

    S.loot = Path(args.loot)
    S.loot.mkdir(parents=True, exist_ok=True)


    CONSOLE.print(BANNER, style="bold cyan")

    if not connect(args.ip, args.user, args.password, args.domain,
                   args.port, args.lmhash, args.nthash, args.encrypt):
        sys.exit(1)

    if args.share:
        S.share = args.share
    else:
        if args.command:
            shares = enum_shares()
            disk = next((s["name"] for s in shares if s["type"] == "disk"), None)
            if not disk:
                CONSOLE.print("[red]no filesystem share available[/]")
                sys.exit(1)
            S.share = disk
        else:
            chosen = pick_share()
            if not chosen:
                sys.exit(1)
            S.share = chosen
    S.cwd = ""
    S.save()

    if args.command:
        for c in args.command:
            dispatch(c)
        return

    interactive()


if __name__ == "__main__":
    cli()
