"""Graphical interface for the PDF tools.

This module provides a small Tk based interface that exposes the
functionality of :class:`PdfSplitter` and :class:`PdfMerger` in a user
friendly manner.  The previous script bundled in the project relied on a
single window where widgets were shown or hidden depending on the mode.  In
practice that approach became difficult to extend.  The interface provided
here uses a :class:`ttk.Notebook` with separate tabs for each operation and
offers clearer input fields and status reporting.

The file can be executed directly:

```
python ui.py
```

Running the module displays a window with three tabs:

* **Split** – Split a PDF file into one file per page.
* **Split chosen pages** – Split a PDF into custom page ranges.
* **Merge** – Merge multiple PDF files into one document.

Each tab contains the relevant input controls and shares a common progress
bar and status line at the bottom of the window.
"""

from __future__ import annotations

import os
from tkinter import Tk, StringVar, filedialog, Canvas
from tkinter import ttk
import tkinter.font as tkfont

from splitter import PdfSplitter
from merger import PdfMerger

APP_TITLE = "PDF Toolkit"

# GitHub Desktop inspired dark color scheme
GITHUB_BG = "#1f2328"
GITHUB_HEADER_BG = "#161b22"
GITHUB_SURFACE = "#2d333b"
GITHUB_TAB_ACTIVE = "#39424a"
GITHUB_PRIMARY = "#2f81f7"
GITHUB_FG = "#f0f6fc"


def _create_round_rect(canvas: Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs) -> int:
    """Draw a rounded rectangle on *canvas* and return the created shape id."""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedButton(Canvas):
    """A button with rounded corners implemented via a :class:`Canvas`."""

    def __init__(
        self,
        master,
        text: str,
        command,
        *,
        width: int | None = None,
        bg: str = GITHUB_SURFACE,
        fg: str = GITHUB_FG,
        active_bg: str = "#444c56",
        radius: int = 10,
    ) -> None:
        super().__init__(master, highlightthickness=0, bd=0, bg=GITHUB_BG)
        self.command = command
        self.bg = bg
        self.active_bg = active_bg
        self.radius = radius
        font = tkfont.Font()
        char_width = font.measure("0")
        w = (width or len(text)) * char_width + 20
        h = font.metrics("linespace") + 10
        self.configure(width=w, height=h)
        self.rect = _create_round_rect(self, 0, 0, w, h, radius, fill=bg, outline="")
        self.create_text(w / 2, h / 2, text=text, fill=fg, font=font)
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.active_bg))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.bg))


class RoundedEntry(ttk.Frame):
    """Entry widget with a rounded background."""

    def __init__(
        self,
        master,
        *,
        textvariable: StringVar | None = None,
        width: int = 45,
        radius: int = 10,
    ) -> None:
        super().__init__(master)
        self.radius = radius
        self.canvas = Canvas(self, highlightthickness=0, bd=0, bg=GITHUB_BG)
        self.canvas.pack(fill="both", expand=True)
        font = tkfont.Font()
        char_width = font.measure("0")
        w = char_width * width + 20
        h = font.metrics("linespace") + 10
        _create_round_rect(self.canvas, 0, 0, w, h, radius, fill=GITHUB_SURFACE, outline="")
        self.entry = ttk.Entry(
            self,
            textvariable=textvariable,
            style="Rounded.TEntry",
        )
        self.entry.place(x=10, y=5, width=w - 20, height=h - 10)
        self.configure(width=w, height=h)
        self.canvas.bind("<Configure>", self._resize)

    def _resize(self, event) -> None:
        w, h = event.width, event.height
        self.canvas.delete("all")
        _create_round_rect(self.canvas, 0, 0, w, h, self.radius, fill=GITHUB_SURFACE, outline="")
        self.entry.place(x=10, y=5, width=w - 20, height=h - 10)

    # Proxy common methods to the underlying entry
    def get(self) -> str:
        return self.entry.get()

    def insert(self, index, value) -> None:
        self.entry.insert(index, value)

    def delete(self, first, last=None) -> None:
        self.entry.delete(first, last)

GITHUB_BG = "#1f2328"
GITHUB_HEADER_BG = "#161b22"
GITHUB_SURFACE = "#2d333b"
GITHUB_TAB_ACTIVE = "#39424a"
GITHUB_PRIMARY = "#2f81f7"
GITHUB_FG = "#f0f6fc"


class _BaseTab(ttk.Frame):
    """Common functionality shared by the individual notebook tabs."""

    def __init__(self, master: ttk.Notebook) -> None:
        super().__init__(master, padding=10)
        self.input_var = StringVar()
        self.output_var = StringVar()

    # Utility helpers -------------------------------------------------
    def _clear_common(self) -> None:
        self.input_var.set("")
        self.output_var.set("")

    def _setup_responsive_buttons(self, frame: ttk.Frame, primary, secondary) -> None:
        self._btn_frame = frame
        self._primary_btn = primary
        self._secondary_btn = secondary
        frame.bind("<Configure>", self._on_btn_frame_resize)

    def _on_btn_frame_resize(self, event) -> None:
        width = event.width
        for child in self._btn_frame.winfo_children():
            child.grid_forget()
        if width < 200:
            self._primary_btn.grid(row=0, column=0, pady=2, sticky="we")
            self._secondary_btn.grid(row=1, column=0, pady=2, sticky="we")
        else:
            self._primary_btn.grid(row=0, column=0, padx=4)
            self._secondary_btn.grid(row=0, column=1, padx=4)


