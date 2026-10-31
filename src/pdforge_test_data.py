"""
PDForge Deterministic Sample Data Generator
Generates clean synthetic PDFs, geometric calibration JPGs, and a sample HTML file
in `test_data/` using PyCairo and Pillow (zero AI-generated images).
"""

import os
import cairo
from PIL import Image, ImageDraw


def generate_all_test_data(base_dir: str) -> None:
    os.makedirs(base_dir, exist_ok=True)

    # 1. Sample 3-page PDF for Merge, Split, Compress, Word, Translate, and Markdown
    pdf_a = os.path.join(base_dir, "pdforge_sample_report.pdf")
    if not os.path.exists(pdf_a):
        surface = cairo.PDFSurface(pdf_a, 595.28, 841.89)
        ctx = cairo.Context(surface)

        pages_data = [
            (
                "PDForge Architecture Overview",
                " Summary & Project Report",
                [
                    "• High speed local PDF manipulation engine",
                    "• Zero cloud uploads or external server dependencies",
                    "• Modular SVG vector icon system in assets/ folder",
                ],
                [
                    ("Description", "Quantity", "Price"),
                    ("Core PDF Engine", "1", "100"),
                    ("Vector UI Suite", "9", "250"),
                ],
            ),
            (
                "Performance & Security",
                "Page 2 Technical Specifications",
                [
                    "• Instant file merge and page range extraction",
                    "• Ghostscript compression profiles (Low, Recommended, Extreme)",
                    "• OpenXML Word document reconstruction",
                ],
                [
                    ("Description", "Quantity", "Amount"),
                    ("Memory Footprint", "65", "MB"),
                    ("Startup Latency", "120", "ms"),
                ],
            ),
            (
                "Invoice & Receipt Summary",
                "Page 3 Financial Overview",
                [
                    "• Customer: ACME Test Lab Corp",
                    "• Date: 2026-10-31",
                    "• Total Amount: 350 USD",
                ],
                [
                    ("Description", "Quantity", "Total"),
                    ("Enterprise License", "1", "350"),
                ],
            ),
        ]

        for p_idx, (title, subtitle, bullets, table_rows) in enumerate(pages_data, start=1):
            ctx.save()
            ctx.set_source_rgb(1, 1, 1)
            ctx.paint()
            ctx.restore()

            # Header bar
            ctx.set_source_rgb(0.12, 0.16, 0.23)
            ctx.rectangle(40, 40, 515, 50)
            ctx.fill()

            # Title
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(22)
            ctx.set_source_rgb(0.15, 0.38, 0.92)
            ctx.move_to(50, 130)
            ctx.show_text(title)

            # Subtitle
            ctx.set_font_size(15)
            ctx.set_source_rgb(0.28, 0.33, 0.41)
            ctx.move_to(50, 165)
            ctx.show_text(subtitle.strip())

            # Bullets
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(12)
            ctx.set_source_rgb(0.1, 0.1, 0.15)
            y = 215
            for b in bullets:
                ctx.move_to(60, y)
                ctx.show_text(b)
                y += 28

            # Table
            y += 30
            for r_idx, row in enumerate(table_rows):
                ctx.select_font_face(
                    "Sans",
                    cairo.FONT_SLANT_NORMAL,
                    cairo.FONT_WEIGHT_BOLD if r_idx == 0 else cairo.FONT_WEIGHT_NORMAL,
                )
                ctx.set_font_size(12)
                x_positions = [60, 260, 400]
                for c_idx, cell in enumerate(row):
                    ctx.move_to(x_positions[c_idx], y)
                    ctx.show_text(cell)
                y += 24

            # Footer
            ctx.set_font_size(10)
            ctx.set_source_rgb(0.5, 0.55, 0.6)
            ctx.move_to(50, 800)
            ctx.show_text(f"PDForge Test Document - Page {p_idx}")
            ctx.show_page()

        surface.finish()

    # 2. Second sample PDF for Merge testing
    pdf_b = os.path.join(base_dir, "pdforge_appendix_b.pdf")
    if not os.path.exists(pdf_b):
        surface = cairo.PDFSurface(pdf_b, 595.28, 841.89)
        ctx = cairo.Context(surface)
        ctx.set_source_rgb(1, 1, 1)
        ctx.paint()
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(20)
        ctx.set_source_rgb(0.05, 0.58, 0.41)
        ctx.move_to(50, 120)
        ctx.show_text("PDForge Appendix B - Secondary File")
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(12)
        ctx.set_source_rgb(0.2, 0.2, 0.25)
        ctx.move_to(50, 160)
        ctx.show_text("This file is used to verify multi-file merging and rotation.")
        ctx.show_page()
        surface.finish()

    # 3. Deterministic geometric test JPGs for JPG-to-PDF
    for idx, color in enumerate([(37, 99, 235), (5, 150, 105)], start=1):
        jpg_path = os.path.join(base_dir, f"calibration_card_{idx}.jpg")
        if not os.path.exists(jpg_path):
            img = Image.new("RGB", (800, 600), (248, 250, 252))
            draw = ImageDraw.Draw(img)
            draw.rectangle([40, 40, 760, 560], outline=color, width=6)
            draw.rectangle([80, 80, 720, 180], fill=color)
            draw.text((110, 120), f"PDForge Geometric Test Card #{idx}", fill=(255, 255, 255))
            draw.ellipse([300, 240, 500, 440], outline=color, width=5)
            img.save(jpg_path, "JPEG", quality=92)

    # 4. Sample HTML file for HTML-to-PDF
    html_path = os.path.join(base_dir, "sample_webpage.html")
    if not os.path.exists(html_path):
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(
                """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>PDForge HTML to PDF Test</title>
  <style>
    body { font-family: sans-serif; margin: 40px; color: #1e293b; }
    h1 { color: #2563eb; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; }
    .box { background: #f1f5f9; padding: 16px; border-radius: 8px; margin-top: 16px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #cbd5e1; padding: 10px; text-align: left; }
    th { background: #e2e8f0; }
  </style>
</head>
<body>
  <h1>PDForge Local HTML-to-PDF Verification</h1>
  <p>This HTML document was rendered locally into a vector PDF by PDForge.</p>
  <div class="box">
    <strong>Key Benefits:</strong> Clean layout preservation, zero external trackers, and instant local execution.
  </div>
  <table>
    <tr><th>Component</th><th>Status</th><th>Mode</th></tr>
    <tr><td>HTML Renderer</td><td>Verified</td><td>Local Headless Engine</td></tr>
    <tr><td>Vector Fonts</td><td>Embedded</td><td>A4 Portrait</td></tr>
  </table>
</body>
</html>
"""
            )

