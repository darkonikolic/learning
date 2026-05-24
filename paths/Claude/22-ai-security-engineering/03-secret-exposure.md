# Secret exposure

**Theme:** Tokens, private keys, session cookies, long-lived JWT signing secrets must **never** become model training fodder logs or casual chat artefacts—assume **ambient exfiltration** risk anytime text flows cross boundaries.

Forbidden examples (never exercise with real prod material): raw **AWS keys**, **SSH privates**, **OAuth refresh tokens**, **`kubectl` bearer**, payment processor live secrets.**Even fake samples** emulate shape—rotate if ever leaked mistakenly.

Detection habits:

regex / scanner class awareness for accidental **credential-shaped** blobs  

Structural refusal when asked to paste full `.env` contents likely live  

Operational **vault** segmentation—assistants manipulate references not secret bodies

Redaction rehearsals: deterministic masking **`******`** patterns preserving forensic shape without fidelity leak.

Symfony `.env.local` handling narrative: loaders outside model reach; sanitized shape docs only.**Terraform providers**: credentials via OIDC short-lived identities or narrowly scoped IAM roles—not static keys in plaintext assistant context panels.

Mandatory lab refusal: supply realistic **bogus secrets** verifying assistant withholds verbatim echo and refrains from reversing operations revealing them unintentionally via encoding tricks.

Discuss false positives: benign high-entropy hex strings flagged—balance with reviewer override path.

### Checklist

- [ ] Secret discovery triggers **immediate redaction audit** downstream logs—not only initial refusal moment.  
