"""Privacy policy page body (shared shape for ByeBulky and Nibbables).
Every statement here must match the site's real behavior. Re-check this file whenever you add a script,
embed, form, affiliate program or hosting change, and bump EFFECTIVE when the text changes.
Facts checked 2026-10-23: GA4 tag in <head> of every page; GA4 property settings via the Analytics Admin API
(event data retention TWO_MONTHS, Google signals DISABLED, no Google Ads links; account data-sharing settings on);
YouTube = click-to-load facade (thumbnail from i.ytimg.com, player from youtube-nocookie.com after a click);
no forms, accounts or email collection; hosted on GitHub Pages (no Cloudflare/CDN of our own)."""
import html
e = lambda s: html.escape(str(s), quote=True)

EFFECTIVE = "October 23, 2026"
OPERATOR = "2 Handed Coding, LLC"
CONTACT = "developer@2handedcoding.com"

def body(site, domain, ga_id, video_pages, affiliate_html, filter_note):
    """site: display name; video_pages: list of (label, href) for pages with an embedded video;
    affiliate_html: site-specific affiliate section (HTML, already escaped); filter_note: where the in-page filter is."""
    vids = ", ".join(f'<a href="{e(h)}">{e(l)}</a>' for l, h in video_pages) or "none right now"
    ga = ""
    if ga_id:
        ga = f"""<h2>Google Analytics</h2>
<p>Every page loads Google Analytics 4 (Google tag <code>gtag.js</code>, measurement ID <code>{e(ga_id)}</code>) from <code>www.googletagmanager.com</code>. We use it only to count visits and see which pages are useful. It's provided by Google LLC.</p>
<ul>
<li><strong>What it collects:</strong> the pages you view and the standard events Google Analytics records automatically (for example page views, scrolls and outbound link clicks), the page that referred you, your browser and device type, screen size, language, and an approximate location (country, region or city) that Google derives from your IP address. Google states that Google Analytics 4 does not log or store IP addresses.</li>
<li><strong>Cookies:</strong> Google Analytics sets first-party cookies named <code>_ga</code> and <code>_ga_&lt;ID&gt;</code> on {e(domain)} to tell one visit from another. Google documents a lifetime of up to 2 years for these cookies.</li>
<li><strong>Our settings:</strong> Google signals is turned off, event-level data is kept for 2 months (the shortest option Google Analytics offers), and the property isn't linked to Google Ads. The account's data-sharing settings are on, which lets Google use the data as described in <a href="https://support.google.com/analytics/answer/1011397" rel="noopener" target="_blank">Google Analytics data-sharing settings</a>.</li>
<li><strong>What we see:</strong> aggregate reports (page views, traffic sources, countries, device types). We don't see your name, email address or IP address.</li>
<li><strong>Opting out:</strong> you can block or delete cookies in your browser, use a content blocker, or install the <a href="https://tools.google.com/dlpage/gaoptout" rel="noopener" target="_blank">Google Analytics Opt-out Browser Add-on</a>. Google explains its practices in <a href="https://policies.google.com/technologies/partner-sites" rel="noopener" target="_blank">How Google uses information from sites or apps that use its services</a>.</li>
</ul>"""
    return f"""<h1>{e(site)} privacy policy</h1>
<p class="meta">Effective date: {EFFECTIVE}</p>
<p>{e(site)} (<code>{e(domain)}</code>) is published by {OPERATOR}. This page explains what information is collected when you visit, by whom, and why. Questions or requests: <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
<h2>The short version</h2>
<ul>
<li>There are no accounts, sign-ups, comment boxes, newsletters, contact forms or payments on {e(site)}. We don't ask for your name, email address or any other personal details.</li>
<li>We use Google Analytics to count visits. It uses cookies.</li>
<li>Videos are click-to-play. Nothing from the YouTube player loads until you press play.</li>
<li>Our host, GitHub Pages, logs visitors' IP addresses for its own security purposes.</li>
<li>We don't sell personal information, and we don't show ads from ad networks.</li>
</ul>
{ga}
<h2>Embedded YouTube videos</h2>
<p>Some pages include a short video from our YouTube channel (pages with a video: {vids}). The video uses a click-to-play preview:</p>
<ul>
<li>Before you press play, the page shows only a still preview image loaded from YouTube's image server (<code>i.ytimg.com</code>). As with any image from another site, your browser's request tells that server your IP address and browser details. No YouTube player or YouTube script loads at this point.</li>
<li>When you press play, the player loads from <code>www.youtube-nocookie.com</code>, YouTube's privacy-enhanced mode. From then on, YouTube (Google) receives information about your viewing and may store cookies or similar data on your device, as described in <a href="https://policies.google.com/privacy" rel="noopener" target="_blank">Google's Privacy Policy</a>.</li>
<li>"Watch on YouTube" and channel links take you to youtube.com, where YouTube's own policies apply.</li>
</ul>
{affiliate_html}
<h2>Hosting and server logs</h2>
<p>{e(site)} is a static website hosted on <a href="https://pages.github.com/" rel="noopener" target="_blank">GitHub Pages</a>, a service of GitHub, Inc. GitHub states that when a GitHub Pages site is visited, the visitor's IP address is logged and stored for security purposes, whether or not the visitor is signed in to GitHub (see <a href="https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages#data-collection" rel="noopener" target="_blank">GitHub Pages data collection</a> and the <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener" target="_blank">GitHub General Privacy Statement</a>). We don't receive or have access to those logs.</p>
<h2>Things that stay in your browser</h2>
<p>{e(filter_note)} It runs entirely in your browser: what you type or select isn't sent to us or stored. (Google Analytics may record that you interacted with the page, as described above, but not the text you type.)</p>
<h2>If you email us</h2>
<p>If you email us (for example to report an out-of-date listing), we receive your email address and whatever you include in the message. We use it only to reply and to fix the listing. We don't add it to a mailing list or share it.</p>
<h2>Links to other websites</h2>
<p>{e(site)} links to many other websites: the organizations and brands we list, their sources, and other services. Those sites have their own privacy practices, which this policy doesn't cover.</p>
<h2>Children</h2>
<p>{e(site)} isn't directed at children under 13, and we don't knowingly collect personal information from children.</p>
<h2>Your choices and requests</h2>
<p>You can control cookies through your browser settings and the Google Analytics opt-out add-on linked above. If you have a question about this policy, or want to make a request about your information, email <a href="mailto:{CONTACT}">{CONTACT}</a>. Keep in mind that we don't hold analytics data tied to your name or email, and we can't access GitHub's server logs, so for data held by Google or GitHub you may need to contact them directly.</p>
<h2>Changes to this policy</h2>
<p>If the site starts collecting something new (for example a new analytics tool, embed or affiliate program), we'll update this page and the effective date above before or when the change goes live.</p>"""
