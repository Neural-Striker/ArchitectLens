const axios = require('axios');
const crypto = require('crypto');
require('dotenv').config();

const secret = process.env.GITHUB_WEBHOOK_SECRET || 'dev_webhook_secret_123';
const url = 'http://localhost:3000/webhook';

const payload = {
  action: 'opened',
  pull_request: {
    number: 42,
    user: {
      login: 'test-author'
    },
    head: {
      sha: 'a1b2c3d4e5f6'
    }
  },
  repository: {
    full_name: 'org/repo-name'
  }
};

const body = JSON.stringify(payload);
const hmac = crypto.createHmac('sha256', secret);
const signature = 'sha256=' + hmac.update(body).digest('hex');

console.log('Sending mock webhook payload to:', url);
console.log('Computed signature:', signature);

axios.post(url, payload, {
  headers: {
    'x-github-event': 'pull_request',
    'x-hub-signature-256': signature,
    'Content-Type': 'application/json'
  }
})
.then(response => {
  console.log('Status:', response.status);
  console.log('Response:', response.data);
})
.catch(error => {
  console.error('Error sending webhook:', error.response ? error.response.data : error.message);
});
