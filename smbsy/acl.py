"""Probe per-share access via smbclient CLI. NT_STATUS in stderr = failure."""
import os
import re
import subprocess
from rich.console import Console

CONSOLE = Console()


def _smb_exec(host, share, user, password, domain, port, commands, timeout=15):
    cred = f"{user}%{password}" if (user or password) else "%"
    args = ["smbclient", f"//{host}/{share}", "-U", cred, "-p", str(port), "-c", commands]
    if domain:
        args += ["-W", domain]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        return 1, "", str(e)


def _ok(rc, err, out=""):
    return rc == 0 and "NT_STATUS" not in err and "NT_STATUS" not in (out or "") and "NT_STATUS" not in (out or "")


def probe_access(host, share, user="", password="", domain="", port=445) -> dict:
    result = {"list": False, "read": False, "write": False,
              "delete": False, "mkdir": False, "rmdir": False}

    # ---- list ----
    rc, out, err = _smb_exec(host, share, user, password, domain, port, "ls")
    if not _ok(rc, err, out):
        return result
    result["list"] = True

    # ---- read: try first regular file ----
    m = re.search(r"^\s+(\S+\.\S+)\s+A", out, re.M)
    if m:
        fname = m.group(1)
        tmp_read = f"/tmp/.smbsy_read_{os.getpid()}"
        rc2, _, err2 = _smb_exec(host, share, user, password, domain, port,
                                 f'get "{fname}" {tmp_read}')
        if _ok(rc2, err2) and os.path.exists(tmp_read):
            result["read"] = True
            try:
                os.remove(tmp_read)
            except Exception:
                pass

    # ---- write / delete ----
    tmp = f"smbsy_w_{os.getpid()}"
    rc, out, err = _smb_exec(host, share, user, password, domain, port,
                             f'put /etc/hostname "{tmp}"')
    if _ok(rc, err, out):
        result["write"] = True
        rc, out, err = _smb_exec(host, share, user, password, domain, port,
                                 f'del "{tmp}"')
        if _ok(rc, err, out):
            result["delete"] = True

    # ---- mkdir / rmdir ----
    tmpd = f"smbsy_d_{os.getpid()}"
    rc, out, err = _smb_exec(host, share, user, password, domain, port,
                             f'mkdir "{tmpd}"')
    if _ok(rc, err, out):
        result["mkdir"] = True
        rc, out, err = _smb_exec(host, share, user, password, domain, port,
                                 f'rmdir "{tmpd}"')
        if _ok(rc, err, out):
            result["rmdir"] = True

    return result


def access_label(a: dict) -> str:
    parts = []
    if a.get("read"): parts.append("R")
    if a.get("write"): parts.append("W")
    if a.get("delete"): parts.append("D")
    if a.get("mkdir"): parts.append("M")
    if not parts and a.get("list"): parts.append("L")
    if not parts: parts.append("-")
    return "".join(parts)
