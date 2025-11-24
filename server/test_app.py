import os
import json
import unittest
from unittest.mock import patch
from importlib import reload

class TestFlaskApp(unittest.TestCase):

    def setUp(self):
        # Enable scan API for tests
        os.environ["ENABLE_FLASK_SCAN_API"] = "true"
        # Reload module to apply env flag
        import server.app as app_module
        reload(app_module)
        self.app_module = app_module
        self.client = app_module.app.test_client()

    def test_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Available endpoints", r.data)

    def test_remediation_missing_file(self):
        # Ensure file missing triggers 500 or 404 gracefully
        with patch("builtins.open", side_effect=FileNotFoundError):
            r = self.client.get("/api/vulns/Chrome/remediation")
            self.assertEqual(r.status_code, 500)

    def test_remediation_success(self):
        fake_db = {
            "outdated_software": {
                "Chrome": {
                    "risk": "High",
                    "remediation": "Update immediately",
                    "reference_cve": "CVE-1234"
                }
            }
        }
        def fake_open(*args, **kwargs):
            from io import StringIO
            return StringIO(json.dumps(fake_db))
        with patch("builtins.open", fake_open):
            r = self.client.get("/api/vulns/Chrome/remediation")
            self.assertEqual(r.status_code, 200)
            data = r.get_json()
            self.assertEqual(data["name"], "Chrome")
            self.assertEqual(data["summary"], "High")

    @patch("server.app.run_all_scans", return_value=([], "Scan complete. No outdated software found."))
    def test_scan_endpoint(self, mock_scan):
        r = self.client.get("/api/scan")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("findings", data)

    def test_receive_vulnerability_scan(self):
        payload = {
            "machine_id": "abc123",
            "timestamp": "2024-01-01T00:00:00",
            "scan_data": {
                "vulnerabilities": [
                    {
                        "name": "Chrome",
                        "installed_version": "89.0",
                        "minimum_version": "90.0",
                        "risk": "High"
                    }
                ]
            }
        }
        r = self.client.post("/api/vulnerability-scan", json=payload)
        self.assertEqual(r.status_code, 200)
        # Retrieve
        r2 = self.client.get("/api/vulnerability-report/abc123")
        self.assertEqual(r2.status_code, 200)
        data = r2.get_json()
        self.assertEqual(len(data["vulnerabilities"]), 1)
        self.assertEqual(data["vulnerabilities"][0]["name"], "Chrome")

    def test_vulnerability_scan_missing_fields(self):
        r = self.client.post("/api/vulnerability-scan", json={})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()