"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const healthRoutes_1 = __importDefault(require("./healthRoutes"));
const webhookRoutes_1 = __importDefault(require("./webhookRoutes"));
const router = (0, express_1.Router)();
// Register sub-routers
router.use('/', healthRoutes_1.default);
router.use('/webhook', webhookRoutes_1.default);
exports.default = router;
