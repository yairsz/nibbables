#!/usr/bin/env python3
"""Snapshot a source page for quote checking.
Usage: python3 scripts/snapshot.py <name> <url>
Writes research/pages/<name>.html and research/pages/<name>.txt. The .txt is the readable text (scripts/h2t.py)
followed by every text fragment in the raw HTML, including embedded Shopify JSON (body_html, tabs, FAQs), so
quotes that only appear in tabs or scripts can still be verified word for word."""
import sys, subprocess, re, html
from pathlib import Path
name, url = sys.argv[1], sys.argv[2]
d = Path(__file__).resolve().parent.parent / "research/pages"; d.mkdir(parents=True, exist_ok=True)
h_path, t_path = d / f"{name}.html", d / f"{name}.txt"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
code = subprocess.run(["curl", "-sL", "--compressed", "-o", str(h_path), "-w", "%{http_code}", url], capture_output=True, text=True).stdout
if code != "200":
    code = subprocess.run(["curl", "-sL", "--compressed", "-A", UA, "-o", str(h_path), "-w", "%{http_code}", url], capture_output=True, text=True).stdout
readable = subprocess.run([sys.executable, str(Path(__file__).parent / "h2t.py"), str(h_path)], capture_output=True, text=True).stdout
raw = h_path.read_text(errors="ignore")
raw = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), raw).replace("\\/", "/").replace("\\n", "\n").replace('\\"', '"')
raw = re.sub(r"<[^>]+>", " ", raw)
raw = re.sub(r"<[^>]+>", " ", html.unescape(raw))
raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
t_path.write_text(f"SOURCE: {url}\nHTTP: {code}\n\n{readable}\n\n=== raw page text (all text in the HTML, incl. embedded JSON) ===\n{raw}")
print(code, t_path.stat().st_size, name)
