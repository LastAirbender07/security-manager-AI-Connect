import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const triggerScan = async (repoUrl: string, targetUrl?: string, githubToken?: string) => {
    const params: Record<string, string> = { repo_url: repoUrl };
    if (targetUrl) {
        params.target_url = targetUrl;
    }
    if (githubToken) {
        params.github_token = githubToken;
    }
    const response = await apiClient.post('/scan', null, { params });
    return response.data;
};

export interface ScanResult {
    id: number;
    repo: string;
    status: string;
    created_at: string;
    tokens_used: number;
}

export interface ScanLog {
    step: string;
    tokens_input: number;
    tokens_output: number;
    tokens_total: number;
    model: string;
    message: string;
    timestamp: string;
}

export const getScans = async (): Promise<ScanResult[]> => {
    const response = await apiClient.get('/scans');
    return response.data;
};

export const getScanLogs = async (scanId: number): Promise<ScanLog[]> => {
    const response = await apiClient.get(`/scans/${scanId}/logs`);
    return response.data;
};

// ─── System Config ─────────────────────────────────────────────────

export interface ConfigEntry {
    key: string;
    value: string;
    is_secret: boolean;
}

export const getConfig = async (): Promise<ConfigEntry[]> => {
    const response = await apiClient.get('/config');
    return response.data;
};

export const setConfig = async (key: string, value: string, isSecret: boolean = false) => {
    const response = await apiClient.post('/config', null, {
        params: { key, value, is_secret: isSecret },
    });
    return response.data;
};
