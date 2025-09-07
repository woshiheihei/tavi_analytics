# TAVI Analytics PDF Render Server

A lightweight service to render high-fidelity PDFs via a headless Chromium browser. Ideal for server-side report generation from HTML or URLs.

## Features

- FastAPI HTTP API
- Headless Chromium rendering via Playwright (SOTA print fidelity)
- Supports HTML string or URL input
- CSS print backgrounds and @page support
- Optional header/footer HTML
- Returns base64 inline or a saved file path

## API

### POST /render/pdf

Request body (JSON):

- html: string (optional) — HTML to render; takes precedence over url
- url: string (optional) — Public URL to render
- format: string (default: A4)
- margin_top|right|bottom|left: string (default: 12mm)
- print_background: bool (default: true)
- prefer_css_page_size: bool (default: true)
- header_template|footer_template: string (optional)
- inline_base64: bool (default: false) — if true, returns base64-encoded PDF

Response (JSON):

- success: bool
- path: string (when inline_base64=false)
- base64: string (when inline_base64=true)
- size_bytes: number
- message: string (on error)

## Run locally

1. Install Python 3.10+
2. Install deps and browsers

```bash
pip install -r requirements.txt
python -m playwright install --with-deps
```

1. Start the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

1. Test

```bash
curl -X POST http://localhost:8080/render/pdf \
  -H "Content-Type: application/json" \
  -d '{"html":"<html><body><h1>Hello PDF</h1></body></html>"}'
```

## Deploy

- Containerize or run as a service.
- Set `PDF_OUT_DIR` to control where files are written.
- Ensure Playwright browsers installed once: `python -m playwright install --with-deps`.
