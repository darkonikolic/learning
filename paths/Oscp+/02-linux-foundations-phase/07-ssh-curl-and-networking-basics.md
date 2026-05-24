# Unit 07 — SSH, curl, and Linux networking basics

## Theme

Talking to other hosts like a server operator.

## Udemy — Linux Administration Bootcamp

Sections:

- SSH  
- Networking introduction  

## Commands to practice

`ssh`, `scp`, `curl`, `wget`, `ssh-keygen`, reading `~/.ssh/id_rsa.pub`, `tmux` install and basic use

## Exercise

```bash
curl https://google.com
curl -I https://google.com
```

Set up **SSH between VMs you control**: generate a key pair, install the public key, connect without password where appropriate.

Practice **tmux**: prefix **`Ctrl+B`**, detach/reattach, split panes basics.

## Topic checklist

- SSH client usage and keys  
- `scp` for file transfer  
- `curl`/headers at a pragmatic level  

## Learning outcome

You can connect to your lab machines reliably, inspect HTTP responses at the CLI, and keep long sessions organized with tmux.
