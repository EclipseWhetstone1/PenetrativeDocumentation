import tkinter as tk
import sys
import json
from ui import SecurityApp
from scanner import run_all_scans

def run_headless_scan():
    """
    Runs the scan without launching the UI and prints the
    results to standard output in a structured JSON format.
    """
    try:
        vulns, summary = run_all_scans()  # Adjusted for new signature
        output_data = {
            "status": "success",
            "summary": summary,
            "vulnerabilities": vulns  # list of dicts
        }
    except Exception as e:
        output_data = {"status": "error", "message": str(e)}

    print(json.dumps(output_data))


if __name__ == "__main__":
    """
    Main entry point for the application.
    Checks for a '--headless' command-line argument to run in a non-interactive
    mode. Otherwise, it launches the standard Tkinter UI.
    """
    if "--headless" in sys.argv:
        run_headless_scan()
    else:
        # This is the original code to run the UI application.
        root = tk.Tk()
        app = SecurityApp(root)
        root.mainloop()