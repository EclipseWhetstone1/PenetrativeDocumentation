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


app.get('/api/health', (req, res) => res.json({ status: 'ok', timestamp: new Date().toISOString() }));

//receive reports
app.post('/api/report', (req, res) => {
  try {
    const payload = req.body;

    // Basic validation 
    if (!payload.machine_id || !payload.timestamp || !payload.event) {
      return res.status(400).json({ error: 'Invalid payload: machine_id, timestamp, and event required' });
    }

    // Append the JSON payload to a log file 
    const line = JSON.stringify({ received_at: new Date().toISOString(), payload }) + '\n';
    fs.appendFileSync(LOG_FILE, line);

    

    return res.status(200).json({ status: 'received' });
  } catch (err) {
    console.error('Error processing report:', err);
    return res.status(500).json({ error: 'server error' });
  }
});

// Start the port
app.listen(PORT, () => {
  console.log(`Monitoring server listening on port ${PORT}`);
  console.log(`POST reports to: http://localhost:${PORT}/api/report`);
});
