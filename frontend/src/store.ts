import { create } from 'zustand';
import type { ReplayedPart } from './api/client';

export type StepName = 'fetch' | 'download' | 'cut' | 'crop' | 'subtitles';

export interface StepState {
    status: 'idle' | 'running' | 'success' | 'failed';
    jobId?: string;
    progress: number;
    error?: string;
    logs: string[];
    outputs?: any;
    result?: any;
}

export interface PipelineState {
    videoId: string;
    numberOfParts: number;
    baseOutputDir: string;

    // Step Data
    replayedParts: ReplayedPart[];
    downloadedFilePath?: string;

    // Steps Status
    steps: Record<StepName, StepState>;

    // Actions
    setVideoId: (id: string) => void;
    setNumberOfParts: (n: number) => void;
    setBaseOutputDir: (dir: string) => void;
    setReplayedParts: (parts: ReplayedPart[]) => void;
    setDownloadedFilePath: (path: string) => void;

    updateStep: (step: StepName, updates: Partial<StepState>) => void;
    appendLog: (step: StepName, log: string) => void;
    reset: () => void;
}

const initialStepState: StepState = {
    status: 'idle',
    progress: 0,
    logs: []
};

export const useStore = create<PipelineState>((set) => ({
    videoId: '',
    numberOfParts: 3,
    baseOutputDir: 'processing_output',

    replayedParts: [],
    downloadedFilePath: undefined,

    steps: {
        fetch: { ...initialStepState },
        download: { ...initialStepState },
        cut: { ...initialStepState },
        crop: { ...initialStepState },
        subtitles: { ...initialStepState }
    },

    setVideoId: (id) => set({ videoId: id }),
    setNumberOfParts: (n) => set({ numberOfParts: n }),
    setBaseOutputDir: (dir) => set({ baseOutputDir: dir }),
    setReplayedParts: (parts) => set({ replayedParts: parts }),
    setDownloadedFilePath: (path) => set({ downloadedFilePath: path }),

    updateStep: (step, updates) => set((state) => ({
        steps: {
            ...state.steps,
            [step]: { ...state.steps[step], ...updates }
        }
    })),

    appendLog: (step, log) => set((state) => {
        const currentLogs = state.steps[step].logs;
        return {
            steps: {
                ...state.steps,
                [step]: { ...state.steps[step], logs: [...currentLogs, log] }
            }
        };
    }),

    reset: () => set({
        replayedParts: [],
        downloadedFilePath: undefined,
        steps: {
            fetch: { ...initialStepState },
            download: { ...initialStepState },
            cut: { ...initialStepState },
            crop: { ...initialStepState },
            subtitles: { ...initialStepState }
        }
    })
}));
