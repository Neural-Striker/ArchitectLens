import { Request, Response } from 'express';
import { QueueService } from '../services/queueService';

/**
 * Controller to handle webhook requests from GitHub.
 */
export class WebhookController {
  /**
   * Handle incoming GitHub webhook events.
   * 
   * @param req - Express Request
   * @param res - Express Response
   */
  public static async handleWebhook(req: Request, res: Response): Promise<Response> {
    const event = req.headers['x-github-event'] as string;
    console.log(`[Webhook] Received GitHub event: ${event}`);

    if (event !== 'pull_request') {
      console.log(`[Webhook] Ignored event type: ${event}`);
      return res.status(200).json({ message: `Ignored event: ${event}` });
    }

    const payload = req.body;
    const action = payload.action as string;

    // Trigger PR analysis when PR is opened, synchronized (new commits), or reopened.
    const triggerActions = ['opened', 'synchronize', 'reopened'];
    if (!triggerActions.includes(action)) {
      console.log(`[Webhook] Ignored pull_request action: ${action}`);
      return res.status(200).json({ message: `Ignored pull_request action: ${action}` });
    }

    try {
      const pr_id = payload.pull_request.number;
      const repo_name = payload.repository.full_name;
      const author = payload.pull_request.user.login;
      const commit_sha = payload.pull_request.head.sha;

      console.log(`[Webhook] Queueing analysis job for PR #${pr_id} | Repo: ${repo_name} | Commit: ${commit_sha}`);

      const job = await QueueService.addAnalysisJob({
        repo_name,
        pr_id,
        author,
        commit_sha,
      });

      console.log(`[Webhook] Job successfully queued with Job ID: ${job.id}`);
      
      return res.status(202).json({
        message: 'PR analysis job successfully queued',
        jobId: job.id,
        prId: pr_id,
        repo: repo_name
      });
    } catch (error: any) {
      console.error('[Webhook] Error queueing PR analysis job:', error);
      return res.status(500).json({
        error: 'Failed to queue PR analysis',
        details: error.message
      });
    }
  }
}
