require('dotenv').config();
const fs = require('fs');
const path = require('path');
const express = require('express');
const morgan = require('morgan');
const bodyParser = require('body-parser');
const cors = require('cors');
const vulnerabilityTemplates = require('./vulnerability_templates');

const port = 3001;
// const PORT = process.env.PORT || 3000; // Old PORT value
<<<<<<< HEAD
=======

app.use(cors());
app.use(bodyParser.json());

// For persistent file storage
const REPORTS_DIR = path.join(__dirname, 'reports');
const EVENTS_LOG_FILE = path.join(__dirname, 'events.log');
>>>>>>> 13d3e07 (Significant changes to App.css, App.js, index.js, package.json, PenetrativeDocumentation.iml, profiles_settings.xml, scanner.py, test_scanner.py.)

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
// let eventsLog = [];
// let vulnerabilityReports = {};

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
    // Writes the full payload to a file. Overwrites previous report.
    fs.writeFileSync(reportPath, JSON.stringify(payload, null, 2));

    console.log(`Successfully saved report to ${reportPath}`);
    res.status(200).json({ message: 'Vulnerability scan data received and saved.' });
  } catch (err) {
    console.error('Failed to save vulnerability report:', err);
    res.status(500).send('Server error saving report');
  }
});

// endpoint to get vulnerability report from machine
app.get('/api/vulnerability-report/:machine_id', (req, res) => {
  const { machine_id } = req.params;

  // --- MODIFIED: Read from the JSON file ---
  try {
    const reportPath = path.join(REPORTS_DIR, `${machine_id}.json`);

    if (fs.existsSync(reportPath)) {
      const rawData = fs.readFileSync(reportPath, 'utf8');
      const payload = JSON.parse(rawData);

      // Use the existing template logic to format the report
<<<<<<< HEAD
      const reportGenerator = vulnerabilityTemplates.generateUserFriendlyReport ||
        vulnerabilityTemplates.generateEasyToUnderstandReport;

      if (typeof reportGenerator !== 'function') {
        console.error('No report generator found in vulnerability_templates.js');
        return res.status(500).json({ error: 'Report generator unavailable' });
      }

      const formattedReport = reportGenerator(payload);
      res.json(formattedReport);
=======
      const easyToUnderstandReport = vulnerabilityTemplates.generateEasyToUnderstandReport(payload);
      res.json(easyToUnderstandReport);
>>>>>>> 13d3e07 (Significant changes to App.css, App.js, index.js, package.json, PenetrativeDocumentation.iml, profiles_settings.xml, scanner.py, test_scanner.py.)

    } else {
      res.status(404).json({ error: `Report not found for machine_id: ${machine_id}` });
    }
  } catch (err) {
    console.error(`Failed to read report for ${machine_id}:`, err);
    res.status(500).send('Server error reading report');
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
<<<<<<< HEAD
<<<<<<< HEAD
app.use((req, res) => {
=======
app.get('*', (req, res) => {
>>>>>>> fad4de8 (Minor changes to scanner.py and index.js while trying to fix bugs)
  res.sendFile(path.join(__dirname, '..', 'frontend', 'build', 'index.html'));
});

if (require.main === module) {
    app.listen(port, () => {
        console.log(`Monitoring server listening on port ${port}`);
    });
};

module.exports = app;

=======
app.listen(port, () => {
  console.log(`Monitoring server listening on port ${port}`);
});

>>>>>>> 13d3e07 (Significant changes to App.css, App.js, index.js, package.json, PenetrativeDocumentation.iml, profiles_settings.xml, scanner.py, test_scanner.py.)


// --- OLD CODE - DELETE LATER ---
//
// require('dotenv').config();
// const fs = require('fs');
// const path = require('path');
// const express = require('express');
// const morgan = require('morgan');
//
// const port = 3001;
// // const PORT = process.env.PORT || 3000;
// const LOG_FILE = path.join(__dirname, 'reports.log');
//
// const app = express();
//
// // middleware
// app.use(morgan('dev'));
// app.use(express.json({ limit: '1mb' }));
//
// // Health check
// app.get('/api/health', (req, res) => res.json({ status: 'ok', timestamp: new Date().toISOString() }));
//
// // main endpoint: receive reports
// app.post('/api/report', (req, res) => {
//   try {
//     const payload = req.body;
//
//     // Basic validation (ensure required fields exist)
//     if (!payload.machine_id || !payload.timestamp || !payload.event) {
//       return res.status(400).json({ error: 'Invalid payload: machine_id, timestamp, and event required' });
//     }
//
//     // Append the JSON payload to a log file (one JSON per line)
//     const line = JSON.stringify({ received_at: new Date().toISOString(), payload }) + '\n';
//     fs.appendFileSync(LOG_FILE, line);
//
//
//
//     return res.status(200).json({ status: 'received' });
//   } catch (err) {
//     console.error('Error processing report:', err);
//     return res.status(500).json({ error: 'server error' });
//   }
// });
//
// // endpoint to receive vulnerability scan results
// app.post('/api/vulnerability-scan', (req, res) => {
//   try {
//     const payload = req.body;
//
//     // Basic validation (ensure requried fields exist)
//     if (!payload.machine_id || !payload.timestamp || !payload.vulnerabilities) {
//       return res.status(400).json({ error: 'Invalid payload: machine_id, timestamp, and vulnerabilities required' });
//     }
//
//     // Log the vulnerability scan results
//     const line = JSON.stringify({
//       received_at: new Date().toISOString(),
//       type: 'vulnerability_scan',
//       payload
//     }) + '\n';
//     fs.appendFileSync(LOG_FILE, line);
//
//     return res.status(200).json({ status: 'vulnerability_scan_received' });
//   } catch (err) {
//     console.error('Error processing vulnerability scan:', err);
//     return res.status(500).json({ error: 'server error' });
//   }
// });
//
// // endpoint to get vulnerability report from machine
// app.get('/api/vulnerability-report/:machine_id', (req, res) => {
//   try {
//     const machineId = req.params.machine_id;
//
//     // Read the log file and find vulnerability scans for this machine
//     const logContent = fs.readFileSync(LOG_FILE, 'utf8');
//     const lines = logContent.trim().split('\n');
//
//     let vulnerabilityData = null;
//
//     // Finds most recent vulnerability scan for this machine
//     for (let i = lines.length - 1; i >= 0; i--) {
//       try {
//         const logEntry = JSON.parse(lines[i]);
//         if (logEntry.type === 'vulnerability_scan' &&
//             logEntry.payload.machine_id === machineId) {
//           vulnerabilityData = logEntry.payload;
//           break;
//         }
//       } catch (e) {
//         continue;
//       }
//     }
//
//     if (!vulnerabilityData) {
//       return res.status(404).json({ error: 'No vulnerability scan found for this machine' });
//     }
//
//     // create our easy to understand report
//     const report = generateUserFriendlyReport(vulnerabilityData);
//
//     return res.json(report);
//   } catch (err) {
//     console.error('Error generating vulnerability report:', err);
//     return res.status(500).json({error: 'server error'});
//   }
// });
//
// // Start
// app.listen(PORT, () => {
//   console.log(`Monitoring server listening on port ${PORT}`);
//   console.log(`POST reports to: http://localhost:${PORT}/api/report`);
// });
