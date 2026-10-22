# -*- coding: utf-8 -*-
"""
PhotoCheck UI - Visual Duplicate Photo Review and Cleanup
Styled with Windows 11 Fluent Design aesthetics (Light and Dark Mode).
"""

import os
import sys
import threading
import queue
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ExifTags

# High-DPI awareness on Windows
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import PhotoCheck

# Windows 11 Fluent Design Theme Palettes
THEMES = {
    "light": {
        "bg": "#f3f3f3",
        "card_bg": "#ffffff",
        "card_border": "#e5e5e5",
        "panel_bg": "#fbfbfd",
        "panel_border": "#ececf1",
        "text_primary": "#1a1a1a",
        "text_secondary": "#5f6368",
        "text_muted": "#8c959f",
        "canvas_bg": "#f8f9fa",
        "canvas_border": "#e9ecef",
        "entry_bg": "#ffffff",
        "entry_fg": "#1a1a1a",
        "entry_border": "#d1d1d1",
        "accent": "#0067c0",
        "accent_hover": "#1975c5",
        "accent_active": "#005fb8",
        "accent_fg": "#ffffff",
        "badge_ref_bg": "#eef4fa",
        "badge_ref_fg": "#0067c0",
        "badge_dup_bg": "#f5f0fa",
        "badge_dup_fg": "#673ab7",
        "btn_sec_bg": "#ffffff",
        "btn_sec_fg": "#1a1a1a",
        "btn_sec_hover": "#f5f5f5",
        "btn_sec_active": "#ebebeb",
        "btn_sec_border": "#c8c8c8",
        "btn_danger_bg": "#fff0f0",
        "btn_danger_fg": "#c42b1c",
        "btn_danger_hover": "#fde0e0",
        "btn_danger_active": "#fad0d0",
        "btn_danger_border": "#f5c2c7",
        "btn_inactive_bg": "#f0f0f0",
        "btn_inactive_fg": "#888888",
        "btn_inactive_border": "#d8d8d8",
        "pill_unsel_bg": "#ffffff",
        "pill_unsel_fg": "#333333",
        "pill_unsel_border": "#d0d0d0",
        "progress_trough": "#e5e5e5",
        "progress_bar": "#0067c0",
    },
    "dark": {
        "bg": "#202020",
        "card_bg": "#2b2b2b",
        "card_border": "#3a3a3a",
        "panel_bg": "#232323",
        "panel_border": "#363636",
        "text_primary": "#f3f3f3",
        "text_secondary": "#a8a8a8",
        "text_muted": "#7a7a7a",
        "canvas_bg": "#1c1c1c",
        "canvas_border": "#363636",
        "entry_bg": "#333333",
        "entry_fg": "#f3f3f3",
        "entry_border": "#4c4c4c",
        "accent": "#0078d4",
        "accent_hover": "#1a8ae5",
        "accent_active": "#0067c0",
        "accent_fg": "#ffffff",
        "badge_ref_bg": "#17304a",
        "badge_ref_fg": "#4cc2ff",
        "badge_dup_bg": "#362247",
        "badge_dup_fg": "#c792ea",
        "btn_sec_bg": "#383838",
        "btn_sec_fg": "#f3f3f3",
        "btn_sec_hover": "#444444",
        "btn_sec_active": "#4d4d4d",
        "btn_sec_border": "#555555",
        "btn_danger_bg": "#3e1e1e",
        "btn_danger_fg": "#ff7b72",
        "btn_danger_hover": "#4e2424",
        "btn_danger_active": "#5e2b2b",
        "btn_danger_border": "#632828",
        "btn_inactive_bg": "#333333",
        "btn_inactive_fg": "#9e9e9e",
        "btn_inactive_border": "#484848",
        "pill_unsel_bg": "#343434",
        "pill_unsel_fg": "#d0d0d0",
        "pill_unsel_border": "#4a4a4a",
        "progress_trough": "#383838",
        "progress_bar": "#0078d4",
    },
}


def detect_system_dark_mode():
    """Check Windows registry for dark theme preference."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return val == 0
        except Exception:
            pass
    return False


def set_native_window_dark_mode(window, is_dark: bool):
    """Set Windows 11 DWM title bar theme attribute."""
    if sys.platform == "win32":
        try:
            window.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            if not hwnd:
                hwnd = window.winfo_id()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            val = ctypes.c_int(1 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(val),
                ctypes.sizeof(val)
            )
        except Exception:
            pass


def format_size(size_bytes):
    """Format file size in human-readable units."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def extract_exif_date_taken(img):
    """Extract photo capture timestamp from EXIF metadata if present."""
    try:
        exif = img.getexif()
        if not exif:
            return None
        for tag_id in (36867, 36868, 306):
            val = exif.get(tag_id)
            if val:
                return str(val).strip()
        try:
            sub_ifd = exif.get_ifd(ExifTags.IFD.Exif)
            for tag_id in (36867, 36868, 306):
                val = sub_ifd.get(tag_id)
                if val:
                    return str(val).strip()
        except Exception:
            pass
    except Exception:
        pass
    return None


