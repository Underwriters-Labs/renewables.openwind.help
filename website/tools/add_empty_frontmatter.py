#!/usr/bin/env python3
"""
Add an empty YAML frontmatter block (---\n---) to every markdown file in the
site content folder that does not already have frontmatter.

Usage:
  python tools/add_empty_frontmatter.py   # from website/ (or repo root adjust path)

The script is idempotent: files that already start with a YAML frontmatter (`---`)
are left unchanged. It writes files in UTF-8 and reports how many files were updated.
"""
import sys
from pathlib import Path


def has_frontmatter(text: str) -> bool:
    """Return True if the file text starts with a YAML frontmatter marker.

    We consider frontmatter present when the first non-empty line is '---'.
    """
    for line in text.splitlines():
        if line.strip() == '':
            continue
        return line.strip() == '---'
    return False


def add_frontmatter_to_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    if has_frontmatter(text):
        return False

    # Insert empty frontmatter at top. Keep a separating blank line for readability.
    new_text = '---\n---\n\n' + text
    path.write_text(new_text, encoding='utf-8')
    return True


def main(content_dir: Path):
    if not content_dir.exists() or not content_dir.is_dir():
        print('Content directory not found:', content_dir)
        return 2

    files = list(content_dir.rglob('*.md'))
    changed = []
    for f in files:
        try:
            if add_frontmatter_to_file(f):
                changed.append(f)
        except Exception as exc:
            print('ERROR processing', f, exc)

    print(f'Scanned {len(files)} .md files, updated {len(changed)}')
    if changed:
        for p in changed:
            print('  +', p)
    return 0


if __name__ == '__main__':
    # The script lives in website/tools; default content dir is ../content
    base = Path(__file__).resolve().parent
    content = (base.parent / 'content')
    sys.exit(main(content))
