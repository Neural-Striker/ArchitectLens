import dotenv from 'dotenv';
// Load environment variables before importing services
dotenv.config();

import express from 'express';
import routes from './routes';
import { QueueService } from './services/queueService';

const app = express();
const PORT = process.env.PORT || 3000;

// Body parser middleware that parses json and captures raw request buffer
// for GitHub signature verification.
app.use(express.json({
  verify: (req: any, res, buf) => {
    req.rawBody = buf;
  }
}));

// Register API routers
app.use('/', routes);

// Boot up redis connection, job queue, and background worker
QueueService.initialize();
QueueService.startWorker();

const server = app.listen(PORT, () => {
  console.log(`ArchitectLens Node.js service listening on port ${PORT}`);
});

/**
 * Handle graceful shutdown of HTTP server and Redis connections.
 */
async function gracefulShutdown(signal: string) {
  console.log(`\nReceived ${signal}. Starting graceful shutdown...`);
  
  // Stop accepting new HTTP requests
  server.close(() => {
    console.log('HTTP server closed.');
  });

  try {
    // Close worker and queue connection pools
    await QueueService.close();
    console.log('Redis connections and BullMQ worker closed successfully.');
    process.exit(0);
  } catch (error) {
    console.error('Error during graceful shutdown:', error);
    process.exit(1);
  }
}

// Intercept exit signals for graceful shutdown
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));
