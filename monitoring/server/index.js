require('dotenv').config();
const fs = require('fs');
const path = require('path');
const express = require('express');
const morgan = require('morgan');
const bodyParser = require('body-parser');
const cors = require('cors');
const vulnerabilityTemplates = require('./vulnerability_templates');
const rateLimit = require('express-rate-limit');

const port = 3001;

const app = express();

// Core middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '..', 'frontend', 'build')));
app.use(morgan('dev'));
app.use(express.json({ limit: '1mb' }));

// === Rate Limiting Configuration ===
const WINDOW_MS = parseInt(process.env.RATE_LIMIT_WINDOW_MS || (60 * 1000), 10);
const REPORT_LIMIT = parseInt(process.env.REPORT_RATE_LIMIT || '30', 10);
const SCAN_LIMIT = parseInt(process.env.SCAN_RATE_LIMIT || '15', 10);
const READ_REPORT_LIMIT = parseInt(process.env.READ_REPORT_RATE_LIMIT || '60', 10);
const EVENTS_LIMIT = parseInt(process.env.EVENTS_RATE_LIMIT || '60', 10);

// Generic helper to build a limiter
const buildLimiter = (limit, message) =>
  rateLimit({
    windowMs: WINDOW_MS,
    limit,
    standardHeaders: 'draft-7',
    legacyHeaders: false,
    keyGenerator: req => req.ip,
    message: { error: message }
  });

// Route-specific limiters
const reportLimiter = buildLimiter(REPORT_LIMIT, 'Too many /api/report requests. Please slow down.');
const scanLimiter = buildLimiter(SCAN_LIMIT, 'Too many /api/vulnerability-scan submissions. Please retry later.');
const readReportLimiter = buildLimiter(READ_REPORT_LIMIT, 'Too many /api/vulnerability-report requests. Try again soon.');
const eventsLimiter = buildLimiter(EVENTS_LIMIT, 'Too many /api/events requests. Please slow down.');
// Optional global limiter (commented)
// app.use(buildLimiter(parseInt(process.env.GLOBAL_RATE_LIMIT || '300', 10), 'Global rate limit exceeded.'));

// === Persistent storage paths ===
const REPORTS_DIR = path.join(__dirname, 'reports');
const EVENTS_LOG_FILE = path.join(__dirname, 'events.log');

if (!fs.existsSync(REPORTS_DIR)) {
  fs.mkdirSync(REPORTS_DIR);
  console.log('Created reports directory.');
}

// Health check (unlimited but could be limited if abused)
app.get('/api/health', (req, res) =>
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
);

// === POST /api/report (rate-limited) ===
app.post('/api/report', reportLimiter, (req, res) => {
  const event = req.body;
  console.log('Received event:', event);
  try {
    const logEntry = JSON.stringify(event) + '\n';
    fs.appendFileSync(EVENTS_LOG_FILE, logEntry);
    return res.status(200).json({ status: 'ok' });
  } catch (err) {
    console.error('Failed to write event log:', err);
    return res.status(500).json({ error: 'Server error writing log', details: err.message });
  }
});

// === POST /api/vulnerability-scan (rate-limited) ===
app.post('/api/vulnerability-scan', scanLimiter, (req, res) => {
  const payload = req.body;
  console.log(`Received scan from machine_id: ${payload.machine_id}`);

  try {
    const machine_id = payload.machine_id;
    if (!machine_id) {
      return res.status(400).json({ error: 'Missing machine_id in payload' });
    }
    // Validate machine_id format
    if (!/^[\w-]+$/.test(machine_id)) {
      return res.status(400).json({ error: 'Invalid machine_id: use alphanumeric, dash or underscore only' });
    }

    const reportPathUnresolved = path.join(REPORTS_DIR, `${machine_id}.json`);
    // Resolve safely
    const resolvedReportPath = path.resolve(reportPathUnresolved);
    const reportsDirResolved = path.resolve(REPORTS_DIR) + path.sep;
    if (!resolvedReportPath.startsWith(reportsDirResolved)) {
      return res.status(400).json({ error: 'Invalid machine_id leads to unsafe path' });
    }

    fs.writeFileSync(resolvedReportPath, JSON.stringify(payload, null, 2));
    console.log(`Successfully saved report to ${resolvedReportPath}`);
    return res.status(200).json({ status: 'ok', machine_id });
  } catch (err) {
    console.error('Failed to save vulnerability report:', err);
    return res.status(500).json({ error: 'Server error saving report', details: err.message });
  }
});

// === GET /api/vulnerability-report/:machine_id (rate-limited) ===
app.get('/api/vulnerability-report/:machine_id', readReportLimiter, (req, res) => {
  const { machine_id } = req.params;

  if (!/^[a-zA-Z0-9_-]+$/.test(machine_id)) {
    return res.status(400).json({ error: 'Invalid machine_id format' });
  }

  try {
    const baseDir = path.resolve(REPORTS_DIR);
    const requestedPath = path.resolve(baseDir, `${machine_id}.json`);
    let realPath;
    try {
      realPath = fs.realpathSync(requestedPath);
    } catch {
      return res.status(404).json({ error: `Report not found for machine_id: ${machine_id}` });
    }
    if (!realPath.startsWith(baseDir)) {
      return res.status(403).json({ error: 'Forbidden: invalid path resolution' });
    }
    if (!fs.existsSync(realPath)) {
      return res.status(404).json({ error: `Report not found for machine_id: ${machine_id}` });
    }

    const rawData = fs.readFileSync(realPath, 'utf8');
    const payload = JSON.parse(rawData);

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
      try {
        formatted = vulnerabilityTemplates.generateEasyToUnderstandReport(payload);
      } catch (e) {
        console.warn('Template failed, fallback to raw strings:', e.message);
        formatted = {
          machine_id: payload.machine_id,
          timestamp: payload.timestamp,
          vulnerabilities: vulnList.map(s => ({
            name: (s && s.split('\n')[0]) || 'Unknown',
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

// === GET /api/events (rate-limited) ===
app.get('/api/events', eventsLimiter, (req, res) => {
  try {
    if (fs.existsSync(EVENTS_LOG_FILE)) {
      const logData = fs.readFileSync(EVENTS_LOG_FILE, 'utf8');
      const events = logData
        .split('\n')
        .filter(line => line)
        .map(line => JSON.parse(line));
      return res.json(events);
    }
    return res.json([]);
  } catch (err) {
    console.error('Failed to read event log:', err);
    return res.status(500).json({ error: 'Server error reading log', details: err.message });
  }
});

// === Catch-all (rate-limited to avoid abuse of static fallback) ===
const catchAllLimiter = buildLimiter(
  parseInt(process.env.CATCH_ALL_RATE_LIMIT || '120', 10),
  'Too many root requests.'
);
app.get('/*', catchAllLimiter, (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'build', 'index.html'));
});

// === Start server (single listen) ===
if (require.main === module) {
  app.listen(port, () => {
    console.log(`Monitoring server listening on port ${port}`);
    console.log(`Rate limits: /api/report=${REPORT_LIMIT}/min, /api/vulnerability-scan=${SCAN_LIMIT}/min, /api/vulnerability-report=${READ_REPORT_LIMIT}/min, /api/events=${EVENTS_LIMIT}/min`);
  });
}

module.exports = app;