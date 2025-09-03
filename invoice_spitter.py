"""Compatibility entry point for launching the Tkinter UI."""

from ui import PdfApp


def main() -> None:
    app = PdfApp()
    app.mainloop()


if __name__ == "__main__":
    main()
