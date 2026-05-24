# Unit 08 — Packet capture (`tcpdump` + Wireshark)

## Theme

Convert frames into evidence-backed hypotheses.

## Ubuntu — `tcpdump` basics

Start with narrowly scoped captures on loopback while exercising a local benign service you control (permission model matters):

```bash
sudo tcpdump -ni lo -c20 'tcp port 80'   
```

Iterate filters: broaden and narrow purposely.

## Wireshark refinement

Sequences:

| Pass | Goal |
|------|------|
| `tcp` filter | Isolate conversation stream |
| `dns` transitions | Correlate lookups |
| `http` baseline | Inspect cleartext legacy traffic only in sanctioned labs |

## TryHackMe

Finish lingering **Network Fundamentals** labs focusing on PCAP interpretation—not speed-running clicks.

## Learning outcome

You can annotate a twenty-packet excerpt: handshake, TLS start (if viewed at edge instrumentation limitations), DNS preceding connect, teardown flags—truthful to what's visible—not speculative Hollywood narrative.
