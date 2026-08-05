from pathlib import Path
import json

PAGE = Path('innolight-global-optical-interconnect-panorama-20260801/index.html')
META = Path('innolight-global-optical-interconnect-panorama-20260801/meta.json')
MARKER = '/* MOBILE-REBUILD-20260805 */'

html = PAGE.read_text(encoding='utf-8')
html = html.replace(
    '<meta name="viewport" content="width=device-width,initial-scale=1">',
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
)
html = html.replace(
    '<meta name="article:modified_time" content="2026-08-01T20:18:00+08:00">',
    '<meta name="article:modified_time" content="2026-08-05T10:58:00+08:00">'
)
html = html.replace(
    '中际旭创提供了观察AI光互联商业化的最佳入口，但完整判断必须继续向上游光源与材料、横向硅光制造与先进封装、向下游光学I/O和系统协议延伸。NVIDIA、美国政府与马斯克的动作，分别对应技术路线、国家备份供应链和私营算力体系垂直整合。',
    '中际旭创是观察AI光互联商业化的最佳入口。完整判断还需向上游光源与材料、硅光制造与先进封装、光学I/O和系统协议延伸，并把NVIDIA、美国政策与马斯克的供应链布局放在同一张图中。'
)
html = html.replace(
    "setTimeout(()=>key.focus(),80);",
    "if(matchMedia('(min-width:761px) and (pointer:fine)').matches)setTimeout(()=>key.focus(),80);"
)

mobile_css = r'''
/* MOBILE-REBUILD-20260805 */
html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
img,svg,video{max-width:100%;height:auto}
@media(max-width:760px){
  body{font-size:16px;line-height:1.8}
  .kw-editorial-gate{display:flex;align-items:center;justify-content:center;padding:max(12px,env(safe-area-inset-top)) 12px max(12px,env(safe-area-inset-bottom));overflow:hidden}
  .gate-paper{width:min(100%,420px);max-width:100%;max-height:calc(100svh - 24px);overflow:auto;border-top-width:4px}
  .gate-head{display:block;padding:10px 16px;font-size:9px;line-height:1.45;white-space:normal;overflow-wrap:anywhere}
  .gate-head span:last-child{display:none}
  .gate-body{grid-template-columns:72px minmax(0,1fr);gap:16px;align-items:start;min-height:0;padding:24px 18px 20px}
  .gate-body>*{min-width:0}
  .gate-seal{width:72px;font-size:13px;line-height:1.15}
  .gate-kicker{font-size:9px;letter-spacing:.12em}
  .gate-title{max-width:100%;margin-top:7px;font-size:clamp(23px,7vw,29px);line-height:1.14;letter-spacing:-.015em;overflow-wrap:anywhere}
  .gate-copy{margin:10px 0 13px;font-size:14px;line-height:1.55}
  .gate-field{min-height:44px;gap:0}
  .gate-field input{width:100%;height:42px;padding:0;font-size:23px}
  .gate-field span{display:none}
  .gate-foot{display:block;padding:10px 16px;font-size:10px;line-height:1.5;overflow-wrap:anywhere}
  .gate-foot span:last-child{display:none}
  .site-shell{width:100%;margin:0;box-shadow:none}
  .topbar{padding:8px 20px;font-size:9px}
  .topbar span:last-child{display:none}
  .masthead{grid-template-columns:minmax(0,1fr) auto;gap:14px;padding:12px 20px}
  .masthead>*{min-width:0}
  .nav{display:none}
  .brand{font-size:23px}
  .brand small{margin-top:5px;font-size:8px}
  .home{font-size:12px;white-space:nowrap}
  .cover{padding:27px 20px 24px}
  .cover-grid{grid-template-columns:1fr;gap:16px}
  .eyebrow{margin-bottom:12px;font-size:9px;line-height:1.5;letter-spacing:.12em}
  .cover h1{font-size:clamp(24px,7vw,28px);line-height:1.18;letter-spacing:-.012em;overflow-wrap:anywhere}
  .cover h1 span{margin-top:12px;font-size:clamp(18px,5.2vw,21px);line-height:1.34}
  .thesis{margin-top:17px;font-size:16px;line-height:1.72}
  .cover-meta{display:grid;grid-template-columns:1fr 1fr;gap:7px 12px;margin-top:20px;padding-top:14px;font-size:11px;line-height:1.55}
  .cover-meta span:last-child{grid-column:1/-1}
  .cover-seal{display:none}
  .scope{padding:14px 20px;font-size:12px;line-height:1.7}
  .section,.enya{padding:30px 20px}
  .section h2{font-size:clamp(23px,6.4vw,26px);line-height:1.25}
  .section h3{margin-top:24px;font-size:19px}
  .lead{font-size:16px;line-height:1.72}
  .two,.three,.related{grid-template-columns:1fr}
  .verdict,.metrics,.capital,.policy,.watch,.flow{grid-template-columns:1fr}
  .verdict>div{border-right:0;border-bottom:1px solid var(--line)}
  .flow>div{min-height:0;border-right:0;border-bottom:1px solid var(--line)}
  .flow>div:last-child{border-bottom:0}
  .related a{border-right:0;border-bottom:1px solid var(--line)}
  .related a:last-child{border-bottom:0}
  .roles{grid-template-columns:1fr}
  .footer{padding:20px}
  .footer-line{display:block}
  .footer-line>div:last-child{margin-top:10px}
  .table-wrap{max-width:100%;-webkit-overflow-scrolling:touch}
  .tools,.tabs{overflow-x:auto;flex-wrap:nowrap;padding-bottom:4px}
  .tools button,.tabs button{flex:0 0 auto;min-height:40px}
}
@media(max-width:520px){
  .chain-row{grid-template-columns:1fr}
  .level{min-height:42px;padding:10px 13px}
  .function{padding:13px}
  .companies{grid-column:auto;padding:11px 13px}
  .cover-meta{grid-template-columns:1fr}
  .cover-meta span:last-child{grid-column:auto}
  .policy>div{padding:18px}
  .dark{padding:21px}
}
@media(max-width:360px){
  .kw-editorial-gate{padding:8px}
  .gate-paper{max-height:calc(100svh - 16px)}
  .gate-body{grid-template-columns:60px minmax(0,1fr);gap:13px;padding:20px 15px 17px}
  .gate-seal{width:60px;font-size:11px}
  .gate-title{font-size:22px}
  .cover,.section,.enya{padding-left:17px;padding-right:17px}
  .masthead{padding-left:17px;padding-right:17px}
  .brand{font-size:21px}
  .home{font-size:11px}
}
'''

if MARKER not in html:
    html = html.replace('</style>', mobile_css + '\n</style>', 1)
else:
    raise SystemExit('mobile patch marker already present')

PAGE.write_text(html, encoding='utf-8')

meta = json.loads(META.read_text(encoding='utf-8'))
meta['updated_at'] = '2026-08-05T10:58:00+08:00'
meta['typography_variant'] = 'mobile-editorial-v2'
meta['typography_variant_reason'] = 'Kerwin mobile screenshots showed gate overflow, excessive cover scale and in-app-browser text inflation; rebuilt the 360–760px layout and disabled mobile autofocus.'
meta['typography_approved_by'] = 'Kerwin'
meta['mobile_qa'] = ['360x800', '390x844', '760px breakpoint', 'no horizontal overflow']
META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('patched', PAGE)
print('patched', META)
