#!/usr/bin/env python3
"""
Compile Markdown under one or more curriculum directories into `{stem}-learning-path.pdf`.

Canonical export for this vault: any **learning-path PDF** (`<stem>-learning-path.pdf`)
or bundle Markdown (`--emit-markdown`) from trace Markdown **must** be produced with
this script — not pandoc, not ad-hoc WeasyPrint/Python, not other CLI exporters.

From vault root:

    cd scripts && (test -x .venv/bin/python || (python3 -m venv .venv && .venv/bin/pip install -r requirements.txt))
    cd ..    # optional; cwd may stay scripts/ if SOURCES are absolute

    scripts/.venv/bin/python scripts/build_learning_path_pdf.py paths/Claude \\
        --workspace "/ABS/path/to/Plan ucenja"

Several traces in **one run** → **multiple PDF files** under vault **`exports/`**
(unless **`--out-dir`** overrides):

    scripts/.venv/bin/python scripts/build_learning_path_pdf.py paths/Claude paths/Oscp+ \\
        --workspace "/ABS/path/to/Plan ucenja"

Same `--layout` / `--emit-markdown` applies to **every** SOURCE. **`--pdf-name`**
requires exactly one SOURCE.

If a PDF already exists at the destination, it is overwritten. Each `SOURCE`
must resolve to a directory inside `--workspace` (e.g. `paths/Go`, `paths/Architect`).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


import markdown
from weasyprint import HTML

SCRIPT_DIR = Path(__file__).resolve().parent


def find_workspace_anchor(start: Path | None = None) -> Path:
    cur = (start or SCRIPT_DIR).resolve()
    if cur.is_file():
        cur = cur.parent
    for _ in range(32):
        if (cur / ".cursor").is_dir():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    raise RuntimeError(
        "Could not find workspace (no ancestor with `.cursor/`). Pass --workspace."
    )


def phase_sort_key(folder: Path) -> tuple[int, str]:
    m = re.match(r"^(\d{2})-", folder.name)
    if not m:
        return (999, folder.name)
    return int(m.group(1)), folder.name


def file_sort_key(path: Path) -> tuple[list[int | str], str]:
    stem = path.stem
    m = re.match(r"^(\d+)", stem)
    if m:
        return ([0, int(m.group(1)), stem], path.name)
    return ([1, stem], path.name)


def slug_from_source(src: Path) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._+-]+", "-", src.name.strip()).strip("-")
    return slug or "curriculum"


def collect_phase_dirs(curriculum_root: Path) -> list[Path]:
    if not curriculum_root.is_dir():
        return []
    out: list[Path] = []
    for child in curriculum_root.iterdir():
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        if re.match(r"^\d{2}-", child.name):
            out.append(child)
    out.sort(key=phase_sort_key)
    return out


def collect_flat_files(curriculum_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in curriculum_root.rglob("*.md"):
        rel = path.relative_to(curriculum_root)
        if any(p.startswith("_") or p.startswith(".") for p in rel.parts):
            continue
        files.append(path)
    files.sort(key=lambda p: str(p.relative_to(curriculum_root)).replace("\\", "/").lower())
    return files


def build_markdown_bundle(
    curriculum_root: Path,
    *,
    layout: str,
    title_human: str,
) -> str:
    lines: list[str] = []

    lines.append(f"# {title_human} — compiled path")
    lines.append("")
    lines.append(
        f"> Compiled from `{curriculum_root.as_posix()}`. "
        f"Canonical sources stay in place."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    if layout == "phase":
        phases = collect_phase_dirs(curriculum_root)
        if not phases:
            raise SystemExit(
                f"No numbered phase dirs (`NN-*`) directly under `{curriculum_root}`.\n"
                "Use `--layout flat` for recursive Markdown, or fix hierarchy."
            )
        first_phase = True
        for phase_dir in phases:
            md_files = sorted(phase_dir.glob("*.md"), key=file_sort_key)
            if not md_files:
                continue
            if not first_phase:
                lines.append('<div style="page-break-before: always;"></div>')
                lines.append("")
            first_phase = False

            lines.append(f"## Phase — {phase_dir.name}")
            lines.append("")
            lines.append(f"*Directory:* `{phase_dir.relative_to(curriculum_root).as_posix()}/`")
            lines.append("")
            lines.append("---")
            lines.append("")

            for md in md_files:
                rel = md.relative_to(curriculum_root)
                raw = md.read_text(encoding="utf-8")
                lines.append(f"### Source: `{rel.as_posix()}`")
                lines.append("")
                lines.append(raw.strip())
                lines.append("")
                lines.append("<hr>")
                lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    # flat recursive
    all_md = collect_flat_files(curriculum_root)
    if not all_md:
        raise SystemExit(f"No `.md` files found under `{curriculum_root}` (after filters).")

    first = True
    for md in all_md:
        if not first:
            lines.append('<div style="page-break-before: always;"></div>')
            lines.append("")
        first = False
        rel = md.relative_to(curriculum_root)
        lines.append(f"## File — `{rel.as_posix()}`")
        lines.append("")
        lines.append(md.read_text(encoding="utf-8").strip())
        lines.append("")
        lines.append("<hr>")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


PRINT_CSS = """
@page {
  size: A4;
  margin: 12mm 14mm 16mm 14mm;
}
html {
  font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
  font-size: 9pt;
  line-height: 1.38;
  color: #111;
}
body { margin: 0; }
h1 {
  font-size: 17pt;
  page-break-after: avoid;
  margin-top: 0;
  page-break-before: avoid;
}
h2 {
  font-size: 13pt;
  page-break-after: avoid;
  border-bottom: 1px solid #ccc;
  padding-bottom: 2px;
}
h3 {
  font-size: 10.5pt;
  page-break-after: avoid;
}
h4, h5, h6 { font-size: 10pt; page-break-after: avoid; }
p { margin: 0.45em 0; }
ul, ol { margin: 0.35em 0 0.5em 1.2em; padding-left: 0.3em; }
li { margin: 0.15em 0; }
blockquote {
  margin: 0.5em 0;
  padding: 0.35em 0.6em;
  border-left: 3px solid #bbb;
  background: #f7f7f7;
  color: #333;
}
code, pre, kbd, samp {
  font-family: "DejaVu Sans Mono", "Liberation Mono", Consolas, monospace;
  font-size: 8.2pt;
}
code {
  background: #f0f0f0;
  padding: 0.05em 0.25em;
  border-radius: 2px;
}
pre {
  background: #f4f4f4;
  border: 1px solid #ddd;
  padding: 6px 8px;
  border-radius: 3px;
  white-space: pre-wrap;
  word-wrap: break-word;
  page-break-inside: avoid;
}
pre code { background: none; padding: 0; }
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 8.2pt;
  margin: 0.5em 0;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid #bbb;
  padding: 3px 5px;
  vertical-align: top;
}
th { background: #eee; }
hr { border: none; border-top: 1px solid #ccc; margin: 10px 0; }
a { color: #06c; text-decoration: none; }
"""


def render_html(md_text: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=[
            "markdown.extensions.extra",
            "markdown.extensions.codehilite",
            "markdown.extensions.smarty",
        ],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": False},
        },
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="generator" content="learning-path-pdf"/>
  <title>Compiled curriculum</title>
  <style>{PRINT_CSS}</style>
  <style>
    .highlight {{ background: #fafafa; }}
    .highlight pre {{ border: none; background: transparent; }}
  </style>
</head>
<body>{body}</body>
</html>
"""


def write_pdf(md_text: str, pdf_target: Path, base_url_uri: str) -> None:
    html = render_html(md_text)
    pdf_target.parent.mkdir(parents=True, exist_ok=True)
    pdf_target.unlink(missing_ok=True)
    HTML(string=html, base_url=base_url_uri).write_pdf(pdf_target)


def resolve_curriculum(workspace: Path, source: Path) -> Path:
    """Resolve SOURCE to an absolute curriculum directory."""
    cand = source.expanduser()
    curriculum = cand if cand.is_absolute() else (Path.cwd() / cand).resolve()
    try:
        curriculum.relative_to(workspace)
    except ValueError:
        sys.exit(
            "`SOURCE` must resolve to a path inside `--workspace`:\n"
            f"  workspace: {workspace}\n"
            f"  got:       {curriculum}"
        )
    return curriculum


def parse_args() -> argparse.Namespace:
    ws_default = find_workspace_anchor()
    p = argparse.ArgumentParser(
        description=(
            "Markdown trees at SOURCE… → `<stem>-learning-path.pdf` each "
            "(overwrites if present). Multiple SOURCES ⇒ one PDF per tree."
        )
    )
    p.add_argument(
        "sources",
        nargs="+",
        type=Path,
        help=(
            "One or more curriculum directories inside `--workspace`. "
            "Each may be absolute or relative to cwd, e.g. paths/Claude or paths/Oscp+."
        ),
    )
    p.add_argument(
        "--workspace",
        type=Path,
        default=ws_default,
        help="Vault root (`paths/*/`, `exports/`, `.cursor/` live here). Detected if omitted.",
    )
    p.add_argument(
        "--layout",
        choices=("phase", "flat"),
        default="phase",
        help=(
            "phase: only direct NN-* folders with *.md | "
            "flat: all *.md recursive (skips ./_*)"
        ),
    )
    p.add_argument(
        "--pdf-name",
        type=str,
        default=None,
        help="Stem when exactly one SOURCE; illegal with multiple SOURCES.",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Write PDFs/markdown bundles here instead of `<workspace>/exports/`.",
    )
    p.add_argument(
        "--emit-markdown",
        action="store_true",
        help="Also write `<stem>-learning-path.md` beside the PDF (overwrite).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    workspace = args.workspace.resolve()

    sources = args.sources
    if len(sources) > 1 and args.pdf_name:
        sys.exit("`--pdf-name` is allowed only when there is exactly one SOURCE.")

    exports_dir = (workspace / "exports").resolve()
    out_dir = (args.out_dir or exports_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base_uri = workspace.as_uri() + "/"

    for raw in sources:
        curriculum = resolve_curriculum(workspace, raw)
        if not curriculum.is_dir():
            sys.exit(f"SOURCE is not a directory: {curriculum}")

        stem = (
            slug_from_source(Path(args.pdf_name))
            if args.pdf_name
            else slug_from_source(curriculum)
        )
        pdf_path = out_dir / f"{stem}-learning-path.pdf"

        md_text = build_markdown_bundle(
            curriculum,
            layout=args.layout,
            title_human=curriculum.name,
        )

        if args.emit_markdown:
            md_path = out_dir / f"{stem}-learning-path.md"
            md_path.unlink(missing_ok=True)
            md_path.write_text(md_text, encoding="utf-8")
            print(f"Wrote Markdown: {md_path.resolve()} ({len(md_text) // 1024} KiB)")

        write_pdf(md_text, pdf_path, base_uri)
        print(f"Wrote PDF: {pdf_path.resolve()} ({pdf_path.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
