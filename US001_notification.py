import tkinter as tk
from tkinter import messagebox

# ----------------------------
# Step 1: Create the main window
# ----------------------------
window = tk.Tk()
window.title("Educational Security Report")  # Title bar text
window.geometry("400x200")  # Window size
window.resizable(False, False)  # Fix the window size

# ----------------------------
# Step 2: Add message body
# ----------------------------
message = (
    "Your system has been safely compromised for educational purposes. "
    "This program will show you how it was done and how to protect yourself from real threats. "
    "No data has been harmed."
)

label = tk.Label(window, text=message, wraplength=380, justify="left")
label.pack(pady=20)

# ----------------------------
# Step 3: Define button actions
# ----------------------------
def learn_more():
    # This would trigger US002 report (placeholder for now)
    messagebox.showinfo("Report", "This would display the report from US002.")

def close_window():
    window.destroy()  # Close the pop-up

# ----------------------------
# Step 4: Add buttons
# ----------------------------
button_frame = tk.Frame(window)
button_frame.pack(pady=10)

learn_button = tk.Button(button_frame, text="Learn More", command=learn_more)
learn_button.pack(side="left", padx=10)

close_button = tk.Button(button_frame, text="Close", command=close_window)
close_button.pack(side="right", padx=10)

# ----------------------------
# Step 5: Run the window
# ----------------------------
window.mainloop()
