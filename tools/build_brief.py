#!/usr/bin/env python3
"""Build a standalone, client-facing web deck from a Slides-artifact project folder.

Usage: python3 tools/build_brief.py <project_dir> <img_dir> <blobmap.json> <out_dir>
  project_dir : folder holding deck.json and slides/<id>.html
  img_dir     : folder holding the image files referenced in blobmap.json
  blobmap.json: {"<blob id>": "<image file name>"}
  out_dir     : e.g. briefs/2026-10  (index.html + img/ are written here)

Speaker notes (<aside>) are removed: the public page is client-facing.
"""
import json, re, shutil, sys, html
from pathlib import Path

proj, imgdir, blobmap, out = map(Path, sys.argv[1:5])
deck = json.loads((proj / "deck.json").read_text())
bm = json.loads(blobmap.read_text())
(out / "img").mkdir(parents=True, exist_ok=True)

slides = []
for sid in deck["order"]:
    s = (proj / "slides" / f"{sid}.html").read_text()
    s = re.sub(r"<aside>.*?</aside>", "", s, flags=re.S)
    def blob(m):
        f = bm[m.group(1)]
        shutil.copy(imgdir / f, out / "img" / f)
        return f"img/{f}"
    s = re.sub(r"/_blob/([0-9a-f]{32})", blob, s)
    s = s.replace("<a href=", '<a target="_blank" rel="noopener" href=')
    slides.append(s)

fonts = "".join(f'<link rel="stylesheet" href="{f["href"]}">' for f in deck["faces"].values())
title = html.escape(deck["title"])
page = f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{fonts}
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;background:#0B1B2E;overflow:hidden}}
#stage{{position:fixed;inset:0;display:flex;align-items:center;justify-content:center}}
#deck{{position:relative;width:1920px;height:1080px;transform-origin:center center;flex:none}}
#deck>section{{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;opacity:0;pointer-events:none;transition:opacity .35s}}
#deck>section.on{{opacity:1;pointer-events:auto}}
section h1,section h2,section h3,section p{{margin:0}}
section img{{display:block}}
section a{{color:inherit}}
section hr{{border:0;height:0}}
section table{{width:100%;border-collapse:collapse;border-radius:12px;overflow:hidden}}
section th{{background:#00396B;color:#F4F2EE;font-weight:600;padding:18px 24px}}
section td{{padding:18px 24px;border-bottom:1px solid #E1E6EC}}
#bar{{position:fixed;left:0;right:0;bottom:0;display:flex;justify-content:space-between;align-items:center;padding:10px 18px;font:14px/1 'IBM Plex Sans Thai',sans-serif;color:#B9CBE0;background:linear-gradient(transparent,rgba(0,0,0,.45));opacity:.0;transition:opacity .3s}}
body:hover #bar{{opacity:1}}
#bar button{{background:rgba(255,255,255,.12);color:#fff;border:0;border-radius:6px;padding:8px 14px;font:inherit;cursor:pointer;margin-left:6px}}
@media print{{
  @page{{size:1920px 1080px;margin:0}}
  html,body{{overflow:visible;background:#fff}}
  #stage{{position:static;display:block}} #deck{{transform:none!important;width:auto;height:auto}}
  #deck>section{{position:relative;opacity:1;page-break-after:always;break-after:page}}
  #bar{{display:none}}
}}
</style></head><body>
<div id="stage"><div id="deck">
{''.join(slides)}
</div></div>
<div id="bar"><span id="count"></span><span><button onclick="go(-1)">‹ ก่อนหน้า</button><button onclick="go(1)">ถัดไป ›</button><button onclick="fs()">เต็มจอ</button><button onclick="window.print()">PDF</button></span></div>
<script>
const S=[...document.querySelectorAll('#deck>section')];let i=0;
function fit(){{const d=document.getElementById('deck');const k=Math.min(innerWidth/1920,innerHeight/1080);d.style.transform='scale('+k+')';}}
function show(n){{i=Math.max(0,Math.min(S.length-1,n));S.forEach((s,j)=>s.classList.toggle('on',j===i));document.getElementById('count').textContent=(i+1)+' / '+S.length;try{{history.replaceState(null,'','#'+(i+1))}}catch(e){{}}}}
function go(d){{show(i+d)}}
function fs(){{document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen()}}
addEventListener('keydown',e=>{{if(['ArrowRight','PageDown',' '].includes(e.key)){{e.preventDefault();go(1)}}if(['ArrowLeft','PageUp'].includes(e.key)){{e.preventDefault();go(-1)}}if(e.key==='f')fs();}});
let x0=null;addEventListener('touchstart',e=>x0=e.touches[0].clientX);addEventListener('touchend',e=>{{if(x0===null)return;const dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>50)go(dx<0?1:-1);x0=null}});
addEventListener('hashchange',()=>{{const n=(parseInt(location.hash.slice(1))||1)-1;if(n!==i)show(n)}});
addEventListener('resize',fit);fit();show((parseInt(location.hash.slice(1))||1)-1);
</script></body></html>"""
(out / "index.html").write_text(page)
print("wrote", out / "index.html", len(slides), "slides")
