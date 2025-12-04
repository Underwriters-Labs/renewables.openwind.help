#!/usr/bin/env python3
"""
Download external images referenced in markdown content and update links to serve them from
the local `static/images` directory. Simple, dependency-free script.

Behavior:
 - Scans `content/` under the provided base (default: repo root or `website` if present).
 - Finds markdown inline images `![alt](URL)` and HTML `<img src="URL">` references.
 - For external URLs (http/https) it downloads the image to `website/static/images` and
   replaces the link with a root-based path `/images/<filename>`.

Usage:
  python tools/download_images.py --dry-run
  python tools/download_images.py --backup   # downloads and updates files, saving .bak copies

This script intentionally keeps behavior simple and conservative. It does not rewrite
relative or local image paths.
"""
import argparse
import hashlib
import os
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path


IMAGE_MD_RE = re.compile(r'!\[([^\]]*)\]\(\s*([^\)\s]+)(?:\s+["\'][^"\']*["\'])?\s*\)')
IMAGE_HTML_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)


def ensure_out_dir(base_dir: Path) -> Path:
    out = base_dir / 'static' / 'images'
    out.mkdir(parents=True, exist_ok=True)
    return out


def filename_for_url(url: str) -> str:
    """Create a stable filename for a URL: sha8-basename.ext (preserving extension)."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.split('?')[0]  # remove query string
    base = os.path.basename(path) or 'image'
    
    # extract extension
    name, ext = os.path.splitext(base)
    if not ext or len(ext) > 10:  # guard against very long or missing extensions
        ext = '.jpg'  # default fallback
    
    # sanitize name (keep only alphanumeric, dots, hyphens)
    name = re.sub(r'[^A-Za-z0-9._-]', '-', name)
    name = name.strip('-')
    
    # prefix with short hash to avoid collisions
    h = hashlib.sha1(url.encode('utf-8')).hexdigest()[:8]
    return f"{h}-{name}{ext}" if name else f"{h}{ext}"


def download_url(url: str, dest: Path) -> bool:
    try:
        # simple downloader; may raise URLError/HTTPError
        urllib.request.urlretrieve(url, str(dest))
        return True
    except Exception:
        return False


def replace_image_links(text: str, mapping: dict) -> (str, int):
    """Replace occurrences of keys in mapping inside markdown and html image links."""

    def repl_md(m):
        alt, href = m.group(1), m.group(2)
        new = mapping.get(href)
        if new:
            return f'![{alt}]({new})'
        return m.group(0)

    def repl_html(m):
        href = m.group(1)
        new = mapping.get(href)
        if new:
            # naive replacement of src value
            return m.group(0).replace(href, new)
        return m.group(0)

    new_text, n1 = IMAGE_MD_RE.subn(repl_md, text)
    new_text, n2 = IMAGE_HTML_RE.subn(repl_html, new_text)
    return new_text, (n1 + n2)


def files_to_scan(base_dir: Path):
    exts = {'.md', '.markdown', '.MD'}
    for p in base_dir.rglob('*'):
        if p.is_file() and p.suffix in exts:
            yield p


def process_file(path: Path, out_dir: Path, dry_run: bool=False, backup: bool=False):
    text = path.read_text(encoding='utf-8')
    urls = set()
    for m in IMAGE_MD_RE.finditer(text):
        href = m.group(2).strip()
        if href.startswith('http://') or href.startswith('https://'):
            urls.add(href)
    for m in IMAGE_HTML_RE.finditer(text):
        href = m.group(1).strip()
        if href.startswith('http://') or href.startswith('https://'):
            urls.add(href)

    if not urls:
        return 0, None, {}

    mapping = {}
    downloads = []
    for url in sorted(urls):
        fname = filename_for_url(url)
        dest = out_dir / fname
        root_href = f"/images/{fname}"
        mapping[url] = root_href
        downloads.append((url, dest, root_href))

    new_text, count = replace_image_links(text, mapping)

    if count > 0 and not dry_run:
        if backup:
            bak = path.with_suffix(path.suffix + '.bak')
            bak.write_text(text, encoding='utf-8')
        path.write_text(new_text, encoding='utf-8')

    # if not dry_run, perform downloads (after writing file to avoid partial state)
    downloaded = []
    if not dry_run:
        for url, dest, root_href in downloads:
            if dest.exists():
                downloaded.append((url, dest))
                continue
            ok = download_url(url, dest)
            if ok:
                downloaded.append((url, dest))
    return count, downloads, downloaded


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', '-b', default='.', help='Base path to scan (default: .)')
    parser.add_argument('--dry-run', action='store_true', help='Show downloads and replacements but do not write files')
    parser.add_argument('--backup', action='store_true', help='Before writing, save a .bak copy of changed files')
    args = parser.parse_args(argv)

    base = Path(args.base).resolve()
    if (base / 'website').is_dir() and base != (base / 'website'):
        content_base = (base / 'website')
    else:
        content_base = base

    scan_dir = content_base / 'content' if (content_base / 'content').is_dir() else content_base
    out_dir = ensure_out_dir(content_base)

    total_changes = 0
    total_files = 0
    summary_downloads = []

    for p in files_to_scan(scan_dir):
        cnt, downloads, downloaded = process_file(p, out_dir, dry_run=args.dry_run, backup=args.backup)
        if cnt:
            total_changes += cnt
            total_files += 1
            if downloads:
                summary_downloads.append((p, downloads))

    if args.dry_run:
        if not summary_downloads:
            print('No external images found.')
            return 0
        print('Dry run — proposed image downloads and replacements:')
        for p, downloads in summary_downloads:
            print(f'  {p}:')
            for url, dest, root_href in downloads:
                print(f'    {url} -> {root_href} (would save to: {dest})')
        print(f'Files that would be changed: {total_files} with {total_changes} replacements total')
        return 0

    # non-dry run: report results
    print(f'Updated {total_files} files with {total_changes} image link replacements')
    return 0


if __name__ == '__main__':
    sys.exit(main())
