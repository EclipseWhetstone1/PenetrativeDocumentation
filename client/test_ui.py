import os
import unittest
if os.environ.get("CI") == "true":
    raise unittest.SkipTest("Skipping UI tests in CI environment without display.")

import os
import sys
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from client.ui import SecurityApp

class TestSecurityApp(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Prevent window popup during tests
        self.app = SecurityApp(self.root)

    def tearDown(self):
        self.root.destroy()

    @patch("client.ui.run_all_scans", return_value=(
        [
            {
                "name": "Chrome",
                "installed_version": "89.0",
                "minimum_version": "90.0",
                "risk": "High"
            }
        ],
        "Scan complete. Found 1 vulnerabilities."
    ))
    def test_show_report_populates_text(self, mock_scan):
        self.app.show_report()
        content = self.app.report_text.get("1.0", tk.END)
        self.assertIn("Scan complete. Found 1 vulnerabilities.", content)
        self.assertIn("Chrome: installed=89.0", content)

    @patch("client.ui.run_all_scans", return_value=([], "Scan complete. No outdated software found."))
    def test_show_report_no_vulns(self, mock_scan):
        self.app.show_report()
        content = self.app.report_text.get("1.0", tk.END)
        self.assertIn("No outdated software found.", content)

    def test_frame_switching(self):
        # Initially main_frame is packed, report_frame hidden
        self.assertTrue(self.app.main_frame.winfo_manager())
        self.assertFalse(self.app.report_frame.winfo_manager())
        # Show report
        with patch("client.ui.run_all_scans", return_value=([], "Scan complete. No outdated software found.")):
            self.app.show_report()
        self.assertFalse(self.app.main_frame.winfo_manager())
        self.assertTrue(self.app.report_frame.winfo_manager())
        # Back
        self.app.show_main_frame()
        self.assertTrue(self.app.main_frame.winfo_manager())
        self.assertFalse(self.app.report_frame.winfo_manager())


if __name__ == "__main__":
    unittest.main()