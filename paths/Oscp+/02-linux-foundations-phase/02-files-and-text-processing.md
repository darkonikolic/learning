# Files and text processing

Read, filter, and reshape text files from the terminal. Core skill for parsing config files, logs, and credential dumps.

## Viewing file content

```bash
cat /etc/passwd                      # dump entire file
less /var/log/syslog                 # paginate (q to quit, / to search)
head -20 /var/log/auth.log           # first 20 lines
tail -f /var/log/auth.log            # follow live output
wc -l /etc/passwd                    # count lines
```

## Sorting and deduplication

```bash
sort /etc/passwd                     # alphabetical sort
sort -t: -k3 -n /etc/passwd          # sort by UID (field 3, numeric)
sort file.txt | uniq                 # remove consecutive duplicates
sort file.txt | uniq -c | sort -rn   # count occurrences, most frequent first
```

## Extracting columns with cut

```bash
cut -d: -f1 /etc/passwd              # extract usernames (field 1, colon delimiter)
cut -d: -f1,3 /etc/passwd            # username and UID
cut -d: -f7 /etc/passwd | sort | uniq  # all shells in use
```

## Redirection and stderr

```bash
ls /etc > etc_files.txt              # stdout to file (overwrite)
ls /etc >> etc_files.txt             # stdout to file (append)
ls /nonexistent 2>/dev/null          # discard errors
ls /etc /nonexistent 2>&1 | less     # merge stderr into stdout
command | tee output.txt             # write to file AND keep stdout flowing
```

## Lab exercise — parse /etc/passwd

```bash
# Extract all usernames and shells, find which shells are used
cut -d: -f1,7 /etc/passwd | sort -t: -k2
# Count how many users per shell
cut -d: -f7 /etc/passwd | sort | uniq -c | sort -rn
# Find users with UID 0 (root-equivalent)
awk -F: '$3 == 0 {print $1}' /etc/passwd
```

## Practice

- LabEx Text-Fu track: https://labex.io/courses/linux-text-processing-and-regular-expressions
- TryHackMe Linux Fundamentals Part 2: https://tryhackme.com/room/linuxfundamentalspart2

## Completion bar

Parse `/etc/passwd` to list all usernames, sort them, deduplicate shells — using only `cut`, `sort`, `uniq`, `wc`, and pipes.
