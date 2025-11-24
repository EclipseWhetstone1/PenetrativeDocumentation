const fs = require('fs');
const path = require('path');
const request = require('supertest');
const app = require('../index');

describe('Monitoring Express Server', () => {
  const reportsDir = path.join(__dirname, '..', 'reports');

  afterAll(() => {
    // Clean up test artifacts
    if (fs.existsSync(reportsDir)) {
      fs.readdirSync(reportsDir).forEach(f => {
        if (f.startsWith('test-machine')) {
          fs.unlinkSync(path.join(reportsDir, f));
        }
      });
    }
  });

  test('GET /api/health returns ok', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  test('POST /api/vulnerability-scan saves report', async () => {
    const payload = {
      machine_id: 'test-machine-1',
      timestamp: new Date().toISOString(),
      vulnerabilities: [
        { name: 'Chrome', risk: 'High', installed_version: '89', vulnerable_version: '90', explanation: 'Old', fix: 'Update' }
      ]
    };
    const res = await request(app)
      .post('/api/vulnerability-scan')
      .send(payload);
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');

    const saved = path.join(reportsDir, 'test-machine-1.json');
    expect(fs.existsSync(saved)).toBe(true);
    const data = JSON.parse(fs.readFileSync(saved, 'utf8'));
    expect(data.machine_id).toBe('test-machine-1');
  });

  test('GET /api/vulnerability-report/:machine_id returns formatted report', async () => {
    // Re-use prior saved file
    const res = await request(app).get('/api/vulnerability-report/test-machine-1');
    expect(res.status).toBe(200);
    expect(res.body.machine_id).toBe('test-machine-1');
    expect(Array.isArray(res.body.vulnerabilities)).toBe(true);
  });

  test('GET /api/events returns array (empty or populated)', async () => {
    const res = await request(app).get('/api/events');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
  });

  test('POST /api/report logs event', async () => {
    const res = await request(app)
      .post('/api/report')
      .send({ type: 'TEST_EVENT', value: 42 });
    expect(res.status).toBe(200);
  });
});