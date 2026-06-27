import axios from 'axios';
import { PRAnalysisRequest, ReviewResponse } from '../types';

/**
 * Service to handle communication with the Python FastAPI analysis service.
 */
export class AnalyzerService {
  /**
   * Call the FastAPI service to analyze a PR diff.
   * 
   * @param payload - The request payload containing details of the PR and diff text
   * @returns The review response from the FastAPI contract
   */
  public static async analyzePR(payload: PRAnalysisRequest): Promise<ReviewResponse> {
    const pythonServiceUrl = process.env.PYTHON_SERVICE_URL || 'http://localhost:8000';
    const internalSecretKey = process.env.INTERNAL_SECRET_KEY;

    if (!internalSecretKey) {
      console.warn('Warning: INTERNAL_SECRET_KEY is not defined in the environment variables.');
    }

    const url = `${pythonServiceUrl}/analyze`;
    const headers: Record<string, string> = {
      'X-Internal-Key': internalSecretKey || '',
      'Content-Type': 'application/json',
    };

    try {
      console.log(`Sending PR #${payload.pr_id} diff to Python analysis service at ${url}...`);
      
      const response = await axios.post<ReviewResponse>(url, payload, {
        headers,
        timeout: 30000, // 30 seconds timeout as per contract
      });

      console.log(`Received successful analysis response for PR #${payload.pr_id}. Severity: ${response.data.severity}`);
      return response.data;
    } catch (error: any) {
      if (error.code === 'ECONNABORTED') {
        console.error(`Analysis request to Python service timed out after 30 seconds.`);
        throw new Error('Python analysis service request timed out.');
      }

      const status = error.response ? error.response.status : 'NETWORK_ERROR';
      const message = error.response && error.response.data ? JSON.stringify(error.response.data) : error.message;
      console.error(`Analysis request to Python service failed [Status: ${status}]: ${message}`);
      throw new Error(`Python analysis service failed: ${message}`);
    }
  }
}
