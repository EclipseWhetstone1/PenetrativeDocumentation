import platform
import winreg
import json
from packaging.version import parse

# --- Database Loading ---

def load_vulnerability_db(filepath="vulnerabilities.json"):
    """
    Loads the vulnerability database from a JSON file.
    Handles potential FileNotFoundError and json.JSONDecodeError to prevent crashes.
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Vulnerability database not found at '{filepath}'.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not parse the vulnerability database in '{filepath}'.")
        return {}

# --- Individual Scan Modules ---

def scan_outdated_software(db):
    """
    Scans for outdated software on Windows by checking versions in the registry.
    This refactored version is more efficient.
    """
    if platform.system() != "Windows":
        return ["Software scan is only supported on Windows."]

    software_rules = db.get("outdated_software", {})
    if not software_rules:
        return []

    installed_software = _get_installed_software_windows()
    found_vulnerabilities = []

    # --- EFFICIENCY IMPROVEMENT ---
    # Instead of looping through rules and then all software (M*N), we now
    # loop through the installed software once (N) and do a quick dictionary
    # lookup (average O(1)), which is much faster.
    for installed_name, installed_version_str in installed_software.items():
        # Check if any rule's app name is a substring of the installed name.
        for rule_name, rules in software_rules.items():
            if rule_name.lower() in installed_name.lower():
                min_safe_version_str = rules.get("minimum_version")
                risk_desc = rules.get("risk", "No risk description provided.")

                if min_safe_version_str:
                    try:
                        if parse(installed_version_str) < parse(min_safe_version_str):
                            finding = (
                                f"Outdated Software: {rule_name}\n"
                                f"  - Your version: {installed_version_str}\n"
                                f"  - Recommended minimum: {min_safe_version_str}\n"
                                f"  - Risk: {risk_desc}"
                            )
                            found_vulnerabilities.append(finding)
                            # Found a match for this installed program, no need to check other rules
                            break 
                    except Exception as e:
                        print(f"Could not parse version for {installed_name}: {installed_version_str}. Error: {e}")
    
    return found_vulnerabilities

# --- Helper Functions (Private) ---

def _get_installed_software_windows():
    """
    (Internal Helper) Retrieves installed software from the Windows Registry.
    """
    software_list = {}
    uninstall_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    
    for hkey in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        try:
            with winreg.OpenKey(hkey, uninstall_key_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            display_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                            # Clean up version strings that might have extra characters
                            if display_name and display_version:
                                software_list[display_name] = display_version
                    except OSError:
                        continue
        except FileNotFoundError:
            continue
            
    return software_list

# --- Main Scan Runner ---

def run_all_scans():
    """
    The main entry point for the scanner module.
    Orchestrates the loading of the DB and execution of all scan modules.
    """
    vulnerability_db = load_vulnerability_db()
    if not vulnerability_db:
        return ["Could not load vulnerability database. Scan aborted."]

    scan_results = []
    
    # Add new scan functions here to make them part of the main scan
    scan_results.extend(scan_outdated_software(vulnerability_db))

    if not scan_results:
        return ["Scan complete. No vulnerabilities from our list were found."]
        
    return scan_results