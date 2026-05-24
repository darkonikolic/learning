#!/usr/bin/env python3
"""
Smoke test: builds PDF from the vault `paths/Claude/` folder (SOURCE under workspace root).

CI / manual check **must** go through **`build_learning_path_pdf.py`** — this file only
shells into that canonical script.

Run from vault root:

    scripts/.venv/bin/python scripts/test_build_learning_path_pdf.py

Or create venv once under scripts/:

    cd scripts && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

Requires WeasyPrint system libs (same as production build).
PDF output is written to **`exports/<stem>-learning-path.pdf`** by default.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


def _vault_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _script() -> Path:
    return Path(__file__).resolve().parent / "build_learning_path_pdf.py"


def _oscpp_trace_has_markdown(root: Path) -> bool:
    o = root / "paths" / "Oscp+"
    if not o.is_dir():
        return False
    return any(p.suffix == ".md" for p in o.rglob("*") if p.is_file())


class TestBuildLearningPathPdf(unittest.TestCase):
    def test_claude_folder_produces_pdf(self) -> None:
        root = _vault_root()
        claude = root / "paths" / "Claude"
        self.assertTrue(
            claude.is_dir(),
            f"Missing {claude} — clone/setup curriculum before running this test.",
        )
        exe = Path(__file__).resolve().parent / ".venv" / "bin" / "python"
        if exe.is_file():
            py = str(exe)
        else:
            py = sys.executable

        r = subprocess.run(
            [
                py,
                str(_script()),
                str(claude),
                "--workspace",
                str(root),
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            r.returncode,
            0,
            msg=(r.stderr or "") + (r.stdout or ""),
        )

        pdf = root / "exports" / "Claude-learning-path.pdf"
        self.assertTrue(pdf.is_file(), msg=f"Expected PDF at {pdf}")

    @unittest.skipUnless(
        _oscpp_trace_has_markdown(_vault_root()),
        "Oscp+ has no Markdown units yet — add .md under paths/Oscp+/ to enable this smoke test.",
    )
    def test_oscpp_phase_layout_produces_pdf(self) -> None:
        root = _vault_root()
        oscpp = root / "paths" / "Oscp+"
        self.assertTrue(oscpp.is_dir(), f"Missing {oscpp}")
        exe = Path(__file__).resolve().parent / ".venv" / "bin" / "python"
        py = str(exe) if exe.is_file() else sys.executable

        r = subprocess.run(
            [
                py,
                str(_script()),
                str(oscpp),
                "--workspace",
                str(root),
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, msg=(r.stderr or "") + (r.stdout or ""))
        self.assertTrue((root / "exports" / "Oscp+-learning-path.pdf").is_file())


if __name__ == "__main__":
    unittest.main()