class SplitTab(_BaseTab):
    """Tab for splitting every page of a PDF into separate files."""

    def __init__(self, master: ttk.Notebook, splitter: PdfSplitter) -> None:
        super().__init__(master)
        self.splitter = splitter
        self._build_widgets()

    # GUI construction ------------------------------------------------
    def _build_widgets(self) -> None:
        ttk.Label(self, text="Input PDF:").grid(row=0, column=0, sticky="w")
        RoundedEntry(self, textvariable=self.input_var, width=45).grid(
            row=0, column=1, padx=5, pady=2, sticky="we"
        )
        RoundedButton(self, text="Browse…", command=self._browse_input).grid(
            row=0, column=2, padx=5, pady=2
        )

        ttk.Label(self, text="Output folder:").grid(row=1, column=0, sticky="w")
        RoundedEntry(self, textvariable=self.output_var, width=45).grid(
            row=1, column=1, padx=5, pady=2, sticky="we"
        )
        RoundedButton(self, text="Choose…", command=self._browse_output).grid(
            row=1, column=2, padx=5, pady=2
        )

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=8, sticky="ew")
        split_btn = RoundedButton(
            btn_frame,
            text="Split PDF",
            command=self._do_split,
            width=15,
            bg=GITHUB_PRIMARY,
            fg="white",
            active_bg="#1b6ac9",
        )
        clear_btn = RoundedButton(
            btn_frame, text="Clear", command=self._clear_common, width=10
        )
        split_btn.grid(row=0, column=0, padx=4)
        clear_btn.grid(row=0, column=1, padx=4)
        self._setup_responsive_buttons(btn_frame, split_btn, clear_btn)

        self.columnconfigure(1, weight=1)

    # Widget callbacks ------------------------------------------------
    def _browse_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Select a PDF", filetypes=[("PDF files", "*.pdf")]
        )
        if not path:
            return
        self.input_var.set(path)
        base = os.path.splitext(os.path.basename(path))[0]
        self.output_var.set(os.path.join(os.path.dirname(path), f"{base}_pages"))

    def _browse_output(self) -> None:
        directory = filedialog.askdirectory(title="Select output folder")
        if directory:
            self.output_var.set(directory)

    def _do_split(self) -> None:
        self.splitter.split(self.input_var.get().strip(), self.output_var.get().strip())


class SplitChosenTab(_BaseTab):
    """Tab for splitting PDFs according to custom page selections."""

    def __init__(self, master: ttk.Notebook, splitter: PdfSplitter) -> None:
        super().__init__(master)
        self.splitter = splitter
        self.pages_var = StringVar()
        self._build_widgets()

    def _build_widgets(self) -> None:
        ttk.Label(self, text="Input PDF:").grid(row=0, column=0, sticky="w")
        RoundedEntry(self, textvariable=self.input_var, width=45).grid(
            row=0, column=1, padx=5, pady=2, sticky="we"
        )
        RoundedButton(self, text="Browse…", command=self._browse_input).grid(
            row=0, column=2, padx=5, pady=2
        )

        ttk.Label(self, text="Output folder:").grid(row=1, column=0, sticky="w")
        RoundedEntry(self, textvariable=self.output_var, width=45).grid(
            row=1, column=1, padx=5, pady=2, sticky="we"
        )
        RoundedButton(self, text="Choose…", command=self._browse_output).grid(
            row=1, column=2, padx=5, pady=2
        )

        ttk.Label(self, text="Page selections:").grid(row=2, column=0, sticky="w")
        RoundedEntry(self, textvariable=self.pages_var, width=45).grid(
            row=2, column=1, padx=5, pady=2, sticky="we"
        )

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=8, sticky="ew")
        split_btn = RoundedButton(
            btn_frame,
            text="Split pages",
            command=self._do_split,
            width=15,
            bg=GITHUB_PRIMARY,
            fg="white",
            active_bg="#1b6ac9",
        )
        clear_btn = RoundedButton(btn_frame, text="Clear", command=self._clear_all, width=10)
        split_btn.grid(row=0, column=0, padx=4)
        clear_btn.grid(row=0, column=1, padx=4)
        self._setup_responsive_buttons(btn_frame, split_btn, clear_btn)

        self.columnconfigure(1, weight=1)

    # Callbacks -------------------------------------------------------
    def _browse_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Select a PDF", filetypes=[("PDF files", "*.pdf")]
        )
        if not path:
            return
        self.input_var.set(path)
        base = os.path.splitext(os.path.basename(path))[0]
        self.output_var.set(os.path.join(os.path.dirname(path), f"{base}_pages"))

    def _browse_output(self) -> None:
        directory = filedialog.askdirectory(title="Select output folder")
        if directory:
            self.output_var.set(directory)

    def _do_split(self) -> None:
        self.splitter.split_chosen_pages(
            self.input_var.get().strip(),
            self.output_var.get().strip(),
            self.pages_var.get().strip(),
        )

    def _clear_all(self) -> None:
        self._clear_common()
        self.pages_var.set("")


