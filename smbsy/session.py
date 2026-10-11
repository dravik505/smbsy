import json
import inspect
from dataclasses import dataclass, field
from pathlib import Path

# -------- monkeypatch BEFORE importing smbclient --------
import smbprotocol.connection as _conn_mod
import smbprotocol.session as _sess_mod
import smbprotocol.tree as _tree_mod
import smbclient._pool as _pool_mod

_orig_conn_init = _conn_mod.Connection.__init__
def _conn_init_patched(self, *a, **kw):
    kw.setdefault("require_signing", False)
    return _orig_conn_init(self, *a, **kw)
if not getattr(_conn_mod.Connection, "_smbsy_patched", False):
    _conn_mod.Connection.__init__ = _conn_init_patched
    _conn_mod.Connection._smbsy_patched = True

_orig_tree_connect = _tree_mod.TreeConnect.connect
def _tree_connect_patched(self, *a, **kw):
    kw["require_secure_negotiate"] = False
    return _orig_tree_connect(self, *a, **kw)
if not getattr(_tree_mod.TreeConnect, "_smbsy_patched", False):
    _tree_mod.TreeConnect.connect = _tree_connect_patched
    _tree_mod.TreeConnect._smbsy_patched = True

# also force the client config default — some paths bypass TreeConnect.connect
_orig_cfg_init = _pool_mod.ClientConfig.__init__
def _cfg_init_patched(self, *a, **kw):
    kw["require_secure_negotiate"] = False
    return _orig_cfg_init(self, *a, **kw)
if not getattr(_pool_mod.ClientConfig, "_smbsy_patched", False):
    _pool_mod.ClientConfig.__init__ = _cfg_init_patched
    _pool_mod.ClientConfig._smbsy_patched = True

import smbclient
from rich.console import Console

CONSOLE = Console()
STATE_FILE = Path.home() / ".smbsy_state.json"


@dataclass
class Session:
    host: str = ""
    port: int = 445
    username: str = ""
    password: str = ""
    domain: str = ""
    lmhash: str = ""
    nthash: str = ""
    encrypt: bool = False
    share: str = ""
    cwd: str = ""
    recurse: bool = False
    connected: bool = False
    loot: Path = field(default_factory=lambda: Path.cwd() / "loot")
    manifest: list = field(default_factory=list)

    def unc(self, extra: str = "") -> str:
        base = f"\\\\{self.host}\\{self.share}"
        parts = [p for p in (self.cwd, extra) if p]
        tail = "\\".join(parts)
        return f"{base}\\{tail}" if tail else base

    def save(self):
        STATE_FILE.write_text(json.dumps({
            "host": self.host, "port": self.port,
            "username": self.username, "domain": self.domain,
            "share": self.share, "cwd": self.cwd,
            "loot": str(self.loot),
        }, indent=2))

    @classmethod
    def load(cls):
        s = cls()
        if STATE_FILE.exists():
            try:
                d = json.loads(STATE_FILE.read_text())
                for k, v in d.items():
                    setattr(s, k, Path(v) if k == "loot" else v)
            except Exception:
                pass
        return s


S = Session.load()


def connect(host, user, password="", domain="", port=445,
            lmhash="", nthash="", encrypt=False) -> bool:
    try:
        smbclient.reset_connection_cache()
    except Exception:
        pass

    full_user = user or ""
    if domain:
        full_user = f"{domain}\\{full_user}"

    sig = set(inspect.signature(smbclient.register_session).parameters.keys())
    kwargs = {"username": full_user, "password": password or "", "port": port}
    if lmhash and "lmhash" in sig:
        kwargs["lmhash"] = lmhash
    if nthash and "nthash" in sig:
        kwargs["nthash"] = nthash
    if "encrypt" in sig:
        kwargs["encrypt"] = bool(encrypt)
    if "require_signing" in sig:
        kwargs["require_signing"] = False

    try:
        smbclient.register_session(host, **kwargs)
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ("guest", "signing", "encryption")):
            kwargs["username"] = ""
            kwargs["password"] = ""
            kwargs.pop("lmhash", None)
            kwargs.pop("nthash", None)
            kwargs.pop("encrypt", None)
            try:
                smbclient.register_session(host, **kwargs)
            except Exception as e2:
                CONSOLE.print(f"[red]connect failed (guest fallback):[/] {e2}")
                return False
        else:
            CONSOLE.print(f"[red]connect failed:[/] {e}")
            return False

    S.host, S.port, S.username, S.domain = host, port, user, domain
    S.password, S.lmhash, S.nthash, S.encrypt = password, lmhash, nthash, encrypt
    S.connected = True
    S.save()
    CONSOLE.print(f"[green][+][/] session {domain + chr(92) if domain else ''}{user or '<null>'}@{host}:{port}")
    return True
