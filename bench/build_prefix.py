"""Build the Phase 0 knowledge prefix: system prompt plus raw site and resume text.

Raw string dumps, not curated Markdown. Only sized to measure latency, not
answer quality. Lines that look like a phone number are dropped.

Usage: python build_prefix.py <portfolio/src/data> <resume.pdf> <out.txt>
"""

import glob
import os
import re
import subprocess
import sys

from latency import SYSTEM

PHONE = re.compile(r"\d{3}-\d{3}-\d{4}")
LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')


def site_sections(data_root: str) -> list[str]:
    files = sorted(glob.glob(os.path.join(data_root, "*.ts")) + glob.glob(os.path.join(data_root, "fun", "*.ts")))
    sections = []
    for f in files:
        text = [x for x in LITERAL.findall(open(f, encoding="utf-8").read())
                if " " in x and not x.startswith("/") and "http" not in x]
        if text:
            sections.append(f"## Site: {os.path.splitext(os.path.basename(f))[0]}\n" + "\n".join(text))
    return sections


def resume_section(pdf: str) -> str:
    text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout
    return "## Resume\n" + "\n".join(line for line in text.splitlines() if not PHONE.search(line))


def main() -> None:
    data_root, pdf, out = sys.argv[1:4]
    system = SYSTEM.replace("<context>", "<knowledge>") + " Each user message lists the relevant knowledge sections first; prefer those sections."
    body = "\n\n".join([resume_section(pdf)] + site_sections(data_root))
    open(out, "w", encoding="utf-8").write(f"{system}\n\n<knowledge>\n{body}\n</knowledge>")


if __name__ == "__main__":
    main()
