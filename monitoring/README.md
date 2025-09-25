## Run server
cd monitoring/server
npm install
node index.js

## Run client
cd monitoring/client
npm install
node report_agent.js

## What to expect
- Server logs POST requests to monitoring/server/reports.log.
- Client creates machine_id.txt and logs failed attempts to failed_reports.log if offline.