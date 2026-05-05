#!/usr/bin/env python3
"""
Master orchestration script: runs all content processing tools in sequence.

Workflow:
  1. add_empty_frontmatter.py   — ensure all .md files have YAML frontmatter
  2. convert_wiki_links.py      — convert [[wiki-links]] to markdown and normalize links
  3. download_images.py         — download external images and update links
  4. generate_search_index.py   — regenerate search index

Usage:
  python tools/run_all_tools.py --base website --dry-run
  python tools/run_all_tools.py --base website --backup
  python tools/run_all_tools.py --base website

Options:
  --base PATH       Base path (default: website)
  --dry-run         Show what would be done without making changes
  --backup          Create .bak files before modifying originals
  --skip-frontmatter  Skip the frontmatter step
  --skip-wiki-links   Skip the wiki-links conversion step
  --skip-images       Skip the image download step
  --skip-search       Skip the search index regeneration step
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a subprocess command and report results."""
    print(f"\n{'='*70}")
    print(f"▶ {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"\n✗ {description} failed with exit code {result.returncode}")
        return False
    print(f"\n✓ {description} completed successfully")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--base', '-b', default='website', help='Base path (default: website)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--backup', action='store_true', help='Create .bak files before modifying originals')
    parser.add_argument('--skip-frontmatter', action='store_true', help='Skip frontmatter step')
    parser.add_argument('--skip-wiki-links', action='store_true', help='Skip wiki-links conversion step')
    parser.add_argument('--skip-images', action='store_true', help='Skip image download step')
    parser.add_argument('--skip-search', action='store_true', help='Skip search index regeneration step')
    args = parser.parse_args(argv)

    base_path = Path(args.base).resolve()
    tools_dir = base_path / 'tools'

    if not tools_dir.is_dir():
        print(f"Error: Tools directory not found at {tools_dir}")
        return 1

    print(f"Orchestrating content processing pipeline")
    print(f"Base path: {base_path}")
    print(f"Dry-run: {args.dry_run}")
    print(f"Backup: {args.backup}")

    results = []

    # Step 1: Add empty frontmatter
    if not args.skip_frontmatter:
        cmd = ['python', str(tools_dir / 'add_empty_frontmatter.py'), '--base', str(base_path)]
        if args.dry_run:
            cmd.append('--dry-run')
        ok = run_command(cmd, "Step 1/4: Add empty frontmatter")
        results.append(('Frontmatter', ok))
    else:
        print("\n⊘ Step 1/4: Skipped (frontmatter)")
        results.append(('Frontmatter', None))

    # Step 2: Convert wiki links
    if not args.skip_wiki_links:
        cmd = ['python', str(tools_dir / 'convert_wiki_links.py'), '--base', str(base_path)]
        if args.dry_run:
            cmd.append('--dry-run')
        if args.backup:
            cmd.append('--backup')
        ok = run_command(cmd, "Step 2/4: Convert wiki links to markdown and normalize")
        results.append(('Wiki Links', ok))
    else:
        print("\n⊘ Step 2/4: Skipped (wiki links)")
        results.append(('Wiki Links', None))

    # Step 3: Download images
    if not args.skip_images:
        cmd = ['python', str(tools_dir / 'download_images.py'), '--base', str(base_path)]
        if args.dry_run:
            cmd.append('--dry-run')
        if args.backup:
            cmd.append('--backup')
        ok = run_command(cmd, "Step 3/4: Download external images and update links")
        results.append(('Images', ok))
    else:
        print("\n⊘ Step 3/4: Skipped (images)")
        results.append(('Images', None))

    # Step 4: Regenerate search index
    if not args.skip_search:
        cmd = ['python', str(tools_dir / 'generate_search_index.py'), '--base', str(base_path)]
        ok = run_command(cmd, "Step 4/4: Regenerate search index")
        results.append(('Search Index', ok))
    else:
        print("\n⊘ Step 4/4: Skipped (search index)")
        results.append(('Search Index', None))

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for name, result in results:
        if result is True:
            status = "✓ Success"
        elif result is False:
            status = "✗ Failed"
        else:
            status = "⊘ Skipped"
        print(f"  {name:20} {status}")

    # Return exit code
    failed = [r for _, r in results if r is False]
    if failed:
        print(f"\n{len(failed)} step(s) failed. Please review the output above.")
        return 1

    print("\n✓ All steps completed!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
