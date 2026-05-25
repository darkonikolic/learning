# Processes and services

Know what is running on a system. Processes expose running services for enumeration; killing and backgrounding processes is required for lab work.

## View running processes

```bash
ps aux                           # all processes, all users, detailed
ps aux | grep nginx              # find specific process
ps aux | grep -v grep | grep ssh # cleaner grep (remove the grep process itself)
top                              # live process monitor (q to quit)
htop                             # better live monitor (install: apt install htop)
pstree                           # process hierarchy tree
```

## Kill processes

```bash
kill 1234                        # send SIGTERM (graceful stop) to PID 1234
kill -9 1234                     # send SIGKILL (force stop) — use when SIGTERM fails
pkill nginx                      # kill by process name
killall python3                  # kill all processes named python3
```

## Background and foreground

```bash
python3 -m http.server 8080 &    # run in background, get PID
jobs                             # list background jobs
fg %1                            # bring job 1 to foreground
bg %1                            # resume stopped job in background
Ctrl+Z                           # suspend current foreground process
```

## systemd service management

```bash
systemctl status ssh             # is SSH running?
sudo systemctl start apache2     # start a service
sudo systemctl stop apache2      # stop a service
sudo systemctl restart apache2   # restart
sudo systemctl enable ssh        # start on boot
sudo systemctl disable apache2   # do not start on boot
systemctl list-units --type=service --state=running  # all running services
```

## Lab exercise — HTTP server lifecycle

```bash
# Start a simple HTTP server in the background
cd /tmp && python3 -m http.server 8080 &
echo "Server PID: $!"

# Verify it is listening
ss -tulpn | grep 8080

# Test it
curl -s http://localhost:8080/ | head -5

# Find the PID and kill it
ps aux | grep "http.server" | grep -v grep
kill $(pgrep -f "http.server")

# Confirm it is gone
ss -tulpn | grep 8080
```

## Security relevance

On a compromised box, `ps aux` reveals running services (databases, web servers, internal apps) that may not be externally visible. Internal services listening on localhost are common pivot targets.

```bash
# Check for internal listeners
ss -tulpn | grep 127.0.0.1
```

## Practice

- TryHackMe "Linux Fundamentals Part 3": https://tryhackme.com/room/linuxfundamentalspart3
- LabEx Linux Process Management: https://labex.io/courses/linux-process-management

## Completion bar

Start a background process, find its PID with `ps` and `pgrep`, kill it, verify it is gone — without looking up flags.
