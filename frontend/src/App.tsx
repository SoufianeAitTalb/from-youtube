import React, { useEffect, useState, useRef } from 'react';
import { useStore } from './store';
import type { StepName } from './store';
import { api } from './api/client';
import { Timeline } from './components/Timeline';
import { LogConsole } from './components/LogConsole';
import { VideoPartEditor } from './components/VideoPartEditor';
import { Play, RotateCcw, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import clsx from 'clsx';

function App() {
  const store = useStore();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isConsoleExpanded, setIsConsoleExpanded] = useState(true);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-collapse console on scroll
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = e.currentTarget.scrollTop;
    if (scrollTop > 100 && isConsoleExpanded) {
      setIsConsoleExpanded(false);
    }
  };

  // Polling Hook (Replaces SSE for reliability)
  const useJobPolling = (step: StepName) => {
    const jobId = store.steps[step].jobId;
    const status = store.steps[step].status;

    useEffect(() => {
      // Only poll if running and we have a job ID
      if (status !== 'running' || !jobId) return;

      const intervalId = setInterval(async () => {
        try {
          const job = await api.getJobStatus(jobId);

          // Update logs (append only new ones would be better, but replacing or appending difference is okay for now)
          // Since our backend returns ALL logs, we can just check length or replace if we want simple logic.
          // But our store has `appendLog`. Let's just update the whole logs array in `updateStep` if we change store logic,
          // OR iterate and append new ones. 
          // For simplicity in this PoC: let's assume we handle log diffing or just don't duplicate.
          // Actually, our `store.appendLog` appends. If backend returns ALL logs, we shouldn't append blindly.
          // Let's rely on `updateStep` to overwrite logs if we want, OR just check length.

          // Hack: just replace logs for now to ensure consistency, requiring store update
          // But store only has appendLog. Let's fix this by adding setLogs to store or just handle it here.
          // Wait, `updateStep` takes Partial<StepState>. So we can pass `logs: job.logs`.

          store.updateStep(step, {
            logs: job.logs,
            progress: job.progress
          });

          if (job.status === 'success' || job.status === 'failed') {
            store.updateStep(step, {
              status: job.status,
              result: job.result,
              error: job.error
            });
            if (job.status === 'success' && step === 'download' && job.result?.videoFilePath) {
              store.setDownloadedFilePath(job.result.videoFilePath);
            }
            clearInterval(intervalId);
          }
        } catch (e) {
          console.error("Polling error", e);
          // Don't fail immediately on network glitch, just retry next tick
        }
      }, 1000); // Poll every 1s

      return () => clearInterval(intervalId);
    }, [jobId, status]);
  };

  useJobPolling('download');
  useJobPolling('cut');
  useJobPolling('crop');
  useJobPolling('subtitles');

  const runFetch = async () => {
    store.updateStep('fetch', { status: 'running', logs: ['Fetching replayed parts...'] });
    try {
      const parts = await api.getReplayedParts(store.videoId);
      store.setReplayedParts(parts);
      store.updateStep('fetch', { status: 'success', logs: [`Found ${parts.length} parts.`] });
    } catch (e: any) {
      store.updateStep('fetch', { status: 'failed', logs: [`Error: ${e.message}`] });
    }
  };

  const runDownload = async () => {
    if (!store.replayedParts.length) return alert("Run Fetch first");
    store.updateStep('download', { status: 'running', logs: ['Starting download...'] });
    try {
      const { jobId } = await api.downloadVideo(store.videoId, `${store.baseOutputDir}/downloaded_videos`);
      store.updateStep('download', { jobId });
    } catch (e: any) {
      store.updateStep('download', { status: 'failed', logs: [`Error: ${e.message}`] });
    }
  };

  const runCut = async () => {
    if (!store.downloadedFilePath) return alert("Download video first");
    store.updateStep('cut', { status: 'running', logs: ['Starting cut...'] });
    try {
      const { jobId } = await api.cutVideo(
        store.videoId,
        store.downloadedFilePath,
        store.replayedParts,
        `${store.baseOutputDir}/video_parts/${store.videoId}`
      );
      store.updateStep('cut', { jobId });
    } catch (e: any) {
      store.updateStep('cut', { status: 'failed', logs: [`Error: ${e.message}`] });
    }
  };

  const runCrop = async () => {
    if (store.steps.cut.status !== 'success') return alert("Cut video first");
    store.updateStep('crop', { status: 'running', logs: ['Starting crop...'] });
    try {
      const { jobId } = await api.cropVideo(
        `${store.baseOutputDir}/video_parts/${store.videoId}`,
        `${store.baseOutputDir}/cropped_video_parts/${store.videoId}`
      );
      store.updateStep('crop', { jobId });
    } catch (e: any) {
      store.updateStep('crop', { status: 'failed', logs: [`Error: ${e.message}`] });
    }
  };

  const runSubtitles = async () => {
    if (store.steps.crop.status !== 'success') return alert("Crop video first");
    store.updateStep('subtitles', { status: 'running', logs: ['Starting subtitles...'] });
    try {
      const { jobId } = await api.addSubtitles(
        `${store.baseOutputDir}/cropped_video_parts/${store.videoId}`,
        `${store.baseOutputDir}/subtitled_video_parts/${store.videoId}`
      );
      store.updateStep('subtitles', { jobId });
    } catch (e: any) {
      store.updateStep('subtitles', { status: 'failed', logs: [`Error: ${e.message}`] });
    }
  };



  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm z-10 transition-all">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded-md text-gray-600 transition-colors"
            title={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
          >
            {isSidebarOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
          </button>
          <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Play className="w-6 h-6 text-red-600 fill-current" />
            YouTube Processor
          </h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={store.reset}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset Pipeline
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Sidebar with Transition */}
        <div className={clsx(
          "transition-all duration-300 ease-in-out border-r border-gray-200 bg-white overflow-hidden",
          isSidebarOpen ? "w-80 opacity-100" : "w-0 opacity-0 border-r-0"
        )}>
          <div className="w-80 h-full">
            <Timeline />
          </div>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden relative">

          {/* Scrollable Content Area - Inputs are now INSIDE here */}
          <div
            className="flex-1 bg-gray-50 overflow-y-auto scroll-smooth"
            onScroll={handleScroll}
            ref={scrollContainerRef}
          >
            <div className="max-w-6xl mx-auto">
              {/* Inputs Area - Now flows with scroll */}
              <div className="p-6 bg-white border-b border-gray-200 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">YouTube Video ID / URL</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={store.videoId}
                        onChange={e => store.setVideoId(e.target.value)}
                        placeholder="e.g. dQw4w9WgXcQ"
                        className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm border p-2"
                      />
                    </div>
                  </div>
                  {/* Number of Parts Input Removed for Auto-Detection */}
                </div>
              </div>

              {/* Step Details & Visuals */}
              <div className="p-6 space-y-8 pb-32"> {/* Added padding bottom for console clearance if needed */}

                {/* Actions Panel */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">Pipeline Controls</h2>
                  <div className="flex flex-wrap gap-4">
                    <StepButton
                      label="1. Fetch Parts"
                      onClick={runFetch}
                      disabled={!store.videoId || store.steps.fetch.status === 'running'}
                      status={store.steps.fetch.status}
                    />
                    <StepButton
                      label="2. Download"
                      onClick={runDownload}
                      disabled={!store.replayedParts.length || store.steps.download.status === 'running'}
                      status={store.steps.download.status}
                    />
                    <StepButton
                      label="3. Cut"
                      onClick={runCut}
                      disabled={!store.downloadedFilePath || store.steps.cut.status === 'running'}
                      status={store.steps.cut.status}
                    />
                    <StepButton
                      label="4. Crop Vertical"
                      onClick={runCrop}
                      disabled={store.steps.cut.status !== 'success' || store.steps.crop.status === 'running'}
                      status={store.steps.crop.status}
                    />
                    <StepButton
                      label="5. Add Subtitles"
                      onClick={runSubtitles}
                      disabled={store.steps.crop.status !== 'success' || store.steps.subtitles.status === 'running'}
                      status={store.steps.subtitles.status}
                    />
                  </div>
                </div>

                {/* Editor - Show if we have downloaded video and parts */}
                {store.replayedParts.length > 0 && store.downloadedFilePath && (
                  <VideoPartEditor
                    parts={store.replayedParts}
                    onPartsChange={store.setReplayedParts}
                    videoUrl={`http://localhost:8001/outputs/${store.downloadedFilePath.split('processing_output')[1]?.replace(/^[\\/]/, '')}`}
                  />
                )}

                {/* Outputs */}
                {Object.entries(store.steps).map(([stepId, state]) => {
                  if (stepId === 'fetch' || !state.outputs && !state.result?.outputs && !state.result?.parts) return null;

                  const items = state.result?.outputs || state.result?.parts || [];
                  if (!items.length) return null;

                  return (
                    <div key={stepId} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between">
                        <h3 className="font-medium text-gray-900 capitalize">{stepId} Outputs</h3>
                      </div>
                      <ul className="divide-y divide-gray-200">
                        {items.map((item: any, i: number) => (
                          <li key={i} className="px-6 py-4 flex items-center justify-between">
                            <div className="text-sm text-gray-900 truncate max-w-lg">{item.path}</div>
                            {/* In a real app we would serve these files via static file server */}
                            <span className="text-xs text-gray-500">
                              {item.path.split(/[\\/]/).pop()}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}

              </div>
            </div>
          </div>

          <LogConsole
            isExpanded={isConsoleExpanded}
            onToggleExpand={() => setIsConsoleExpanded(!isConsoleExpanded)}
          />
        </div>
      </main>
    </div>
  );
}

function StepButton({ label, onClick, disabled, status }: any) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        "px-4 py-2 rounded-md text-sm font-medium transition-colors border shadow-sm",
        status === 'running' ? "bg-blue-50 text-blue-700 border-blue-200" :
          status === 'success' ? "bg-green-50 text-green-700 border-green-200" :
            status === 'failed' ? "bg-red-50 text-red-700 border-red-200" :
              disabled ? "bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed" :
                "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
      )}
    >
      {label}
    </button>
  );
}

export default App;
