import json
import os
import sys
from pathlib import Path

import requests

SERVER = os.getenv("PDF_SERVER", "http://localhost:8080")


def render_pdf_from_html(html: str, out_path: Path) -> Path:
    payload = {
        "html": html,
        "format": "A4",
        "margin_top": "12mm",
        "margin_right": "12mm",
        "margin_bottom": "12mm",
        "margin_left": "12mm",
        "print_background": True,
        "prefer_css_page_size": True,
        "inline_base64": False,
    }
    r = requests.post(f"{SERVER}/render/pdf", json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(data.get("message", "render failed"))

    # Download the file from server path
    server_path = data.get("path")
    # In a real deployment, serve files via HTTP. For demo, we just save a placeholder.
    # Here, we call inline_base64=True in a second request to fetch bytes directly.
    payload["inline_base64"] = True
    r2 = requests.post(f"{SERVER}/render/pdf", json=payload, timeout=120)
    r2.raise_for_status()
    data2 = r2.json()
    pdf_b64 = data2.get("base64")
    if not pdf_b64:
        raise RuntimeError("No base64 returned")
    out_path.write_bytes(__import__("base64").b64decode(pdf_b64))
    return out_path


if __name__ == "__main__":
    html = "<html><body><h1>Test</h1></body></html>"
    out = Path.cwd() / "sample.pdf"
    p = render_pdf_from_html(html, out)
    print(f"saved to {p}")
