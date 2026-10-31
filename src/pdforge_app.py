#!/usr/bin/env python3
"""
PDForge - Local Desktop PDF Studio
A lightweight, standalone native GTK3 desktop application replicating all 9 PDF
workflows locally
"""

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Pango

from pdforge_engine import (
    compress_pdf,
    get_pdf_page_count,
    html_to_pdf,
    jpg_to_pdf,
    merge_pdfs,
    ocr_pdf,
    pdf_to_markdown,
    pdf_to_word,
    render_pdf_thumbnail,
    split_pdf,
    translate_pdf,
)
from pdforge_test_data import generate_all_test_data

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
TEST_DATA_DIR = ROOT_DIR / "test_data"
OUTPUT_DIR = ROOT_DIR / "output"

TOOLS_SPEC = [
    {
        "id": "merge",
        "title": "Merge PDF",
        "subtitle": "Combine multiple PDFs into one unified document in your desired order.",
        "icon": ASSETS_DIR / "tools" / "tool-merge-pdf.svg",
        "accept": "pdf",
        "multi": True,
        "default_out": "merged_document.pdf",
    },
    {
        "id": "split",
        "title": "Split PDF",
        "subtitle": "Extract page ranges or split a PDF at fixed intervals into separate files.",
        "icon": ASSETS_DIR / "tools" / "tool-split-pdf.svg",
        "accept": "pdf",
        "multi": False,
        "default_out": "split_output.pdf",
    },
    {
        "id": "compress",
        "title": "Compress PDF",
        "subtitle": "Reduce PDF file size while optimizing visual quality and streams.",
        "icon": ASSETS_DIR / "tools" / "tool-compress-pdf.svg",
        "accept": "pdf",
        "multi": False,
        "default_out": "compressed_document.pdf",
    },
    {
        "id": "pdfword",
        "title": "PDF to Word",
        "subtitle": "Convert PDF pages into editable OpenXML (.docx) Word documents.",
        "icon": ASSETS_DIR / "tools" / "tool-pdf-to-word.svg",
        "accept": "pdf",
        "multi": False,
        "default_out": "converted_document.docx",
    },
    {
        "id": "imagepdf",
        "title": "JPG to PDF",
        "subtitle": "Transform JPG & PNG images into a clean PDF with custom margins & layout.",
        "icon": ASSETS_DIR / "tools" / "tool-jpg-to-pdf.svg",
        "accept": "image",
        "multi": True,
        "default_out": "images_compiled.pdf",
    },
    {
        "id": "htmlpdf",
        "title": "HTML to PDF",
        "subtitle": "Convert local HTML files or web URLs into vector PDF documents.",
        "icon": ASSETS_DIR / "tools" / "tool-html-to-pdf.svg",
        "accept": "html",
        "multi": False,
        "default_out": "webpage_rendered.pdf",
    },
    {
        "id": "pdfocr",
        "title": "OCR PDF",
        "subtitle": "Recognize text in scanned PDFs and inject a searchable text layer.",
        "icon": ASSETS_DIR / "tools" / "tool-ocr-pdf.svg",
        "accept": "pdf",
        "multi": False,
        "default_out": "ocr_searchable.pdf",
    },
    {
        "id": "translate",
        "title": "Translate PDF",
        "subtitle": "Translate PDF text blocks while preserving original (x, y) layout coordinates.",
        "icon": ASSETS_DIR / "tools" / "tool-translate-pdf.svg",
        "accept": "pdf",
        "multi": False,
        "default_out": "translated_document.pdf",
    },
    {
        "id": "markdown",
        "title": "PDF to Markdown",
        "subtitle": "Convert PDF headings, lists, and tables into clean LLM-ready Markdown (.md).",
        "icon": ASSETS_DIR / "tools" / "tool-pdf-to-markdown.svg",
        "accept": "pdf",
        "multi": False,
        "default_out": "extracted_document.md",
    },
]

