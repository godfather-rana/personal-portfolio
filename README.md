# Ameet Kumar Rana

Personal site for Ameet Kumar Rana, a Go backend and distributed systems engineer. It is a static page: one HTML file, one stylesheet, and a small script for the theme and the mobile menu. There is no server to run in production.

All public copy lives in [`content.json`](content.json). The layout does not need to change to add a project.

## Edit the content

1. Open `content.json`.
2. Change the text you want. Keep claims limited to what is true. The build rejects an em dash, an en dash, a phone number, and the word TODO in rendered fields.
3. Rebuild:

```bash
python3 build.py
```

4. Preview the `dist/` folder:

```bash
python3 -m http.server 47321 --directory dist
```

Open `http://127.0.0.1:47321`.

`dist/` is generated. Do not edit it by hand. The next build overwrites it.

### Add a project

Append an object to `projects`:

```json
{
  "id": "short-id",
  "title": "Project title",
  "context": "Where and when",
  "metric": "12",
  "metricLabel": "what the number means",
  "summary": "Two or three sentences of what shipped and why it mattered.",
  "facts": ["Fact one", "Fact two"],
  "links": []
}
```

A link is shown only when you add one:

```json
"links": [{ "label": "Write-up", "url": "https://example.com/post" }]
```

The URL has to start with `http://` or `https://`.

### Add a photo

The resume has no photo, so the header uses initials. To show a portrait, put an image in `assets/` and set:

```json
"photo": "assets/portrait.jpg",
"photoAlt": "Portrait of Ameet Kumar Rana"
```

Then rebuild. `photo: null` keeps the initials.

### Resume PDF

The downloadable file is `assets/Ameet-Kumar-Rana-Resume.pdf`. The mobile number has been removed from that file. If you replace it, remove the phone number before publishing.

### What is intentionally unfinished

`todos` in `content.json` is the list of placeholders. Those notes are not rendered. See the end of this file.

## Deploy to GitHub Pages

The repository is [godfather-rana/personal-portfolio](https://github.com/godfather-rana/personal-portfolio). GitHub Pages serves a project site from a subpath, not the user-site root:

`https://godfather-rana.github.io/personal-portfolio/`

1. Push the `main` branch to that repository.
2. In the repository, open Settings, then Pages. Under Build and deployment, set Source to GitHub Actions.
3. The workflow in `.github/workflows/pages.yml` runs `python3 build.py` and deploys the `dist/` folder.
4. After the first green run, the site is at `https://godfather-rana.github.io/personal-portfolio/`.

`site.url` in `content.json` is that address. The build writes it into the canonical link, Open Graph tags, JSON-LD, and `sitemap.xml`. Stylesheets, scripts, fonts, the resume, and images use relative paths (`styles.css`, `assets/...`), so they load under `/personal-portfolio/` and also when you open `dist/` on its own for a local preview. Do not switch those to root paths such as `/styles.css`. Those would skip the project folder and 404 on GitHub Pages.

## Layout

| File | Role |
| --- | --- |
| `content.json` | All copy, links, projects, skills, and placeholders |
| `build.py` | Writes `dist/` and checks the page for banned text |
| `src/styles.css` | Layout, light theme, dark theme |
| `src/main.js` | Theme toggle and mobile menu |
| `assets/` | Resume, fonts, favicon, social image |

Fraunces and IBM Plex Sans are included under the SIL Open Font License. The license texts are in `assets/fonts/`.

## Placeholders

These are missing on purpose. They are listed in `content.json` under `todos` and are not shown to visitors.

- **Photo.** No portrait was on the resume. Set `person.photo` when you have one.
- **Project links.** The resume does not include repository or write-up URLs for the Druva or Momentum work. Add `projects[].links` when a URL exists.
- **Phone number.** The mobile number is on the resume and is left out of the site and out of the downloadable PDF. Do not add it.
