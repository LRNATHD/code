"""
Portfolio Sync Script
Scans for markdown files with `portfolio:` frontmatter and syncs them to MkDocs docs folder.

Usage:
    python sync_to_portfolio.py
    python sync_to_portfolio.py --dry-run  # Preview without copying
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional

# Configuration
CODE_DIR = Path(r"c:\Users\LRNA\Desktop\code")
PORTFOLIO_DOCS_DIR = Path(r"c:\Users\LRNA\Desktop\portfolio\docs")

# Regex to extract frontmatter
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract frontmatter and remaining content from markdown."""
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content
    
    frontmatter_text = match.group(1)
    body = content[match.end():]
    
    # Simple YAML parsing (key: value per line)
    frontmatter = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip()
    
    return frontmatter, body


def find_portfolio_files(root: Path) -> list[tuple[Path, dict, str]]:
    """Find all markdown files with portfolio frontmatter."""
    results = []
    
    for md_file in root.rglob("*.md"):
        # Skip common unwanted directories
        parts = md_file.parts
        if any(skip in parts for skip in ['node_modules', 'venv', '.git', '__pycache__']):
            continue
        
        try:
            content = md_file.read_text(encoding='utf-8')
            frontmatter, body = parse_frontmatter(content)
            
            if 'portfolio' in frontmatter:
                results.append((md_file, frontmatter, body))
        except Exception as e:
            print(f"  Warning: Could not read {md_file}: {e}")
    
    return results


def find_local_assets(md_file: Path, content: str) -> list[tuple[str, Path]]:
    """Find local image/asset references in markdown content."""
    assets = []
    md_dir = md_file.parent
    
    # Match ![alt](path) and <img src="path">
    img_patterns = [
        r'!\[.*?\]\(([^)]+)\)',  # ![alt](path)
        r'<img[^>]+src=["\']([^"\']+)["\']',  # <img src="path">
    ]
    
    for pattern in img_patterns:
        for match in re.finditer(pattern, content):
            ref = match.group(1)
            # Skip URLs
            if ref.startswith(('http://', 'https://', '//')):
                continue
            
            asset_path = md_dir / ref
            if asset_path.exists():
                assets.append((ref, asset_path))
    
    return assets


def sync_file(source: Path, frontmatter: dict, body: str, dry_run: bool = False) -> bool:
    """Sync a single file to the portfolio."""
    portfolio_path = frontmatter['portfolio']
    
    # Ensure .md extension
    if not portfolio_path.endswith('.md'):
        portfolio_path = portfolio_path + '.md'
    
    dest_path = PORTFOLIO_DOCS_DIR / portfolio_path
    
    # Prepare content (strip portfolio frontmatter, keep other frontmatter if any)
    clean_frontmatter = {k: v for k, v in frontmatter.items() if k != 'portfolio'}
    if clean_frontmatter:
        fm_text = '---\n' + '\n'.join(f'{k}: {v}' for k, v in clean_frontmatter.items()) + '\n---\n\n'
        output_content = fm_text + body
    else:
        output_content = body
    
    print(f"  {source.relative_to(CODE_DIR)}")
    print(f"    -> {dest_path.relative_to(PORTFOLIO_DOCS_DIR.parent)}")
    
    if dry_run:
        print(f"    (dry run - not copied)")
        return True
    
    # Create directory if needed
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    dest_path.write_text(output_content, encoding='utf-8')
    
    # Copy any local assets
    full_content = source.read_text(encoding='utf-8')
    assets = find_local_assets(source, full_content)
    for ref, asset_path in assets:
        asset_dest = dest_path.parent / ref
        asset_dest.parent.mkdir(parents=True, exist_ok=True)
        if not dry_run:
            shutil.copy2(asset_path, asset_dest)
        print(f"    + asset: {ref}")
    
    return True


def main():
    import sys
    dry_run = '--dry-run' in sys.argv
    
    print(f"Portfolio Sync")
    print(f"  Source: {CODE_DIR}")
    print(f"  Target: {PORTFOLIO_DOCS_DIR}")
    if dry_run:
        print(f"  Mode: DRY RUN (no files will be modified)")
    print()
    
    print("Scanning for portfolio files...")
    files = find_portfolio_files(CODE_DIR)
    
    if not files:
        print("No files with 'portfolio:' frontmatter found.")
        return
    
    print(f"Found {len(files)} file(s) to sync:\n")
    
    synced = 0
    for source, frontmatter, body in files:
        if sync_file(source, frontmatter, body, dry_run):
            synced += 1
        print()
    
    print(f"Done! Synced {synced}/{len(files)} files.")
    if not dry_run:
        print(f"\nRun 'mkdocs serve' in {PORTFOLIO_DOCS_DIR.parent} to preview.")


if __name__ == '__main__':
    main()