class MergeTab(_BaseTab):
    """Tab for merging multiple PDFs into one file."""

    def __init__(self, master: ttk.Notebook, merger: PdfMerger) -> None:
        super().__init__(master)
        self.merger = merger
        self._build_widgets()

    def _build_widgets(self) -> None:
        ttk.Label(self, text="PDFs to merge:").grid(row=0, column=0, sticky="w")
        RoundedEntry(self, textvariable=self.input_var, width=45).grid(
            row=0, column=1, padx=5, pady=2, sticky="we"
        )
        RoundedButton(self, text="Browse…", command=self._browse_input).grid(
            row=0, column=2, padx=5, pady=2
        )

        ttk.Label(self, text="Output PDF:").grid(row=1, column=0, sticky="w")
        RoundedEntry(self, textvariable=self.output_var, width=45).grid(
            row=1, column=1, padx=5, pady=2, sticky="we"
        )
        RoundedButton(self, text="Save As…", command=self._browse_output).grid(
            row=1, column=2, padx=5, pady=2
        )

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=8, sticky="ew")
        merge_btn = RoundedButton(
            btn_frame,
            text="Merge PDFs",
            command=self._do_merge,
            width=15,
            bg=GITHUB_PRIMARY,
            fg="white",
            active_bg="#1b6ac9",
        )
        clear_btn = RoundedButton(btn_frame, text="Clear", command=self._clear_common, width=10)
        merge_btn.grid(row=0, column=0, padx=4)
        clear_btn.grid(row=0, column=1, padx=4)
        self._setup_responsive_buttons(btn_frame, merge_btn, clear_btn)

        self.columnconfigure(1, weight=1)

    def _browse_input(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select PDF files", filetypes=[("PDF files", "*.pdf")]
        )
        if paths:
            self.input_var.set("; ".join(paths))
            self.output_var.set(os.path.join(os.path.dirname(paths[0]), "merged.pdf"))

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            self.output_var.set(path)

    def _do_merge(self) -> None:
        self.merger.merge(self.input_var.get().strip(), self.output_var.get().strip())


# ---------------------------------------------------------------------------


class PdfApp(Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(560, 300)
        self.configure(bg=GITHUB_BG)

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        # Base widget styling
        style.configure("TFrame", background=GITHUB_BG)
        style.configure("TLabel", background=GITHUB_BG, foreground=GITHUB_FG)
        style.configure(
            "Rounded.TEntry",
            fieldbackground=GITHUB_SURFACE,
            foreground=GITHUB_FG,
            insertcolor=GITHUB_FG,
            borderwidth=0,
            relief="flat",
        )
        style.configure("TNotebook", background=GITHUB_BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            padding=(12, 8),
            background=GITHUB_SURFACE,
            foreground=GITHUB_FG,
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", GITHUB_TAB_ACTIVE)],
            padding=[("selected", (12, 8)), ("!selected", (12, 8))],
        )
        style.configure("Header.TFrame", background=GITHUB_HEADER_BG)
        style.configure(
            "Header.TLabel",
            background=GITHUB_HEADER_BG,
            foreground="white",
            font=("Segoe UI", 12, "bold"),
        )
        style.configure(
            "TProgressbar",
            background=GITHUB_PRIMARY,
            troughcolor=GITHUB_SURFACE,
        )

        # Header bar
        header = ttk.Frame(self, style="Header.TFrame", height=40)
        header.grid(row=0, column=0, columnspan=3, sticky="nsew")
        ttk.Label(header, text=APP_TITLE, style="Header.TLabel").pack(
            side="left", padx=10, pady=10
        )

        self.status_var = StringVar()
        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate")
        self.progress.grid(row=2, column=0, columnspan=3, pady=(8, 2), sticky="we")
        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.grid(row=3, column=0, columnspan=3, sticky="we")

        # Set up backend objects with callbacks
        splitter = PdfSplitter(self._update_status, self._update_progress)
        merger = PdfMerger(self._update_status, self._update_progress)

        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, columnspan=3, sticky="nsew")
        notebook.add(SplitTab(notebook, splitter), text="Split")
        notebook.add(SplitChosenTab(notebook, splitter), text="Split chosen pages")
        notebook.add(MergeTab(notebook, merger), text="Merge")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.bind("<Configure>", self._on_resize)

    # Backend callbacks -----------------------------------------------
    def _update_status(self, msg: str) -> None:
        self.status_var.set(msg)
        self.update_idletasks()

    def _update_progress(self, current: int, total: int) -> None:
        self.progress["maximum"] = total
        self.progress["value"] = current
        self.update_idletasks()

    def _on_resize(self, event) -> None:
        width = event.width - 20
        if width > 0:
            self.progress.configure(length=width)
            self.status_label.configure(wraplength=width)


def main() -> None:
    app = PdfApp()
    app.mainloop()


if __name__ == "__main__":
    main()

