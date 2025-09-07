import asyncio
import base64
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="TAVI Analytics PDF Render Server", version="0.1.0")


class PdfRenderRequest(BaseModel):
    # Either provide html string or a public URL; html takes precedence if provided
    html: Optional[str] = Field(None, description="HTML content to render as PDF")
    url: Optional[str] = Field(None, description="Public URL to render as PDF")

    # Page settings
    format: str = Field("A4", description="Paper format e.g. A4, Letter")
    margin_top: str = Field("12mm")
    margin_right: str = Field("12mm")
    margin_bottom: str = Field("12mm")
    margin_left: str = Field("12mm")

    # Rendering options
    print_background: bool = Field(True, description="Print CSS backgrounds")
    prefer_css_page_size: bool = Field(True, description="Respect @page size if provided")

    # Optional header/footer HTML (without <html> wrapper). Use minimal inline CSS.
    header_template: Optional[str] = None
    footer_template: Optional[str] = None

    # If true, return base64-encoded PDF bytes in response. Otherwise save to temp and return path.
    inline_base64: bool = Field(False)


class PdfRenderResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    path: Optional[str] = None
    size_bytes: Optional[int] = None
    base64: Optional[str] = None


# Lazy playwright loader so server can start even if browsers aren't installed yet
_browser_install_hint = (
    "Playwright browsers are not installed. Install once on the server: 'playwright install --with-deps'"
)


async def _render_pdf_with_playwright(req: PdfRenderRequest) -> bytes:
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        raise RuntimeError(f"playwright import failed: {e}. {_browser_install_hint}")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            if req.html:
                # Ensure base URL so relative resources can resolve if needed (optional)
                await page.set_content(req.html, wait_until="load")
            elif req.url:
                await page.goto(req.url, wait_until="networkidle")
            else:
                raise ValueError("Either 'html' or 'url' must be provided")

            pdf_bytes = await page.pdf(
                format=req.format,
                margin={
                    "top": req.margin_top,
                    "right": req.margin_right,
                    "bottom": req.margin_bottom,
                    "left": req.margin_left,
                },
                print_background=req.print_background,
                prefer_css_page_size=req.prefer_css_page_size,
                header_template=req.header_template or None,
                footer_template=req.footer_template or None,
            )
        finally:
            try:
                await context.close()
                await browser.close()
            except Exception:
                pass

    return pdf_bytes


@app.post("/render/pdf", response_model=PdfRenderResponse)
async def render_pdf(req: PdfRenderRequest):
    try:
        pdf_bytes = await _render_pdf_with_playwright(req)
        if req.inline_base64:
            return PdfRenderResponse(
                success=True,
                base64=base64.b64encode(pdf_bytes).decode("ascii"),
                size_bytes=len(pdf_bytes),
            )
        # Save to a temp file and return the path for download by the client
        out_dir = Path(os.getenv("PDF_OUT_DIR", str(Path.cwd() / "out")))
        out_dir.mkdir(parents=True, exist_ok=True)
        tmp_name = f"tavr_report_{os.getpid()}_{asyncio.get_event_loop().time():.0f}.pdf"
        out_path = out_dir / tmp_name
        out_path.write_bytes(pdf_bytes)
        return PdfRenderResponse(success=True, path=str(out_path), size_bytes=len(pdf_bytes))
    except Exception as e:
        return JSONResponse(status_code=500, content=PdfRenderResponse(success=False, message=str(e)).model_dump())


# Health check
@app.get("/health")
async def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")), reload=False)
