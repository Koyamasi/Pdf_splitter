from tkinter import messagebox


def human_error(msg: str, details: str = "") -> None:
    """Show a concise error dialog and print details to console."""
    if details:
        print(details)
    messagebox.showerror("Error", msg)
