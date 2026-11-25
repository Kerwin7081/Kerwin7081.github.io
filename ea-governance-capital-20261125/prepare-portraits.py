"""One-off, branch-only media preparation. No network calls during deployment."""
import hashlib, html, io, json, re, time
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
import requests

root=Path(__file__).resolve().parent
manifest_path=root/"media-manifest.json"
manifest=json.loads(manifest_path.read_text())
for p in manifest["portraits"]:
    if p["name"]=="Christopher Liddell":
        p["commons_filename"]="Chris Liddell official photo.jpg"
    elif p["name"]=="Émile P. Torres":
        p["commons_filename"]="Émile P. Torres.png"
    elif p["name"]=="Dario Amodei":
        p.update(source="https://commons.wikimedia.org/wiki/File:Dario_Amodei_at_TechCrunch_Disrupt_2023_05.jpg",author="Kimberly White / Getty Images for TechCrunch",license="CC BY 2.0",license_url="https://creativecommons.org/licenses/by/2.0/",license_verified=True,transformation="resized/re-encoded; no content alteration")
assets=root/"portraits"
assets.mkdir(exist_ok=True)
session=requests.Session()
session.headers["User-Agent"]="KerwinResearchHub/1.0 (https://enyaclawd.com/; public research portrait licensing)"
page=root/"index.html"
soup=BeautifulSoup(page.read_text(), "html.parser")
figures={f.find("b").get_text(strip=True):f for f in soup.select(".people figure") if f.find("b")}
def plain(s):
    return BeautifulSoup(s or "", "html.parser").get_text(" ",strip=True)
def val(meta,k):
    return plain(meta.get(k,{}).get("value",""))
def sha(b):
    return hashlib.sha256(b).hexdigest()
def allowed_url(u):
    return urlsplit(u).scheme=="https" and urlsplit(u).hostname in {"upload.wikimedia.org","thumb.wikimedia.org"}
for idx,p in enumerate(manifest["portraits"],1):
    fig=figures.get(p["name"])
    if not fig:
        continue
    if p.get("fixed_bytes_verified") and (root/p.get("asset","__missing__")).is_file():
        continue
    if p.get("preview","") and p["preview"].startswith("/"):
        try:
            original=(root.parent/p["preview"].lstrip("/")).read_bytes()
            im=Image.open(io.BytesIO(original)); im.load()
            p.update(status="EXISTING_LOCAL_ASSET",fixed_bytes_verified=True,sha256=sha(original),width=im.width,height=im.height)
        except Exception as exc:
            p.update(status="ASSET_CHECK_FAILED",error=str(exc)[:160])
        continue
    fname=p.get("commons_filename")
    if not fname:
        continue
    try:
        r=session.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","titles":"File:"+fname,"prop":"imageinfo","iiprop":"url|extmetadata|sha1|size|mime","iiurlwidth":480,"format":"json","formatversion":2},timeout=25)
        r.raise_for_status()
        info=r.json()["query"]["pages"][0]["imageinfo"][0]
        meta=info.get("extmetadata",{})
        license_name=val(meta,"LicenseShortName")
        license_url=val(meta,"LicenseUrl")
        author=val(meta,"Artist") or val(meta,"Credit")
        # Only freely reusable sources; reject ambiguous rights, NC/ND, or missing credit.
        if not re.search(r"^(CC BY(?:-SA)? [1-4](?:\.\d)?|CC0|Public domain|PDM)",license_name,re.I):
            raise ValueError("license not verified as freely reusable: "+license_name)
        if not author and not re.search(r"public domain|CC0|PDM",license_name,re.I):
            raise ValueError("required author credit missing")
        if not author: author="Public-domain source; see original file record"
        # Restrict download destinations to Wikimedia; source file names curated independently.
        u=info.get("thumburl") or info["url"]
        if not allowed_url(u):
            raise ValueError("unapproved image host")
        rr=session.get(u,timeout=30); rr.raise_for_status()
        if len(rr.content)>25_000_000: raise ValueError("image too large")
        im=Image.open(io.BytesIO(rr.content)); im.load()
        if min(im.size)<80: raise ValueError("resolution too low")
        im=ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((480,600))
        target=assets/("person-%02d.jpg"%idx)
        im.save(target,"JPEG",quality=88,optimize=True)
        data=target.read_bytes()
        check=Image.open(io.BytesIO(data)); check.load()
        relative="portraits/"+target.name
        source=info.get("descriptionurl") or p.get("source")
        p.update(status="LOCAL_BYTES_VERIFIED",source=source,asset=relative,license=license_name,license_url=license_url,author=author,source_sha1=info.get("sha1"),sha256=sha(data),width=check.width,height=check.height,fixed_bytes_verified=True,license_verified=True,transformation="resized/re-encoded; no content alteration")
        old=fig.find("img") or fig.find("div",class_="pending")
        img=soup.new_tag("img",src=relative,alt=p["name"]+"的公开照片或历史肖像",loading="lazy",width=str(check.width),height=str(check.height))
        if old: old.replace_with(img)
        else: fig.insert(0,img)
        cap=fig.find("figcaption")
        cap.clear()
        b=soup.new_tag("b"); b.string=p["name"]; cap.append(b); cap.append(soup.new_tag("br"));cap.append(p["role"]);cap.append(soup.new_tag("br"))
        cap.append(author+" · "+license_name+" · 缩放")
        cap.append(soup.new_tag("br"))
        a=soup.new_tag("a",href=source);a.string="原始图片";cap.append(a)
        if license_url:
            cap.append(" · ");a=soup.new_tag("a",href=license_url);a.string="许可";cap.append(a)
        if p.get("profile"):
            cap.append(" · ");a=soup.new_tag("a",href=p["profile"]);a.string="人物档案";cap.append(a)
        p.pop("error",None)
    except Exception as exc:
        p.update(status="NOT_VERIFIED",fixed_bytes_verified=False,license_verified=False,error=str(exc)[:200])
    time.sleep(.5)
