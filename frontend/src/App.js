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