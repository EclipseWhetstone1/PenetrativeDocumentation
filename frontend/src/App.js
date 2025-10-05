import React, { useState } from "react";

// CSS-in-JS styling, just to keep all the styling in one file.
const styles = {
  container: {
    fontFamily: 'Arial, sans-serif',
    maxWidth: '800px',
    margin: '0 auto',
    padding: '20px',
    backgroundColor: '#f4f7f6',
    borderRadius: '8px'
  },
  header: {
    fontSize: '2.5em',
    color: '#333',
    textAlign: 'center',
    marginBottom: '30px'
  },
  buttonContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: '30px'
  },
  button: {
    padding: '12px 25px',
    fontSize: '1.1em',
    margin: '0 10px',
    cursor: 'pointer',
    border: 'none',
    borderRadius: '5px',
    backgroundColor: '#007bff',
    color: 'white',
    transition: 'background-color 0.3s ease'
  },
  buttonDisabled: {
    backgroundColor: '#cccccc',
    cursor: 'not-allowed'
  },
  section: {
    marginTop: '20px',
    border: '1px solid #ddd',
    padding: '15px',
    borderRadius: '5px',
    backgroundColor: 'white'
  },
  sectionTitle: {
    fontSize: '1.5em',
    marginBottom: '10px',
    color: '#555'
  },
  preformatted: {
    whiteSpace: 'pre-wrap',
    wordWrap: 'break-word',
    backgroundColor: '#efefef',
    padding: '10px',
    borderRadius: '4px',
    maxHeight: '250px',
    overflowY: 'auto'
  },
  log: {
    backgroundColor: '#2b2b2b',
    color: '#a9b7c6',
    fontFamily: 'monospace',
    minHeight: '200px'
  }
};

function App() {
  const [status, setStatus] = useState("");
  const [scanResults, setScanResults] = useState('');
  const [simulationLog, setSimulationLog] = useState([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isScanning, setIsScanning] = useState(false);

  // --- INTEGRATION: Handles the actual data from the Flask backend's /api/scan endpoint ---
  const handleScan = async () => {
    setIsScanning(true);
    setScanResults('Scanning system, please wait...');
    try {
      // Proxy in package.json forwards request to http://localhost:5000
      const response = await fetch('/api/scan');
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      const data = await response.json();
      // Format the array of strings into a single block of text
      setScanResults(data.join('\n'));
    } catch (error) {
      setScanResults(`Error: Could not perform scan. ${error.message}`);
    } finally {
      setIsScanning(false);
    }
  };

  // --- INTEGRATION: Handles the test simulation stream from the Flask backend ---
  const handleSimulate = () => {
    setIsSimulating(true);
    setSimulationLog([]); // Clear previous logs

    const eventSource = new EventSource('/api/simulate', { method: 'POST' });

    eventSource.onmessage = (event) => {
      if (event.data === "FINISHED") {
        eventSource.close();
        setIsSimulating(false);
      } else {
        setSimulationLog(prevLog => [...prevLog, event.data]);
      }
    };

    eventSource.onerror = () => {
      setSimulationLog(prevLog => [...prevLog, 'Error: Connection to simulation server lost.']);
      eventSource.close();
      setIsSimulating(false);
    };
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>Security Simulation Control Panel</h1>

      <div style={styles.buttonContainer}>
        <button
          onClick={handleScan}
          style={{...styles.button, ...(isScanning && styles.buttonDisabled)}}
          disabled={isScanning || isSimulating}
        >
          {isScanning ? 'Scanning...' : 'Run System Scan'}
        </button>
        <button
          onClick={handleSimulate}
          style={{...styles.button, ...(isSimulating && styles.buttonDisabled)}}
          disabled={isSimulating || isScanning}
        >
          {isSimulating ? 'Simulation in Progress...' : 'Start Attack Simulation'}
        </button>
      </div>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Scan Results</h2>
        <pre style={styles.preformatted}>{scanResults || 'Click "Run System Scan" to begin.'}</pre>
      </div>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Simulation Log</h2>
        <pre style={{...styles.preformatted, ...styles.log}}>
          {simulationLog.length > 0 ? simulationLog.join('\n') : 'Simulation log will appear here.'}
        </pre>
      </div>
    </div>
  );
}

export default App;

/*
// --- Eclipse's original block of code ---

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
 */