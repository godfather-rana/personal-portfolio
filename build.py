#!/usr/bin/env python3
"""Build the static site in dist/ from content.json."""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
CONTENT = ROOT / "content.json"

BANNED_IN_HTML = (
    "\u2014",  # em dash
    "\u2013",  # en dash
    "TODO",
    "lorem ipsum",
)
PHONE_DIGITS = re.compile(r"\d{10}")

REQUIRED_IN_HTML = (
    "Ameet Kumar Rana",
    "mail2ameetrana@gmail.com",
    "https://github.com/godfather-rana",
    "https://www.linkedin.com/in/ameet-kumar-rana-294b77161/",
    "On-Demand Meta Hydration Pipeline",
    "High-volume Microsoft Graph downloader",
    "Graph API migration",
    "TraceIQ",
    "65%",
    "One-click cloud setup",
    "$64K",
    "525+",
    "2,000+",
    "6M+",
    "58+",
    "99%",
    "95%",
    "Momentum Robotics",
    "Army Institute of Technology",
    "8.35",
    "HackerRank",
    "AWS Bedrock",
    "Thanos",
    "Backupset",
    "Exchange Online",
    "goroutines",
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load() -> dict:
    try:
        data = json.loads(CONTENT.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit("content.json is missing. It is the only copy source for the site.")
    except json.JSONDecodeError as err:
        sys.exit(f"content.json is not valid JSON: {err}")
    return data


def scan_strings(node: object, path: str, errors: list[str]) -> None:
    if path == "todos" or path.startswith("todos.") or path.startswith("todos["):
        return
    if path in {"_note"} or path.startswith("_"):
        return
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else key
            scan_strings(value, child, errors)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            scan_strings(value, f"{path}[{index}]", errors)
    elif isinstance(node, str):
        for banned in ("\u2014", "\u2013"):
            if banned in node:
                errors.append(f"{path} contains {banned!r}")
        if PHONE_DIGITS.search(node):
            errors.append(f"{path} contains a 10-digit number. Do not publish a phone number.")
        if "TODO" in node:
            errors.append(f"{path} contains TODO. Put unfinished items under todos, not in rendered copy.")


def section_title(index: str, title: str, heading_id: str) -> str:
    return (
        f'<h2 class="section-title" id="{esc(heading_id)}">'
        f'<span class="idx" aria-hidden="true">{esc(index)}</span> {esc(title)}</h2>'
    )


def actions_html(actions: list[dict], skip_mailto: bool = False) -> str:
    parts = ['<div class="actions">']
    for action in actions:
        href = action["href"]
        if skip_mailto and href.startswith("mailto:"):
            continue
        classes = "btn btn-primary" if action.get("kind") == "primary" else "btn"
        attrs = [f'class="{classes}"', f'href="{esc(href)}"']
        if action.get("ariaLabel") and action["ariaLabel"] != action["label"]:
            attrs.append(f'aria-label="{esc(action["ariaLabel"])}"')
        if action.get("download"):
            attrs.append(f'download="{esc(action["download"])}"')
        rel = action.get("rel")
        if rel:
            attrs.append(f'rel="{esc(rel)}"')
        parts.append(f'<a {" ".join(attrs)}>{esc(action["label"])}</a>')
    parts.append("</div>")
    return "\n".join(parts)


def highlights_html(items: list[dict]) -> str:
    rows = []
    for item in items:
        rows.append(
            "<li>"
            f"<strong>{esc(item['value'])}</strong>"
            f"<span>{esc(item['label'])}</span>"
            "</li>"
        )
    return (
        '<aside class="impact" aria-label="Selected impact">'
        '<p class="impact-label">Selected impact</p>'
        f"<ul>{''.join(rows)}</ul>"
        "</aside>"
    )


def snapshot_html(items: list[dict]) -> str:
    rows = []
    for item in items:
        rows.append(
            "<div>"
            f"<dt>{esc(item['label'])}</dt>"
            f"<dd>{esc(item['value'])}</dd>"
            "</div>"
        )
    return f'<dl class="snapshot">{"".join(rows)}</dl>'


def paragraphs_html(paragraphs: list[str]) -> str:
    return "".join(f"<p>{esc(p)}</p>" for p in paragraphs)


def experience_html(jobs: list[dict]) -> str:
    if not jobs:
        return '<p class="empty">Experience is added in content.json.</p>'
    blocks = []
    for job in jobs:
        roles = []
        for role in job["roles"]:
            bullets = "".join(f"<li>{esc(b)}</li>" for b in role["bullets"])
            roles.append(
                '<div class="role">'
                f"<h4>{esc(role['title'])}</h4>"
                f'<p class="dates">{esc(role["dates"])}</p>'
                f"<ul>{bullets}</ul>"
                "</div>"
            )
        note = f'<p class="job-meta">{esc(job["note"])}</p>' if job.get("note") else ""
        blocks.append(
            '<article class="job">'
            '<header class="job-head">'
            f"<h3>{esc(job['company'])}</h3>"
            f'<p class="job-meta">{esc(job["location"])}</p>'
            "</header>"
            f"{note}"
            f"{''.join(roles)}"
            "</article>"
        )
    return "".join(blocks)


def projects_html(projects: list[dict]) -> str:
    if not projects:
        return '<p class="empty">Featured work is added in content.json.</p>'
    cards = []
    for project in projects:
        facts = "".join(f"<li>{esc(fact)}</li>" for fact in project.get("facts", []))
        links = []
        for link in project.get("links") or []:
            url = link.get("url", "")
            if not url.startswith("https://") and not url.startswith("http://"):
                raise SystemExit(f"Project {project.get('id')} has a link that is not an http(s) URL.")
            links.append(f'<a href="{esc(url)}">{esc(link["label"])}</a>')
        link_html = f'<p class="card-links">{"".join(links)}</p>' if links else ""
        cards.append(
            f'<article class="card" id="project-{esc(project["id"])}">'
            f'<p class="card-context">{esc(project["context"])}</p>'
            f"<h3>{esc(project['title'])}</h3>"
            '<p class="metric">'
            f'<span class="metric-value">{esc(project["metric"])}</span>'
            f'<span class="metric-label">{esc(project["metricLabel"])}</span>'
            "</p>"
            f"<p>{esc(project['summary'])}</p>"
            f"<ul class=\"facts\">{facts}</ul>"
            f"{link_html}"
            "</article>"
        )
    return f'<div class="cards">{"".join(cards)}</div>'


def skills_html(groups: list[dict]) -> str:
    if not groups:
        return '<p class="empty">Skills are added in content.json.</p>'
    blocks = []
    for group in groups:
        chips = "".join(f"<li>{esc(item)}</li>" for item in group["items"])
        blocks.append(
            '<div class="skill-block">'
            f"<h3>{esc(group['level'])}</h3>"
            f'<ul class="chips">{chips}</ul>'
            "</div>"
        )
    return f'<div class="skills-grid">{"".join(blocks)}</div>'


def education_html(schools: list[dict], certifications: list[dict]) -> str:
    cards = []
    for school in schools:
        detail = f'<p>{esc(school["detail"])}</p>' if school.get("detail") else ""
        cards.append(
            '<article class="edu-card">'
            f"<h3>{esc(school['school'])}</h3>"
            f'<p>{esc(school["credential"])}</p>'
            f"{detail}"
            f'<p class="muted">{esc(school["location"])}</p>'
            f'<p class="muted">{esc(school["dates"])}</p>'
            "</article>"
        )
    for cert in certifications:
        issuer = f'<p class="muted">{esc(cert["issuer"])}</p>' if cert.get("issuer") else ""
        cards.append(
            '<article class="cert-card">'
            f"<h3>{esc(cert['name'])}</h3>"
            f"{issuer}"
            "</article>"
        )
    if not cards:
        return '<p class="empty">Education is added in content.json.</p>'
    return f'<div class="edu-grid">{"".join(cards)}</div>'


def nav_html(items: list[dict]) -> str:
    links = "".join(
        f'<a href="{esc(item["href"])}">{esc(item["label"])}</a>' for item in items
    )
    return f'<nav id="site-nav" class="nav" data-nav aria-label="Sections">{links}</nav>'


def json_ld(data: dict) -> str:
    person = data["person"]
    skills = [item for group in data["skills"] for item in group["items"]]
    payload = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": person["name"],
        "jobTitle": person["jobTitle"],
        "worksFor": {"@type": "Organization", "name": person["employer"]},
        "email": f"mailto:{person['email']}",
        "url": canonical_url(data),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Pune",
            "addressCountry": "IN",
        },
        "sameAs": [person["github"], person["linkedin"]],
        "alumniOf": {
            "@type": "CollegeOrUniversity",
            "name": data["education"][0]["school"],
        },
        "knowsAbout": skills,
    }
    if person.get("photo"):
        payload["image"] = person["photo"]
    raw = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return raw