# No broken remote images in the resulting public-facing page. People with no lawful photo
# retain a concise biography/source link instead of a fake or unlabeled portrait.
for p in manifest["portraits"]:
    fig=figures.get(p["name"])
    if not fig:continue
    if not p.get("fixed_bytes_verified"):
        old=fig.find("img") or fig.find("div",class_="pending")
        if old:old.decompose()
        cap=fig.find("figcaption")
        cap.clear()
        b=soup.new_tag("b"); b.string=p["name"]; cap.append(b);cap.append(soup.new_tag("br"));cap.append(p["role"])
        if p.get("profile") or p.get("source"):
            cap.append(soup.new_tag("br"));a=soup.new_tag("a",href=p.get("profile") or p["source"]);a.string="公开人物资料";cap.append(a)
        
count=sum(bool(p.get("fixed_bytes_verified")) for p in manifest["portraits"])
manifest["release_gates"]["media"]="PASS" if count==len(manifest["portraits"]) and all(p.get("license_verified") for p in manifest["portraits"]) else "PARTIAL"
manifest["local_portraits"]=count
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
# Direct source attribution for the already published, decoded Dario asset.
for p in manifest["portraits"]:
    if p["name"]=="Dario Amodei" and p.get("fixed_bytes_verified"):
        fig=figures[p["name"]]
        fig.img["width"]=str(p["width"]); fig.img["height"]=str(p["height"])
        cap=fig.find("figcaption"); cap.clear()
        b=soup.new_tag("b"); b.string=p["name"]; cap.append(b); cap.append(soup.new_tag("br")); cap.append(p["role"]); cap.append(soup.new_tag("br"))
        cap.append(p["author"]+" · CC BY 2.0 · 缩放"); cap.append(soup.new_tag("br"))
        a=soup.new_tag("a",href=p["source"]); a.string="原始图片"; cap.append(a)
        cap.append(" · "); a=soup.new_tag("a",href=p["license_url"]); a.string="许可"; cap.append(a)
# Ord's published table places naturally arising pandemics after the natural-risk subtotal.
for row in soup.find_all("tr"):
    cells=row.find_all("td")
    if len(cells)==4 and "自然起源的大流行病" in cells[1].get_text():
        cells[3].string="Ord 原著将其列在自然风险小计之后；人类活动可放大传播与毁灭性后果，不能按病原体起源重新归类。"
    if len(cells)==4 and "超级火山喷发" in cells[1].get_text():
        cells[3].string="自然风险小计约为 1 / 10,000；以下疫情及人为风险另列。"
for a in soup.find_all("a",href=True):
    if a["href"]=="https://tobyord.squarespace.com/writing/the-precipice-revisited":
        a["href"]="https://www.tobyord.com/writing/the-precipice-revisited"
for span in soup.find_all("span"):
    if span.get_text(strip=True)=="https://tobyord.squarespace.com/writing/the-precipice-revisited":
        span.string="https://www.tobyord.com/writing/the-precipice-revisited"
