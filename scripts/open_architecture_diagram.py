#!/usr/bin/env python3
"""
Generate system architecture diagram from DOT file
This script opens the DOT file in default browser using online Graphviz renderer
Author: Nguyễn Văn Đạt
"""
import webbrowser
import urllib.parse
from pathlib import Path

def main():
    dot_file = Path(__file__).parent.parent / 'docs' / 'system_architecture.dot'
    
    print("=" * 70)
    print("System Architecture Diagram Generator")
    print("=" * 70)
    
    if not dot_file.exists():
        print(f"✗ DOT file not found: {dot_file}")
        return
    
    # Read DOT content
    with open(dot_file, 'r', encoding='utf-8') as f:
        dot_content = f.read()
    
    # Encode for URL
    encoded = urllib.parse.quote(dot_content)
    
    # Online Graphviz editors
    urls = [
        f"https://dreampuf.github.io/GraphvizOnline/#{encoded}",
        f"https://edotor.net/?engine=dot#{encoded}",
    ]
    
    print(f"\n✓ DOT file loaded: {dot_file}")
    print(f"  Lines: {len(dot_content.splitlines())}")
    print(f"  Size: {len(dot_content)} bytes")
    
    print("\nOpening in browser...")
    print("Choose an editor:")
    print("  1. GraphvizOnline (recommended)")
    print("  2. Edotor.net")
    
    # Open first URL
    webbrowser.open(urls[0])
    print(f"\n✓ Opened: {urls[0][:60]}...")
    
    print("\nInstructions:")
    print("  1. Wait for diagram to render")
    print("  2. Click 'Export' → 'SVG' to download")
    print("  3. Save as 'system_architecture.svg'")
    print("  4. Copy to: sphinx-docs/source/_static/diagrams/")
    
    print("\n" + "=" * 70)
    
    # Save short URL for manual use
    short_url_file = dot_file.parent / 'system_architecture_url.txt'
    with open(short_url_file, 'w') as f:
        f.write(f"GraphvizOnline: {urls[0]}\n")
        f.write(f"Edotor: {urls[1]}\n")
    
    print(f"URLs saved to: {short_url_file}")

if __name__ == '__main__':
    main()
