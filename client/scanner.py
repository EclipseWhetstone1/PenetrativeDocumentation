import os
import winreg
import json
import requests
import uuid
import datetime
import logging
from packaging import version

# --- Server/Machine ID Configuration ---
SERVER_URL = "http://localhost:5000/api/scan"
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

#
# def get_machine_id():
#     # Reads a persistent machine ID from a file, or creates one if it doesn't exist.
#     try:
#         with open(MACHINE_ID_FILE, 'r') as f:
#             machine_id = f.read().strip()
#         if not machine_id:
#             raise FileNotFoundError
#         return machine_id
#     except FileNotFoundError:
#         print("Machine ID file not found, creating one...")
#         machine_id = str(uuid.uuid4())
#         try:
#             with open(MACHINE_ID_FILE, 'w') as f:
#                 f.write(machine_id)
#             return machine_id
#         except Exception as e:
#             print(f"Error writing machine ID file: {e}")
#             return "volatile-machine-id-" + str(uuid.uuid4())  # Fallback


def send_vulnerability_report(vulnerabilities):
    # Sends the list of found vulnerabilities to the monitoring server.
    machine_id = get_machine_id()

    payload = {
        "machine_id": machine_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "VULNERABILITY_SCAN_RESULT",
        "scan_data": {
            "vulnerabilities": vulnerabilities,
            "raw_output": f"Scan complete. Found {len(vulnerabilities)} vulnerabilities."
        }
    }

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


# ---- Scan Functions ----


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
                    timeline_logger.info(f"Vulnerability found: {vuln} (Version: {installed_version})")
                    finding = {
                        "name": vuln,
                        "installed_version": installed_version,
                        "minimum_version": vuln_details.get('minimum_version'),
                        "risk": vuln_details.get('risk')
                    }
                    outdated_software.append(finding)
            except version.InvalidVersion:
                # Catches empty or invalid versions
                print(f"Warning: Could not compare versions for {vuln['name']}. Invalid format.")
                print(f"  Installed: '{installed_version}', Vulnerable: '{vuln['minimum_version']}'")
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
    # Loads DB, scans registry, and sends report.
    timeline_logger.info("----SCAN STARTED----")
    print("Loading vulnerability database...")
    vulnerability_db = _load_vulnerability_database()
    if not vulnerability_db:
        return "Error: Could not load vulnerability database."

    print("Scanning for installed software...")
    installed_software = _get_installed_software_windows()
    if not installed_software:
        print("Could not find any installed software in the registry.")
        # Still send an "empty" report
        send_vulnerability_report([])
        return "Could not find any installed software."

    print(f"Found {len(installed_software)} software entries. Comparing against database...")
    outdated_software = scan_outdated_software(installed_software, vulnerability_db)

    print("Sending report to server...")
    send_vulnerability_report(outdated_software)

    if not outdated_software:
        return "Scan complete. No outdated software found."
    else:
        timeline_logger.info(f"--- Scan Complete: {len(outdated_software)} vulnerabilities found. ---")
        return f"Scan complete. Found {len(outdated_software)} vulnerabilities."

if __name__ == '__main__':
    print("Running standalone scan...")
    report = run_all_scans()
    print(report)



# --- OLD CODE - DELETE LATER ---
#
# import platform
# import winreg
# import json
# from packaging.version import parse
#
# # --- Database Loading ---
#
# # def load_vulnerability_db(filepath="vulnerabilities.json"):
# def load_vulnerability_db(filepath="vulnerability_database.py"):
#     """
#     Loads the vulnerability database from a JSON file.
#     Handles potential FileNotFoundError and json.JSONDecodeError to prevent crashes.
#     """
#     try:
#         with open(filepath, 'r') as f:
#             return json.load(f)
#     except FileNotFoundError:
#         print(f"Error: Vulnerability database not found at '{filepath}'.")
#         return {}
#     except json.JSONDecodeError:
#         print(f"Error: Could not parse the vulnerability database in '{filepath}'.")
#         return {}
#
# # --- Individual Scan Modules ---
#
# def scan_outdated_software(db):
#     """
#     Scans for outdated software on Windows by checking versions in the registry.
#     Gets outdated software list, gets installed software, checks each software against
#     vulnerability database.
#     """
#     if platform.system() != "Windows":
#         return ["Software scan is only supported on Windows."]
#
#     software_rules = db.get("outdated_software", {})
#     if not software_rules:
#         return []
#
#     installed_software = _get_installed_software_windows()
#     found_vulnerabilities = []
#
#     # --- EFFICIENCY IMPROVEMENT ---
#     # Instead of looping through rules and then all software (M*N), we now
#     # loop through the installed software once (N) and do a quick dictionary
#     # lookup (average O(1)), which is much faster.
#     for installed_name, installed_version_str in installed_software.items():
#         # Check if any rule's app name is a substring of the installed name.
#         for rule_name, rules in software_rules.items():
#             if rule_name.lower() in installed_name.lower():
#                 min_safe_version_str = rules.get("minimum_version")
#                 risk_desc = rules.get("risk", "No risk description provided.")
#
#                 if min_safe_version_str:
#                     try:
#                         if parse(installed_version_str) < parse(min_safe_version_str):
#                             finding = (
#                                 f"Outdated Software: {rule_name}\n"
#                                 f"  - Your version: {installed_version_str}\n"
#                                 f"  - Recommended minimum: {min_safe_version_str}\n"
#                                 f"  - Risk: {risk_desc}"
#                             )
#                             found_vulnerabilities.append(finding)
#                             # Found a match for this installed program, no need to check other rules
#                             break
#                     except Exception as e:
#                         print(f"Could not parse version for {installed_name}: {installed_version_str}. Error: {e}")
#
#     return found_vulnerabilities
#
# # --- Helper Functions (Private) ---
#
# def _get_installed_software_windows():
#     """
#     Retrieves installed software from the Windows Registry.
#     """
#     software_list = {}
#     uninstall_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
#
#     for hkey in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
#         try:
#             with winreg.OpenKey(hkey, uninstall_key_path) as key:
#                 for i in range(winreg.QueryInfoKey(key)[0]):
#                     try:
#                         subkey_name = winreg.EnumKey(key, i)
#                         with winreg.OpenKey(key, subkey_name) as subkey:
#                             display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
#                             display_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
#                             # Clean up version strings that might have extra characters
#                             if display_name and display_version:
#                                 software_list[display_name] = display_version
#                     except OSError:
#                         continue
#         except FileNotFoundError:
#             continue
#
#     return software_list
#
# # --- Main Scan Runner ---
#
# def run_all_scans():
#     """
#     The main entry point for the scanner module.
#     Loads vulnerabilities, runs scanning process.
#     """
#     vulnerability_db = load_vulnerability_db()
#     if not vulnerability_db:
#         return ["Could not load vulnerability database. Scan aborted."]
#
#     scan_results = []
#
#     # Add new scan functions here to make them part of the main scan
#     scan_results.extend(scan_outdated_software(vulnerability_db))
#
#     if not scan_results:
#         return ["Scan complete. No vulnerabilities from our list were found."]
#
#     return scan_results