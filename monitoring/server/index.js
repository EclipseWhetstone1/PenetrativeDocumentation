require('dotenv').config();
const fs = require('fs');
const path = require('path');
const express = require('express');
const morgan = require('morgan');

const PORT = process.env.PORT || 3000;
const LOG_FILE = path.join(__dirname, 'reports.log');

const app = express();

// middleware
app.use(morgan('dev'));
app.use(express.json({ limit: '1mb' }));

// Health check
app.get('/api/health', (req, res) => res.json({ status: 'ok', timestamp: new Date().toISOString() }));

// main endpoint: receive reports
app.post('/api/report', (req, res) => {
  try {
    const payload = req.body;

    // Basic validation (ensure required fields exist)
    if (!payload.machine_id || !payload.timestamp || !payload.event) {
      return res.status(400).json({ error: 'Invalid payload: machine_id, timestamp, and event required' });
    }

    // Append the JSON payload to a log file (one JSON per line)
    const line = JSON.stringify({ received_at: new Date().toISOString(), payload }) + '\n';
    fs.appendFileSync(LOG_FILE, line);

    

    return res.status(200).json({ status: 'received' });
  } catch (err) {
    console.error('Error processing report:', err);
    return res.status(500).json({ error: 'server error' });
  }
});

// endpoint to receive vulnerability scan results
app.post('/api/vulnerability-scan', (req, res) => {
  try {
    const payload = req.body;

    // Basic validation (ensure requried fields exist)
    if (!payload.machine_id || !payload.timestamp || !payload.vulnerabilities) {
      return res.status(400).json({ error: 'Invalid payload: machine_id, timestamp, and vulnerabilities required' });
    }

    // Log the vulnerability scan results
    const line = JSON.stringify({ 
      received_at: new Date().toISOString(), 
      type: 'vulnerability_scan',
      payload 
    }) + '\n';
    fs.appendFileSync(LOG_FILE, line);

    return res.status(200).json({ status: 'vulnerability_scan_received' });
  } catch (err) {
    console.error('Error processing vulnerability scan:', err);
    return res.status(500).json({ error: 'server error' });
  }
});

// endpoint to get vulnerability report from machine
app.get('/api/vulnerability-report/:machine_id', (req, res) => {
  try {
    const machineId = req.params.machine_id;
    
    // Read the log file and find vulnerability scans for this machine
    const logContent = fs.readFileSync(LOG_FILE, 'utf8');
    const lines = logContent.trim().split('\n');
    
    let vulnerabilityData = null;
    
    // Finds most recent vulnerability scan for this machine
    for (let i = lines.length - 1; i >= 0; i--) {
      try {
        const logEntry = JSON.parse(lines[i]);
        if (logEntry.type === 'vulnerability_scan' && 
            logEntry.payload.machine_id === machineId) {
          vulnerabilityData = logEntry.payload;
          break;
        }
      } catch (e) {
        continue; 
      }
    }
    
    if (!vulnerabilityData) {
      return res.status(404).json({ error: 'No vulnerability scan found for this machine' });
    }
    
    // create our easy to understand report
    const report = generateUserFriendlyReport(vulnerabilityData);
    
    return res.json(report);
  } catch (err) { 
    console.error('Error generating vulnerability report:', err);
    return res.status(500).json({error: 'server error'});
  }
});

// Start
app.listen(PORT, () => {
  console.log(`Monitoring server listening on port ${PORT}`);
  console.log(`POST reports to: http://localhost:${PORT}/api/report`);
});
