"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const router = (0, express_1.Router)();
// Health Check Endpoint
router.get('/', (req, res) => {
    res.json({
        status: 'ok',
        service: 'architectlens-node',
        timestamp: new Date().toISOString(),
    });
});
exports.default = router;