def portrait_html(person: dict) -> str:
    photo = person.get("photo")
    if not photo:
        return ""
    return (
        f'<img class="portrait" src="{esc(photo)}" alt="{esc(person["photoAlt"])}" '
        'width="160" height="160">'
    )


def render(data: dict) -> str:
    person = data["person"]
    site = data["site"]
    email = person["email"]
    description = site["description"]
    title = site["title"]
    url = canonical_url(data)
    og = site["ogImage"]
    return f"""<!DOCTYPE html>
<html lang="{esc(site["language"])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <meta name="keywords" content="{esc(site["keywords"])}">
  <meta name="author" content="{esc(person["name"])}">
  <meta name="robots" content="index, follow">
  <meta name="format-detection" content="telephone=no">
  <meta name="theme-color" content="{esc(site["themeColorLight"])}" data-light="{esc(site["themeColorLight"])}" data-dark="{esc(site["themeColorDark"])}">
  <meta name="color-scheme" content="light dark">
  <title>{esc(title)}</title>
  <link rel="canonical" href="{esc(url)}">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="assets/apple-touch.png">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="{esc(site["locale"])}">
  <meta property="og:site_name" content="{esc(person["name"])}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(url)}">
  <meta property="og:image" content="{esc(url + og)}">
  <meta property="og:image:alt" content="{esc(site["ogImageAlt"])}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{esc(url + og)}">
  <meta name="twitter:image:alt" content="{esc(site["ogImageAlt"])}">
  <link rel="preload" href="assets/fonts/fraunces-600.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="assets/fonts/plex-400.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="styles.css">
  <script type="application/ld+json">{json_ld(data)}</script>
  <script>
    (function () {{
      try {{
        var stored = localStorage.getItem("theme");
        var theme = stored || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
        document.documentElement.setAttribute("data-theme", theme);
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute("content", theme === "dark" ? meta.getAttribute("data-dark") : meta.getAttribute("data-light"));
      }} catch (err) {{
        document.documentElement.setAttribute("data-theme", "light");
      }}
    }})();
  </script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <noscript><p class="noscript">Theme and menu controls use JavaScript. The page content is all here.</p></noscript>
  <header class="site-header" id="top">
    <div class="wrap header-inner">
      <a class="brand" href="#top">
        <span class="mark" aria-hidden="true">{esc(person["initials"])}</span>
        <span class="brand-name">{esc(person["name"])}</span>
      </a>
      <div class="header-tools">
        {nav_html(data["nav"])}
        <button class="icon-btn" type="button" data-theme-toggle aria-label="Switch theme" aria-pressed="false">
          <svg class="icon-moon" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 14.5A8.5 8.5 0 1 1 9.5 3 7 7 0 0 0 21 14.5z"/></svg>
          <svg class="icon-sun" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M3 12h2M19 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        </button>
        <button class="icon-btn menu-toggle" type="button" data-menu-toggle aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">
          <svg class="icon-menu" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
          <svg class="icon-close" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
      </div>
    </div>
  </header>
  <main id="main">
    <section class="hero" aria-labelledby="hero-title">
      <div class="wrap hero-grid">
        <div>
          <p class="status"><span class="dot" aria-hidden="true"></span> {esc(person["status"])}</p>
          <p class="eyebrow">{esc(person["eyebrow"])}</p>
          <h1 id="hero-title">{esc(person["name"])}</h1>
          {portrait_html(person)}
          <p class="positioning">{esc(person["positioning"])}</p>
          <p class="summary">{esc(person["summary"])}</p>
          {actions_html(data["actions"])}
        </div>
        {highlights_html(data["highlights"])}
      </div>
    </section>
    <section id="about" aria-labelledby="about-title">
      <div class="wrap">
        {section_title("01", "About", "about-title")}
        <div class="about-grid">
          <div class="prose">{paragraphs_html(data["about"]["paragraphs"])}</div>
          {snapshot_html(data["snapshot"])}
        </div>
      </div>
    </section>
    <section id="experience" aria-labelledby="experience-title">
      <div class="wrap">
        {section_title("02", "Experience", "experience-title")}
        {experience_html(data["experience"])}
      </div>
    </section>
    <section id="work" aria-labelledby="work-title">
      <div class="wrap">
        {section_title("03", "Featured work", "work-title")}
        {projects_html(data["projects"])}
      </div>
    </section>
    <section id="skills" aria-labelledby="skills-title">
      <div class="wrap">
        {section_title("04", "Skills", "skills-title")}
        {skills_html(data["skills"])}
      </div>
    </section>
    <section id="education" aria-labelledby="education-title">
      <div class="wrap">
        {section_title("05", "Education", "education-title")}
        {education_html(data["education"], data["certifications"])}
      </div>
    </section>
    <section id="contact" aria-labelledby="contact-title">
      <div class="wrap">
        {section_title("06", "Contact", "contact-title")}
        <p class="contact-lead">{esc(data["contact"]["text"])}</p>
        <p><a class="email-link" href="mailto:{esc(email)}">{esc(email)}</a></p>
        {actions_html(data["actions"])}
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <p>{esc(data["footer"])}</p>
      <p><a href="#top">Back to top</a></p>
    </div>
  </footer>
  <script src="main.js"></script>
</body>
</html>
"""


