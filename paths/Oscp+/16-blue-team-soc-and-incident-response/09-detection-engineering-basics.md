# Detection Engineering Basics

Write rules that find attackers — Sigma, Suricata, YARA. Turn hunts into automated detections.

## Sigma Rules (SIEM-Agnostic)

Sigma is a generic signature format. Write once, convert to any SIEM.

```yaml
# Example Sigma rule: mimikatz detection
title: Mimikatz Execution via Command Line
id: e1f5f2c8-f1c6-4b9e-a67d-c0e8b3f2a1d4
status: experimental
description: Detects mimikatz execution or references in command line
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        EventID: 4688
        CommandLine|contains:
            - 'mimikatz'
            - 'sekurlsa'
            - 'lsadump'
            - 'kerberos::ptt'
    condition: selection
falsepositives:
    - Security testing
level: high
```

```bash
# Convert Sigma rule to Splunk query
pip install sigmatools
sigma convert -t splunk -r mimikatz.yml

# Convert to Elastic
sigma convert -t elasticsearch mimikatz.yml

# Online converter
# https://uncoder.io/
```

## More Sigma Examples

```yaml
# Encoded PowerShell
detection:
    selection:
        EventID: 4688
        Image|endswith: '\powershell.exe'
        CommandLine|contains:
            - ' -enc '
            - ' -EncodedCommand '
    condition: selection

# New local admin account
detection:
    selection:
        EventID: 4720
    group_add:
        EventID: 4732
        TargetUserName: 'Administrators'
    condition: selection or group_add
```

## Suricata Network Rules

```suricata
# Alert on EternalBlue SMB exploit attempt
alert tcp any any -> any 445 (msg:"Possible EternalBlue Exploit"; content:"|FF|SMB"; sid:1000001; rev:1;)

# Detect Metasploit default User-Agent
alert http any any -> any any (msg:"Metasploit User-Agent"; http.user_agent; content:"Meterpreter"; sid:1000002; rev:1;)

# DNS tunneling — suspiciously long subdomain
alert dns any any -> any any (msg:"Long DNS Query - Possible Tunneling"; dns.query; pcre:"/[a-zA-Z0-9]{50,}/"; sid:1000003; rev:1;)

# C2 beacon — regular HTTP to non-standard port
alert http any any -> any !80 (msg:"HTTP on Non-Standard Port"; sid:1000004; rev:1;)
```

```bash
# Test Suricata rule against PCAP
suricata -r capture.pcap -S custom.rules -l /tmp/output/
cat /tmp/output/fast.log
```

## YARA Rules (File Pattern Matching)

```yara
rule Mimikatz_Strings
{
    meta:
        description = "Detects Mimikatz binary or strings"
        author = "YourName"
    strings:
        $s1 = "sekurlsa::logonpasswords" ascii nocase
        $s2 = "kerberos::ptt" ascii nocase
        $s3 = "lsadump::dcsync" ascii nocase
        $s4 = "mimikatz" ascii nocase wide
    condition:
        2 of them
}
```

```bash
# Scan a file
yara mimikatz.yar suspicious.exe

# Scan a directory recursively
yara -r mimikatz.yar /tmp/samples/

# YARA rules repo
# https://github.com/Yara-Rules/rules
# https://github.com/Neo23x0/signature-base
```

## Detection Rule Lifecycle

```
1. Trigger: threat intel, hunt finding, red team result
2. Write rule: start broad, refine
3. Test: run against known-good logs → measure false positive rate
4. Tune: add exclusions for legitimate activity
5. Deploy: push to SIEM/IDS
6. Monitor: review alert quality weekly, adjust as needed
```

## Detection Quality Metrics

- True positive rate: does it catch real attacks?
- False positive rate: does it fire on normal activity?
- Specificity: is it precise (low FP) or noisy?
- Coverage: which ATT&CK techniques are covered by your ruleset?

## Resources

- Sigma GitHub: https://github.com/SigmaHQ/sigma
- Uncoder.io (convert between formats): https://uncoder.io/
- YARA documentation: https://yara.readthedocs.io/
- Suricata rule writing guide: https://docs.suricata.io/en/latest/rules/
- Florian Roth's signature-base: https://github.com/Neo23x0/signature-base
