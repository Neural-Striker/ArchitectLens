"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const dotenv_1 = __importDefault(require("dotenv"));
// Load environment variables before importing services
dotenv_1.default.config();
const express_1 = __importDefault(require("express"));
const routes_1 = __importDefault(require("./routes"));
const queueService_1 = require("./services/queueService");
const app = (0, express_1.default)();
const PORT = process.env.PORT || 3000;
// Body parser middleware that parses json and captures raw request buffer
// for GitHub signature verification.
app.use(express_1.default.json({
    verify: (req, res, buf) => {
        req.rawBody = buf;
    }
}));
// Register API routers
app.use('/', routes_1.default);
// Boot up redis connection, job queue, and background worker
queueService_1.QueueService.initialize();
queueService_1.QueueService.startWorker();
const server = app.listen(PORT, () => {
    console.log(`ArchitectLens Node.js service listening on port ${PORT}`);
});
/**
 * Handle graceful shutdown of HTTP server and Redis connections.
 */
async function gracefulShutdown(signal) {
    console.log(`\nReceived ${signal}. Starting graceful shutdown...`);
    // Stop accepting new HTTP requests
    server.close(() => {
        console.log('HTTP server closed.');
    });
    try {
        // Close worker and queue connection pools
        await queueService_1.QueueService.close();
        console.log('Redis connections and BullMQ worker closed successfully.');
        process.exit(0);
    }
    catch (error) {
        console.error('Error during graceful shutdown:', error);
        process.exit(1);
    }
}
// Intercept exit signals for graceful shutdown
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));
