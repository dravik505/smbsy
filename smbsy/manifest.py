import json
from pathlib import Path

from rich.console import Console

from .session import S

CONSOLE = Console()


def cmd_loot(args):
    if args and args[0] == "clear":
        S.manifest.clear()
        CONSOLE.print("[green]manifest cleared[/]")
        return
    S.loot.mkdir(parents=True, exist_ok=True)
    CONSOLE.print(f"loot dir: {S.loot}  ({len(S.manifest)} manifest entries)")


def cmd_manifest(args):
    out = Path(args[0]) if args else Path("manifest.json")
    out.write_text(json.dumps(S.manifest, indent=2, default=str))
    CONSOLE.print(f"[green]{len(S.manifest)} entries →[/] {out}")
