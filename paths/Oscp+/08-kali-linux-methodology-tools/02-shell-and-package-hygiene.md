# Kali Shell Setup for Pentest Work

Configure your shell and terminal before starting any lab — saves time during active testing.

## tmux for Pentest Sessions

```bash
tmux new -s pentest          # start named session
Ctrl+B %                     # split vertically
Ctrl+B "                     # split horizontally
Ctrl+B arrow                 # navigate panes
Ctrl+B d                     # detach (session persists)
tmux attach -t pentest       # reattach
```

## History and Search

```bash
history | grep nmap          # find past nmap commands
history | grep gobuster
Ctrl+R                       # reverse search — type partial command
```

## Useful Pentest Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias ll='ls -la'
alias www='python3 -m http.server 80'
alias www8='python3 -m http.server 8080'
alias listen='nc -lvnp 4444'
```

Reload: `source ~/.bashrc`

## Per-Target Directory Structure

```bash
mkdir -p ~/labs/target/{recon,exploit,loot,report,screenshots}
```

Use target IP or hostname as directory name, e.g. `~/labs/10.10.10.5/`.

## File Serving and Listeners

Serve files to victim (run on Kali):

```bash
python3 -m http.server 8080
```

Netcat listener (basic):

```bash
nc -lvnp 4444
```

socat listener (better — supports full TTY):

```bash
socat TCP-LISTEN:4444,reuseaddr FILE:`tty`,raw,echo=0
```

## Note-Taking

Create a `notes.md` in each target directory. Minimum entries: IP, open ports, credentials found, flags captured, exploit path used.
