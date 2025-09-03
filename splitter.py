import os
import traceback
from typing import List, Callable, Optional

try:
    from pypdf import PdfReader, PdfWriter
except Exception:
    print("Missing dependency 'pypdf'. Install with: pip install pypdf")
    raise

from error_handler import human_error
from page_selection import parse_page_selection


class PdfSplitter:
    """Split PDF files into individual pages or selected groups."""

    def __init__(
        self,
        status_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        self.status_callback = status_callback
        self.progress_callback = progress_callback

    def _status(self, msg: str) -> None:
        if self.status_callback:
            self.status_callback(msg)

    def _progress(self, current: int, total: int) -> None:
        if self.progress_callback:
            self.progress_callback(current, total)

    def split(self, pdf_path: str, out_dir: str) -> None:
        """Split each page of *pdf_path* into separate files inside *out_dir*."""
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
        except Exception:
            human_error("Cannot create the output folder.", traceback.format_exc())
            return
        try:
            self._status("Reading PDF...")
            reader = PdfReader(pdf_path)
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
            for idx, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)
                out_name = f"{base}_p{idx:03d}.pdf"
                out_path = os.path.join(out_dir, out_name)
                with open(out_path, "wb") as f:
                    writer.write(f)
                self._status(f"Writing page {idx}/{total_pages}...")
                self._progress(idx, total_pages)
            self._status(f"Done. Wrote {total_pages} files to:\n{out_dir}")
            try:
                os.startfile(out_dir)  # type: ignore[attr-defined]
            except Exception:
                pass
        except Exception:
            human_error("An unexpected error occurred while splitting.", traceback.format_exc())
            self._status("")

    def split_chosen_pages(self, pdf_path: str, out_dir: str, pages_spec: str) -> None:
        """Split *pdf_path* into groups of pages defined by *pages_spec*."""
        if not pdf_path:
            human_error("Please select a PDF file first.")
            return
        if not os.path.isfile(pdf_path):
            human_error("The selected PDF file does not exist.")
            return
        if not out_dir:
            human_error("Please choose an output folder.")
            return
        if not pages_spec:
            human_error("Please specify page selections.")
            return
        groups = [g.strip() for g in pages_spec.split(";") if g.strip()]
        if not groups:
            human_error("Please specify page selections.")
            return
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            human_error("Cannot create the output folder.", traceback.format_exc())
            return
        try:
            self._status("Reading PDF...")
            reader = PdfReader(pdf_path)
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
            base = os.path.splitext(os.path.basename(pdf_path))[0]
            total_groups = len(groups)
            for idx, group in enumerate(groups, start=1):
                try:
                    page_numbers = parse_page_selection(group, total_pages)
                except ValueError as e:
                    human_error(str(e))
                    return
                writer = PdfWriter()
                for p in page_numbers:
                    writer.add_page(reader.pages[p - 1])
                out_name = f"{base}_sel{idx:02d}.pdf"
                out_path = os.path.join(out_dir, out_name)
                with open(out_path, "wb") as f:
                    writer.write(f)
                self._status(f"Writing file {idx}/{total_groups}...")
                self._progress(idx, total_groups)
            self._status(f"Done. Wrote {total_groups} files to:\n{out_dir}")
            try:
                os.startfile(out_dir)  # type: ignore[attr-defined]
            except Exception:
                pass
        except Exception:
            human_error("An unexpected error occurred while splitting.", traceback.format_exc())
            self._status("")
