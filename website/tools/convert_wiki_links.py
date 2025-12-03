#!/usr/bin/env python3
"""
Convert wiki-style [[links]] to root-based markdown links in files.

Behavior and examples:
 - [[File Name]]           -> [File Name](/file-name)
 - [[Display|Target File]] -> [Display](/target-file)

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
import urllib.parse


WIKI_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
LINK_RE = re.compile(r'(?<!!)\[([^\]]+)\]\(\s*([^\)\s]+)(?:\s+["\'].*?["\'])?\s*\)')


def normalize_target(target: str) -> str:
    """Normalize the target to a root path.

    - strip surrounding whitespace
    - replace sequences of whitespace with hyphen
    - preserve existing punctuation/hyphens
    """
    t = target.strip()
    # remove any leading/trailing slashes the user may have added
    t = t.strip('/')
    # replace spaces and consecutive whitespace with single hyphen
    t = re.sub(r"\s+", "-", t)
    # lowercase the path so generated links are always lowercase
    t = t.lower()
    return '/' + t


def replace_in_text(text: str) -> tuple[str, int]:
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


def normalize_markdown_links(text: str) -> tuple[str, int]:
    """Lowercase internal markdown link targets. Returns (new_text, count)."""

    def repl(match: re.Match):
        label = match.group(1)
        href = match.group(2)
        # skip absolute URLs (with scheme) and anchors
        if '://' in href or href.startswith('#'):
            return match.group(0)
        # normalize path: remove leading ./ or ../ or leading slashes, lowercase, then prefix with '/'
        parsed = urllib.parse.urlparse(href)
        path = parsed.path
        # remove leading './' and '../' and any leading slashes
        path = re.sub(r'^(\.{1,2}/)+', '', path)
        path = path.lstrip('/')
        # lowercase the path
        path = path.lower()
        # ensure root prefix
        new_path = '/' + path if path != '' else '/'
        # rebuild URL preserving query/fragment
        new_href = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment))
        return f'[{label}]({new_href})'

    new_text, n = LINK_RE.subn(repl, text)
    return new_text, n


def files_to_scan(base_dir: Path):
    exts = {'.md', '.markdown', '.MD'}
    for p in base_dir.rglob('*'):
        if p.is_file() and p.suffix in exts:
            yield p


def process_file(path: Path, dry_run: bool=False, backup: bool=False, lowercase_links: bool=False):
    text = path.read_text(encoding='utf-8')
    total_count = 0

    # first, convert wiki links
    new_text, count = replace_in_text(text)
    total_count += count

    # optionally normalize existing markdown links
    if lowercase_links:
        new_text2, count2 = normalize_markdown_links(new_text)
        new_text = new_text2
        total_count += count2

    if total_count > 0:
        if dry_run:
            return total_count, new_text
        if backup:
            bak = path.with_suffix(path.suffix + '.bak')
            bak.write_text(text, encoding='utf-8')
        path.write_text(new_text, encoding='utf-8')
    return total_count, None


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', '-b', default='.', help='Base path to scan (default: .)')
    parser.add_argument('--dry-run', action='store_true', help='Show changes but do not write files')
    parser.add_argument('--backup', action='store_true', help='Before writing, save a .bak copy of changed files')
    parser.add_argument('--lowercase-links', action='store_true', help='Lowercase internal markdown link targets')
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
        cnt, _ = process_file(p, dry_run=args.dry_run, backup=args.backup, lowercase_links=args.lowercase_links)
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
