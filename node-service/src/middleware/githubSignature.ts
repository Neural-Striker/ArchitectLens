import { Request, Response, NextFunction } from 'express';
import crypto from 'crypto';

/**
 * Custom Request interface to include the captured rawBody buffer.
 */
export interface RequestWithRawBody extends Request {
  rawBody?: Buffer;
}

/**
 * Express middleware to verify HMAC-SHA256 signatures for incoming GitHub webhooks.
 */
export function verifyGitHubSignature(
  req: RequestWithRawBody,
  res: Response,
  next: NextFunction
) {
  const secret = process.env.GITHUB_WEBHOOK_SECRET;
  
  if (!secret) {
    console.warn('[Webhook] GITHUB_WEBHOOK_SECRET is not configured. Skipping signature verification.');
    return next();
  }

  const signature = req.headers['x-hub-signature-256'] as string;
  if (!signature) {
    console.warn('[Webhook] Rejecting request: X-Hub-Signature-256 header is missing.');
    return res.status(401).json({ error: 'Signature verification failed. X-Hub-Signature-256 is missing.' });
  }

  if (!req.rawBody) {
    console.error('[Webhook] Rejecting request: Raw body is not available for signature verification.');
    return res.status(500).json({ error: 'Internal server error during signature verification.' });
  }

  const hmac = crypto.createHmac('sha256', secret);
  const expectedSignature = 'sha256=' + hmac.update(req.rawBody).digest('hex');

  try {
    if (crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature))) {
      return next();
    }
  } catch (error) {
    // timingSafeEqual throws an error if buffer lengths do not match
  }

  console.warn('[Webhook] Rejecting request: Signature mismatch.');
  return res.status(401).json({ error: 'Signature verification failed. Signatures do not match.' });
}
