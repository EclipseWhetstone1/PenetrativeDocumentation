import os
import json
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from packaging import version

# change import path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.scanner import (
    scan_outdated_software,
    _load_vulnerability_database,
    run_all_scans,
    send_vulnerability_report,
    get_machine_id
)


class TestScanner(unittest.TestCase):

    def setUp(self):
        # New vulnerability.json database format (mapping of name -> details)
        self.mock_vulnerability_db = {
            "Google Chrome": {
                "minimum_version": "90.0.4430.85",
                "risk": "High"
            },
            "Mozilla Firefox": {
                "minimum_version": "80.0.1",
                "risk": "Medium"
            },
            "7-Zip": {
                "minimum_version": "21.01",
                "risk": "Critical"
            }
        }

    def test_version_is_vulnerable(self):
        installed = [
            {"name": "Google Chrome", "version": "89.0.4389.90"}  # lower version
        ]
        results = scan_outdated_software(installed, self.mock_vulnerability_db)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Google Chrome")

    def test_version_is_safe_equal(self):
        # Tests that the version equal to minimum is not flagged as vulnerable.
        installed = [
            {"name": "Google Chrome", "version": "90.0.4430.85"}  # equal boundary
        ]
        results = scan_outdated_software(installed, self.mock_vulnerability_db)
        self.assertEqual(len(results), 0)

    def test_version_is_safe_newer(self):
        installed = [
            {"name": "Mozilla Firefox", "version": "81.0"}  # newer version
        ]
        results = scan_outdated_software(installed, self.mock_vulnerability_db)
        self.assertEqual(len(results), 0)

    def test_complex_version_is_vulnerable(self):
        installed = [
            {"name": "7-Zip", "version": "18.06"}  # lower version
        ]
        results = scan_outdated_software(installed, self.mock_vulnerability_db)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "7-Zip")

    def test_software_not_in_db(self):
        installed = [
            {"name": "Microsoft Word", "version": "16.0"}
        ]
        results = scan_outdated_software(installed, self.mock_vulnerability_db)
        self.assertEqual(len(results), 0)

    def test_empty_software_list(self):
        results = scan_outdated_software([], self.mock_vulnerability_db)
        self.assertEqual(len(results), 0)

    def test_invalid_version_string(self):
        installed = [
            {"name": "Google Chrome", "version": "latest-beta"}  # invalid version
        ]
        # Result should be empty, so this shouldn't raise an exception
        results = scan_outdated_software(installed, self.mock_vulnerability_db)
        self.assertEqual(len(results), 0)

    @patch("client.scanner.requests.post")
    def test_send_vulnerability_report_payload(self, mock_post):
        mock_post.return_value.status_code = 200
        temp_dir = tempfile.mkdtemp()
        try:
            # Patch PROGRAMDATA to temp dir to avoid writing to real location
            with patch.dict(os.environ, {"PROGRAMDATA": temp_dir}):
                vulns = [
                    {
                        "name": "Google Chrome",
                        "installed_version": "89.0",
                        "minimum_version": "90.0",
                        "risk": "High"
                    }
                ]
                send_vulnerability_report(vulns)

                # Local payload file existence
                payload_path = os.path.join(os.path.dirname(__file__), 'last_scan_payload.json')
                self.assertTrue(os.path.exists(payload_path))
                with open(payload_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.assertEqual(len(data.get("vulnerabilities", [])), 1)
                self.assertIn("machine_id", data)
                mock_post.assert_called_once()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_machine_id_persistence(self):
        temp_dir = tempfile.mkdtemp()
        try:
            with patch.dict(os.environ, {"PROGRAMDATA": temp_dir}):
                first = get_machine_id()
                second = get_machine_id()
                self.assertEqual(first, second)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch("client.scanner._get_installed_software_windows")
    @patch("client.scanner._load_vulnerability_database")
    @patch("client.scanner.send_vulnerability_report")
    def test_run_all_scans_integration(self, mock_send, mock_load, mock_get_installed):
        mock_load.return_value = {
            "App A": {"minimum_version": "2.0", "risk": "Low"}
        }
        mock_get_installed.return_value = [
            {"name": "App A", "version": "1.0"}
        ]

        vulns, summary = run_all_scans()
        self.assertEqual(len(vulns), 1)
        self.assertIn("Found 1", summary)
        mock_send.assert_called_once()

    @patch("client.scanner._get_installed_software_windows")
    @patch("client.scanner._load_vulnerability_database")
    @patch("client.scanner.send_vulnerability_report")
    def test_run_all_scans_no_installed(self, mock_send, mock_load, mock_get_installed):
        mock_load.return_value = {
            "App A": {"minimum_version": "2.0", "risk": "Low"}
        }
        mock_get_installed.return_value = []
        vulns, summary = run_all_scans()
        self.assertEqual(len(vulns), 0)
        self.assertIn("Could not find any installed software", summary)
        mock_send.assert_called_once()


if __name__ == '__main__':
    unittest.main()