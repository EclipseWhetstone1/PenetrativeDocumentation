import React, { useState } from "react";

function App() {
  const [status, setStatus] = useState("");

  const sendReport = async () => {
    const payload = {
      machine_id: "test-client",
      timestamp: new Date().toISOString(),
      event: "REPORT_VIEWED",
      data: {}
    };

    try {
      const res = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const json = await res.json();
      setStatus("Server response: " + JSON.stringify(json));
    } catch (err) {
      setStatus("Error: " + err.message);
    }
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Virus App Frontend</h1>
      <button onClick={sendReport}>Send Test Report</button>
      <p>{status}</p>
    </div>
  );
}

export default App;