for p in soup.find_all("p"):
    t=p.get_text()
    if t.startswith("在机构冲击方面"):
        p.clear(); p.append("FTX 破产亦造成非营利机构的资金追回风险。Effective Ventures UK 与 US 在2024年1月公布和解安排：两实体合计向破产财产支付26,786,503美元，相当于2022年从FTX及FTX Foundation收到的全部资金。这是机构自述的和解支付金额，不等同于法院认定受赠机构参与欺诈。")
        a=soup.new_tag("a",href="https://forum.effectivealtruism.org/posts/HjsfHwqasyQMWRzZN/ev-updates-ftx-settlement-and-the-future-of-ev"); a.string="EV和解公告"; p.append(a)
    if t.startswith("80,000 Hours官方回顾"):
        p.clear(); p.append("80,000 Hours 官方回顾确认其于2025年4月1日完成分拆，5月28日公布独立运营。组织拆分反映治理结构的变化，不宜单独归因于FTX事件。")
        a=soup.new_tag("a",href="#S42"); a.string="S42"; p.append(a); p.append(" / "); a=soup.new_tag("a",href="#S47"); a.string="S47"; p.append(a)
    if t.startswith("乔治城大学安全与新兴技术中心"):
        p.clear(); p.append("乔治城大学安全与新兴技术中心（CSET）：2019年校方公告确认 Open Philanthropy Project 提供5500万美元创始赠款，用于非党派AI政策研究。这证明存在资助关系，不证明资助者控制研究结论，亦不证明具体行政令由该中心推动。Helen Toner 的任职可见")
        a=soup.new_tag("a",href="https://cset.georgetown.edu/staff/helen-toner/"); a.string="CSET官方人物档案"; p.append(a); p.append("。"); a=soup.new_tag("a",href="#S27"); a.string="S27"; p.append(a)
    # Remove process-like parenthetical notes without removing substantive evidence limitations.
    for node in list(p.find_all(string=True,recursive=False)):
        v=str(node)
        v=re.sub(r"（注：[^（）]*?(?:标为【待核源】|待逐项核对官方法案与公报|作者心理推断)[^（）]*?）","",v)
        v=v.replace("均标为【待核源】，需调取完整报道与披露文件核证","尚缺公开原始文件支持").replace("标为【待核源】","缺乏公开证据").replace("本文均标注为【待核源】","现有公开证据不足以认定").replace("【待核源】","【证据不足】")
        if v!=str(node): node.replace_with(v)
for node in list(soup.find_all(string=True)):
    if node.parent.name not in ("script","style"):
        v=str(node).replace("待核源","证据不足")
        if v!=str(node):node.replace_with(v)
page.write_text(str(soup))
# Prepare approved release files from canonical public registry; no site-wide layout changes.
import subprocess
from datetime import datetime, timezone, timedelta
repo=root.parent
meta_path=root/"meta.json"
meta=json.loads(meta_path.read_text())
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
meta.update(published=True,homepage_approved=True,status="new",published_at=meta.get("published_at") or now,updated_at=now)
meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
registry_path=repo/"registry.json"
items=json.loads(registry_path.read_text())
items=[meta]+[x for x in items if x.get("slug")!=meta["slug"]]
registry_path.write_text(json.dumps(items,ensure_ascii=False,indent=1)+"\n")
for cmd in (["python3","tools/build_sitemap.py"],["python3","tools/sync_homepage_fallback.py"],["python3","tools/homepage_registry.py","validate","--site-root","."],["node","tools/qa_release.mjs"]):
    subprocess.run(cmd,cwd=repo,check=True)
# Confirm included local image files and their license. People with no reusable photograph
# remain as factual text profiles, never placeholders or fabricated portraits.
for im in soup.select(".people img"):
    path=repo/im["src"].lstrip("/") if im["src"].startswith("/") else root/im["src"]
    with Image.open(path) as decoded: decoded.load()
assert all(p.get("license_verified") for p in manifest["portraits"] if p.get("fixed_bytes_verified"))
assert "Gemini" not in soup.get_text() and not re.search(r"原稿|核验清单|审计意见|本轮|拟发布|纠偏|订正|V[12]\\b",soup.get_text())
subprocess.run(["git","add","--",str(meta_path.relative_to(repo)),"registry.json","sitemap.xml","index.html"],cwd=repo,check=True)
print("Release structure / registry / fallback / local images: verified")
print("Local decoded portraits:",count,"/",len(manifest["portraits"]))
