#!/usr/bin/env python3
"""
Simple generator for a search index JSON file.

Walks the website/content folder, extracts title and the first paragraph from markdown
and writes a small JSON array to website/static/js/search-index.json so client-side
search can read it quickly.

This script is intentionally small and dependency-free.
"""
import os
import re
import json

ROOT = os.path.join(os.path.dirname(__file__), '..')
CONTENT_DIR = os.path.normpath(os.path.join(ROOT, 'content'))
OUT_DIR = os.path.normpath(os.path.join(ROOT, 'static', 'js'))
OUT_FILE = os.path.join(OUT_DIR, 'search-index.json')

md_heading = re.compile(r'^#+\s*(.+)')
front_matter_title = re.compile(r'^title:\s*(.+)$', re.IGNORECASE)

def extract_title_and_summary(path):
    title = None
    summary = None
    with open(path, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f]

    # Skip YAML front matter if present
    i = 0
    if len(lines) and lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            m = front_matter_title.match(lines[i].strip())
            if m:
                title = m.group(1).strip().strip('"')
            i += 1
        i = i + 1 if i < len(lines) else i

    # Find first heading if we don't have title
    for j in range(i, len(lines)):
        m = md_heading.match(lines[j])
        if m:
            if not title:
                title = m.group(1).strip()
            # summary is likely after the heading — collect up to 3 paragraphs
            k = j+1
            # skip leading blank lines
            while k < len(lines) and lines[k].strip() == '':
                k += 1
            paras = []
            while k < len(lines) and len(paras) < 3:
                # stop collecting if we hit another heading
                if md_heading.match(lines[k]):
                    break
                # accumulate paragraph lines until blank
                buf = []
                while k < len(lines) and lines[k].strip() != '':
                    buf.append(lines[k].strip())
                    k += 1
                if buf:
                    paras.append(re.sub(r'\s+', ' ', ' '.join(buf)))
                # skip blanks between paragraphs
                while k < len(lines) and lines[k].strip() == '':
                    k += 1
            if paras:
                summary = ' '.join(paras)
            break

    # fallback: use filename as title
    if not title:
        title = os.path.splitext(os.path.basename(path))[0]

    return title, summary or ''

def main():
    pages = []
    for dirpath, _, filenames in os.walk(CONTENT_DIR):
        for fname in filenames:
            if not fname.lower().endswith('.md'):
                continue
            # ignore index files that start with underscore? We'll include top-level ones only
            if fname.startswith('_'):
                # we may still include _index.md; keep behavior: ignore leading underscore files
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, CONTENT_DIR)
            # define link path from filepath
            # convert backslashes to slashes, replace whitespace with hyphens, and lowercase
            slug = os.path.splitext(rel)[0].replace('\\', '/')
            slug = re.sub(r"\s+", '-', slug)
            slug = slug.lower()
            link = '/' + slug
            title, summary = extract_title_and_summary(full)
            pages.append({'title': title, 'summary': summary, 'link': link})

    # ensure output dir exists
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(pages, f, indent=2, ensure_ascii=False)

    print('Wrote', OUT_FILE, 'with', len(pages), 'entries')

if __name__ == '__main__':
    main()
