"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.GitHubService = void 0;
const axios_1 = __importDefault(require("axios"));
/**
 * Service to handle communications with the GitHub API.
 */
class GitHubService {
    /**
     * Fetch the raw unified diff text for a given pull request.
     *
     * @param repoName - Full repository name (e.g., 'owner/repo')
     * @param prId - Pull request number
     * @returns The raw diff text
     */
    static async fetchPRDiff(repoName, prId) {
        const token = process.env.GITHUB_TOKEN;
        const url = `https://api.github.com/repos/${repoName}/pulls/${prId}`;
        const headers = {
            'User-Agent': 'ArchitectLens-Node-Service',
            'Accept': 'application/vnd.github.v3.diff',
        };
        if (token) {
            headers['Authorization'] = `token ${token}`;
        }
        else {
            console.warn('Warning: GITHUB_TOKEN is not set. GitHub API requests may fail due to rate limits or access restrictions.');
        }
        try {
            console.log(`Fetching diff for PR #${prId} from repository ${repoName}...`);
            const response = await axios_1.default.get(url, { headers, responseType: 'text' });
            return response.data;
        }
        catch (error) {
            const status = error.response ? error.response.status : 'NETWORK_ERROR';
            const message = error.response && error.response.data ? JSON.stringify(error.response.data) : error.message;
            console.error(`Failed to fetch diff for PR #${prId} [Status: ${status}]: ${message}`);
            throw new Error(`Failed to fetch PR diff: ${message}`);
        }
    }
    /**
     * Post a review comment to the pull request.
     * In GitHub, comments on PRs are posted to the issue comments endpoint.
     *
     * @param repoName - Full repository name (e.g., 'owner/repo')
     * @param prId - Pull request number (issue number)
     * @param commentBody - Markdown text to comment
     * @returns The API response payload
     */
    static async postPRComment(repoName, prId, commentBody) {
        const token = process.env.GITHUB_TOKEN;
        const url = `https://api.github.com/repos/${repoName}/issues/${prId}/comments`;
        const headers = {
            'User-Agent': 'ArchitectLens-Node-Service',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
        };
        if (token) {
            headers['Authorization'] = `token ${token}`;
        }
        else {
            console.warn('Warning: GITHUB_TOKEN is not set. Cannot post comment to GitHub.');
            throw new Error('GITHUB_TOKEN is required to post comments.');
        }
        try {
            console.log(`Posting review comment to PR #${prId} on repository ${repoName}...`);
            const response = await axios_1.default.post(url, { body: commentBody }, { headers });
            console.log(`Successfully posted comment to PR #${prId}`);
            return response.data;
        }
        catch (error) {
            const status = error.response ? error.response.status : 'NETWORK_ERROR';
            const message = error.response && error.response.data ? JSON.stringify(error.response.data) : error.message;
            console.error(`Failed to post comment to PR #${prId} [Status: ${status}]: ${message}`);
            throw new Error(`Failed to post comment: ${message}`);
        }
    }
}
exports.GitHubService = GitHubService;
