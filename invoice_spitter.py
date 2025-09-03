import os
import traceback
from tkinter import Tk, StringVar, filedialog, messagebox
from tkinter import ttk

# External dependency: pypdf
try:
    from pypdf import PdfReader, PdfWriter
except Exception as e:
    # If pypdf isn't installed, show a helpful message in console and GUI
    print("Missing dependency 'pypdf'. Install with: pip install pypdf")
    raise

APP_TITLE = "TolisInvoiceSplitter"


def human_error(msg: str, details: str = ""):
    """Show a concise error dialog (and print details to console)."""
    if details:
        print(details)
    messagebox.showerror("Error", msg)


def mode() -> str:
    """Return the current mode in lowercase."""
    return mode_var.get().lower()


def browse_input():
    if mode() == "split":
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
    if mode() == "split":
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


def split_pdf():
    pdf_path = input_var.get().strip()
    out_dir = output_var.get().strip()

    if not pdf_path:
        human_error("Please select a PDF file first.")
        return
    if not os.path.isfile(pdf_path):
        human_error("The selected PDF file does not exist.")
        return
    if not out_dir:
        human_error("Please choose an output folder.")
        return

    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        human_error("Cannot create the output folder.", traceback.format_exc())
        return

    try:
        status_var.set("Reading PDF...")
        root.update_idletasks()

        reader = PdfReader(pdf_path)

        # Handle encrypted PDFs (best-effort empty password)
        if getattr(reader, "is_encrypted", False):
            try:
                ok = reader.decrypt("")
                if ok == 0:
                    human_error("This PDF appears to be password-protected. Decryption failed.")
                    return
            except Exception:
                human_error("This PDF appears to be password-protected. Decryption failed.")
                return

        total_pages = len(reader.pages)
        if total_pages == 0:
            human_error("No pages found in the PDF.")
            return

        base = os.path.splitext(os.path.basename(pdf_path))[0]
        progress_bar["maximum"] = total_pages
        progress_bar["value"] = 0

        for idx, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)

            out_name = f"{base}_p{idx:03d}.pdf"
            out_path = os.path.join(out_dir, out_name)
            with open(out_path, "wb") as f:
                writer.write(f)

            status_var.set(f"Writing page {idx}/{total_pages}...")
            progress_bar["value"] = idx
            root.update_idletasks()

        status_var.set(f"Done. Wrote {total_pages} files to:\n{out_dir}")
        try:
            # Windows only: open the output folder in Explorer
            os.startfile(out_dir)  # type: ignore[attr-defined]
        except Exception:
            pass

    except Exception as e:
        human_error("An unexpected error occurred while splitting.", traceback.format_exc())
        status_var.set("")


def merge_pdfs():
    paths_str = input_var.get().strip()
    out_path = output_var.get().strip()

    if not paths_str:
        human_error("Please select PDF files to merge.")
        return
    paths = [p.strip() for p in paths_str.split(";") if p.strip()]
    if not out_path:
        human_error("Please choose an output file.")
        return

    try:
        writer = PdfWriter()
        progress_bar["maximum"] = len(paths)
        progress_bar["value"] = 0

        for idx, path in enumerate(paths, start=1):
            if not os.path.isfile(path):
                human_error(f"File not found: {path}")
                return

            reader = PdfReader(path)
            if getattr(reader, "is_encrypted", False):
                try:
                    ok = reader.decrypt("")
                    if ok == 0:
                        human_error("One of the PDFs is password-protected. Decryption failed.")
                        return
                except Exception:
                    human_error("One of the PDFs is password-protected. Decryption failed.")
                    return

            for page in reader.pages:
                writer.add_page(page)

            status_var.set(f"Processed {idx}/{len(paths)} files...")
            progress_bar["value"] = idx
            root.update_idletasks()

        with open(out_path, "wb") as f:
            writer.write(f)

        status_var.set(f"Done. Wrote merged PDF to:\n{out_path}")
        try:
            os.startfile(out_path)  # type: ignore[attr-defined]
        except Exception:
            pass

    except Exception as e:
        human_error("An unexpected error occurred while merging.", traceback.format_exc())
        status_var.set("")


def clear_fields():
    input_var.set("")
    output_var.set("")
    progress_bar["value"] = 0
    status_var.set("")


def perform_action():
    if mode() == "split":
        split_pdf()
    else:
        merge_pdfs()


def update_ui():
    if mode() == "split":
        input_label.config(text="Input PDF:")
        output_label.config(text="Output folder:")
        output_browse_btn.config(text="Choose...")
        action_btn.config(text="Split PDF")
    else:
        input_label.config(text="PDFs to merge:")
        output_label.config(text="Output PDF:")
        output_browse_btn.config(text="Save As...")
        action_btn.config(text="Merge PDFs")
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

row = 0
ttk.Label(root, text="Mode:").grid(row=row, column=0, sticky="w", padx=8, pady=6)
mode_combo = ttk.Combobox(root, textvariable=mode_var, values=["Split", "Merge"], state="readonly", width=10)
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
progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=420)
progress_bar.grid(row=row, column=0, columnspan=3, padx=8, pady=10, sticky="we")

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

