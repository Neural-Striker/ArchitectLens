import { Router } from 'express';
import healthRoutes from './healthRoutes';
import webhookRoutes from './webhookRoutes';

const router = Router();

// Register sub-routers
router.use('/', healthRoutes);
router.use('/webhook', webhookRoutes);

export default router;
