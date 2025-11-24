import os
import winreg
import json
import requests
import uuid
import datetime
import logging
from packaging import version

# --- Server/Machine ID Configuration ---
SERVER_URL = "http://localhost:3001/api/vulnerability-scan"
MACHINE_ID_FILE = os.path.join(os.path.dirname(__file__), '..', 'monitoring', 'client', 'machine_id.txt')

# --- Timeline Configuration ---
APP_DATA_DIR = os.path.join(os.environ['PROGRAMDATA'], 'EducationalScanner')
TIMELINE_LOG_FILE = os.path.join(APP_DATA_DIR, 'timeline.log')
try:
    os.makedirs(APP_DATA_DIR, exist_ok=True)
except OSError:
    pass

timeline_logger = logging.getLogger('TimelineLogger')
timeline_logger.setLevel(logging.INFO)
try:
    handler = logging.FileHandler(TIMELINE_LOG_FILE, mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%dT%H:%M:%SZ'))
    timeline_logger.addHandler(handler)
except Exception:
    print("Warning: Could not create timeline log file.")

def get_machine_id():
    """
    Reads a persistent machine ID from a file in C: ProgramData,
    or creates one if it doesn't exist.
    """
    # Use a system-wide, writable directory
    APP_DATA_DIR = os.path.join(os.environ['PROGRAMDATA'], 'EducationalScanner')
    MACHINE_ID_FILE = os.path.join(APP_DATA_DIR, 'machine_id.txt')

    # Ensure the directory exists
    try:
        os.makedirs(APP_DATA_DIR, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {APP_DATA_DIR}: {e}")
        # Fallback to a volatile ID if we can't create the dir
        return "volatile-machine-id-" + str(uuid.uuid4())

    try:
        with open(MACHINE_ID_FILE, 'r') as f:
            machine_id = f.read().strip()
        if not machine_id:
            raise FileNotFoundError
        return machine_id
    except FileNotFoundError:
        print(f"Machine ID file not found at {MACHINE_ID_FILE}, creating one...")
        machine_id = str(uuid.uuid4())
        try:
            with open(MACHINE_ID_FILE, 'w') as f:
                f.write(machine_id)
            return machine_id
        except Exception as e:
            print(f"Error writing machine ID file: {e}")
            return "volatile-machine-id-" + str(uuid.uuid4())


def send_vulnerability_report(vulnerabilities):
    # Sends the list of found vulnerabilities to the monitoring server.
    machine_id = get_machine_id()

    normalized_vulns = []
    for v in (vulnerabilities or []):
        if isinstance(v, dict):
            normalized_vulns.append({
                "name": v.get("name"),
                "risk": v.get("risk", ""),
                "installed_version": v.get("installed_version") or v.get("installedVersion", ""),
                "vulnerable_version": v.get("minimum_version") or v.get("vulnerable_version", ""),
                "explanation": v.get("risk", "") or v.get("explanation"),
                "fix": v.get("remediation") or v.get("fix", "")
            })
        else:
            # Fallback for unexpected formats
            normalized_vulns.append({
                "name": str(v),
                "risk": "",
                "installed_version": "",
                "vulnerable_version": "",
                "explanation": "",
                "fix": ""
            })

    payload = {
        "machine_id": machine_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "vulnerabilities": normalized_vulns, # moved up. Check if this fixes it.
        "type": "VULNERABILITY_SCAN_RESULT",
        "scan_data": {  # moved down
            "vulnerabilities": normalized_vulns,
            "raw_output": f"Scan complete. Found {len(normalized_vulns)} vulnerabilities."
        }
    }

    # Write local copy of payload for debugging
    try:
        out_path = os.path.join(os.path.dirname(__file__), 'last_scan_payload.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        print(f"Local scan payload written to {out_path}")
    except Exception as e:
        print(f"Warning: Could not write local scan payload file: {e}")

    print(f"Sending report to {SERVER_URL}...")
    try:
        response = requests.post(SERVER_URL, json=payload)
        if response.status_code == 200:
            print("Report successfully sent to server.")
        else:
            print(f"Failed to send report. Server responded with: {response.status_code} {response.text}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Is it running?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# --- Scan Functions ---


# --- Database Loading ---

def _load_vulnerability_database():
    """
    Loads the vulnerability database from the JSON file.
    """
    # This now correctly looks for 'vulnerabilities.json'
    db_path = os.path.join(os.path.dirname(__file__), 'vulnerabilities.json')
    timeline_logger.info("Vulnerability database loaded.")

    if not os.path.exists(db_path):
        print(f"Error: Vulnerability database not found at {db_path}.")
        print("Please ensure 'vulnerability_database.py' has been renamed to 'vulnerabilities.json'")
        return []

    try:
        with open(db_path, 'r') as f:
            data = json.load(f)
            return data.get("outdated_software", {})
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {db_path}. Is it a valid JSON file?")
        return []
    except FileNotFoundError:
        print(f"Error: Vulnerability database not found at {db_path}.")
        return []


# --- Individual Scan Modules ---

def scan_outdated_software(installed_software, vulnerability_db):
    # Compares installed software versions against the vulnerability database.
    outdated_software = []

    installed_map = {item['name'].lower(): item['version'] for item in installed_software}
    timeline_logger.info("Scan module started: scan_outdated_software")

    for vuln, vuln_details in vulnerability_db.items():
        vuln_name_lower = vuln.lower()
        if vuln_name_lower in installed_map:
            installed_version = installed_map[vuln_name_lower]

            try:
                if version.parse(installed_version) < version.parse(vuln_details['minimum_version']):
                    outdated_software.append({
                        "name": vuln,
                        "installed_version": installed_version,
                        "minimum_version": vuln_details.get('minimum_version'),
                        "risk": vuln_details.get('risk')
                    })
            except version.InvalidVersion:
                # FIXED: vuln is a string key, not dict
                print(f"Warning: Could not compare versions for '{vuln}'. Invalid format.")
                print(f"  Installed: '{installed_version}', Minimum: '{vuln_details.get('minimum_version')}'")
                continue
                
    timeline_logger.info("Scan module finished: scan_outdated_software")
    
    return outdated_software


# --- Helper Functions (Private) ---

def _get_installed_software_windows():
    # Retrieves a list of installed software from the Windows Registry.
    installed_software = []
    # Paths to check (User, 32-bit, and 64-bit applications)
    registry_paths = [
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    ]

    for hive, path in registry_paths:
        try:
            with winreg.OpenKey(hive, path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            # Use .get() to avoid errors if DisplayName or DisplayVersion don't exist
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            display_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]

                            if display_name and display_version:
                                installed_software.append({
                                    "name": display_name,
                                    "version": display_version
                                })
                    except OSError:
                        continue  # Skips entries that cause errors
        except FileNotFoundError:
            continue  # If registry path doesn't exist

    return installed_software


# --- Main Scanner ---

def run_all_scans():    
    timeline_logger.info("----SCAN STARTED----")
    # Loads DB, scans registry, and sends report.
    print("Loading vulnerability database...")
    vulnerability_db = _load_vulnerability_database()
    if not vulnerability_db:
        send_vulnerability_report([])
        return [], "Error: Could not load vulnerability database."

    print("Scanning for installed software...")
    installed_software = _get_installed_software_windows()
    if not installed_software:
        # Still send an "empty" report
        send_vulnerability_report([])
        return [], "Could not find any installed software."

    print(f"Found {len(installed_software)} software entries. Comparing against database...")
    outdated_software = scan_outdated_software(installed_software, vulnerability_db)

    print("Sending report to server...")
    send_vulnerability_report(outdated_software)

    summary = ("Scan complete. Found {0} vulnerabilities.".format(len(outdated_software))
               if outdated_software else "Scan complete. No outdated software found.")
    return outdated_software, summary

if __name__ == '__main__':
    print("Running standalone scan...")
    vulns, summary = run_all_scans()
    print(summary)
