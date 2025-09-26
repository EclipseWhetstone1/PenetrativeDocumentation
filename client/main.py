import tkinter as tk
from ui import SecurityApp

if __name__ == "__main__":
    """
    Main entry point for the application.
    """
    root = tk.Tk()
    app = SecurityApp(root)

    root.mainloop()
