import os
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


APP_TITLE = "Security"

def parse_iso_timestamp(ts):
    if not ts:
        return datetime.min
    try:
        if ts.endswith('Z'):
            ts = ts.replace('Z', '+00:00')
        return datetime.fromisoformat(ts)
    except Exception:
        try:
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return datetime.min

class MonitoringUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")
        self.create_widgets()

    def create_widgets(self):
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        
        report_tab = ttk.Frame(self.notebook)
        self.notebook.add(report_tab, text='Report')
        lbl = ttk.Label(report_tab, text="Report view placeholder.\n(US002)", padding=10)
        lbl.pack(anchor='nw')

        
        self.attack_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.attack_tab, text='Attack Timeline')

        
        self.canvas = tk.Canvas(self.attack_tab)
        self.vsb = ttk.Scrollbar(self.attack_tab, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.timeline_frame = ttk.Frame(self.canvas)

        def _on_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.timeline_frame.bind("<Configure>", _on_frame_configure)

        self.canvas.create_window((0, 0), window=self.timeline_frame, anchor='nw')

        self.canvas.pack(side='left', fill='both', expand=True)
        self.vsb.pack(side='right', fill='y')

        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def clear_timeline(self):
        for w in self.timeline_frame.winfo_children():
            w.destroy()

    def load_attack_timeline(self):
        self.clear_timeline()
        json_path = os.path.join(os.path.dirname(__file__), 'attack_timeline.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as fh:
                events = json.load(fh)
        except FileNotFoundError:
            ttk.Label(self.timeline_frame,
                      text="No attack_timeline.json found in the UI folder.",
                      foreground='red').pack(anchor='w', padx=10, pady=10)
            return
        except Exception as e:
            ttk.Label(self.timeline_frame,
                      text=f"Error loading timeline: {e}",
                      foreground='red', wraplength=800).pack(anchor='w', padx=10, pady=10)
            return

        
        try:
            events.sort(key=lambda e: parse_iso_timestamp(e.get('timestamp')))
        except Exception:
            pass

       
        for ev in events:
            ts = parse_iso_timestamp(ev.get('timestamp'))
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S UTC") if ts != datetime.min else ev.get('timestamp', '')
            header_text = f"{ts_str} — {ev.get('title', 'Untitled event')}"
            header = ttk.Label(self.timeline_frame, text=header_text, font=('TkDefaultFont', 10, 'bold'))
            header.pack(anchor='w', padx=10, pady=(12, 2))
            desc = ttk.Label(self.timeline_frame, text=ev.get('description', ''), wraplength=820, justify='left')
            desc.pack(anchor='w', padx=20)
            sep = ttk.Separator(self.timeline_frame, orient='horizontal')
            sep.pack(fill='x', pady=(8, 2), padx=8)

    def on_tab_changed(self, event):
        widget = event.widget
        try:
            selected_index = widget.index("current")
            tab_text = widget.tab(selected_index, option="text")
        except Exception:
            tab_text = ''
        if tab_text == 'Attack Timeline':
            self.load_attack_timeline()

if __name__ == "__main__":
    app = MonitoringUI()
    app.mainloop()

