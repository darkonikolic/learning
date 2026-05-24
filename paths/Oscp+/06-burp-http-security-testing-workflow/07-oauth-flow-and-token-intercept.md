# Unit 07 — JWT + OAuth flow interception drill

Reuse Academy JWT + OAuth exercises while mirroring interception in **authorised Symfony OAuth** playgrounds.

Observe **authorise** ⇒ **callback** choreography:

`/oauth/authorize` query parameters (**client_id**, **redirect_uri**, **state**)  

Captured **authorization code hop** ⇒ token exchange artefacts

Document **misconfiguration hypotheses** tied to lax redirect allowances or absent **PKCE** when public clients analogue appears.
