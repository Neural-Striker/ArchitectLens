import { Router, Request, Response } from 'express';

const router = Router();

// Health Check Endpoint
router.get('/', (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    service: 'architectlens-node',
    timestamp: new Date().toISOString(),
  });
});

export default router;
