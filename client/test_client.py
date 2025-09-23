import requests
from payload import assemble_payload

url = "http://localhost:5000/api/report"
payload = assemble_payload("PROGRAM_STARTED")

response = requests.post(url, json=payload)
print("Status:", response.status_code)
print("Response:", response.json())
