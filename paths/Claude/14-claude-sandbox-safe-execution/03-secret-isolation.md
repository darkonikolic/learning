# Secret isolation

**Theme:** Assume assistant context **will** echo, log, or serialise secrets—design so production truth **never enters** that context.

### Non-negotiables

Do **not** mount or paste into agent context:

Production **cloud tokens**, **kubeconfigs** pointing at prod, raw **GitHub PATs**, **SSH private keys**, payment provider live keys—the user’s prohibition list applies even when “only for a minute.”

### Safer substitutes

Scoped **fake credentials** for local mocks  

Short-lived tokens from a vault or cloud identity—with **narrow IAM** bound to disposable sandboxes  

**Runtime injection** into processes that assistants never see (secrets manager → app only)

Treat `.env` in repos as **config shape documentation**—populate from local secret store templates, never commit real values.

### LAB

Maintain a **credential inventory table** per integration: tool name → **exact secret artefact class** → **whether the AI execution layer can observe it** (yes/no + mitigation).

### Checklist

- [ ] Rotate anything that ever appeared in chat logs or shared screenshots—assume compromise for learning setups.  