def canonical_url(data: dict) -> str:
    return data["site"]["url"].rstrip("/") + "/"


def write_robots(data: dict) -> None:
    url = canonical_url(data)
    (DIST / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: " + url + "sitemap.xml\n",
        encoding="utf-8",
    )
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url>\n"
        f"    <loc>{esc(url)}</loc>\n"
        "  </url>\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    (DIST / ".nojekyll").write_text("", encoding="utf-8")


def generate_images(data: dict) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        missing = [
            name
            for name in ("assets/og.png", "assets/apple-touch.png")
            if not (ROOT / name).exists()
        ]
        if missing:
            sys.exit("Pillow is not installed and these images are missing: " + ", ".join(missing))
        return

    def font(path: str, size: int):
        return ImageFont.truetype(path, size)

    serif_bold = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
    sans = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"
    sans_reg = "/usr/share/fonts/truetype/macos/Inter-Regular.ttf"
    if not Path(serif_bold).exists() or not Path(sans).exists():
        if not (ROOT / "assets" / "og.png").exists():
            sys.exit("System fonts for the social image are missing, and assets/og.png does not exist.")
        return

    person = data["person"]
    width, height = 1200, 630
    image = Image.new("RGB", (width, height), "#141311")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 16, height), fill="#0f5c4c")
    draw.text((80, 78), "GO BACKEND AND DISTRIBUTED SYSTEMS", font=font(sans, 20), fill="#9fe0d2")
    draw.text((80, 130), person["name"], font=font(serif_bold, 76), fill="#f4f0e7")
    draw.text((80, 240), person["positioning"], font=font(sans_reg, 32), fill="#c1b9ad")
    draw.text((80, 292), person["eyebrow"], font=font(sans, 26), fill="#f4f0e7")
    draw.line((80, 360, 1120, 360), fill="#34302a", width=2)
    highlights = data["highlights"][:3]
    x = 80
    for item in highlights:
        draw.text((x, 400), item["value"], font=font(serif_bold, 48), fill="#9fe0d2")
        label = item["label"]
        # wrap a long label onto two lines so cards stay inside the canvas
        words = label.split()
        line1: list[str] = []
        line2: list[str] = []
        label_font = font(sans_reg, 20)
        for word in words:
            trial = " ".join(line1 + [word])
            if draw.textlength(trial, font=label_font) < 300:
                line1.append(word)
            else:
                line2.append(word)
        if len(line2) == 1 and line1:
            line2.insert(0, line1.pop())
        draw.text((x, 464), " ".join(line1), font=font(sans_reg, 20), fill="#c1b9ad")
        if line2:
            draw.text((x, 490), " ".join(line2), font=font(sans_reg, 20), fill="#c1b9ad")
        x += 340
    parsed = urlparse(data["site"]["url"])
    public_path = (parsed.netloc + parsed.path).rstrip("/")
    draw.text((80, 568), public_path, font=font(sans, 20), fill="#8a8378")
    og_path = ROOT / "assets" / "og.png"
    image.save(og_path, "PNG", optimize=True)

    icon = Image.new("RGB", (180, 180), "#1c1915")
    idraw = ImageDraw.Draw(icon)
    idraw.rounded_rectangle((0, 0, 179, 179), radius=36, fill="#1c1915")
    mark = font(serif_bold, 72)
    box = idraw.textbbox((0, 0), person["initials"], font=mark)
    tw, th = box[2] - box[0], box[3] - box[1]
    idraw.text(((180 - tw) / 2, (180 - th) / 2 - 8), person["initials"], font=mark, fill="#f4f1ea")
    icon.save(ROOT / "assets" / "apple-touch.png", "PNG", optimize=True)


