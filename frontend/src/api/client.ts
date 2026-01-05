import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8001/api';

const client = axios.create({
    baseURL: API_BASE_URL,
});

export interface ReplayedPart {
    start: number;
    end: number;
    position: number;
    duration?: number;
}

export interface JobStatusResponse {
    status: 'idle' | 'running' | 'success' | 'failed';
    progress: number;
    logs: string[];
    result?: any;
    error?: string;
}

export const api = {
    getReplayedParts: async (videoId: string, numberOfParts: number) => {
        const res = await axios.get(`http://localhost:8001/most-replayed`, { params: { videoId, numberOfParts } });
        return res.data.replayedParts;
    },
    downloadVideo: async (videoId: string, outputDir: string) => {
        const res = await client.post('/download', { videoId, outputDir });
        return res.data; // { jobId }
    },
    cutVideo: async (videoId: string, videoFilePath: string, replayedParts: ReplayedPart[], outputDir: string) => {
        const res = await client.post('/cut', { videoId, videoFilePath, replayedParts, outputDir });
        return res.data;
    },
    cropVideo: async (inputDir: string, outputDir: string) => {
        const res = await client.post('/crop', { inputDir, outputDir });
        return res.data;
    },
    addSubtitles: async (inputDir: string, outputDir: string, modelSize: string = 'medium') => {
        const res = await client.post('/subtitles', { inputDir, outputDir, modelSize });
        return res.data;
    },
    getJobStatus: async (jobId: string) => {
        const res = await client.get<JobStatusResponse>(`/jobs/${jobId}`);
        return res.data;
    }
};
