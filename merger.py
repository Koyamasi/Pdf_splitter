import os
import traceback
from typing import Callable, Optional

try:
    from pypdf import PdfReader, PdfWriter
except Exception:
    print("Missing dependency 'pypdf'. Install with: pip install pypdf")
    raise

from error_handler import human_error


class PdfMerger:
    """Merge multiple PDF files into a single document."""

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

    def merge(self, paths_str: str, out_path: str) -> None:
        """Merge the PDF files in *paths_str* into *out_path*."""
        if not paths_str:
            human_error("Please select PDF files to merge.")
            return
        paths = [p.strip() for p in paths_str.split(";") if p.strip()]
        if not out_path:
            human_error("Please choose an output file.")
            return
        try:
            writer = PdfWriter()
            total = len(paths)
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
                self._status(f"Processed {idx}/{total} files...")
                self._progress(idx, total)
            with open(out_path, "wb") as f:
                writer.write(f)
            self._status(f"Done. Wrote merged PDF to:\n{out_path}")
            try:
                os.startfile(out_path)  # type: ignore[attr-defined]
            except Exception:
                pass
        except Exception:
            human_error("An unexpected error occurred while merging.", traceback.format_exc())
            self._status("")
