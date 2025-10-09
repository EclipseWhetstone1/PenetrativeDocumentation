require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const SERVER_URL = process.env.SERVER_URL || 'http://127.0.0.1:3000/api/report';
const MACHINE_ID_FILE = path.join(__dirname, 'machine_id.txt');
const FAILED_LOG = path.join(__dirname, 'failed_reports.log');


if (typeof fetch !== 'function') {
  console.error('Error: fetch is not available in this Node runtime. Use Node 18+ or add a fetch polyfill.');
  process.exit(1);
}


let machineId;
if (fs.existsSync(MACHINE_ID_FILE)) {
  machineId = fs.readFileSync(MACHINE_ID_FILE, 'utf8').trim();
} else {
  machineId = uuidv4();
  fs.writeFileSync(MACHINE_ID_FILE, machineId);
}

async function sendEvent(eventName, data = {}) {
  const payload = {
    machine_id: machineId,
    timestamp: new Date().toISOString(),
    event: eventName,
    data
  };

  try {
    const resp = await fetch(SERVER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const text = await resp.text().catch(()=>'<no-body>');
      console.error(`Server returned ${resp.status}: ${text}`);
      // log failure 
      fs.appendFileSync(FAILED_LOG, JSON.stringify({ attempted_at: new Date().toISOString(), payload, status: resp.status }) + '\n');
    } else {
      console.log('Report sent:', payload);
    }
  } catch (err) {
    console.warn('Could not reach server — logging locally:', err.message || err);
    fs.appendFileSync(FAILED_LOG, JSON.stringify({ attempted_at: new Date().toISOString(), payload, error: (err && err.message) || String(err) }) + '\n');
  }
}

(async () => {
  await sendEvent('PROGRAM_STARTED', { note: 'Simulator started for demo' });
  setTimeout(() => sendEvent('REPORT_VIEWED', { page: 'educational_report' }), 1000);
})();
