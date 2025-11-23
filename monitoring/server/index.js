require('dotenv').config();
const fs = require('fs');
const path = require('path');
const express = require('express');
const morgan = require('morgan');
const bodyParser = require('body-parser');
const cors = require('cors');
const vulnerabilityTemplates = require('./vulnerability_templates');

const port = 3001;
// const PORT = process.env.PORT || 3000; // Old PORT value // 5001 is used by Flask server

const app = express();

app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '..', 'frontend', 'build')));

// For persistent file storage
const REPORTS_DIR = path.join(__dirname, 'reports');
const EVENTS_LOG_FILE = path.join(__dirname, 'events.log');


// middleware
app.use(morgan('dev'));
app.use(express.json({ limit: '1mb' }));


// Health check
app.get('/api/health', (req, res) => res.json({ status: 'ok', timestamp: new Date().toISOString() }));

// Checks that the 'reports' directory exists
if (!fs.existsSync(REPORTS_DIR)) {
  fs.mkdirSync(REPORTS_DIR);
  console.log('Created reports directory.');
}

// --- DEPRECATED: In-memory storage ---

// main endpoint: receive reports
app.post('/api/report', (req, res) => {
  const event = req.body;
  console.log('Received event:', event);

  // --- MODIFIED: Append to log file ---
  try {
    const logEntry = JSON.stringify(event) + '\n';
    fs.appendFileSync(EVENTS_LOG_FILE, logEntry);
    res.status(200).send('Event received');
  } catch (err) {
    console.error('Failed to write event log:', err);
    res.status(500).send('Server error writing log');
  }
});

// endpoint to receive vulnerability scan results
app.post('/api/vulnerability-scan', (req, res) => {
  const payload = req.body;
  console.log(`Received scan from machine_id: ${payload.machine_id}`);

    // --- MODIFIED: Write to a specific JSON file ---
    try {
        const machine_id = payload.machine_id;
        if (!machine_id) {
            return res.status(400).json({ error: 'Missing machine_id in payload' });
        }

        const reportPath = path.join(REPORTS_DIR, `${machine_id}.json`);
        fs.writeFileSync(reportPath, JSON.stringify(payload, null, 2));
        console.log(`Successfully saved report to ${reportPath}`);
        return res.status(200).json({ status: 'ok', machine_id });
    } catch (err) {
        console.error('Failed to save vulnerability report:', err);
        return res.status(500).json({ error: 'Server error saving report', details: err.message });
    }
});

// endpoint to get vulnerability report from machine
app.get('/api/vulnerability-report/:machine_id', (req, res) => {
    const { machine_id } = req.params;

    try {
        const reportPath = path.join(REPORTS_DIR, `${machine_id}.json`);
        if (!fs.existsSync(reportPath)) {
            return res.status(404).json({ error: `Report not found for machine_id: ${machine_id}` });
        }

        const rawData = fs.readFileSync(reportPath, 'utf8');
        const payload = JSON.parse(rawData);

        // extract vulerability list
        const vulnList =
            payload.vulnerabilities ||
            (payload.scan_data && payload.scan_data.vulnerabilities) ||
            [];

        let formatted;
        if (vulnList.length && typeof vulnList[0] === 'object') {
            formatted = {
                machine_id: payload.machine_id,
                timestamp: payload.timestamp,
                vulnerabilities: vulnList.map(v => ({
                    name: v.name,
                    risk: v.risk || '',
                    installed_version: v.installed_version || '',
                    vulnerable_version: v.vulnerable_version || v.minimum_version || '',
                    explanation: v.explanation || v.risk || '',
                    fix: v.fix || v.remediation || ''
                }))
            };
        } else {
            // string format
            try {
                formatted =
                    vulnerabilityTemplates.generateEasyToUnderstandReport(payload);
            } catch (e) {
                console.warn('Template failed, falling back to raw strings:', e.message);
                formatted = {
                    machine_id: payload.machine_id,
                    timestamp: payload.timestamp,
                    vulnerabilities: vulnList.map(s => ({
                        name: s.split('\n')[0] || 'Unknown',
                        risk: '',
                        installed_version: '',
                        vulnerable_version: '',
                        explanation: s,
                        fix: ''
                    }))
                };
            }
        }

        return res.json(formatted);
    } catch (err) {
        console.error(`Failed to read report for ${machine_id}:`, err);
        return res.status(500).json({ error: 'Server error reading report', details: err.message });
    }
});

// Endpoint to get all simulation events (for timeline)
app.get('/api/events', (req, res) => {

  // --- MODIFIED: Read from the event log file ---
  try {
    if (fs.existsSync(EVENTS_LOG_FILE)) {
      const logData = fs.readFileSync(EVENTS_LOG_FILE, 'utf8');

      // Splits by newline, filters out the empty lines, and parses each line as JSON
      const events = logData
        .split('\n')
        .filter(line => line)
        .map(line => JSON.parse(line));

      res.json(events);
    } else {
      // If there isn't a log file it just returns an empty array
      res.json([]);
    }
  } catch (err) {
    console.error('Failed to read event log:', err);
    res.status(500).send('Server error reading log');
  }
});

// Start
app.use((req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'build', 'index.html'));
});

if (require.main === module) {
    app.listen(port, () => {
        console.log(`Monitoring server listening on port ${port}`);
    });
};

module.exports = app;