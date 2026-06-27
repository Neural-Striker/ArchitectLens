import { Router } from 'express';
import { WebhookController } from '../controllers/webhookController';
import { verifyGitHubSignature } from '../middleware/githubSignature';

const router = Router();

// Map POST /webhook to signature validation and webhook controller
router.post('/', verifyGitHubSignature, WebhookController.handleWebhook);

export default router;
