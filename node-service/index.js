require('dotenv').config();
const express = require('express');

const app = express();
const PORT = 3000;

app.get('/', (req, res) => {
  res.send('Node.js service is running.');
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});