class FluentButton(tk.Button):
    """High-contrast Fluent styled button with dynamic theme adaptation."""

    def __init__(self, parent, text="", style_type="secondary", command=None, width=None, padx=16, pady=8, font_size=9, **kwargs):
        self.style_type = style_type
        self.command_callback = command
        self._is_enabled = True

        self.normal_bg = "#ffffff"
        self.normal_fg = "#1a1a1a"
        self.hover_bg = "#f5f5f5"
        self.active_bg = "#ebebeb"
        self.active_fg = "#1a1a1a"
        self.border_color = "#c8c8c8"
        self.inactive_bg = "#f0f0f0"
        self.inactive_fg = "#888888"
        self.inactive_border = "#d8d8d8"

        super().__init__(
            parent,
            text=text,
            font=("Segoe UI", font_size, "bold" if style_type in ("primary", "danger") else "normal"),
            relief="solid",
            bd=1,
            highlightthickness=0,
            padx=padx,
            pady=pady,
            cursor="hand2",
            command=self._on_click,
            width=width,
            **kwargs
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_click(self):
        if self._is_enabled and self.command_callback:
            self.command_callback()

    def apply_theme(self, theme: dict):
        if self.style_type == "primary":
            self.normal_bg = theme["accent"]
            self.normal_fg = theme["accent_fg"]
            self.hover_bg = theme["accent_hover"]
            self.active_bg = theme["accent_active"]
            self.active_fg = theme["accent_fg"]
            self.border_color = theme["accent"]
            self.config(relief="flat", bd=0)
        elif self.style_type == "danger":
            self.normal_bg = theme["btn_danger_bg"]
            self.normal_fg = theme["btn_danger_fg"]
            self.hover_bg = theme["btn_danger_hover"]
            self.active_bg = theme["btn_danger_active"]
            self.active_fg = theme["btn_danger_fg"]
            self.border_color = theme["btn_danger_border"]
            self.config(relief="solid", bd=1)
        else:
            self.normal_bg = theme["btn_sec_bg"]
            self.normal_fg = theme["btn_sec_fg"]
            self.hover_bg = theme["btn_sec_hover"]
            self.active_bg = theme["btn_sec_active"]
            self.active_fg = theme["btn_sec_fg"]
            self.border_color = theme["btn_sec_border"]
            self.config(relief="solid", bd=1)

        self.inactive_bg = theme["btn_inactive_bg"]
        self.inactive_fg = theme["btn_inactive_fg"]
        self.inactive_border = theme["btn_inactive_border"]

        self._render_state()

    def _render_state(self):
        if self._is_enabled:
            self.config(
                bg=self.normal_bg,
                fg=self.normal_fg,
                activebackground=self.active_bg,
                activeforeground=self.active_fg,
                cursor="hand2"
            )
            if self.style_type != "primary":
                self.config(highlightbackground=self.border_color)
        else:
            self.config(
                bg=self.inactive_bg,
                fg=self.inactive_fg,
                activebackground=self.inactive_bg,
                activeforeground=self.inactive_fg,
                cursor="arrow"
            )
            if self.style_type != "primary":
                self.config(highlightbackground=self.inactive_border)

    def _on_enter(self, e):
        if self._is_enabled:
            self.config(bg=self.hover_bg)

    def _on_leave(self, e):
        if self._is_enabled:
            self.config(bg=self.normal_bg)

    def set_enabled(self, enabled: bool):
        self._is_enabled = enabled
        self._render_state()


class SimilarityPillSelector(tk.Frame):
    """Modern Windows 11 high-contrast segmented pill buttons for similarity threshold."""

    OPTIONS = [
        (0, "0 (Exact)"),
        (2, "2 (Strict)"),
        (4, "4 (Balanced)"),
        (6, "6 (Relaxed)"),
        (8, "8 (Loose)"),
    ]

    DESCRIPTIONS = {
        0: "Exact match: detects byte-identical, re-saved, and format-converted copies.",
        2: "Strict match: allows minor compression artifacts or imperceptible noise.",
        4: "Balanced match: catches slightly edited, compressed, or resized photos.",
        6: "Relaxed match: catches photos with moderate cropping, color tuning, or filters.",
        8: "Loose match: catches photos with substantial visual edits or different angles.",
    }

    def __init__(self, parent, on_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.selected_value = 0
        self.on_change = on_change
        self.current_theme = THEMES["light"]
        self.buttons = {}

        # Pill row container
        self.pills_frame = tk.Frame(self)
        self.pills_frame.pack(side="left")

        for val, label_text in self.OPTIONS:
            btn = tk.Button(
                self.pills_frame,
                text=label_text,
                font=("Segoe UI", 9),
                relief="solid",
                bd=1,
                highlightthickness=0,
                padx=11,
                pady=4,
                cursor="hand2",
                command=lambda v=val: self.select(v)
            )
            btn.pack(side="left", padx=(0, 4))
            self.buttons[val] = btn

        # Description label
        self.desc_label = tk.Label(
            self,
            text="",
            font=("Segoe UI", 8),
            anchor="w"
        )
        self.desc_label.pack(side="left", padx=(8, 0))
        self._update_desc()

    def select(self, val):
        self.selected_value = val
        self._update_desc()
        self._update_button_styles()
        if self.on_change:
            self.on_change(val)

    def get(self):
        return self.selected_value

    def _update_desc(self):
        desc = self.DESCRIPTIONS.get(self.selected_value, "")
        self.desc_label.config(text=f"({desc})")

    def _update_button_styles(self):
        t = self.current_theme
        for val, btn in self.buttons.items():
            if val == self.selected_value:
                # Active selected pill
                btn.config(
                    bg=t["accent"],
                    fg=t["accent_fg"],
                    font=("Segoe UI", 9, "bold"),
                    activebackground=t["accent_hover"],
                    activeforeground=t["accent_fg"],
                    relief="flat",
                    bd=0
                )
            else:
                # Inactive pill
                btn.config(
                    bg=t["pill_unsel_bg"],
                    fg=t["pill_unsel_fg"],
                    font=("Segoe UI", 9),
                    activebackground=t["btn_sec_hover"],
                    activeforeground=t["pill_unsel_fg"],
                    relief="solid",
                    bd=1,
                    highlightbackground=t["pill_unsel_border"]
                )

    def apply_theme(self, theme: dict):
        self.current_theme = theme
        self.config(bg=theme["card_bg"])
        self.pills_frame.config(bg=theme["card_bg"])
        self.desc_label.config(bg=theme["card_bg"], fg=theme["text_secondary"])
        self._update_button_styles()


class ImageCard(tk.Frame):
    """Card widget displaying a photo thumbnail and detailed file metadata."""

    def __init__(self, parent, title="Image A", badge_text="REFERENCE", is_reference=True, **kwargs):
        super().__init__(
            parent,
            padx=16,
            pady=16,
            **kwargs
        )
        self.file_path = None
        self.photo_img = None
        self.is_reference = is_reference
        self.badge_text = badge_text
        self.current_theme = THEMES["light"]

        # 1. Card Header: Title + Pill Badge
        self.header_frame = tk.Frame(self)
        self.header_frame.pack(fill="x", pady=(0, 10))

        self.title_label = tk.Label(
            self.header_frame,
            text=title,
            font=("Segoe UI", 12, "bold")
        )
        self.title_label.pack(side="left")

        self.badge = tk.Label(
            self.header_frame,
            text=f" {badge_text} ",
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=2
        )
        self.badge.pack(side="right")

        # 2. Thumbnail Preview Canvas
        self.canvas_size = (420, 260)
        self.canvas = tk.Canvas(
            self,
            width=self.canvas_size[0],
            height=self.canvas_size[1],
            highlightthickness=1
        )
        self.canvas.pack(fill="both", expand=True)

        # 3. Inner Metadata Panel
        self.meta_container = tk.Frame(
            self,
            highlightthickness=1,
            padx=12,
            pady=10
        )
        self.meta_container.pack(fill="x", pady=(12, 0))

        # Path display row
        self.path_row = tk.Frame(self.meta_container)
        self.path_row.pack(fill="x", pady=(0, 6))

        self.path_label = tk.Label(
            self.path_row,
            text="PATH:",
            font=("Segoe UI", 8, "bold"),
            width=9,
            anchor="w"
        )
        self.path_label.pack(side="left")

        self.path_var = tk.StringVar(value="-")
        self.path_entry = tk.Entry(
            self.path_row,
            textvariable=self.path_var,
            state="readonly",
            font=("Segoe UI", 8),
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        self.path_entry.pack(side="left", fill="x", expand=True)

        # Metadata grid
        self.grid_frame = tk.Frame(self.meta_container)
        self.grid_frame.pack(fill="x")
        grid_cols = [
            ("RESOLUTION", "res_val"),
            ("FILE SIZE", "size_val"),
            ("DATE TAKEN", "taken_val"),
            ("CREATED", "created_val"),
            ("MODIFIED", "modified_val"),
        ]

        self.val_labels = {}
        self.key_labels = []
        for r_idx, (text, key) in enumerate(grid_cols):
            lbl_title = tk.Label(
                self.grid_frame,
                text=text + ":",
                font=("Segoe UI", 8, "bold"),
                anchor="w",
                width=11
            )
            lbl_title.grid(row=r_idx, column=0, sticky="w", pady=2)
            self.key_labels.append(lbl_title)

            lbl_val = tk.Label(
                self.grid_frame,
                text="-",
                font=("Segoe UI", 8),
                anchor="w"
            )
            lbl_val.grid(row=r_idx, column=1, sticky="w", pady=2)
            self.val_labels[key] = lbl_val

        # 4. Action Buttons
        self.btn_row = tk.Frame(self)
        self.btn_row.pack(fill="x", pady=(12, 0))

        self.open_btn = FluentButton(self.btn_row, text="Open in Viewer", style_type="secondary", command=self.open_file)
        self.open_btn.pack(side="left", padx=(0, 6))

        self.folder_btn = FluentButton(self.btn_row, text="Show in Folder", style_type="secondary", command=self.open_folder)
        self.folder_btn.pack(side="left")

        self.clear()

    def apply_theme(self, theme: dict):
        self.current_theme = theme
        self.config(
            bg=theme["card_bg"],
            highlightbackground=theme["card_border"],
            highlightthickness=1
        )
        self.header_frame.config(bg=theme["card_bg"])
        self.title_label.config(bg=theme["card_bg"], fg=theme["text_primary"])

        if self.is_reference:
            self.badge.config(bg=theme["badge_ref_bg"], fg=theme["badge_ref_fg"])
        else:
            self.badge.config(bg=theme["badge_dup_bg"], fg=theme["badge_dup_fg"])

        self.canvas.config(
            bg=theme["canvas_bg"],
            highlightbackground=theme["canvas_border"]
        )

        self.meta_container.config(
            bg=theme["panel_bg"],
            highlightbackground=theme["panel_border"]
        )
        self.path_row.config(bg=theme["panel_bg"])
        self.path_label.config(bg=theme["panel_bg"], fg=theme["text_secondary"])
        self.path_entry.config(
            bg=theme["entry_bg"],
            fg=theme["entry_fg"],
            readonlybackground=theme["entry_bg"]
        )

        self.grid_frame.config(bg=theme["panel_bg"])
        for lbl in self.key_labels:
            lbl.config(bg=theme["panel_bg"], fg=theme["text_secondary"])

        for key in self.val_labels:
            self.val_labels[key].config(bg=theme["panel_bg"], fg=theme["text_primary"])

        self.btn_row.config(bg=theme["card_bg"])
        self.open_btn.apply_theme(theme)
        self.folder_btn.apply_theme(theme)

        if not self.file_path:
            self.canvas.delete("all")
            self.canvas.create_text(
                self.canvas_size[0] // 2,
                self.canvas_size[1] // 2,
                text="No image loaded",
                fill=theme["text_muted"],
                font=("Segoe UI", 10)
            )

    def load_image(self, path):
        self.file_path = path
        if not path or not os.path.exists(path):
            self.clear()
            return

        self.path_var.set(os.path.abspath(path))

        # Filesystem metadata
        try:
            stat = os.stat(path)
            size_formatted = format_size(stat.st_size)
            size_exact = f"{size_formatted}  ({stat.st_size:,} bytes)"
            self.val_labels["size_val"].config(text=size_exact)

            ctime_str = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d  %H:%M:%S")
            self.val_labels["created_val"].config(text=ctime_str)

            mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d  %H:%M:%S")
            self.val_labels["modified_val"].config(text=mtime_str)
        except Exception:
            self.val_labels["size_val"].config(text="Unknown")
            self.val_labels["created_val"].config(text="Unknown")
            self.val_labels["modified_val"].config(text="Unknown")

        # Image thumbnail & EXIF
        try:
            with Image.open(path) as img:
                w, h = img.size
                self.val_labels["res_val"].config(text=f"{w} × {h} px")

                exif_date = extract_exif_date_taken(img)
                if exif_date:
                    self.val_labels["taken_val"].config(text=exif_date)
                else:
                    self.val_labels["taken_val"].config(text="Not available (no EXIF tag)")

                preview = img.copy()
                preview.thumbnail(self.canvas_size, Image.Resampling.LANCZOS)
                self.photo_img = ImageTk.PhotoImage(preview)

                self.canvas.delete("all")
                cx = self.canvas_size[0] // 2
                cy = self.canvas_size[1] // 2
                self.canvas.create_image(cx, cy, image=self.photo_img, anchor="center")
        except Exception as err:
            self.canvas.delete("all")
            self.canvas.create_text(
                self.canvas_size[0] // 2,
                self.canvas_size[1] // 2,
                text=f"Error previewing image:\n{err}",
                fill="#cc0000",
                justify="center",
                font=("Segoe UI", 9)
            )
            self.val_labels["res_val"].config(text="Error reading image")
            self.val_labels["taken_val"].config(text="Not available")

    def clear(self):
        self.file_path = None
        self.photo_img = None
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas_size[0] // 2,
            self.canvas_size[1] // 2,
            text="No image loaded",
            fill=self.current_theme["text_muted"],
            font=("Segoe UI", 10)
        )
        self.path_var.set("-")
        for key in self.val_labels:
            self.val_labels[key].config(text="-")

    def open_file(self):
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.startfile(self.file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open photo:\n{e}")

    def open_folder(self):
        if self.file_path and os.path.exists(self.file_path):
            try:
                subprocess.run(["explorer", f"/select,{os.path.normpath(self.file_path)}"])
            except Exception:
                try:
                    os.startfile(os.path.dirname(self.file_path))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open folder:\n{e}")


class PhotoCheckUI(tk.Tk):
    """Main application window with dynamic light and dark theme switching."""

    def __init__(self):
        super().__init__()
        self.title("PhotoCheck - Duplicate Photo Detector")
        self.geometry("1100x890")
        self.minsize(980, 760)

        # Style engine
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Detect system preference on launch
        self.is_dark = detect_system_dark_mode()
        self.current_theme = THEMES["dark" if self.is_dark else "light"]

        # Data state
        self.clusters = []
        self.current_cluster_idx = 0
        self.compare_idx = 1
        self.total_comparisons_done = 0
        self.total_deleted = 0
        self.total_freed_bytes = 0
        self.scan_queue = queue.Queue()
        self.is_scanning = False

        self._build_ui()
        self._bind_shortcuts()
        self.apply_theme()
        self.after(100, self._process_scan_queue)

    def _build_ui(self):
        self.main_container = tk.Frame(self)
        self.main_container.pack(fill="both", expand=True, padx=16, pady=14)

        # 1. Top Card: Command & Scan Settings Bar
        self.top_card = tk.Frame(
            self.main_container,
            padx=16,
            pady=14
        )
        self.top_card.pack(fill="x", pady=(0, 10))

        # Title row inside card
        self.top_title_row = tk.Frame(self.top_card)
        self.top_title_row.pack(fill="x", pady=(0, 10))

        self.app_title_label = tk.Label(
            self.top_title_row,
            text="Scan Settings",
            font=("Segoe UI", 11, "bold")
        )
        self.app_title_label.pack(side="left")

        # Theme toggle button in top title row
        self.theme_btn = FluentButton(
            self.top_title_row,
            text="Toggle Theme",
            style_type="secondary",
            command=self.toggle_theme,
            font_size=8,
            padx=10,
            pady=3
        )
        self.theme_btn.pack(side="right")

        # Folder selection row
        self.folder_row = tk.Frame(self.top_card)
        self.folder_row.pack(fill="x", pady=2)

        self.folder_lbl = tk.Label(
            self.folder_row,
            text="Target Folder:",
            font=("Segoe UI", 9, "bold"),
            width=13,
            anchor="w"
        )
        self.folder_lbl.pack(side="left")

        self.folder_var = tk.StringVar(value=os.getcwd())
        self.folder_entry = tk.Entry(
            self.folder_row,
            textvariable=self.folder_var,
            font=("Segoe UI", 9),
            relief="solid",
            bd=1,
            highlightthickness=0
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)

        self.browse_btn = FluentButton(self.folder_row, text="Browse...", style_type="secondary", command=self.browse_folder)
        self.browse_btn.pack(side="left", padx=(0, 8))

        self.scan_btn = FluentButton(self.folder_row, text="Scan for Duplicates", style_type="primary", command=self.start_scan)
        self.scan_btn.pack(side="left")

        # Options row
        self.opts_row = tk.Frame(self.top_card)
        self.opts_row.pack(fill="x", pady=(10, 0))

        self.sim_lbl = tk.Label(
            self.opts_row,
            text="Similarity:",
            font=("Segoe UI", 9, "bold"),
            width=13,
            anchor="w"
        )
        self.sim_lbl.pack(side="left")

        # High-contrast segmented pill buttons
        self.sim_selector = SimilarityPillSelector(self.opts_row)
        self.sim_selector.pack(side="left")

        self.confirm_delete_var = tk.BooleanVar(value=False)
        self.confirm_chk = tk.Checkbutton(
            self.opts_row,
            text="Confirm before deleting",
            variable=self.confirm_delete_var,
            font=("Segoe UI", 9),
            highlightthickness=0,
            bd=0
        )
        self.confirm_chk.pack(side="right")

        # 2. Status & Progress Strip
        self.status_card = tk.Frame(
            self.main_container,
            padx=14,
            pady=8
        )
        self.status_card.pack(fill="x", pady=(0, 10))

        self.indicator_dot = tk.Label(self.status_card, text="●", font=("Segoe UI", 10))
        self.indicator_dot.pack(side="left", padx=(0, 6))

        self.status_var = tk.StringVar(value="Ready. Select a folder and click 'Scan for Duplicates'.")
        self.status_label = tk.Label(
            self.status_card,
            textvariable=self.status_var,
            font=("Segoe UI", 9)
        )
        self.status_label.pack(side="left")

        self.progress_bar = ttk.Progressbar(self.status_card, style="Horizontal.TProgressbar", mode="determinate", length=220)
        self.progress_bar.pack(side="right")

        # 3. Main Side-by-Side Comparison Frame
        self.compare_frame = tk.Frame(self.main_container)
        self.compare_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.compare_frame.columnconfigure(0, weight=1)
        self.compare_frame.columnconfigure(1, weight=1)
        self.compare_frame.rowconfigure(0, weight=1)

        self.left_card = ImageCard(
            self.compare_frame,
            title="Image A (Left)",
            badge_text="REFERENCE",
            is_reference=True
        )
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.right_card = ImageCard(
            self.compare_frame,
            title="Image B (Right)",
            badge_text="DUPLICATE",
            is_reference=False
        )
        self.right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # 4. Decision Bar Card (Bottom)
        self.decision_card = tk.Frame(
            self.main_container,
            padx=16,
            pady=14
        )
        self.decision_card.pack(fill="x")

        self.dec_header = tk.Frame(self.decision_card)
        self.dec_header.pack(fill="x", pady=(0, 8))

        self.dec_title = tk.Label(
            self.dec_header,
            text="Decision",
            font=("Segoe UI", 11, "bold")
        )
        self.dec_title.pack(side="left")

        self.dec_hint = tk.Label(
            self.dec_header,
            text="Use keyboard shortcuts: [A] Keep Left, [D] Keep Right, [K] Keep Both, [Del] Delete Both",
            font=("Segoe UI", 8)
        )
        self.dec_hint.pack(side="right")

        # Decision sub-notice
        self.dec_notice = tk.Label(
            self.decision_card,
            text="Waiting for scan. Click 'Scan for Duplicates' to begin reviewing photo matches.",
            font=("Segoe UI", 8),
            anchor="w"
        )
        self.dec_notice.pack(fill="x", pady=(0, 10))

        self.btn_row = tk.Frame(self.decision_card)
        self.btn_row.pack(fill="x", expand=True)

        self.keep_left_btn = FluentButton(
            self.btn_row,
            text="Keep Left, Delete Right [A]",
            style_type="primary",
            command=self.action_keep_left,
            font_size=10,
            pady=10
        )
        self.keep_left_btn.pack(side="left", fill="x", expand=True, padx=4)

        self.keep_both_btn = FluentButton(
            self.btn_row,
            text="Keep Both (Skip) [K]",
            style_type="secondary",
            command=self.action_keep_both,
            font_size=10,
            pady=10
        )
        self.keep_both_btn.pack(side="left", fill="x", expand=True, padx=4)

        self.keep_right_btn = FluentButton(
            self.btn_row,
            text="Keep Right, Delete Left [D]",
            style_type="primary",
            command=self.action_keep_right,
            font_size=10,
            pady=10
        )
        self.keep_right_btn.pack(side="left", fill="x", expand=True, padx=4)

        self.delete_both_btn = FluentButton(
            self.btn_row,
            text="Delete Both [Del]",
            style_type="danger",
            command=self.action_delete_both,
            font_size=10,
            pady=10
        )
        self.delete_both_btn.pack(side="left", fill="x", expand=True, padx=4)

        self._set_action_buttons_state(False)

    def toggle_theme(self):
        """Toggle between Windows 11 Light and Dark mode."""
        self.is_dark = not self.is_dark
        self.current_theme = THEMES["dark" if self.is_dark else "light"]
        self.apply_theme()

    def apply_theme(self):
        """Apply current color palette to window, title bar, and all widgets."""
        t = self.current_theme
        set_native_window_dark_mode(self, self.is_dark)

        # Window & containers
        self.configure(bg=t["bg"])
        self.main_container.configure(bg=t["bg"])
        self.compare_frame.configure(bg=t["bg"])

        # Top settings card
        self.top_card.configure(
            bg=t["card_bg"],
            highlightbackground=t["card_border"],
            highlightthickness=1
        )
        self.top_title_row.configure(bg=t["card_bg"])
        self.app_title_label.configure(bg=t["card_bg"], fg=t["text_primary"])
        self.theme_btn.config(text="Mode: Dark" if self.is_dark else "Mode: Light")
        self.theme_btn.apply_theme(t)

        self.folder_row.configure(bg=t["card_bg"])
        self.folder_lbl.configure(bg=t["card_bg"], fg=t["text_primary"])
        self.folder_entry.configure(
            bg=t["entry_bg"],
            fg=t["entry_fg"],
            insertbackground=t["text_primary"],
            highlightbackground=t["entry_border"]
        )
        self.browse_btn.apply_theme(t)
        self.scan_btn.apply_theme(t)

        self.opts_row.configure(bg=t["card_bg"])
        self.sim_lbl.configure(bg=t["card_bg"], fg=t["text_primary"])
        self.sim_selector.apply_theme(t)
        self.confirm_chk.configure(
            bg=t["card_bg"],
            fg=t["text_primary"],
            activebackground=t["card_bg"],
            activeforeground=t["text_primary"],
            selectcolor=t["entry_bg"]
        )

        # Status strip
        self.status_card.configure(
            bg=t["card_bg"],
            highlightbackground=t["card_border"],
            highlightthickness=1
        )
        self.indicator_dot.configure(bg=t["card_bg"], fg=t["accent"])
        self.status_label.configure(bg=t["card_bg"], fg=t["text_primary"])

        # Progress bar
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=t["progress_trough"],
            background=t["progress_bar"],
            bordercolor=t["progress_trough"],
            lightcolor=t["progress_bar"],
            darkcolor=t["progress_bar"]
        )

        # Image comparison cards
        self.left_card.apply_theme(t)
        self.right_card.apply_theme(t)

        # Decision bar
        self.decision_card.configure(
            bg=t["card_bg"],
            highlightbackground=t["card_border"],
            highlightthickness=1
        )
        self.dec_header.configure(bg=t["card_bg"])
        self.dec_title.configure(bg=t["card_bg"], fg=t["text_primary"])
        self.dec_hint.configure(bg=t["card_bg"], fg=t["text_secondary"])
        self.dec_notice.configure(bg=t["card_bg"], fg=t["text_secondary"])
        self.btn_row.configure(bg=t["card_bg"])

        self.keep_left_btn.apply_theme(t)
        self.keep_both_btn.apply_theme(t)
        self.keep_right_btn.apply_theme(t)
        self.delete_both_btn.apply_theme(t)

    def _bind_shortcuts(self):
        self.bind("<Key-a>", lambda e: self.action_keep_left())
        self.bind("<Key-A>", lambda e: self.action_keep_left())
        self.bind("<Left>", lambda e: self.action_keep_left())

        self.bind("<Key-d>", lambda e: self.action_keep_right())
        self.bind("<Key-D>", lambda e: self.action_keep_right())
        self.bind("<Right>", lambda e: self.action_keep_right())

        self.bind("<Key-k>", lambda e: self.action_keep_both())
        self.bind("<Key-K>", lambda e: self.action_keep_both())
        self.bind("<Down>", lambda e: self.action_keep_both())

        self.bind("<Delete>", lambda e: self.action_delete_both())

    def browse_folder(self):
        selected = filedialog.askdirectory(initialdir=self.folder_var.get())
        if selected:
            self.folder_var.set(selected)

    def start_scan(self):
        target = self.folder_var.get().strip()
        if not target or not os.path.isdir(target):
            messagebox.showerror("Invalid Folder", "Please select a valid directory to scan.")
            return

        self.is_scanning = True
        self.scan_btn.set_enabled(False)
        self.browse_btn.set_enabled(False)
        self._set_action_buttons_state(False)
        self.dec_notice.config(text="Scanning in progress... please wait.")
        self.left_card.clear()
        self.right_card.clear()
        self.indicator_dot.config(fg=self.current_theme["accent"])
        self.status_var.set("Scanning for images and computing perceptual hashes...")
        self.progress_bar.config(mode="determinate", value=0, maximum=100)

        threshold = self.sim_selector.get()

        def worker():
            try:
                def progress_cb(current, total, filepath):
                    self.scan_queue.put(("progress", current, total, filepath))

                raw_clusters = PhotoCheck.find_duplicates(
                    target,
                    hash_size=16,
                    threshold=threshold,
                    progress_callback=progress_cb
                )

                cleaned = []
                for c in raw_clusters:
                    file_list = [p for p in c[1:] if os.path.exists(p)]
                    if len(file_list) > 1:
                        cleaned.append(file_list)

                self.scan_queue.put(("done", cleaned))
            except Exception as e:
                self.scan_queue.put(("error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _process_scan_queue(self):
        try:
            while True:
                msg = self.scan_queue.get_nowait()
                msg_type = msg[0]

                if msg_type == "progress":
                    _, current, total, path = msg
                    pct = int((current / total) * 100) if total > 0 else 0
                    self.progress_bar.config(value=pct)
                    self.status_var.set(f"Scanning ({current}/{total}): {os.path.basename(path)}")

                elif msg_type == "done":
                    _, cleaned_clusters = msg
                    self.is_scanning = False
                    self.scan_btn.set_enabled(True)
                    self.browse_btn.set_enabled(True)
                    self.clusters = cleaned_clusters
                    self.current_cluster_idx = 0
                    self.compare_idx = 1
                    self.total_deleted = 0
                    self.total_freed_bytes = 0

                    if not self.clusters:
                        self.indicator_dot.config(fg="#0f7b55")
                        self.status_var.set("Scan complete: No duplicate or similar photos found.")
                        self.dec_notice.config(text="No duplicates found in selected folder.")
                        messagebox.showinfo("Result", "No duplicate or similar photos found in this folder.")
                        self._set_action_buttons_state(False)
                    else:
                        self.indicator_dot.config(fg=self.current_theme["accent"])
                        total_dups = sum(len(c) for c in self.clusters)
                        self.status_var.set(f"Found {len(self.clusters)} duplicate groups ({total_dups} total photos).")
                        self._show_current_pair()

                elif msg_type == "error":
                    _, err_msg = msg
                    self.is_scanning = False
                    self.scan_btn.set_enabled(True)
                    self.browse_btn.set_enabled(True)
                    self.indicator_dot.config(fg="#c42b1c")
                    self.status_var.set("Scan failed.")
                    self.dec_notice.config(text=f"Scan failed: {err_msg}")
                    messagebox.showerror("Scan Error", f"An error occurred while scanning:\n{err_msg}")

        except queue.Empty:
            pass

        self.after(100, self._process_scan_queue)

    def _set_action_buttons_state(self, enabled: bool):
        self.keep_left_btn.set_enabled(enabled)
        self.keep_both_btn.set_enabled(enabled)
        self.keep_right_btn.set_enabled(enabled)
        self.delete_both_btn.set_enabled(enabled)

    def _show_current_pair(self):
        while self.current_cluster_idx < len(self.clusters):
            curr_group = self.clusters[self.current_cluster_idx]
            if len(curr_group) < 2 or self.compare_idx >= len(curr_group):
                self.current_cluster_idx += 1
                self.compare_idx = 1
            else:
                break

        if self.current_cluster_idx >= len(self.clusters):
            self.left_card.clear()
            self.right_card.clear()
            self._set_action_buttons_state(False)
            freed_str = format_size(self.total_freed_bytes)
            self.indicator_dot.config(fg="#0f7b55")
            self.status_var.set(f"All duplicates reviewed! Deleted {self.total_deleted} files, freed {freed_str}.")
            self.dec_notice.config(text=f"Review finished. Deleted {self.total_deleted} files, freed {freed_str}.")
            messagebox.showinfo(
                "Review Finished",
                f"Duplicate review complete!\n\nFiles deleted: {self.total_deleted}\nDisk space freed: {freed_str}"
            )
            return

        group = self.clusters[self.current_cluster_idx]
        left_path = group[0]
        right_path = group[self.compare_idx]

        self.left_card.load_image(left_path)
        self.right_card.load_image(right_path)
        self._set_action_buttons_state(True)

        group_num = self.current_cluster_idx + 1
        total_groups = len(self.clusters)
        status_msg = f"Group {group_num} of {total_groups} (Comparing image 1 and {self.compare_idx + 1} of {len(group)})"
        self.status_var.set(status_msg)
        self.dec_notice.config(text=f"Action required for: {os.path.basename(left_path)} vs {os.path.basename(right_path)}")

    def _delete_file(self, path):
        """Delete a file using standard os.remove."""
        if not path or not os.path.exists(path):
            return 0
        if self.confirm_delete_var.get():
            confirmed = messagebox.askyesno(
                "Confirm Deletion",
                f"Permanently delete this file?\n\n{path}"
            )
            if not confirmed:
                return 0
        try:
            size = os.path.getsize(path)
            os.remove(path)
            self.total_deleted += 1
            self.total_freed_bytes += size
            return size
        except Exception as e:
            messagebox.showerror("Delete Error", f"Could not delete:\n{path}\n\nError: {e}")
            return 0

    def action_keep_left(self):
        """Keep left image, delete right image."""
        if self.current_cluster_idx >= len(self.clusters):
            return
        group = self.clusters[self.current_cluster_idx]
        right_path = group[self.compare_idx]
        self._delete_file(right_path)
        group.pop(self.compare_idx)
        self._show_current_pair()

    def action_keep_right(self):
        """Keep right image, delete left image."""
        if self.current_cluster_idx >= len(self.clusters):
            return
        group = self.clusters[self.current_cluster_idx]
        left_path = group[0]
        self._delete_file(left_path)
        group.pop(0)
        self.compare_idx = 1
        self._show_current_pair()

    def action_keep_both(self):
        """Skip deletion, keep both images."""
        if self.current_cluster_idx >= len(self.clusters):
            return
        self.compare_idx += 1
        self._show_current_pair()

    def action_delete_both(self):
        """Delete both images currently displayed."""
        if self.current_cluster_idx >= len(self.clusters):
            return
        group = self.clusters[self.current_cluster_idx]
        right_path = group[self.compare_idx]
        left_path = group[0]
        self._delete_file(right_path)
        self._delete_file(left_path)
        group.pop(self.compare_idx)
        group.pop(0)
        self.compare_idx = 1
        self._show_current_pair()


def main():
    app = PhotoCheckUI()
    app.mainloop()


if __name__ == "__main__":
    main()
