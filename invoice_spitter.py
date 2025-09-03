import os
from tkinter import Tk, Menu, StringVar, filedialog
from tkinter import ttk

from splitter import PdfSplitter
from merger import PdfMerger

APP_TITLE = "TolisInvoiceSplitter"


def mode() -> str:
    """Return the current mode in lowercase with spaces replaced by underscores."""
    return mode_var.get().lower().replace(" ", "_")


def set_mode(new_mode: str):
    """Set the current mode and refresh the UI."""
    display_map = {
        "split": "Split",
        "merge": "Merge",
        "split_chosen_pages": "Split chosen pages",
    }
    mode_var.set(display_map.get(new_mode.lower(), new_mode))
    update_ui()


def browse_input():
    if mode() in ("split", "split_chosen_pages"):
        path = filedialog.askopenfilename(
            title="Select a PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not path:
            return
        input_var.set(path)

        # Default output folder: "<pdf_dir>/<pdf_basename>_pages"
        base = os.path.splitext(os.path.basename(path))[0]
        default_out = os.path.join(os.path.dirname(path), f"{base}_pages")
        output_var.set(default_out)
    else:
        paths = filedialog.askopenfilenames(
            title="Select PDF files to merge",
            filetypes=[("PDF files", "*.pdf")],
        )
        if paths:
            input_var.set("; ".join(paths))
            output_var.set(os.path.join(os.path.dirname(paths[0]), "merged.pdf"))


def browse_output():
    if mode() in ("split", "split_chosen_pages"):
        dir_ = filedialog.askdirectory(title="Select output folder")
        if dir_:
            output_var.set(dir_)
    else:
        path = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            output_var.set(path)
def clear_fields():
    input_var.set("")
    output_var.set("")
    pages_var.set("")
    progress_bar["value"] = 0
    status_var.set("")


def perform_action():
    if mode() == "split":
        splitter.split(input_var.get().strip(), output_var.get().strip())
    elif mode() == "split_chosen_pages":
        splitter.split_chosen_pages(
            input_var.get().strip(),
            output_var.get().strip(),
            pages_var.get().strip(),
        )
    else:
        merger.merge(input_var.get().strip(), output_var.get().strip())


def update_ui():
    if mode() == "split":
        input_label.config(text="Input PDF:")
        output_label.config(text="Output folder:")
        output_browse_btn.config(text="Choose...")
        action_btn.config(text="Split PDF")
        pages_label.grid_remove()
        pages_entry.grid_remove()
    elif mode() == "split_chosen_pages":
        input_label.config(text="Input PDF:")
        output_label.config(text="Output folder:")
        output_browse_btn.config(text="Choose...")
        action_btn.config(text="Split pages")
        pages_label.grid()
        pages_entry.grid()
    else:
        input_label.config(text="PDFs to merge:")
        output_label.config(text="Output PDF:")
        output_browse_btn.config(text="Save As...")
        action_btn.config(text="Merge PDFs")
        pages_label.grid_remove()
        pages_entry.grid_remove()
    clear_fields()


# ---------------- GUI ----------------
root = Tk()
root.title(APP_TITLE)
root.minsize(540, 240)
root.configure(padx=10, pady=10)

style = ttk.Style(root)
if "clam" in style.theme_names():
    style.theme_use("clam")

mode_var = StringVar(value="Split")
input_var = StringVar(value="")
output_var = StringVar(value="")
status_var = StringVar(value="")
pages_var = StringVar(value="")

# Menu to switch modes
menubar = Menu(root)
mode_menu = Menu(menubar, tearoff=0)
mode_menu.add_command(label="Split PDF", command=lambda: set_mode("split"))
mode_menu.add_command(label="Merge PDFs", command=lambda: set_mode("merge"))
mode_menu.add_command(label="Split chosen pages", command=lambda: set_mode("split_chosen_pages"))
menubar.add_cascade(label="Mode", menu=mode_menu)
root.config(menu=menubar)

row = 0
ttk.Label(root, text="Mode:").grid(row=row, column=0, sticky="w", padx=8, pady=6)
mode_combo = ttk.Combobox(
    root,
    textvariable=mode_var,
    values=["Split", "Merge", "Split chosen pages"],
    state="readonly",
    width=20,
)
mode_combo.grid(row=row, column=1, sticky="w", padx=6, pady=6)
mode_combo.bind("<<ComboboxSelected>>", lambda e: update_ui())

row += 1
input_label = ttk.Label(root, text="Input PDF:")
input_label.grid(row=row, column=0, sticky="w", padx=8, pady=6)
ttk.Entry(root, textvariable=input_var, width=55).grid(row=row, column=1, padx=6, pady=6)
ttk.Button(root, text="Browse...", command=browse_input).grid(row=row, column=2, padx=6, pady=6)

row += 1
output_label = ttk.Label(root, text="Output folder:")
output_label.grid(row=row, column=0, sticky="w", padx=8, pady=6)
ttk.Entry(root, textvariable=output_var, width=55).grid(row=row, column=1, padx=6, pady=6)
output_browse_btn = ttk.Button(root, text="Choose...", command=browse_output)
output_browse_btn.grid(row=row, column=2, padx=6, pady=6)

row += 1
pages_label = ttk.Label(root, text="Page selections:")
pages_label.grid(row=row, column=0, sticky="w", padx=8, pady=6)
pages_entry = ttk.Entry(root, textvariable=pages_var, width=55)
pages_entry.grid(row=row, column=1, columnspan=2, padx=6, pady=6, sticky="we")
pages_label.grid_remove()
pages_entry.grid_remove()

row += 1
progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=420)
progress_bar.grid(row=row, column=0, columnspan=3, padx=8, pady=10, sticky="we")


def status_update(msg: str) -> None:
    status_var.set(msg)
    root.update_idletasks()


def progress_update(current: int, total: int) -> None:
    progress_bar["maximum"] = total
    progress_bar["value"] = current
    root.update_idletasks()


splitter = PdfSplitter(status_update, progress_update)
merger = PdfMerger(status_update, progress_update)


row += 1
ttk.Label(root, textvariable=status_var, wraplength=480).grid(row=row, column=0, columnspan=3, padx=8, pady=4, sticky="w")

row += 1
btn_frame = ttk.Frame(root)
btn_frame.grid(row=row, column=0, columnspan=3, pady=8)
action_btn = ttk.Button(btn_frame, text="Split PDF", command=perform_action, width=15)
action_btn.grid(row=0, column=0, padx=6)
ttk.Button(btn_frame, text="Clear", command=clear_fields, width=10).grid(row=0, column=1, padx=6)
ttk.Button(btn_frame, text="Exit", command=root.destroy, width=8).grid(row=0, column=2, padx=6)

# Make columns resize nicely
root.grid_columnconfigure(1, weight=1)

update_ui()

if __name__ == "__main__":
    root.mainloop()

