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
# Enable toggling Flask debug mode via environment variable FLASK_DEBUG
# Accepts: "1", "true", "True", "yes" to enable. Defaults to False.
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
import subprocess

# --- INTEGRATION: Step 1 ---
try:
    from scanner import run_all_scans
except ImportError:
    def run_all_scans():
        return ["ERROR: scanner.py not found or contains an error."]

# --- VirtualBox Configuration ---
# TODO: We will have to update these values to match our VM snapshot when we are ready to run and test.
VM_NAME = "Windows 10 Dev"  # The name of our VM
SNAPSHOT_NAME = "CleanInstall"   # The name of the snapshot to revert to
# VBoxManage is usually in the VirtualBox installation directory for Windows.
# We will have to update this path if we are using a different installation directory.
VBOXMANAGE_PATH = "C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe"

# --- GUEST VM CONFIGURATION ---
# TODO: Update these values for our Target VM.
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
    """Helper function to run VBoxManage commands."""
    command = [VBOXMANAGE_PATH] + args
    print(f"Running command: {' '.join(command)}")
    try:
        # Using check=True will raise a CalledProcessError if the command fails
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return True, result.stdout
    except FileNotFoundError:
        error_msg = f"Error: VBoxManage.exe not found at '{VBOXMANAGE_PATH}'. Please check the path."
        print(error_msg)
        return False, error_msg
    except subprocess.CalledProcessError as e:
        error_msg = f"Error executing command: {e}\n{e.stderr}"
        print(error_msg)
        return False, error_msg
    except subprocess.TimeoutExpired:
        error_msg = "Error: VBoxManage command timed out after 2 minutes."
        print(error_msg)
        return False, error_msg

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
@app.route('/api/scan', methods=['GET'])
def get_scan_results():
    """Runs the enhanced scanner and returns Recompute Findings."""
    print("Received request to /api/scan. Running enhanced scanner...")
    try:
        findings = run_all_scans()  # updated scanner.py returns multi-line strings
        # Wrap in JSON according to INT002B contract
        return jsonify({"findings": findings}), 200
    except Exception as e:
        print(f"Error during scan: {e}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


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
            yield f"data: ERROR: {output}\n\n"
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

if __name__ == '__main__':
    # app.run(debug=True, port=5000) # left off host="0.0.0.0"
    app.run(debug=FLASK_DEBUG, port=5000)


# --- Eclipse's original block of code ---
# logging.basicConfig(
#     filename="reports.log",
#     level=logging.INFO,
#     format="%(message)s"
# )
#
# def validate_payload(data):
#     required = ["machine_id", "timestamp", "event", "data"]
#     return all(key in data for key in required)
#
# @app.route("/api/report", methods=["POST"])
# def report():
#     if not request.is_json:
#         return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
#
#     data = request.get_json()
#     if not validate_payload(data):
#         return jsonify({"status": "error", "message": "Missing required fields"}), 400
#
#     logging.info(json.dumps(data))
#     return jsonify({"status": "ok", "received_event": data["event"]}), 200
#
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)


# --- Original app.py before modifications to Guest VM ---
# from flask import Flask, request, jsonify, Response
# from flask_cors import CORS
# import logging
# import json
# import time
# import os
# import subprocess
#
# # --- INTEGRATION: Step 1 ---
# try:
#     from scanner import run_all_scans
# except ImportError:
#     def run_all_scans():
#         return ["ERROR: scanner.py not found or contains an error."]
#
# # --- VirtualBox Configuration ---
# # TODO: We will have to update these values to match our VM snapshot when we are ready to run and test.
# VM_NAME = "Windows 10 Dev"  # The name of our VM
# SNAPSHOT_NAME = "CleanInstall"   # The name of the snapshot to revert to
# # VBoxManage is usually in the VirtualBox installation directory for Windows.
# # We will have to update this path if we are using a different installation directory.
# VBOXMANAGE_PATH = "C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe"
#
# app = Flask(__name__)
# CORS(app)
#
#
# # --- VBoxManage Helper Functions ---
#
# def run_vbox_command(args):
#     """Helper function to run VBoxManage commands."""
#     command = [VBOXMANAGE_PATH] + args
#     print(f"Running command: {' '.join(command)}")
#     try:
#         # Using check=True will raise a CalledProcessError if the command fails
#         result = subprocess.run(command, check=True, capture_output=True, text=True)
#         return True, result.stdout
#     except FileNotFoundError:
#         error_msg = f"Error: VBoxManage.exe not found at '{VBOXMANAGE_PATH}'. Please check the path."
#         print(error_msg)
#         return False, error_msg
#     except subprocess.CalledProcessError as e:
#         error_msg = f"Error executing command: {e}\n{e.stderr}"
#         print(error_msg)
#         return False, error_msg
#
# def revert_to_snapshot():
#     """Reverts the VM to the clean snapshot."""
#     return run_vbox_command(["snapshot", VM_NAME, "restore", SNAPSHOT_NAME])
#
# def start_vm():
#     """Starts the VM without pulling up the window."""
#     return run_vbox_command(["startvm", VM_NAME, "--type", "headless"])
#
# def stop_vm():
#     """Shuts down the VM."""
#     return run_vbox_command(["controlvm", VM_NAME, "poweroff"])
#
#
# # --- API Endpoints ---
# # --- INTEGRATION: Step 2 ---
# @app.route('/api/scan', methods=['GET'])
# def get_scan_results():
#     """Runs the actual scanner."""
#     print("Received request to /api/scan. Running scanner...")
#     try:
#         results = run_all_scans()
#         print(f"Scan complete. Found {len(results)} items.")
#         return jsonify(results)
#     except Exception as e:
#         print(f"An error occurred during scan: {e}")
#         return jsonify({"error": "An internal server error occurred during the scan."}), 500
#
# @app.route('/api/simulate', methods=['POST'])
# def start_simulation():
#     """
#     This endpoint now runs a real simulation using VirtualBox.
#     It streams status updates back to the React frontend.
#     """
#
#     def event_stream():
#         # Step 1: Revert the VM to a clean state
#         yield "data: Reverting VM to clean snapshot...\n\n"
#         success, output = revert_to_snapshot()
#         if not success:
#             yield f"data: ERROR: {output}\n\n"
#             yield "data: FINISHED\n\n"
#             return
#         yield "data: Revert successful.\n\n"
#         time.sleep(1)
#
#         # Step 2: Start the VM
#         yield "data: Starting virtual machine... (this may take a moment)\n\n"
#         success, output = start_vm()
#         if not success:
#             yield f"data: ERROR: {output}\n\n"
#             yield "data: FINISHED\n\n"
#             return
#         yield "data: VM started successfully in the background.\n\n"
#         time.sleep(5)  # Gives the VM time to boot
#
#         # Step 3: Run the exploit inside the VM (currently only placeholder with time.sleep(10) )
#         # (In a real scenario, we would use VBoxManage guestcontrol to run a script inside the VM)
#         yield "data: Running simulated exploit against the running VM...\n\n"
#         time.sleep(10) # Simulate exploit running for 10 seconds
#         yield "data: Exploit simulation complete.\n\n"
#
#         # Step 4: Shut down the VM
#         yield "data: Shutting down the VM...\n\n"
#         success, output = stop_vm()
#         if not success:
#             yield f"data: ERROR: {output}\n\n"
#         else:
#             yield "data: VM powered off.\n\n"
#
#         yield "data: FINISHED\n\n"
#
#     return Response(event_stream(), mimetype='text/event-stream')
#
# if __name__ == '__main__':
#     app.run(debug=True, port=5000) # left off host="0.0.0.0"