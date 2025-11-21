import tkinter as tk
from tkinter import messagebox
from scanner import run_all_scans # MODIFIED: Changed to call the main runner function

# --- US001 & US002: User Interface ---

class SecurityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Educational Security Tool")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # --- US001: Initial Notification View ---
        self.main_frame = tk.Frame(root, padx=20, pady=20)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        title_label = tk.Label(self.main_frame, text="System Vulnerability Demonstration", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        intro_text = (
            "Your system has been safely 'compromised' for educational purposes.\n\n"
            "This program will show you how it was done and how to protect yourself from real threats. "
            "No data has been harmed or stolen."
        )
        intro_label = tk.Label(self.main_frame, text=intro_text, justify=tk.LEFT, wraplength=550)
        intro_label.pack(pady=15)
        
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=20)
        
        learn_more_btn = tk.Button(button_frame, text="View Report", command=self.show_report, width=15, height=2)
        learn_more_btn.pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Button(button_frame, text="Close", command=root.quit, width=15, height=2)
        close_btn.pack(side=tk.LEFT, padx=10)

        # --- US002: Report View (initially hidden) ---
        self.report_frame = tk.Frame(root, padx=20, pady=20)
        
        report_title = tk.Label(self.report_frame, text="Vulnerability Report", font=("Helvetica", 16, "bold"))
        report_title.pack(pady=10)

        self.report_text = tk.Text(self.report_frame, wrap=tk.WORD, height=15, width=70, font=("Courier New", 10))
        self.report_text.pack(pady=10)

        back_btn = tk.Button(self.report_frame, text="Back", command=self.show_main_frame, width=15, height=2)
        back_btn.pack(pady=10)

    def show_report(self):
        """Hides the main frame and shows the vulnerability report."""
        self.main_frame.pack_forget()
        self.report_frame.pack(expand=True, fill=tk.BOTH)
        
        # --- Trigger the scan when showing the report ---
        vulnerabilities = run_all_scans() # MODIFIED: Calls the new main runner
        
        # Display the results in the text box
        self.report_text.delete('1.0', tk.END) # Clear previous results
        report_content = "".join(vulnerabilities)
        self.report_text.insert(tk.END, report_content)
        
    def show_main_frame(self):
        """Hides the report frame and shows the main welcome frame."""
        self.report_frame.pack_forget()
        self.main_frame.pack(expand=True, fill=tk.BOTH)