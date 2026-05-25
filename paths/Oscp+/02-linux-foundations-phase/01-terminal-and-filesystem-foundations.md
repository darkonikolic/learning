# Terminal and filesystem foundations

Learn to navigate and manipulate the Linux filesystem from the command line. Everything else in this path builds on this muscle memory.

## Core navigation

```bash
pwd                                  # print working directory
ls -la /etc                          # list with permissions and hidden files
cd /var/log && ls                    # change dir and list
cd ~                                 # go to home directory
cd -                                 # jump back to previous directory
```

## Create, copy, move, delete

```bash
mkdir -p ~/lab/tools/scripts ~/lab/targets/10.10.10.1
touch ~/lab/targets/10.10.10.1/notes.txt
cp notes.txt notes.bak
mv notes.bak archive/notes-$(date +%F).txt
rm -rf ~/lab/tmp/
```

## Inspect files and metadata

```bash
file /usr/bin/python3                # what type: binary, text, symlink
stat /etc/passwd                     # size, permissions, timestamps, inode
ls -lah /var/log/                    # human-readable sizes
tree ~/lab -L 2                      # directory tree, 2 levels deep
```

## Lab exercise — build a pentest directory structure

```bash
mkdir -p ~/pentest/{recon,exploit,loot,notes}
touch ~/pentest/notes/targets.txt
echo "10.10.10.1 - HackTheBox" > ~/pentest/notes/targets.txt
cat ~/pentest/notes/targets.txt
ls -R ~/pentest
```

Expected: four subdirectories, one file with content.

## What to observe

- Absolute paths (`/etc/passwd`) vs relative paths (`../etc/passwd`) — critical distinction for exploits
- Hidden files start with `.` — `ls -a` reveals them, relevant when hunting for credentials in home dirs
- `file` distinguishes ELF binary from shell script — matters when dealing with unknown executables

## Practice

- LabEx Grasshopper track: https://labex.io/courses/linux-basic-commands-practice-online
- TryHackMe Linux Fundamentals Part 1: https://tryhackme.com/room/linuxfundamentalspart1

## Completion bar

Run all of these without looking up flags: `pwd` `ls -la` `cd -` `mkdir -p` `cp` `mv` `rm -rf` `file` `stat` `tree`
