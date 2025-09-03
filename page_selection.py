from typing import List


def parse_page_selection(selection: str, total_pages: int) -> List[int]:
    """Convert a page selection like '1-3,5' into a list of page numbers."""
    pages: List[int] = []
    for part in selection.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            try:
                start = int(start_s)
                end = int(end_s)
            except ValueError:
                raise ValueError(f"Invalid range: {part}")
            if not (1 <= start <= end <= total_pages):
                raise ValueError(f"Page range out of bounds: {part}")
            pages.extend(range(start, end + 1))
        else:
            try:
                page = int(part)
            except ValueError:
                raise ValueError(f"Invalid page number: {part}")
            if not (1 <= page <= total_pages):
                raise ValueError(f"Page out of bounds: {part}")
            pages.append(page)
    return pages
