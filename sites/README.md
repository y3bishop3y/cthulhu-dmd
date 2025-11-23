# Cthulhu: Death May Die - Character Database Website

A static website for browsing character data from Cthulhu: Death May Die.

## Structure

```
sites/
├── index.html          # Main HTML page
├── js/
│   └── app.js         # JavaScript application logic
├── data/              # Generated JSON data (gitignored)
│   ├── seasons.json   # List of all seasons
│   └── seasons/       # Individual season JSON files
│       ├── season1.json
│       ├── season2.json
│       └── ...
└── scripts/
    └── generate_site.py  # Script to generate JSON from character data
```

## Setup

1. Generate the website data files:
```bash
uv run python sites/scripts/generate_site.py
```

This reads character JSON files from `data/` and generates:
- `sites/data/seasons.json` - List of all seasons
- `sites/data/seasons/season*.json` - Character data for each season

## Development

### Local Development Server

You can use Python's built-in HTTP server:

```bash
cd sites
python3 -m http.server 8000
```

Then open http://localhost:8000 in your browser.

### Regenerating Data

After updating character JSON files, regenerate the website data:

```bash
uv run python sites/scripts/generate_site.py
```

## Features

- **Sidebar Navigation**: Expandable categories (starting with Seasons)
- **Season Pages**: List all characters in a season with name and motto
- **Responsive Design**: Works on desktop and mobile
- **Tailwind CSS**: Modern styling framework

## Adding New Categories

To add new sidebar categories:

1. Add HTML structure in `index.html` sidebar
2. Add JavaScript handlers in `js/app.js`
3. Update `generate_site.py` to generate data for new categories

## Deployment

The site is static HTML/CSS/JS, so it can be deployed to any static hosting:
- GitHub Pages
- Netlify
- Vercel
- Any web server

Just ensure the `data/` directory is included in deployment.

