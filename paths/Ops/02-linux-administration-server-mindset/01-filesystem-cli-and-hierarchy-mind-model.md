# Unit 01 — Filesystem posture, hierarchy literacy, habitual CLI navigation

Comfortable primitives: `pwd`, `ls`, `cd`, `mkdir`, `rm`, `mv`, `cp`, `touch`, directory trees (tooling like `tree` when installed), shell history ergonomics (`history`, purposeful clearing rituals — never erase audit trails accidentally on shared infra).

Labs:

```text
mkdir -p app logs backup
touch nginx.log db.log
cp nginx.log backup/
mv db.log logs/
```

## Mental anchors

Interpret **absolute versus relative paths** consciously when scripting — surprises often trace back ambiguous `cwd`.

Locate standard hierarchy anchors (`/etc`, `/var`, `/tmp`, `/home`, `/usr`, …) and articulate what classes of mutable vs configuration-of-record artefacts typically reside where.
