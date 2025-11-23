import React, { useState } from 'react';
import './App.css';

function App() {
  const [machineId, setMachineId] = useState('');
  const [report, setReport] = useState(null);

  // loading and error messages
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetches the latest vulnerability report for a specific machine ID.
  const fetchScanReport = async () => {
    if (!machineId) {
      setError('Please enter a Machine ID.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setReport(null);

    try {
        // We proxy this request to our server running on port 3001
        const response = await fetch(`http://localhost:3001/api/vulnerability-report/${machineId}`);
        if (!response.ok) {
            let errPayload;
            try {
                errPayload = await response.json();
            } catch {
                const text = await response.text();
                errPayload = { error: text };
            }
            throw new Error(errPayload.error || `Server error: ${response.status}`);
        }
      //const response = await fetch(`http://localhost:3001/api/vulnerability-report/${machineId}`);

      //if (!response.ok) {
      //  const err = await response.json();
      //  throw new Error(err.error || `Server error: ${response.status}`);
      //}

        const reportData = await response.json();
        setReport(reportData);
    } catch (err) {
      console.error('Fetch error:', err);
      setError(`Failed to fetch report: ${err.message}. Is the server running?`);
    } finally {
      setIsLoading(false);
    }
  };

  // Saves the vulnerability report in a readable format.
  const renderReport = () => {
    if (!report) return null;

    return (
      <div className="report-container">
        <h2>Report for: {report.machine_id}</h2>
        <p><strong>Last Scan:</strong> {new Date(report.timestamp).toLocaleString()}</p>

        {report.vulnerabilities.length > 0 ? (
          <ul>
            {report.vulnerabilities.map((vuln, index) => (
              <li key={index} className="vulnerability-item">
                <h3>{vuln.name} (Severity: {vuln.risk})</h3>
                <p><strong>Installed Version:</strong> {vuln.installed_version}</p>
                <p><strong>Vulnerable Version:</strong> {vuln.vulnerable_version}</p>
                <p><strong>Explanation:</strong> {vuln.explanation}</p>
                <p><strong>Solution:</strong> {vuln.fix}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p>No vulnerabilities found.</p>
        )}
      </div>
    );
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Analyst Dashboard</h1>
      </header>
      <div className="controls">
        <input
          type="text"
          value={machineId}
          onChange={(e) => setMachineId(e.target.value)}
          placeholder="Enter Target Machine ID"
          className="machine-id-input"
        />
        <button onClick={fetchScanReport} disabled={isLoading}>
          {isLoading ? 'Fetching...' : 'Fetch Scan Report'}
        </button>
        <button className="simulation-button" disabled>Run Simulation (US008)</button>
      </div>

      <div className="results">
        {error && <div className="error-message">{error}</div>}
        {isLoading && <div className="loading-message">Loading report...</div>}
        {report && renderReport()}
      </div>
    </div>
  );
}

export default App;


// --- OLD CODE - DELETE LATER ---
//
// import React, { useState } from "react";
//
// // CSS-in-JS styling, just to keep all the styling in one file.
// const styles = {
//   container: {
//     fontFamily: 'Arial, sans-serif',
//     maxWidth: '800px',
//     margin: '0 auto',
//     padding: '20px',
//     backgroundColor: '#f4f7f6',
//     borderRadius: '8px'
//   },
//   header: {
//     fontSize: '2.5em',
//     color: '#333',
//     textAlign: 'center',
//     marginBottom: '30px'
//   },
//   buttonContainer: {
//     display: 'flex',
//     justifyContent: 'center',
//     marginBottom: '30px'
//   },
//   button: {
//     padding: '12px 25px',
//     fontSize: '1.1em',
//     margin: '0 10px',
//     cursor: 'pointer',
//     border: 'none',
//     borderRadius: '5px',
//     backgroundColor: '#007bff',
//     color: 'white',
//     transition: 'background-color 0.3s ease'
//   },
//   buttonDisabled: {
//     backgroundColor: '#cccccc',
//     cursor: 'not-allowed'
//   },
//   section: {
//     marginTop: '20px',
//     border: '1px solid #ddd',
//     padding: '15px',
//     borderRadius: '5px',
//     backgroundColor: 'white'
//   },
//   sectionTitle: {
//     fontSize: '1.5em',
//     marginBottom: '10px',
//     color: '#555'
//   },
//   preformatted: {
//     whiteSpace: 'pre-wrap',
//     wordWrap: 'break-word',
//     backgroundColor: '#efefef',
//     padding: '10px',
//     borderRadius: '4px',
//     maxHeight: '250px',
//     overflowY: 'auto'
//   },
//   log: {
//     backgroundColor: '#2b2b2b',
//     color: '#a9b7c6',
//     fontFamily: 'monospace',
//     minHeight: '200px'
//   }
// };
//
// function App() {
//   const [status, setStatus] = useState("");
//   const [scanResults, setScanResults] = useState('');
//   const [simulationLog, setSimulationLog] = useState([]);
//   const [isSimulating, setIsSimulating] = useState(false);
//   const [isScanning, setIsScanning] = useState(false);
//
//   // --- INTEGRATION: Handles the actual data from the Flask backend's /api/scan endpoint ---
//   const handleScan = async () => {
//     setIsScanning(true);
//     setScanResults('Scanning system, please wait...');
//     try {
//       // Proxy in package.json forwards request to http://localhost:5000
//       const response = await fetch('/api/scan');
//       if (!response.ok) {
//         throw new Error(`Server responded with status: ${response.status}`);
//       }
//       const data = await response.json();
//       // Format the array of strings into a single block of text
//       setScanResults(data.join('\n'));
//     } catch (error) {
//       setScanResults(`Error: Could not perform scan. ${error.message}`);
//     } finally {
//       setIsScanning(false);
//     }
//   };
//
//   // --- INTEGRATION: Handles the test simulation stream from the Flask backend ---
//   const handleSimulate = () => {
//     setIsSimulating(true);
//     setSimulationLog([]); // Clear previous logs
//
//     const eventSource = new EventSource('/api/simulate', { method: 'POST' });
//
//     eventSource.onmessage = (event) => {
//       if (event.data === "FINISHED") {
//         eventSource.close();
//         setIsSimulating(false);
//       } else {
//         setSimulationLog(prevLog => [...prevLog, event.data]);
//       }
//     };
//
//     eventSource.onerror = () => {
//       setSimulationLog(prevLog => [...prevLog, 'Error: Connection to simulation server lost.']);
//       eventSource.close();
//       setIsSimulating(false);
//     };
//   };
//
//   return (
//     <div style={styles.container}>
//       <h1 style={styles.header}>Security Simulation Control Panel</h1>
//
//       <div style={styles.buttonContainer}>
//         <button
//           onClick={handleScan}
//           style={{...styles.button, ...(isScanning && styles.buttonDisabled)}}
//           disabled={isScanning || isSimulating}
//         >
//           {isScanning ? 'Scanning...' : 'Run System Scan'}
//         </button>
//         <button
//           onClick={handleSimulate}
//           style={{...styles.button, ...(isSimulating && styles.buttonDisabled)}}
//           disabled={isSimulating || isScanning}
//         >
//           {isSimulating ? 'Simulation in Progress...' : 'Start Attack Simulation'}
//         </button>
//       </div>
//
//       <div style={styles.section}>
//         <h2 style={styles.sectionTitle}>Scan Results</h2>
//         <pre style={styles.preformatted}>{scanResults || 'Click "Run System Scan" to begin.'}</pre>
//       </div>
//
//       <div style={styles.section}>
//         <h2 style={styles.sectionTitle}>Simulation Log</h2>
//         <pre style={{...styles.preformatted, ...styles.log}}>
//           {simulationLog.length > 0 ? simulationLog.join('\n') : 'Simulation log will appear here.'}
//         </pre>
//       </div>
//     </div>
//   );
// }
//
// export default App;
//
// /*
// // --- Eclipse's original block of code ---
//
// function App() {
//   const [status, setStatus] = useState("");
//
//   const sendReport = async () => {
//     const payload = {
//       machine_id: "test-client",
//       timestamp: new Date().toISOString(),
//       event: "REPORT_VIEWED",
//       data: {}
//     };
//
//     try {
//       const res = await fetch("/api/report", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(payload)
//       });
//
//       const json = await res.json();
//       setStatus("Server response: " + JSON.stringify(json));
//     } catch (err) {
//       setStatus("Error: " + err.message);
//     }
//   };
//
//   return (
//     <div style={{ padding: "2rem" }}>
//       <h1>Virus App Frontend</h1>
//       <button onClick={sendReport}>Send Test Report</button>
//       <p>{status}</p>
//     </div>
//   );
// }
//
// export default App;
//  */