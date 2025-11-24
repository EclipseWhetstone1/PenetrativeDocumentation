# # (add the os import + FLASK_DEBUG env var logic)

# # Stage and commit the changes
# git add server/app.py
# git commit -m "Make Flask debug configurable via FLASK_DEBUG env var"

# # Push to GitHub (retry HTTPS if SSH fails)
# git push -u origin feature/flask-debug-env
# # or if SSH keeps failing, switch to HTTPS:
# git remote set-url origin https://github.com/EclipseWhetstone1/PenetrativeDocumentation.git
# git push -u origin feature/flask-debug-env# (add the os import + FLASK_DEBUG env var logic)

# # Stage and commit the changes
# git add server/app.py
# git commit -m "Make Flask debug configurable via FLASK_DEBUG env var"

# # Push to GitHub (retry HTTPS if SSH fails)
# git push -u origin feature/flask-debug-env
# # or if SSH keeps failing, switch to HTTPS:
# git remote set-url origin https://github.com/EclipseWhetstone1/PenetrativeDocumentation.git
# git push -u origin feature/flask-debug-env

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging
import json
import time
import os
import pathlib
import traceback

# Enable toggling Flask debug mode via environment variable FLASK_DEBUG
# Accepts: "1", "true", "True", "yes" to enable. Defaults to False.
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
import subprocess

# using FLASK_PORT and ENABLE_FLASK_SCAN_API as testing variables
FLASK_PORT = int(os.getenv("FLASK_PORT", "3002"))
ENABLE_FLASK_SCAN_API = os.getenv("ENABLE_FLASK_SCAN_API", "false").lower() in ("1", "true", "yes")

# --- INTEGRATION: Step 1 ---
try:
    from scanner import run_all_scans
except ImportError:
    def run_all_scans():
        return ["ERROR: scanner.py not found or contains an error."]

# --- VirtualBox Configuration ---
# Final version will have to update these values to match our VM snapshot when we are ready to run and test.
VM_NAME = "Windows 10 Dev"  # The name of our VM
SNAPSHOT_NAME = "CleanInstall"   # The name of the snapshot to revert to
# VBoxManage is usually in the VirtualBox installation directory for Windows.
# We will have to update this path if we are using a different installation directory.
VBOXMANAGE_PATH = "C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe"

# --- GUEST VM CONFIGURATION ---
# For final scanning application: Update these values for our Target VM.
GUEST_USERNAME = "VMUsername"  # The username for an account INSIDE the Windows VM
GUEST_PASSWORD = "VMPassword"  # The password for that account
# The full path to the Python executable INSIDE the VM.
GUEST_PYTHON_PATH = "C:\\Users\\VMUsername\\AppData\\Local\\Programs\\Python\\Python39\\python.exe"
# The full path to the main.py script INSIDE the VM.
GUEST_SCRIPT_PATH = "C:\\Users\\VMUsername\\Desktop\\client\\main.py"

app = Flask(__name__)
CORS(app)


# --- VBoxManage Helper Functions ---

def run_vbox_command(args):
    def run_vbox_command(args):
        """Helper function to run VBoxManage commands safely without exposing sensitive data."""
    command = [VBOXMANAGE_PATH] + args

    # Create a redacted version for logging
    redacted = []
    skip_next = False
    
    for item in command:
        if skip_next:
            redacted.append("***REDACTED***")
            skip_next = False
        elif item.lower() in ("--password", "-p"):
            skip_next = True
            redacted.append(item)
        else:
            redacted.append(item)

    print("Running VBoxManage command (arguments redacted for security).")

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout

    except FileNotFoundError:
        error_msg = f"Error: VBoxManage.exe not found at '{VBOXMANAGE_PATH}'. Please check the path."
        logging.error(error_msg)
        return False, "An internal error occurred while running the VM command."

    except subprocess.CalledProcessError as e:
        error_msg = f"Error executing command: {e}\n{e.stderr}"
        logging.error(error_msg)
        return False, "An internal error occurred while running the VM command."

    except subprocess.TimeoutExpired:
        error_msg = "Error: VBoxManage command timed out after 2 minutes."
        logging.error(error_msg)
        return False, "An internal error occurred while running the VM command."


