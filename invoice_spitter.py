import os
import sys
import traceback
from tkinter import Tk, Label, Button, Entry, StringVar, filedialog, messagebox
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

def select_pdf():
    path = filedialog.askopenfilename(
        title="Select a PDF",
        filetypes=[("PDF files", "*.pdf")],
    )
    if not path:
        return
    pdf_path_var.set(path)

    # Default output folder: "<pdf_dir>/<pdf_basename>_pages"
    base = os.path.splitext(os.path.basename(path))[0]
    default_out = os.path.join(os.path.dirname(path), f"{base}_pages")
    output_dir_var.set(default_out)

def select_output_dir():
    dir_ = filedialog.askdirectory(title="Select output folder")
    if dir_:
        output_dir_var.set(dir_)

def split_pdf():
    pdf_path = pdf_path_var.get().strip()
    out_dir = output_dir_var.get().strip()

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

def clear_fields():
    pdf_path_var.set("")
    output_dir_var.set("")
    progress_bar["value"] = 0
    status_var.set("")

# ---------------- GUI ----------------
root = Tk()
root.title(APP_TITLE)
root.minsize(520, 220)

pdf_path_var = StringVar(value="")
output_dir_var = StringVar(value="")
status_var = StringVar(value="")

row = 0
Label(root, text="Input PDF:").grid(row=row, column=0, sticky="w", padx=8, pady=6)
Entry(root, textvariable=pdf_path_var, width=55).grid(row=row, column=1, padx=6, pady=6)
Button(root, text="Browse...", command=select_pdf).grid(row=row, column=2, padx=6, pady=6)

row += 1
Label(root, text="Output folder:").grid(row=row, column=0, sticky="w", padx=8, pady=6)
Entry(root, textvariable=output_dir_var, width=55).grid(row=row, column=1, padx=6, pady=6)
Button(root, text="Choose...", command=select_output_dir).grid(row=row, column=2, padx=6, pady=6)

row += 1
progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=420)
progress_bar.grid(row=row, column=0, columnspan=3, padx=8, pady=10, sticky="we")

row += 1
Label(root, textvariable=status_var, wraplength=480, fg="#333").grid(row=row, column=0, columnspan=3, padx=8, pady=4, sticky="w")

row += 1
btn_frame = ttk.Frame(root)
btn_frame.grid(row=row, column=0, columnspan=3, pady=8)
Button(btn_frame, text="Split PDF", command=split_pdf, width=15).grid(row=0, column=0, padx=6)
Button(btn_frame, text="Clear", command=clear_fields, width=10).grid(row=0, column=1, padx=6)
Button(btn_frame, text="Exit", command=root.destroy, width=8).grid(row=0, column=2, padx=6)

# Make columns resize nicely
root.grid_columnconfigure(1, weight=1)

if __name__ == "__main__":
    root.mainloop()
