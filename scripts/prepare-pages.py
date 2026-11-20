#!/usr/bin/env python3
"""Split a complete local build into two Cloudflare Pages Free deployments.

The gallery, thumbnails and medium images stay on the main site. Original PNGs
and large outfit WebPs live on the asset site, reached via static redirects.
No image request invokes a Function. dist/ stays complete for local previews.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-origin', required=True)
    args = parser.parse_args()
    origin = args.assets_origin.rstrip('/')
    url = urlsplit(origin)
    if url.scheme != 'https' or not url.netloc or url.path or url.query or url.fragment or url.username:
        parser.error('--assets-origin must be an HTTPS origin without a path')

    source = Path('dist')
    if not (source / 'index.html').is_file():
        parser.error('Run python build.py first')
    main_dir, assets_dir = Path('dist-pages'), Path('dist-originals')
    for directory in (main_dir, assets_dir):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir()

    for file in source.rglob('*'):
        if not file.is_file():
            continue
        relative = file.relative_to(source)
        target_dir = assets_dir if relative.parts[0] == 'o' or relative.parts[:2] in [('c', 'i'), ('a', 'i')] else main_dir
        target = target_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(file, target)
        except OSError:
            shutil.copy2(file, target)

    # Replace the linked file so dist/_headers remains suitable for local use.
    headers = (main_dir / '_headers').read_text()
    headers = headers.replace("img-src 'self'", f"img-src 'self' {origin}")
    headers = headers.replace("connect-src 'self'", f"connect-src 'self' {origin}")
    (main_dir / '_headers').unlink()
    (main_dir / '_headers').write_text(headers)
    redirects = main_dir / '_redirects'
    old_redirects = redirects.read_text() if redirects.exists() else ''
    if redirects.exists():
        redirects.unlink()
    redirects.write_text(old_redirects + ''.join(
        f'{path}/* {origin}{path}/:splat 302\n' for path in ['/o', '/c/i', '/a/i']))
    routes = main_dir / '_routes.json'
    if routes.exists():
        routes.unlink()
    routes.write_text(json.dumps({'version': 1, 'include': ['/api/proxy'], 'exclude': []}) + '\n')
    (assets_dir / '_headers').write_text(
        '/*\n'
        '  Access-Control-Allow-Origin: *\n'
        '  Cache-Control: public, max-age=31536000, immutable\n'
        '  X-Content-Type-Options: nosniff\n'
        '  X-Robots-Tag: noindex\n'
        '/o/*\n'
        '  Content-Disposition: attachment\n')
    (assets_dir / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')

    for directory in (main_dir, assets_dir):
        files = [file for file in directory.rglob('*') if file.is_file()]
        large = [str(file) for file in files if file.stat().st_size > 25 * 1024 * 1024]
        if len(files) > 20000 or large:
            raise SystemExit(f'{directory}: exceeds Pages Free limits ({len(files)} files; oversized: {large})')
        print(f'{directory}: {len(files):,} files; {sum(file.stat().st_size for file in files) / 1024**3:.2f} GiB')


if __name__ == '__main__':
    main()