APP_CSS = b"""
window {
    background-color: #F8FAFC;
}
.sidebar {
    background-color: #0F172A;
    color: #F8FAFC;
    padding: 16px 10px;
}
.brand-title {
    color: #FFFFFF;
    font-size: 20px;
    font-weight: 800;
}
.brand-subtitle {
    color: #94A3B8;
    font-size: 11px;
}
.nav-btn {
    background: transparent;
    color: #CBD5E1;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    font-weight: 600;
}
.nav-btn:hover {
    background-color: #1E293B;
    color: #FFFFFF;
}
.nav-btn-active {
    background-color: #2563EB;
    color: #FFFFFF;
}
.tool-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
}
.tool-card:hover {
    border-color: #3B82F6;
}
.card-title {
    color: #0F172A;
    font-size: 15px;
    font-weight: 700;
}
.card-desc {
    color: #64748B;
    font-size: 12px;
}
.panel-box {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px;
}
.primary-btn {
    background-image: none;
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 700;
    border-radius: 8px;
    padding: 10px 18px;
    border: none;
}
.primary-btn:hover {
    background-color: #1D4ED8;
}
.secondary-btn {
    background-image: none;
    background-color: #F1F5F9;
    color: #1E293B;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 14px;
    border: 1px solid #CBD5E1;
}
.file-row {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px;
}
.status-banner {
    background-color: #ECFDF5;
    border: 1px solid #10B981;
    border-radius: 10px;
    padding: 12px 16px;
}
"""


def load_svg_image(svg_path: Path, size: int = 32) -> Gtk.Image:
    """Load an SVG or PNG from `assets/` into a Gtk.Image at the desired pixel size."""
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            str(svg_path), size, size, True
        )
        return Gtk.Image.new_from_pixbuf(pixbuf)
    except Exception:
        return Gtk.Image.new_from_icon_name("application-pdf", Gtk.IconSize.DIALOG)


class PDForgeWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="PDForge — Local PDF Studio")
        self.set_default_size(1140, 740)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Ensure sample data and output dir exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        generate_all_test_data(str(TEST_DATA_DIR))

        # Set window icon from replaceable asset
        logo_path = ASSETS_DIR / "brand" / "pdforge-logo.svg"
        if logo_path.exists():
            try:
                self.set_icon_from_file(str(logo_path))
            except Exception:
                pass

        # Apply CSS styling
        provider = Gtk.CssProvider()
        provider.load_from_data(APP_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.active_tool: Dict[str, Any] = TOOLS_SPEC[0]
        self.file_queue: List[Dict[str, Any]] = []
        self.nav_buttons: Dict[str, Gtk.Button] = {}
        self.last_output_path: Optional[str] = None

        self._build_layout()
        self.show_dashboard()

    def _build_layout(self) -> None:
        root_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(root_hbox)

        # ---------------- LEFT SIDEBAR ----------------
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sidebar.set_size_request(240, -1)
        sidebar.get_style_context().add_class("sidebar")
        root_hbox.pack_start(sidebar, False, False, 0)

        # Brand Header
        brand_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        brand_box.set_margin_bottom(14)
        brand_box.pack_start(
            load_svg_image(ASSETS_DIR / "brand" / "pdforge-logo.svg", 38),
            False,
            False,
            0,
        )
        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_title = Gtk.Label(label="PDForge", xalign=0)
        lbl_title.get_style_context().add_class("brand-title")
        lbl_sub = Gtk.Label(label="Local PDF Workbench", xalign=0)
        lbl_sub.get_style_context().add_class("brand-subtitle")
        title_vbox.pack_start(lbl_title, False, False, 0)
        title_vbox.pack_start(lbl_sub, False, False, 0)
        brand_box.pack_start(title_vbox, True, True, 0)
        sidebar.pack_start(brand_box, False, False, 0)

        # Dashboard Home Button
        home_btn = Gtk.Button()
        home_btn.get_style_context().add_class("nav-btn")
        home_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        home_lbl = Gtk.Label(label="All 9 PDF Tools (Home)", xalign=0)
        home_box.pack_start(home_lbl, True, True, 0)
        home_btn.add(home_box)
        home_btn.connect("clicked", lambda *_: self.show_dashboard())
        sidebar.pack_start(home_btn, False, False, 0)
        self.nav_buttons["home"] = home_btn

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(6)
        sep.set_margin_bottom(6)
        sidebar.pack_start(sep, False, False, 0)

        # Tool Buttons
        for spec in TOOLS_SPEC:
            btn = Gtk.Button()
            btn.get_style_context().add_class("nav-btn")
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            hbox.pack_start(load_svg_image(spec["icon"], 22), False, False, 0)
            lbl = Gtk.Label(label=spec["title"], xalign=0)
            hbox.pack_start(lbl, True, True, 0)
            btn.add(hbox)
            btn.connect("clicked", self._on_select_tool, spec["id"])
            sidebar.pack_start(btn, False, False, 0)
            self.nav_buttons[spec["id"]] = btn

        # ---------------- MAIN CONTENT STACK ----------------
        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.main_stack.set_transition_duration(150)
        root_hbox.pack_start(self.main_stack, True, True, 0)

        self.dashboard_view = self._build_dashboard_view()
        self.workbench_view = self._build_workbench_view()

        self.main_stack.add_named(self.dashboard_view, "dashboard")
        self.main_stack.add_named(self.workbench_view, "workbench")

    def _build_dashboard_view(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        vbox.set_margin_top(24)
        vbox.set_margin_bottom(24)
        vbox.set_margin_start(28)
        vbox.set_margin_end(28)

        header = Gtk.Label(
            label="<b><span size='xx-large' foreground='#0F172A'>Every tool you need to work with PDFs locally</span></b>",
            use_markup=True,
            xalign=0,
        )
        sub = Gtk.Label(
            label="<span size='medium' foreground='#475569'>100% offline-capable local engine • Custom replaceable SVG assets in assets/ • Zero cloud uploads</span>",
            use_markup=True,
            xalign=0,
        )
        vbox.pack_start(header, False, False, 0)
        vbox.pack_start(sub, False, False, 0)

        grid = Gtk.Grid()
        grid.set_column_spacing(16)
        grid.set_row_spacing(16)
        grid.set_column_homogeneous(True)

        for idx, spec in enumerate(TOOLS_SPEC):
            card_btn = Gtk.Button()
            card_btn.get_style_context().add_class("tool-card")
            card_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

            top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            top_row.pack_start(load_svg_image(spec["icon"], 42), False, False, 0)
            t_lbl = Gtk.Label(label=spec["title"], xalign=0)
            t_lbl.get_style_context().add_class("card-title")
            top_row.pack_start(t_lbl, True, True, 0)

            d_lbl = Gtk.Label(label=spec["subtitle"], xalign=0)
            d_lbl.set_line_wrap(True)
            d_lbl.set_max_width_chars(32)
            d_lbl.get_style_context().add_class("card-desc")

            card_vbox.pack_start(top_row, False, False, 0)
            card_vbox.pack_start(d_lbl, False, False, 0)
            card_btn.add(card_vbox)
            card_btn.connect("clicked", self._on_select_tool, spec["id"])

            grid.attach(card_btn, idx % 3, idx // 3, 1, 1)

        vbox.pack_start(grid, False, False, 8)
        scroll.add(vbox)
        return scroll

    def _build_workbench_view(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_margin_top(20)
        outer.set_margin_bottom(20)
        outer.set_margin_start(24)
        outer.set_margin_end(24)

        # Tool Header Bar
        header_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        self.wb_icon = load_svg_image(TOOLS_SPEC[0]["icon"], 44)
        header_hbox.pack_start(self.wb_icon, False, False, 0)

        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.wb_title = Gtk.Label(xalign=0, use_markup=True)
        self.wb_subtitle = Gtk.Label(xalign=0, use_markup=True)
        title_vbox.pack_start(self.wb_title, False, False, 0)
        title_vbox.pack_start(self.wb_subtitle, False, False, 0)
        header_hbox.pack_start(title_vbox, True, True, 0)

        # Quick Load Sample Data Button
        sample_btn = Gtk.Button(label="Load Test Sample")
        sample_btn.get_style_context().add_class("secondary-btn")
        sample_btn.connect("clicked", self._on_load_sample)
        header_hbox.pack_end(sample_btn, False, False, 0)

        add_btn = Gtk.Button()
        add_btn.get_style_context().add_class("secondary-btn")
        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        add_box.pack_start(
            load_svg_image(ASSETS_DIR / "ui" / "ui-add-file.svg", 18), False, False, 0
        )
        add_box.pack_start(Gtk.Label(label="Select File(s)..."), False, False, 0)
        add_btn.add(add_box)
        add_btn.connect("clicked", self._on_pick_files)
        header_hbox.pack_end(add_btn, False, False, 0)

        outer.pack_start(header_hbox, False, False, 0)

        # Main 2-Column Workspace (Left: Files Queue, Right: Tool Options & Execute)
        workspace_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        outer.pack_start(workspace_hbox, True, True, 0)

        # Left Column: File Queue / Empty Dropzone
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        left_panel.get_style_context().add_class("panel-box")
        workspace_hbox.pack_start(left_panel, True, True, 0)

        q_scroll = Gtk.ScrolledWindow()
        q_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.queue_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        q_scroll.add(self.queue_vbox)
        left_panel.pack_start(q_scroll, True, True, 0)

        # Right Column: Tool Options + Run Button
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        right_panel.set_size_request(330, -1)
        right_panel.get_style_context().add_class("panel-box")
        workspace_hbox.pack_start(right_panel, False, False, 0)

        opt_header = Gtk.Label(
            label="<b><span size='large' foreground='#0F172A'>Tool Configuration</span></b>",
            use_markup=True,
            xalign=0,
        )
        right_panel.pack_start(opt_header, False, False, 0)

        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_panel.pack_start(self.options_box, True, True, 0)

        # Resulting Document Name Box
        out_name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        out_name_lbl = Gtk.Label(
            label="<b><span foreground='#0F172A'>Resulting Document Name:</span></b>",
            use_markup=True,
            xalign=0,
        )
        self.output_name_entry = Gtk.Entry()
        self.output_name_entry.set_placeholder_text("e.g. split_pdforge_sample_report_1.pdf")
        out_name_box.pack_start(out_name_lbl, False, False, 0)
        out_name_box.pack_start(self.output_name_entry, False, False, 0)
        right_panel.pack_start(out_name_box, False, False, 4)

        self.run_btn = Gtk.Button(label="Run PDForge Task")
        self.run_btn.get_style_context().add_class("primary-btn")
        self.run_btn.connect("clicked", self._on_run_task)
        right_panel.pack_end(self.run_btn, False, False, 0)

        # Bottom Status Banner
        self.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.status_bar.get_style_context().add_class("status-banner")
        self.status_icon = load_svg_image(
            ASSETS_DIR / "ui" / "ui-status-success.svg", 24
        )
        self.status_lbl = Gtk.Label(xalign=0, use_markup=True)
        self.status_lbl.set_line_wrap(True)

        self.open_folder_btn = Gtk.Button(label="Open Output Folder")
        self.open_folder_btn.get_style_context().add_class("secondary-btn")
        self.open_folder_btn.connect("clicked", self._on_open_output_folder)

        self.status_bar.pack_start(self.status_icon, False, False, 0)
        self.status_bar.pack_start(self.status_lbl, True, True, 0)
        self.status_bar.pack_end(self.open_folder_btn, False, False, 0)
        outer.pack_end(self.status_bar, False, False, 0)

        return outer

    # ---------------- NAVIGATION & STATE ----------------
    def _highlight_nav(self, active_id: str) -> None:
        for k, btn in self.nav_buttons.items():
            ctx = btn.get_style_context()
            if k == active_id:
                ctx.add_class("nav-btn-active")
            else:
                ctx.remove_class("nav-btn-active")

    def show_dashboard(self) -> None:
        self._highlight_nav("home")
        self.main_stack.set_visible_child_name("dashboard")

    def _on_select_tool(self, _widget: Gtk.Widget, tool_id: str) -> None:
        for spec in TOOLS_SPEC:
            if spec["id"] == tool_id:
                self.active_tool = spec
                break

        self._highlight_nav(tool_id)
        self.file_queue.clear()
        self.status_bar.hide()

        # Update Header
        pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            str(self.active_tool["icon"]), 42, 42, True
        )
        self.wb_icon.set_from_pixbuf(pix)
        self.wb_title.set_markup(
            f"<b><span size='x-large' foreground='#0F172A'>{GLib.markup_escape_text(self.active_tool['title'])}</span></b>"
        )
        self.wb_subtitle.set_markup(
            f"<span foreground='#64748B'>{GLib.markup_escape_text(self.active_tool['subtitle'])}</span>"
        )
        self.run_btn.set_label(f"Execute {self.active_tool['title']}")

        self._rebuild_options_panel()
        self._refresh_queue_ui()
        self.main_stack.set_visible_child_name("workbench")

    # ---------------- DYNAMIC TOOL OPTIONS ----------------
    def _rebuild_options_panel(self) -> None:
        for child in self.options_box.get_children():
            self.options_box.remove(child)

        tid = self.active_tool["id"]

        if tid == "merge":
            lbl = Gtk.Label(
                label="• Reorder files using ↑ / ↓ buttons.\n• Rotate individual PDFs (90° steps) before merging.",
                xalign=0,
            )
            lbl.set_line_wrap(True)
            self.options_box.pack_start(lbl, False, False, 0)

        elif tid == "split":
            self.split_mode_combo = Gtk.ComboBoxText()
            self.split_mode_combo.append("ranges", "Custom Page Ranges")
            self.split_mode_combo.append("fixed_range", "Fixed Page Step (Every N pages)")
            self.split_mode_combo.set_active_id("ranges")
            self.options_box.pack_start(
                Gtk.Label(label="Split Mode:", xalign=0), False, False, 0
            )
            self.options_box.pack_start(self.split_mode_combo, False, False, 0)

            self.split_ranges_entry = Gtk.Entry()
            self.split_ranges_entry.set_text("1-2, 3")
            self.options_box.pack_start(
                Gtk.Label(label="Page Ranges (e.g. 1-2, 3):", xalign=0), False, False, 0
            )
            self.options_box.pack_start(self.split_ranges_entry, False, False, 0)

            self.split_merge_chk = Gtk.CheckButton(
                label="Merge extracted ranges into one PDF"
            )
            self.options_box.pack_start(self.split_merge_chk, False, False, 0)

        elif tid == "compress":
            self.comp_combo = Gtk.ComboBoxText()
            self.comp_combo.append("extreme", "Extreme Compression (Smallest size)")
            self.comp_combo.append("recommended", "Recommended Compression (Balanced)")
            self.comp_combo.append("low", "Low Compression (High visual quality)")
            self.comp_combo.set_active_id("recommended")
            self.options_box.pack_start(
                Gtk.Label(label="Compression Profile:", xalign=0), False, False, 0
            )
            self.options_box.pack_start(self.comp_combo, False, False, 0)

        elif tid == "pdfword":
            lbl = Gtk.Label(
                label="Reconstructs headings, paragraphs, and layout spacing into an editable OpenXML (.docx) file.",
                xalign=0,
            )
            lbl.set_line_wrap(True)
            self.options_box.pack_start(lbl, False, False, 0)

        elif tid == "imagepdf":
            self.img_size_combo = Gtk.ComboBoxText()
            self.img_size_combo.append("A4", "A4 (210 × 297 mm)")
            self.img_size_combo.append("Letter", "US Letter")
            self.img_size_combo.append("Fit", "Fit Page to Image Dimensions")
            self.img_size_combo.set_active_id("A4")

            self.img_orient_combo = Gtk.ComboBoxText()
            self.img_orient_combo.append("portrait", "Portrait")
            self.img_orient_combo.append("landscape", "Landscape")
            self.img_orient_combo.set_active_id("portrait")

            self.img_margin_combo = Gtk.ComboBoxText()
            self.img_margin_combo.append("0", "No Margin (0 px)")
            self.img_margin_combo.append("20", "Small Margin (20 px)")
            self.img_margin_combo.append("40", "Big Margin (40 px)")
            self.img_margin_combo.set_active_id("20")

            self.options_box.pack_start(
                Gtk.Label(label="Page Size:", xalign=0), False, False, 0
            )
            self.options_box.pack_start(self.img_size_combo, False, False, 0)
            self.options_box.pack_start(
                Gtk.Label(label="Orientation:", xalign=0), False, False, 0
            )
            self.options_box.pack_start(self.img_orient_combo, False, False, 0)
            self.options_box.pack_start(
                Gtk.Label(label="Margins:", xalign=0), False, False, 0
            )
            self.options_box.pack_start(self.img_margin_combo, False, False, 0)

        elif tid == "htmlpdf":
            self.html_url_entry = Gtk.Entry()
            self.html_url_entry.set_placeholder_text(
                "Or enter https://example.com URL..."
            )
            self.options_box.pack_start(
                Gtk.Label(label="Web URL (or select local .html file):", xalign=0),
                False,
                False,
                0,
            )
            self.options_box.pack_start(self.html_url_entry, False, False, 0)

        elif tid == "pdfocr":
            self.ocr_lang_combo = Gtk.ComboBoxText()
            self.ocr_lang_combo.append("eng", "English (eng)")
            self.ocr_lang_combo.append("spa", "Spanish (spa)")
            self.ocr_lang_combo.set_active_id("eng")
            self.options_box.pack_start(
                Gtk.Label(label="Document OCR Language:", xalign=0), False, False, 0
            )
            self.options_box.pack_start(self.ocr_lang_combo, False, False, 0)

        elif tid == "translate":
            self.trans_src_combo = Gtk.ComboBoxText()
            self.trans_src_combo.append("en", "English (EN)")
            self.trans_src_combo.append("es", "Spanish (ES)")
            self.trans_src_combo.append("ja", "Japanese (日本語)")
            self.trans_src_combo.set_active_id("en")

            self.trans_tgt_combo = Gtk.ComboBoxText()
            self.trans_tgt_combo.append("es", "Spanish (ES)")
            self.trans_tgt_combo.append("en", "English (EN)")
            self.trans_tgt_combo.append("ja", "Japanese (日本語)")
            self.trans_tgt_combo.set_active_id("es")

            self.options_box.pack_start(
                Gtk.Label(label="Source Language:", xalign=0), False, False, 0
            )
            self.options_box.pack_start(self.trans_src_combo, False, False, 0)
            self.options_box.pack_start(
                Gtk.Label(label="Target Language:", xalign=0), False, False, 0
            )
            self.options_box.pack_start(self.trans_tgt_combo, False, False, 0)

        elif tid == "markdown":
            lbl = Gtk.Label(
                label="Extracts document hierarchy (H1/H2/H3), bullet lists, and multi-column tables into clean GitHub-Flavored Markdown (.md).",
                xalign=0,
            )
            lbl.set_line_wrap(True)
            self.options_box.pack_start(lbl, False, False, 0)

        self.options_box.show_all()

    # ---------------- QUEUE MANAGEMENT & PREVIEWS ----------------
    def _refresh_queue_ui(self) -> None:
        for child in self.queue_vbox.get_children():
            self.queue_vbox.remove(child)

        if not self.file_queue:
            empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            empty_box.set_valign(Gtk.Align.CENTER)
            empty_box.set_margin_top(60)
            empty_box.pack_start(
                load_svg_image(ASSETS_DIR / "brand" / "dropzone-empty.svg", 76),
                False,
                False,
                0,
            )
            empty_lbl = Gtk.Label(
                label="<b><span size='large' foreground='#334155'>No files loaded yet</span></b>\n"
                "<span foreground='#64748B'>Click 'Select File(s)...' or 'Load Test Sample' above to begin.</span>",
                use_markup=True,
                justify=Gtk.Justification.CENTER,
            )
            empty_box.pack_start(empty_lbl, False, False, 0)
            self.queue_vbox.pack_start(empty_box, True, True, 0)
        else:
            for idx, item in enumerate(self.file_queue):
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                row.get_style_context().add_class("file-row")

                # Thumbnail preview if available
                thumb_path = item.get("thumb")
                if thumb_path and os.path.exists(thumb_path):
                    pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        thumb_path, 54, 72, True
                    )
                    row.pack_start(Gtk.Image.new_from_pixbuf(pix), False, False, 0)
                else:
                    row.pack_start(
                        load_svg_image(self.active_tool["icon"], 36), False, False, 0
                    )

                # File info
                info_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                fname = os.path.basename(item["path"])
                fsize_kb = os.path.getsize(item["path"]) // 1024
                pages_txt = (
                    f" • {item['pages']} page(s)" if item.get("pages") else ""
                )
                rot_txt = (
                    f" • Rotated {item['rotate']}°" if item.get("rotate", 0) else ""
                )

                name_lbl = Gtk.Label(
                    label=f"<b>{GLib.markup_escape_text(fname)}</b>",
                    use_markup=True,
                    xalign=0,
                )
                name_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
                meta_lbl = Gtk.Label(
                    label=f"<span size='small' foreground='#64748B'>{fsize_kb} KB{pages_txt}{rot_txt}</span>",
                    use_markup=True,
                    xalign=0,
                )
                info_vbox.pack_start(name_lbl, False, False, 0)
                info_vbox.pack_start(meta_lbl, False, False, 0)
                row.pack_start(info_vbox, True, True, 0)

                # Action buttons (Rotate, Move Up/Down, Remove)
                if self.active_tool["id"] == "merge":
                    rot_btn = Gtk.Button()
                    rot_btn.set_tooltip_text("Rotate 90° CW")
                    rot_btn.add(
                        load_svg_image(ASSETS_DIR / "ui" / "ui-rotate-cw.svg", 16)
                    )
                    rot_btn.connect("clicked", self._on_rotate_item, idx)
                    row.pack_start(rot_btn, False, False, 0)

                if len(self.file_queue) > 1:
                    up_btn = Gtk.Button()
                    up_btn.add(load_svg_image(ASSETS_DIR / "ui" / "ui-move-up.svg", 16))
                    up_btn.connect("clicked", self._on_move_item, idx, -1)
                    row.pack_start(up_btn, False, False, 0)

                    dn_btn = Gtk.Button()
                    dn_btn.add(
                        load_svg_image(ASSETS_DIR / "ui" / "ui-move-down.svg", 16)
                    )
                    dn_btn.connect("clicked", self._on_move_item, idx, 1)
                    row.pack_start(dn_btn, False, False, 0)

                del_btn = Gtk.Button()
                del_btn.set_tooltip_text("Remove file")
                del_btn.add(
                    load_svg_image(ASSETS_DIR / "ui" / "ui-remove-file.svg", 16)
                )
                del_btn.connect("clicked", self._on_remove_item, idx)
                row.pack_start(del_btn, False, False, 0)

                self.queue_vbox.pack_start(row, False, False, 0)

        self.queue_vbox.show_all()
        self._update_default_output_name()

    def _update_default_output_name(self) -> None:
        tid = self.active_tool["id"]
        ext = Path(self.active_tool["default_out"]).suffix or ".pdf"
        if self.file_queue:
            first_stem = Path(self.file_queue[0]["path"]).stem
            if tid == "split":
                default_name = f"{tid}_{first_stem}_1{ext}"
            else:
                default_name = f"{tid}_{first_stem}{ext}"
        else:
            default_name = self.active_tool["default_out"]
        self.output_name_entry.set_text(default_name)

    def _add_path_to_queue(self, path: str) -> None:
        if not self.active_tool["multi"]:
            self.file_queue.clear()

        pages = 0
        thumb = None
        if path.lower().endswith(".pdf"):
            pages = get_pdf_page_count(path)
            thumb = render_pdf_thumbnail(path, 1, 100)
        elif path.lower().endswith((".jpg", ".jpeg", ".png")):
            thumb = path

        self.file_queue.append(
            {"path": path, "rotate": 0, "pages": pages, "thumb": thumb}
        )

    def _on_load_sample(self, _btn: Gtk.Button) -> None:
        tid = self.active_tool["id"]
        self.file_queue.clear()

        if tid == "merge":
            self._add_path_to_queue(str(TEST_DATA_DIR / "pdforge_sample_report.pdf"))
            self._add_path_to_queue(str(TEST_DATA_DIR / "pdforge_appendix_b.pdf"))
        elif tid == "imagepdf":
            self._add_path_to_queue(str(TEST_DATA_DIR / "calibration_card_1.jpg"))
            self._add_path_to_queue(str(TEST_DATA_DIR / "calibration_card_2.jpg"))
        elif tid == "htmlpdf":
            self._add_path_to_queue(str(TEST_DATA_DIR / "sample_webpage.html"))
        else:
            self._add_path_to_queue(str(TEST_DATA_DIR / "pdforge_sample_report.pdf"))

        self._refresh_queue_ui()

    def _on_pick_files(self, _btn: Gtk.Button) -> None:
        dlg = Gtk.FileChooserDialog(
            title=f"Select file(s) for {self.active_tool['title']}",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dlg.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        dlg.set_select_multiple(self.active_tool["multi"])
        downloads_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        if not downloads_dir or not os.path.isdir(downloads_dir):
            downloads_dir = str(Path.home() / "Downloads")
        if os.path.isdir(downloads_dir):
            dlg.set_current_folder(downloads_dir)
        else:
            dlg.set_current_folder(str(Path.home()))

        flt = Gtk.FileFilter()
        accept = self.active_tool["accept"]
        if accept == "pdf":
            flt.set_name("PDF Documents (*.pdf)")
            flt.add_pattern("*.pdf")
        elif accept == "image":
            flt.set_name("Images (*.jpg, *.jpeg, *.png)")
            flt.add_pattern("*.jpg")
            flt.add_pattern("*.jpeg")
            flt.add_pattern("*.png")
        else:
            flt.set_name("HTML Files (*.html, *.htm)")
            flt.add_pattern("*.html")
            flt.add_pattern("*.htm")
        dlg.add_filter(flt)

        if dlg.run() == Gtk.ResponseType.OK:
            for p in dlg.get_filenames():
                self._add_path_to_queue(p)
            self._refresh_queue_ui()
        dlg.destroy()

    def _on_rotate_item(self, _btn: Gtk.Button, idx: int) -> None:
        self.file_queue[idx]["rotate"] = (self.file_queue[idx]["rotate"] + 90) % 360
        self._refresh_queue_ui()

    def _on_move_item(self, _btn: Gtk.Button, idx: int, delta: int) -> None:
        new_idx = idx + delta
        if 0 <= new_idx < len(self.file_queue):
            self.file_queue[idx], self.file_queue[new_idx] = (
                self.file_queue[new_idx],
                self.file_queue[idx],
            )
            self._refresh_queue_ui()

    def _on_remove_item(self, _btn: Gtk.Button, idx: int) -> None:
        if 0 <= idx < len(self.file_queue):
            self.file_queue.pop(idx)
            self._refresh_queue_ui()

    # ---------------- TASK EXECUTION ----------------
    def _on_run_task(self, _btn: Gtk.Button) -> None:
        tid = self.active_tool["id"]

        if tid != "htmlpdf" and not self.file_queue:
            self._show_status("Please select at least one input file first.", error=True)
            return

        custom_name = self.output_name_entry.get_text().strip()
        if not custom_name:
            custom_name = self.active_tool["default_out"]
        default_ext = Path(self.active_tool["default_out"]).suffix or ".pdf"
        if not Path(custom_name).suffix:
            custom_name += default_ext
        out_path = str(OUTPUT_DIR / os.path.basename(custom_name))
        self.run_btn.set_sensitive(False)
        self.run_btn.set_label("Processing locally...")

        def worker() -> None:
            try:
                if tid == "merge":
                    res = merge_pdfs(self.file_queue, out_path)
                elif tid == "split":
                    mode = self.split_mode_combo.get_active_id() or "ranges"
                    rng = self.split_ranges_entry.get_text().strip()
                    merge_after = self.split_merge_chk.get_active()
                    step = int(rng) if (mode == "fixed_range" and rng.isdigit()) else 1
                    res = split_pdf(
                        self.file_queue[0]["path"],
                        out_path,
                        split_mode=mode,
                        ranges_str=rng,
                        fixed_step=step,
                        merge_after=merge_after,
                    )
                elif tid == "compress":
                    lvl = self.comp_combo.get_active_id() or "recommended"
                    res = compress_pdf(self.file_queue[0]["path"], out_path, lvl)
                elif tid == "pdfword":
                    res = pdf_to_word(self.file_queue[0]["path"], out_path)
                elif tid == "imagepdf":
                    psize = self.img_size_combo.get_active_id() or "A4"
                    orient = self.img_orient_combo.get_active_id() or "portrait"
                    margin = int(self.img_margin_combo.get_active_id() or "20")
                    res = jpg_to_pdf(
                        [x["path"] for x in self.file_queue],
                        out_path,
                        page_size=psize,
                        orientation=orient,
                        margin_px=margin,
                    )
                elif tid == "htmlpdf":
                    url_txt = self.html_url_entry.get_text().strip()
                    src = (
                        url_txt
                        if url_txt
                        else (
                            self.file_queue[0]["path"]
                            if self.file_queue
                            else str(TEST_DATA_DIR / "sample_webpage.html")
                        )
                    )
                    res = html_to_pdf(src, out_path)
                elif tid == "pdfocr":
                    lang = self.ocr_lang_combo.get_active_id() or "eng"
                    res = ocr_pdf(self.file_queue[0]["path"], out_path, lang)
                elif tid == "translate":
                    sl = self.trans_src_combo.get_active_id() or "en"
                    tl = self.trans_tgt_combo.get_active_id() or "es"
                    res = translate_pdf(self.file_queue[0]["path"], out_path, sl, tl)
                elif tid == "markdown":
                    res = pdf_to_markdown(self.file_queue[0]["path"], out_path)
                else:
                    raise ValueError(f"Unknown tool: {tid}")

                GLib.idle_add(self._on_task_complete, res, False)
            except Exception as exc:
                GLib.idle_add(
                    self._on_task_complete,
                    {"message": f"Error: {exc}", "output_path": None},
                    True,
                )

        threading.Thread(target=worker, daemon=True).start()

    def _on_task_complete(self, res: Dict[str, Any], is_error: bool) -> bool:
        self.run_btn.set_sensitive(True)
        self.run_btn.set_label(f"Execute {self.active_tool['title']}")
        self.last_output_path = res.get("output_path")

        msg = GLib.markup_escape_text(res.get("message", "Done."))
        if self.last_output_path:
            msg += f"\n<span size='small' foreground='#047857'>Saved to: {GLib.markup_escape_text(self.last_output_path)}</span>"
        self._show_status(msg, error=is_error)
        return False

    def _show_status(self, markup_msg: str, error: bool = False) -> None:
        icon_file = (
            ASSETS_DIR / "ui" / ("ui-status-warning.svg" if error else "ui-status-success.svg")
        )
        pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(icon_file), 24, 24, True)
        self.status_icon.set_from_pixbuf(pix)
        self.status_lbl.set_markup(f"<b>{markup_msg}</b>")
        self.status_bar.show_all()

    def _on_open_output_folder(self, _btn: Gtk.Button) -> None:
        target_dir = str(OUTPUT_DIR)
        try:
            subprocess.Popen(["xdg-open", target_dir])
        except Exception:
            pass


def main() -> None:
    win = PDForgeWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    win.status_bar.hide()
    Gtk.main()


if __name__ == "__main__":
    main()