def revert_to_snapshot():
    """Reverts the VM to the clean snapshot."""
    return run_vbox_command(["snapshot", VM_NAME, "restore", SNAPSHOT_NAME])

def start_vm():
    """Starts the VM without pulling up the window."""
    return run_vbox_command(["startvm", VM_NAME, "--type", "headless"])

def stop_vm():
    """Shuts down the VM."""
    return run_vbox_command(["controlvm", VM_NAME, "poweroff"])

def run_in_guest():
    """
    Executes the Python client application inside the running guest VM.
    NOTE: This requires VirtualBox Guest Additions to be installed in the VM.
    """
    args = [
        "guestcontrol", VM_NAME, "run",
        "--username", GUEST_USERNAME,
        "--password", GUEST_PASSWORD,
        "--exe", GUEST_PYTHON_PATH,
        "--", GUEST_SCRIPT_PATH,
        "--headless" # Arguments to the executable
    ]
    return run_vbox_command(args)


# --- API Endpoints ---

# --- INTEGRATION: Step 2 ---

@app.route('/api/simulate', methods=['POST'])
def start_simulation():
    """
    This endpoint now runs a real simulation using VirtualBox.
    It streams status updates back to the React frontend.
    """
    def event_stream():
        # Step 1: Revert the VM to a clean state
        yield "data: Reverting VM to clean snapshot...\n\n"
        success, output = revert_to_snapshot()
        if not success:
            yield "data: ERROR: An internal server error occurred while executing the simulation.\n\n"
            yield "data: FINISHED\n\n"
            return
        yield "data: Revert successful.\n\n"
        time.sleep(1)

        # Step 2: Start the VM
        yield "data: Starting virtual machine... (this may take a moment)\n\n"
        success, output = start_vm()
        if not success:
            yield f"data: ERROR: {output}\n\n"
            yield "data: FINISHED\n\n"
            return
        yield "data: VM started successfully in the background.\n\n"
        time.sleep(30)  # Gives the VM time to boot

        # Step 3: Run the exploit inside the VM
        yield "data: Executing the client application inside the VM...\n\n"
        success, output = run_in_guest()
        if not success:
            yield f"data: ERROR during guest execution: {output}\n\n"
        else:
            yield "data: Client execution complete. Parsing results...\n\n"
            try:
                # The output variable now contains the JSON string from main.py
                scan_results = json.loads(output)
                if scan_results.get("status") == "success":
                    vulnerabilities = scan_results.get("vulnerabilities", [])
                    if vulnerabilities:
                        yield "data: --- SIMULATION RESULTS ---\n\n"
                        for vuln in vulnerabilities:
                            # Send each finding back to the UI
                            yield f"data: {vuln.replace('\\n', ' ')}\n\n"
                    else:
                        yield "data: Scan completed inside VM. No vulnerabilities found.\n\n"
                else:
                    error_msg = scan_results.get('message', 'Unknown error in client.')
                    yield f"data: ERROR from client: {error_msg}\n\n"
            except json.JSONDecodeError:
                yield "data: ERROR: Failed to parse JSON response from the client script in the VM.\n\n"
                print(f"Raw output from guest: {output}")

        # Step 4: Shut down the VM
        yield "data: Shutting down the VM...\n\n"
        success, output = stop_vm()
        if not success:
            yield f"data: ERROR: {output}\n\n"
        else:
            yield "data: VM powered off.\n\n"

        yield "data: FINISHED\n\n"

    return Response(event_stream(), mimetype='text/event-stream')

# --- Remediation endpoint (US010) ---
@app.route("/", methods=["GET"])
def index():
    """Basic root endpoint for testing."""
    return """
    <h2>Penetrative Documentation Server</h2>
    <p>Available endpoints:</p>
    <ul>
      <li><code>/api/vulns/&lt;vuln_key&gt;/remediation</code></li>
      <li><code>/api/scan</code></li>
      <li><code>/api/simulate</code></li>
    </ul>
    """, 200
