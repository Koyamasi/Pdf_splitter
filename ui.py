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
from tkinter import Tk, StringVar, filedialog
from tkinter import ttk

from splitter import PdfSplitter
from merger import PdfMerger

APP_TITLE = "PDF Toolkit"


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


class SplitTab(_BaseTab):
    """Tab for splitting every page of a PDF into separate files."""

    def __init__(self, master: ttk.Notebook, splitter: PdfSplitter) -> None:
        super().__init__(master)
        self.splitter = splitter
        self._build_widgets()

    # GUI construction ------------------------------------------------
    def _build_widgets(self) -> None:
        ttk.Label(self, text="Input PDF:").grid(row=0, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.input_var, width=45).grid(
            row=0, column=1, padx=5, pady=2, sticky="we"
        )
        ttk.Button(self, text="Browse…", command=self._browse_input).grid(
            row=0, column=2, padx=5, pady=2
        )

        ttk.Label(self, text="Output folder:").grid(row=1, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.output_var, width=45).grid(
            row=1, column=1, padx=5, pady=2, sticky="we"
        )
        ttk.Button(self, text="Choose…", command=self._browse_output).grid(
            row=1, column=2, padx=5, pady=2
        )

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=8)
        ttk.Button(btn_frame, text="Split PDF", command=self._do_split, width=15).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(btn_frame, text="Clear", command=self._clear_common, width=10).grid(
            row=0, column=1, padx=4
        )

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
        ttk.Entry(self, textvariable=self.input_var, width=45).grid(
            row=0, column=1, padx=5, pady=2, sticky="we"
        )
        ttk.Button(self, text="Browse…", command=self._browse_input).grid(
            row=0, column=2, padx=5, pady=2
        )

        ttk.Label(self, text="Output folder:").grid(row=1, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.output_var, width=45).grid(
            row=1, column=1, padx=5, pady=2, sticky="we"
        )
        ttk.Button(self, text="Choose…", command=self._browse_output).grid(
            row=1, column=2, padx=5, pady=2
        )

        ttk.Label(self, text="Page selections:").grid(row=2, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.pages_var, width=45).grid(
            row=2, column=1, padx=5, pady=2, sticky="we"
        )

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=8)
        ttk.Button(
            btn_frame, text="Split pages", command=self._do_split, width=15
        ).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="Clear", command=self._clear_all, width=10).grid(
            row=0, column=1, padx=4
        )

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
        ttk.Entry(self, textvariable=self.input_var, width=45).grid(
            row=0, column=1, padx=5, pady=2, sticky="we"
        )
        ttk.Button(self, text="Browse…", command=self._browse_input).grid(
            row=0, column=2, padx=5, pady=2
        )

        ttk.Label(self, text="Output PDF:").grid(row=1, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.output_var, width=45).grid(
            row=1, column=1, padx=5, pady=2, sticky="we"
        )
        ttk.Button(self, text="Save As…", command=self._browse_output).grid(
            row=1, column=2, padx=5, pady=2
        )

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=8)
        ttk.Button(btn_frame, text="Merge PDFs", command=self._do_merge, width=15).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(btn_frame, text="Clear", command=self._clear_common, width=10).grid(
            row=0, column=1, padx=4
        )

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
        self.minsize(560, 280)
        self.configure(padx=10, pady=10)

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        self.status_var = StringVar()
        self.progress = ttk.Progressbar(
            self, orient="horizontal", mode="determinate", length=440
        )
        self.progress.grid(row=1, column=0, columnspan=3, pady=(8, 2), sticky="we")
        ttk.Label(self, textvariable=self.status_var, wraplength=500).grid(
            row=2, column=0, columnspan=3, sticky="w"
        )

        # Set up backend objects with callbacks
        splitter = PdfSplitter(self._update_status, self._update_progress)
        merger = PdfMerger(self._update_status, self._update_progress)

        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, columnspan=3, sticky="nsew")
        notebook.add(SplitTab(notebook, splitter), text="Split")
        notebook.add(SplitChosenTab(notebook, splitter), text="Split chosen pages")
        notebook.add(MergeTab(notebook, merger), text="Merge")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    # Backend callbacks -----------------------------------------------
    def _update_status(self, msg: str) -> None:
        self.status_var.set(msg)
        self.update_idletasks()

    def _update_progress(self, current: int, total: int) -> None:
        self.progress["maximum"] = total
        self.progress["value"] = current
        self.update_idletasks()


def main() -> None:
    app = PdfApp()
    app.mainloop()


if __name__ == "__main__":
    main()

