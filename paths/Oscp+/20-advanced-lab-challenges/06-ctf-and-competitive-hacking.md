# CTF and Competitive Hacking

CTFs sharpen specific skills faster than lab machines. They force creative problem solving, deep technique application, and reading source code — all directly transferable to pentesting.

## Platforms

| Platform | Level | Best For |
|----------|-------|----------|
| PicoCTF | Beginner | First CTF, no team required |
| CTFtime.org | All | Finding upcoming events, team search |
| HackTheBox CTF events | Intermediate | Regular team events, competitive |
| SANS Holiday Hack | Intermediate | Annual, excellent quality, solo-friendly |
| pwn.college | Advanced | Binary exploitation depth |

## CTF Categories and Pentest Relevance

**Web** (most relevant): SQL injection, XSS, SSRF, deserialization, authentication bypass, JWT attacks, prototype pollution. Direct skill transfer to web app pentesting.

**Pwn / Binary Exploitation**: Buffer overflows, ROP chains, heap exploitation. Relevant for exploit development and understanding how memory corruption works.

**Crypto**: Weak encryption, padding oracles, hash length extension. Helps recognize crypto misuse in real applications.

**Forensics**: Log analysis, memory forensics, steganography. Overlaps with incident response and blue team skills.

**Reverse Engineering**: Decompile binaries, understand obfuscated code, crack license checks. Useful for malware analysis and thick client testing.

**OSINT**: Find information from public sources, social media, domain intelligence. Direct pentest skill.

## Starting Point: PicoCTF

```
1. Create account at picoctf.org
2. Start with "General Skills" category — zero barrier
3. Move to "Web Exploitation" — most relevant for pentest path
4. Each challenge has a hint system — use sparingly
5. After solving: read other writeups to see alternative approaches
```

## Finding CTF Teams

CTFtime.org → Teams → Search → filter by country or language. Most active teams recruit via Discord. Finding a team dramatically improves learning speed — other members solve categories you don't know yet.

## SANS Holiday Hack

Runs every December. Free. Multi-challenge format tied to a storyline. Very high production quality. Writeups are encouraged after the competition window. Highly recommended as your first structured CTF experience.

## CTF Skills That Directly Transfer to OSCP

- Web exploitation: every web CTF challenge is a pattern you'll see in PG/HTB machines
- Reading source code: CTF reverse challenges teach you to extract logic quickly
- Lateral thinking: CTFs reward creative approaches — same mindset for stuck machines
- Working under time pressure: CTF time limits build the urgency habit for 24-hour exams

## Minimum CTF Practice Recommendation

Before OSCP exam: complete 20 PicoCTF web challenges + participate in 1 live CTF event.
This builds comfort with time-pressure exploitation that lab machines do not replicate.
