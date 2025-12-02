#!/usr/bin/env python3
"""
Convert wiki-style [[links]] to root-based markdown links in files.

Behavior and examples:
 - [[File Name]]           -> [File Name](/File-Name)
 - [[Display|Target File]] -> [Display](/Target-File)

By default the script scans 'website/content' directory repo root.
It modifies files in-place, but supports --dry-run and --backup flags.

Usage:
  python tools/convert_wiki_links.py --dry-run
  python tools/convert_wiki_links.py  # applies the changes

This script will process files with extensions: .md .markdown .MD
"""
import argparse
import re
from pathlib import Path
import sys


WIKI_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def normalize_target(target: str) -> str:
    """Normalize the target to a root path.

    - strip surrounding whitespace
    - replace sequences of whitespace with hyphen
    - preserve existing punctuation/hyphens
    """
    t = target.strip()
    # replace spaces and consecutive whitespace with single hyphen
    t = re.sub(r"\s+", "-", t)
    return '/' + t


def replace_in_text(text: str) -> (str, int):
    """Return (new_text, count) with wiki links converted."""

    def repl(match: re.Match):
        label = match.group(1).strip()
        target = match.group(2)
        if target:
            target = target.strip()
        else:
            target = label
        href = normalize_target(target)
        return f'[{label}]({href})'

    new_text, n = WIKI_RE.subn(repl, text)
    return new_text, n


def files_to_scan(base_dir: Path):
    exts = {'.md', '.markdown', '.MD'}
    for p in base_dir.rglob('*'):
        if p.is_file() and p.suffix in exts:
            yield p


def process_file(path: Path, dry_run: bool=False, backup: bool=False):
    text = path.read_text(encoding='utf-8')
    new_text, count = replace_in_text(text)
    if count > 0:
        if dry_run:
            return count, new_text
        if backup:
            bak = path.with_suffix(path.suffix + '.bak')
            bak.write_text(text, encoding='utf-8')
        path.write_text(new_text, encoding='utf-8')
    return count, None


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', '-b', default='.', help='Base path to scan (default: .)')
    parser.add_argument('--dry-run', action='store_true', help='Show changes but do not write files')
    parser.add_argument('--backup', action='store_true', help='Before writing, save a .bak copy of changed files')
    args = parser.parse_args(argv)

    base = Path(args.base).resolve()
    # default scan: website/ under repo root if exists else current
    if (base / 'website').is_dir() and base != (base / 'website'):
        content_base = (base / 'website')
    else:
        content_base = base

    processed = 0
    changed_files = []

    # scan content files under website/content if that exists, else whole base
    scan_dir = content_base / 'content' if (content_base / 'content').is_dir() else content_base

    for p in files_to_scan(scan_dir):
        cnt, _ = process_file(p, dry_run=args.dry_run, backup=args.backup)
        if cnt:
            processed += cnt
            changed_files.append((p, cnt))

    # Output summary
    if args.dry_run:
        if not changed_files:
            print('No wiki-style links found.')
            return 0
        print('Dry run — proposed changes:')
        for p, cnt in changed_files:
            print(f'  {p}  -> {cnt} replacements')
        return 0

    print(f'Applied replacements: {processed} occurrences across {len(changed_files)} files')
    for p, cnt in changed_files:
        print(f'  modified {p} ({cnt} replacements)')

    return 0


if __name__ == '__main__':
    sys.exit(main())
