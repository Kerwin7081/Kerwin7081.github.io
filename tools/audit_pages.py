#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path('/opt/kerwin-agent/repos/site')
IGNORE = {'.git', '.github', 'publish'}


def iter_html_files():
    for path in ROOT.rglob('*.html'):
        rel = path.relative_to(ROOT)
        if any(part in IGNORE for part in rel.parts):
            continue
        yield path


def check_file(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    issues = []
    warns = []
    rel = path.relative_to(ROOT).as_posix()
    is_homepage = rel == 'index.html'
    is_redirect = 'http-equiv="refresh"' in text or "http-equiv='refresh'" in text

    if not is_homepage and '← 返回首页' not in text:
        issues.append('missing_back_button')
    if 'pv-counter data-page-slug=' not in text:
        issues.append('missing_pv_marker')
    if 'counter-num' not in text:
        issues.append('missing_counter_node')
    if 'enyaclawd-counter.kerwin-finance.workers.dev' not in text:
        issues.append('missing_counter_script')
    if not re.search(r'@media\s*\(max-width:\s*\d+px\)', text):
        issues.append('missing_mobile_media_query')
    has_topbar = any(k in text for k in ['topbar', 'top-header', 'masthead', 'brand-strip'])
    has_hero = any(k in text for k in ['hero', 'top-grid', 'brand-band'])
    has_780 = any(k in text for k in ['max-width:780px', 'max-width: 780px', 'width: min(780px'])
    has_700 = any(k in text for k in ['max-width:700px', 'max-width: 700px', 'max-width:680px', 'max-width: 680px'])

    if not is_homepage and not is_redirect and not has_topbar:
        warns.append('missing_topbar_keyword')
    if not is_homepage and not is_redirect and not has_hero:
        warns.append('missing_hero_keyword')
    if not is_homepage and not has_780:
        warns.append('missing_780_container')
    if not is_homepage and 'wrap' in text and not has_700:
        warns.append('missing_700_wrap')
    if re.search(r'font-size:\s*(1[6-9]|[2-9]\d)px', text) and not re.search(r'@media\s*\(max-width:\s*\d+px\)', text):
        warns.append('large_fixed_fonts_without_mobile_fallback')
    if '/-tmp/' in path.as_posix() or path.as_posix().endswith('-tmp/index.html'):
        warns.append('tmp_page_path')

    return {
        'path': str(path.relative_to(ROOT)),
        'issues': issues,
        'warnings': warns,
        'ok': not issues,
    }


def main():
    results = [check_file(p) for p in iter_html_files()]
    bad = [r for r in results if r['issues']]
    warn = [r for r in results if r['warnings']]
    summary = {
        'total_html': len(results),
        'with_issues': len(bad),
        'with_warnings': len(warn),
        'results': results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
