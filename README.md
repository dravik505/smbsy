# smbsy

Interactive SMB operator console. Multi-file Python tool for SMB enumeration, share access probing, and file operations.

**Dev:** Dravik — TG: [@x_tcp](https://t.me/x_tcp)

## Features

- Share enumeration via `smbclient -L` subprocess
- Per-share access probing: **R**ead, **W**rite, **D**elete, **M**kdir, **L**ist-only
- Interactive shell: `ls`, `cd`, `pwd`, `use`, `shares`, `get`, `mget`, `put`, `rm`, `mkdir`, `rmdir`, `find`, `info`, `recurse`, `loot`, `manifest`, `whoami`, `save`, `help`
- Non-interactive mode: `-c 'cmd'` repeatable
- Manifest export to JSON
- Null session, password, NT hash, and domain auth

## Install

    git clone https://github.com/dravik505/smbsy.git
    cd smbsy
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Usage

    python3 smb-sy.py -ip 10.0.0.5 -u administrator -p ''

Non-interactive:

    python3 smb-sy.py -ip 10.0.0.5 -u administrator -p '' -share DD -c 'ls' -c 'manifest /tmp/dd.json'

## Access legend

| Code | Meaning |
|------|---------|
| R    | read files |
| W    | write files |
| D    | delete files |
| M    | create directories |
| L    | list only |
| -    | no access |

## CLI flags

    -ip     target IP or hostname
    -u      username (empty = null)
    -p      password (empty = blank)
    -d      NTLM domain
    -P      SMB port (default 445)
    -hash   NT hash for pass-the-hash
    -share  skip share prompt
    -o      loot directory
    -c      run command non-interactively (repeatable)

## Disclaimer

Provided as-is for security research and authorized testing. The author assumes no liability for misuse or damage caused by this tool.

## License

MIT
