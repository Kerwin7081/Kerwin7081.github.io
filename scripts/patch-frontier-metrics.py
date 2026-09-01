from pathlib import Path

page = Path('frontier-model-economics-listed-labs-20260901/index.html')
fragment = Path('scripts/frontier-metrics-fragment.html')
s = page.read_text(encoding='utf-8')
start_marker = '<div class="dark-panel"><h3>除了 P/S，最值得一起看的四个简单指标</h3>'
end_marker = '<p>如果只能选两个指标做快速投资筛选'
start = s.find(start_marker)
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('Target markers not found')
replacement = fragment.read_text(encoding='utf-8')
s = s[:start] + replacement + s[end:]
page.write_text(s, encoding='utf-8')
print('Patched', page)
