"""Lightweight YouTube embeds (click-to-load, youtube-nocookie) + VideoObject JSON-LD.
Data: data/videos.json -> {"/page/path/": {"id","name","description","uploadDate","duration"}}"""
import json, html
from pathlib import Path

e = lambda s: html.escape(str(s), quote=True)
_F = Path(__file__).parent / "data" / "videos.json"
VIDEOS = json.loads(_F.read_text()) if _F.exists() else {}

YT_JS = """<script>document.querySelectorAll('.yt[data-id]').forEach(function(d){d.querySelector('button').addEventListener('click',function(){
var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+d.dataset.id+'?autoplay=1&playsinline=1&rel=0';
f.title=d.dataset.title;f.allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';f.allowFullscreen=true;d.innerHTML='';d.appendChild(f);});});</script>"""

def video_for(path):
    return VIDEOS.get(path)

def _transcript_html(v):
    t = v.get("transcript")
    if not t: return ""
    paras = "".join(f"<p>{e(x)}</p>" for x in t)
    return f'<details class="vtx"><summary>Read the video transcript</summary>{paras}</details>'

def embed(path, channel_url, channel_name):
    v = VIDEOS.get(path)
    if not v: return ""
    vid = v["id"]
    return f"""<section class="vid"><h2>Watch: {e(v['heading'])}</h2>
<div class="yt" data-id="{e(vid)}" data-title="{e(v['name'])}"><button type="button" aria-label="Play video: {e(v['name'])}">
<img src="https://i.ytimg.com/vi/{e(vid)}/hqdefault.jpg" alt="{e(v['name'])}" loading="lazy" decoding="async" width="480" height="360"><span class="ytplay" aria-hidden="true"></span></button></div>
<p class="meta">{e(v.get('caption', ''))} <a href="https://www.youtube.com/watch?v={e(vid)}" rel="noopener" target="_blank">Watch on YouTube</a> · <a href="{e(channel_url)}" rel="noopener" target="_blank">{e(channel_name)} on YouTube</a></p>{_transcript_html(v)}</section>
{YT_JS}"""

def _iso_dt(s):
    """Google wants uploadDate as a full ISO 8601 datetime with a timezone.
    Store the real YouTube publish time in videos.json (yt-dlp --print "%(timestamp)s");
    a bare date falls back to midnight US Eastern."""
    if "T" in s: return s
    import datetime, zoneinfo
    return datetime.datetime.fromisoformat(s).replace(tzinfo=zoneinfo.ZoneInfo("America/New_York")).isoformat()

def video_ld(path):
    v = VIDEOS.get(path)
    if not v: return None
    vid = v["id"]
    return {"@context": "https://schema.org", "@type": "VideoObject", "name": v["name"], "description": v["description"],
            "thumbnailUrl": [f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg", f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"],
            "uploadDate": _iso_dt(v["uploadDate"]), "duration": v["duration"],
            "embedUrl": f"https://www.youtube.com/embed/{vid}", "contentUrl": f"https://www.youtube.com/watch?v={vid}",
            **({"transcript": " ".join(v["transcript"])} if v.get("transcript") else {})}

YT_CSS = """
.vid{margin:20px 0}
.yt{position:relative;width:100%;max-width:300px;aspect-ratio:9/16;background:#000;border-radius:12px;overflow:hidden}
.yt button{all:unset;cursor:pointer;display:block;width:100%;height:100%;position:relative}
.yt img{width:100%;height:100%;object-fit:cover;display:block}
.yt iframe{width:100%;height:100%;border:0;display:block}
.ytplay{position:absolute;left:50%;top:50%;width:68px;height:48px;margin:-24px 0 0 -34px;background:#f00;border-radius:12px;opacity:.9}
.ytplay::after{content:"";position:absolute;left:27px;top:14px;border-style:solid;border-width:10px 0 10px 17px;border-color:transparent transparent transparent #fff}
.yt button:focus-visible{outline:3px solid #fff;outline-offset:-3px}
.vtx{margin-top:8px;max-width:640px}
.vtx summary{cursor:pointer;font-weight:600}
.vtx p{margin:6px 0}
"""