def validate(data: dict, page: str) -> None:
    errors: list[str] = []
    scan_strings(data, "", errors)
    for banned in BANNED_IN_HTML:
        if banned in page:
            errors.append(f"generated HTML contains {banned!r}")
    if PHONE_DIGITS.search(page):
        errors.append("generated HTML contains a 10-digit number. Do not publish a phone number.")
    for required in REQUIRED_IN_HTML:
        if required not in page:
            errors.append(f"generated HTML is missing {required!r}")
    lowered = page.lower()
    if "phone" in lowered and "telephone=no" not in lowered:
        errors.append("unexpected phone mention in HTML")
    canonical = canonical_url(data)
    if f'rel="canonical" href="{esc(canonical)}"' not in page:
        errors.append(f"canonical URL is not {canonical}")
    if f'property="og:url" content="{esc(canonical)}"' not in page:
        errors.append(f"og:url is not {canonical}")
    if f'property="og:image" content="{esc(canonical + data["site"]["ogImage"])}"' not in page:
        errors.append("og:image is not under the project pages URL")
    for token in ('href="/', 'src="/'):
        if token in page:
            errors.append(f"root-absolute path {token} found; project pages need relative asset paths")
    if errors:
        sys.exit("Build blocked:\n- " + "\n- ".join(errors))
    pdf = DIST / "assets" / "Ameet-Kumar-Rana-Resume.pdf"
    raw = pdf.read_bytes()
    # The source resume labels the number "Mobile :". Binary digit runs inside
    # the PDF are font and xref data, so only the label is checked here.
    if b"Mobile :" in raw or b"Mobile:" in raw:
        sys.exit("The resume PDF still has a mobile line. Remove the phone number before publishing.")


def main() -> None:
    data = load()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    generate_images(data)
    shutil.copytree(ROOT / "assets", DIST / "assets")
    shutil.copy(ROOT / "src" / "styles.css", DIST / "styles.css")
    shutil.copy(ROOT / "src" / "main.js", DIST / "main.js")
    page = render(data)
    (DIST / "index.html").write_text(page, encoding="utf-8")
    write_robots(data)
    validate(data, page)
    print(f"Built {DIST / 'index.html'}")
    print("Placeholders (not shown on the site):")
    for item in data.get("todos", []):
        print(f"- {item['field']}: {item['note']}")


if __name__ == "__main__":
    main()
