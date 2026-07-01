/**
 * ArchitectLens API Request Contract
 */
export interface PRAnalysisRequest {
  pr_id: number;
  repo_name: string;
  diff_text: string;
  author: string;
  commit_sha: string;
}

/**
 * ArchitectLens API Success Response Contract
 */
export interface ReviewResponse {
  review_markdown: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  flags: string[];
}

/**
 * Payload stored in the BullMQ queue
 */
export interface PRAnalysisJobData {
  pr_id: number;
  repo_name: string;
  author: string;
  commit_sha: string;
}
