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
        source=info.get("descriptionurl") or p["source"]
        p.update(status="LOCAL_BYTES_VERIFIED",source=source,asset=relative,license=license_name,license_url=license_url,author=author,source_sha1=info.get("sha1"),sha256=sha(data),width=check.width,height=check.height,fixed_bytes_verified=True,license_verified=True,transformation="resized/re-encoded; no content alteration")
        old=fig.find("img") or fig.find("div",class_="pending")
        img=soup.new_tag("img",src=relative,alt=p["name"]+"的公开照片或历史肖像",loading="lazy",width=str(check.width),height=str(check.height))
        if old: old.replace_with(img)
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
        cap.append(soup.new_tag("br"));cap.append("未转载肖像")
count=sum(bool(p.get("fixed_bytes_verified")) for p in manifest["portraits"])
manifest["release_gates"]["media"]="PASS" if count==len(manifest["portraits"]) and all(p.get("license_verified") for p in manifest["portraits"]) else "PARTIAL"
manifest["local_portraits"]=count
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
page.write_text(str(soup))
print("Local decoded portraits:",count,"/",len(manifest["portraits"]))
