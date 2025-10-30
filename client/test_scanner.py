import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.scanner import scan_outdated_software

class TestScanner(unittest.TestCase):
    def setUp(self):
        # Test vulnerability DB
        self.mock_vulnerability_db = [
            {
                "name": "Mozilla Firefox",
                "vulnerable_version": "80.0",
                "cve": "CVE-2020-15673",
                "solution": "Update to Firefox 80.0.1 or later."
            },
            {
                "name": "Google Chrome",
                "vulnerable_version": "90.0.4430.85",
                "cve": "CVE-2021-21224",
                "solution": "Update to Google Chrome 90.0.4430.85 or later."
            },
            {
                "name": "7-Zip",
                "vulnerable_version": "19.00",
                "cve": "CVE-2019-12345",
                "solution": "Update to 7-Zip 21.01 or later."
            }
        ]

    def test_version_is_vulnerable(self):
        # Tests to make sure a bug was removed that saw 10.0.1 as lower than 9.1.0
        mock_installed_software = [
            {"name": "Google Chrome", "version": "89.0.4389.90"}  # Vulnerable
        ]

        results = scan_outdated_software(mock_installed_software, self.mock_vulnerability_db)

        # Should expect 1 result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Google Chrome")

    def test_version_is_safe(self):
        # Tests that a newer version is not flagged as vulnerable.
        mock_installed_software = [
            {"name": "Google Chrome", "version": "90.0.4430.85"},  # Safe (equal)
            {"name": "Mozilla Firefox", "version": "81.0"}  # Safe (newer)
        ]

        results = scan_outdated_software(mock_installed_software, self.mock_vulnerability_db)

        # Should expect 0 results
        self.assertEqual(len(results), 0)

    def test_complex_version_is_vulnerable(self):
        # Tests a more complex version string.
        mock_installed_software = [
            {"name": "7-Zip", "version": "18.06"}  # Vulnerable
        ]

        results = scan_outdated_software(mock_installed_software, self.mock_vulnerability_db)

        # Should expect exactly 1 result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "7-Zip")

    def test_software_not_in_db(self):
        # Tests that a software not in our vulnerability database is not flagged.
        mock_installed_software = [
            {"name": "Microsoft Word", "version": "16.0"}  # Not in test DB
        ]

        results = scan_outdated_software(mock_installed_software, self.mock_vulnerability_db)

        # Should expect 0 results
        self.assertEqual(len(results), 0)

    def test_empty_software_list(self):
        # Tests that an empty list of installed software actually returns an empty list.
        mock_installed_software = []

        results = scan_outdated_software(mock_installed_software, self.mock_vulnerability_db)

        # Should expect 0 results
        self.assertEqual(len(results), 0)

    def test_invalid_version_string(self):
        # Checks that malformed strings don't crash the scanner
        mock_installed_software = [
            {"name": "Google Chrome", "version": "latest-beta"}  # Invalid version
        ]

        # We just want to make sure this doesn't crash
        try:
            results = scan_outdated_software(mock_installed_software, self.mock_vulnerability_db)
            # Should expect 0 results
            self.assertEqual(len(results), 0)
        except Exception as e:
            self.fail(f"Test crashed with invalid version string: {e}")


if __name__ == '__main__':
    # Lets file run directly
    unittest.main()