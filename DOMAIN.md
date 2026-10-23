# DOMAIN.md: pointing nibbables.com at GitHub Pages (and redirecting nibbable.com)

Status on 2026-10-23: **nothing has been changed.** Both domains are still on Namecheap's default records. The site is live at https://yairsz.github.io/nibbables/. `site.json` holds `"cname_pending": "nibbables.com"`, so no CNAME file is published yet and the github.io URL keeps working.

## Current DNS (read-only check via dns.google, 2026-10-23)
| Domain | Record | Value |
|---|---|---|
| nibbables.com | NS | dns1.registrar-servers.com, dns2.registrar-servers.com (Namecheap BasicDNS) |
| nibbables.com | A @ | 192.64.119.177 (Namecheap parking) |
| nibbables.com | CNAME www | parkingpage.namecheap.com |
| nibbables.com | MX @ | eforward1–5.registrar-servers.com (priorities 10, 10, 10, 15, 20) (Namecheap email forwarding) |
| nibbables.com | TXT @ | `v=spf1 include:spf.efwd.registrar-servers.com ~all` |
| nibbables.com | TXT @ | `google-site-verification=sZR0Q0aNJTJ04XN0E1Z-yyS_fR_4BW1FPFo5bO9jV48` |
| nibbable.com | A @ | 162.255.119.180 (Namecheap parking) |
| nibbable.com | CNAME www | parkingpage.namecheap.com |
| nibbable.com | MX / TXT | same email-forwarding MX and SPF as above |

## Part 1: nibbables.com → GitHub Pages (Yair does this in Namecheap)
Namecheap → Domain List → nibbables.com → **Manage** → **Advanced DNS**.

1. Under **Host Records**, **delete** the parking records: whatever sits on `@` (it shows as a parking "URL Redirect Record @" or an `A Record @`. It currently resolves to 192.64.119.177. A URL Redirect Record adds a hidden A record that only goes away when you delete the redirect record itself). Also check the **Domain** tab → **Redirect Domain** for a bare-domain entry and remove it and the `CNAME www → parkingpage.namecheap.com`.
2. **Add** these records (TTL Automatic):

| Type | Host | Value |
|---|---|---|
| A Record | @ | 185.199.108.153 |
| A Record | @ | 185.199.109.153 |
| A Record | @ | 185.199.110.153 |
| A Record | @ | 185.199.111.153 |
| AAAA Record | @ | 2606:50c0:8000::153 |
| AAAA Record | @ | 2606:50c0:8001::153 |
| AAAA Record | @ | 2606:50c0:8002::153 |
| AAAA Record | @ | 2606:50c0:8003::153 |
| CNAME Record | www | yairsz.github.io. |

3. **Keep email working.** Leave the **Mail Settings** section set to **Email Forwarding** (that's what creates the eforward1–5 MX records). Keep the TXT records `v=spf1 include:spf.efwd.registrar-servers.com ~all` and `google-site-verification=sZR0Q0aNJTJ04XN0E1Z-yyS_fR_4BW1FPFo5bO9jV48`. Don't delete any MX or TXT record.
4. Wait for DNS to propagate (usually minutes, up to a few hours). Check:
   ```
   curl -s "https://dns.google/resolve?name=nibbables.com&type=A"   | python3 -m json.tool   # expect the four 185.199.x.153
   curl -s "https://dns.google/resolve?name=www.nibbables.com&type=CNAME" | python3 -m json.tool  # expect yairsz.github.io.
   curl -s "https://dns.google/resolve?name=nibbables.com&type=MX"  | python3 -m json.tool   # expect eforward1-5 still there
   ```

## Part 2: switch the site to the domain (agent can do this after DNS resolves and Yair approves)
1. In `site.json`, rename `cname_pending` → `cname` and set `"base_url": "https://nibbables.com"`.
2. Commit, push, and run `./publish.sh`. This publishes a `CNAME` file containing `nibbables.com`.
3. Set the Pages custom domain: `gh api -X PUT repos/yairsz/nibbables/pages -f cname=nibbables.com` (or repo **Settings → Pages → Custom domain**).
4. Once GitHub has issued the certificate (can take up to about an hour), enforce HTTPS: `gh api -X PUT repos/yairsz/nibbables/pages -F https_enforced=true` (or tick **Enforce HTTPS**).
5. Verify: `curl -sI https://nibbables.com/` → 200, `curl -sI https://www.nibbables.com/` → 301 to the apex, and `curl -sI https://yairsz.github.io/nibbables/` → 301 to nibbables.com.
6. Optional: add the domain in Google Search Console (the existing google-site-verification TXT may already verify it) and submit `https://nibbables.com/sitemap.xml`.
7. Optional hardening: verify the domain for the yairsz account (GitHub **Settings → Pages → Verified domains**) to stop domain takeover. It adds one TXT record `_github-pages-challenge-yairsz` with the value GitHub shows.

## Part 3: 301-redirect nibbable.com → nibbables.com (Yair does this in Namecheap)
Namecheap → Domain List → nibbable.com → **Manage** → **Advanced DNS** → **Host Records**:

1. Delete the parking `A Record @ → 162.255.119.180` and the `CNAME www → parkingpage.namecheap.com`.
2. Add two **URL Redirect Records**:

| Type | Host | Value | Redirect type |
|---|---|---|---|
| URL Redirect Record | @ | https://nibbables.com/ | **Permanent (301)** |
| URL Redirect Record | www | https://nibbables.com/ | **Permanent (301)** |

3. **Path preservation:** keep the trailing `/` on the destination (`https://nibbables.com/`). Namecheap's own guide says a destination ending in `/` passes the path through (`nibbable.com/antlers/` → `https://nibbables.com/antlers/`), and one without it sends everything to the home page (https://www.namecheap.com/support/knowledgebase/article.aspx/385/2237/how-to-set-up-a-url-redirect-for-a-domain/). The "wildcard" redirect (Host `*`) is only for subdomains such as `blog.nibbable.com`. It's optional and not needed here. After saving (it can take about 30 minutes), test: `curl -sI http://nibbable.com/antlers/` should show `301` and `Location: https://nibbables.com/antlers/`.
4. **HTTPS caveat:** Namecheap's URL redirect is served over plain HTTP. `https://nibbable.com` may show a certificate warning because Namecheap doesn't issue certificates for redirect-only domains. If that matters later, the alternatives are a second tiny GitHub Pages repo for nibbable.com with a redirect page (that would be a meta-refresh, not a true 301) or moving nibbable.com's DNS to Cloudflare and using a redirect rule (a true 301 with HTTPS). Both need Yair's approval.
5. Keep **Mail Settings → Email Forwarding** and the SPF TXT record as they are, so email to @nibbable.com keeps forwarding.