@app.route("/api/vulns/<vuln_key>/remediation", methods=["GET"])
def get_remediation(vuln_key):
    """
    Return public remediation guidance for a given vulnerability key.
    Uses vulnerability_database.json -> outdated_software mapping.
    """
    import json
    from flask import jsonify
    from urllib.parse import unquote
    import os

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "vulnerability_database.json")

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            vulns = data.get("outdated_software", {})
    except FileNotFoundError:
        return jsonify({"error": "vulnerability_database.json not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "failed to parse vulnerability_database.json"}), 500

    key = unquote(vuln_key)

    # Case-insensitive lookup
    if key not in vulns:
        for k in vulns:
            if k.lower() == key.lower():
                key = k
                break

    if key not in vulns:
        return jsonify({"error": "vulnerability not found"}), 404

    vuln = vulns[key]
    safe_content = {
        "name": key,
        "summary": vuln.get("risk", ""),
        "remediation": vuln.get("remediation", ""),
        "reference_cve": vuln.get("reference_cve"),
        "tutorial_url": vuln.get("tutorial_url", ""),
        "walkthrough": vuln.get("walkthrough", [])
    }
    return jsonify(safe_content), 200

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")
pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

def _load_reports():
    try:
        with open(REPORTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        # Corrupt file: return empty store (caller may overwrite)
        return {}

def _save_reports(reports):
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)


if ENABLE_FLASK_SCAN_API:
    @app.route('/api/scan', methods=['GET'])
    def get_scan_results():
        """Runs the enhanced scanner and returns Recompute Findings."""
        print("Received request to /api/scan (Flask). Running enhanced scanner...")
        try:
            findings = run_all_scans()  # updated scanner.py returns multi-line strings
            # Wrap in JSON according to INT002B contract
            return jsonify({"findings": findings}), 200
        except Exception as e:
            logging.error("Error during scan:\n%s", traceback.format_exc())
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/vulnerability-scan", methods=["POST"])
    def receive_vulnerability_scan():
        """
        Accepts POSTs from the client/scanner.py.
        Normalizes payload to the format that React expects and stores it by machine_id.
        """
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        payload = request.get_json()
        machine_id = payload.get("machine_id")
        timestamp = payload.get("timestamp")
        scan_data = payload.get("scan_data", {})
        vulnerabilities = scan_data.get("vulnerabilities", [])

        if not machine_id or not timestamp:
            return jsonify({"error": "Missing required fields: machine_id or timestamp"}), 400

        # tried to change schema to match React frontend expectations
        normalized = []
        for v in vulnerabilities:
            # scanner.py provides: name, installed_version, minimum_version, risk
            normalized.append({
                "name": v.get("name"),
                "risk": v.get("risk"),
                "installed_version": v.get("installed_version") or v.get("installedVersion"),
                "vulnerable_version": v.get("minimum_version") or v.get("vulnerable_version"),
                "explanation": v.get("risk") or "",
                "fix": v.get("remediation") or ""
            })

        reports = _load_reports()
        reports[machine_id] = {
            "machine_id": machine_id,
            "timestamp": timestamp,
            "vulnerabilities": normalized
        }
        _save_reports(reports)

        return jsonify({"status": "ok", "machine_id": machine_id}), 200

    @app.route("/api/vulnerability-report/<machine_id>", methods=["GET"])
    def get_vulnerability_report(machine_id):
        """
        Returns the latest stored report for a machine_id (the React frontend calls this).
        """
        reports = _load_reports()
        if machine_id not in reports:
            return jsonify({"error": "report not found"}), 404
        return jsonify(reports[machine_id]), 200
else:
    print("Flask vulnerability scan API is DISABLED. Set ENABLE_FLASK_SCAN_API=True to enable.")

if __name__ == '__main__':
    # app.run(debug=True, port=5000) # left off host="0.0.0.0"
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
