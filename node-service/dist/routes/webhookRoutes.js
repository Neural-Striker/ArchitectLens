"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const webhookController_1 = require("../controllers/webhookController");
const githubSignature_1 = require("../middleware/githubSignature");
const router = (0, express_1.Router)();
// Map POST /webhook to signature validation and webhook controller
router.post('/', githubSignature_1.verifyGitHubSignature, webhookController_1.WebhookController.handleWebhook);
exports.default = router;
