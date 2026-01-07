import React, { useEffect, useState, useRef } from 'react';
import { useStore } from './store';
import type { StepName } from './store';
import { api } from './api/client';
import { Timeline } from './components/Timeline';
import { LogConsole } from './components/LogConsole';
import { VideoPartEditor } from './components/VideoPartEditor';
import { Play, RotateCcw, PanelLeftClose, PanelLeftOpen, Search, Download, Scissors, Crop, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { Button } from './components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/Card';
import { Badge } from './components/ui/Badge';

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
    <div className="flex flex-col h-screen bg-gray-50/50">
      {/* Glass Header */}
      <header className="glass sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            title={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
          >
            {isSidebarOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
          </Button>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-indigo-600 rounded-xl shadow-lg shadow-indigo-200">
              <Play className="w-5 h-5 text-white fill-current" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-gray-900">
              Antigravity <span className="text-indigo-600">VideoLab</span>
            </h1>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={store.reset}
            className="gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className={clsx(
          "transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)] border-r border-gray-200 bg-white overflow-hidden shadow-sm z-40",
          isSidebarOpen ? "w-80 opacity-100 translate-x-0" : "w-0 opacity-0 -translate-x-full border-r-0"
        )}>
          <div className="w-80 h-full p-4">
            <Timeline />
          </div>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden relative">

          {/* Scrollable Content Area */}
          <div
            className="flex-1 overflow-y-auto scroll-smooth p-4 md:p-8"
            onScroll={handleScroll}
            ref={scrollContainerRef}
          >
            <div className="max-w-5xl mx-auto space-y-8">

              {/* Hero Input Section */}
              <section className="space-y-4 text-center py-8">
                <h2 className="text-4xl font-bold tracking-tighter text-gray-900 sm:text-5xl">
                  Create Viral Shorts from <br />
                  <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">YouTube Videos</span>
                </h2>
                <p className="text-gray-500 max-w-2xl mx-auto text-lg">
                  Paste a link, select key moments, and generate captioned vertical videos instantly.
                </p>

                <div className="max-w-2xl mx-auto mt-8 relative">
                  <div className="flex gap-2 p-1.5 bg-white rounded-2xl shadow-xl shadow-gray-200/50 border border-gray-100 items-center">
                    <div className="pl-4 text-gray-400">
                      <Search className="w-5 h-5" />
                    </div>
                    <input
                      type="text"
                      value={store.videoId}
                      onChange={e => store.setVideoId(e.target.value)}
                      placeholder="Paste YouTube Link or ID (e.g. dQw4w9WgXcQ)"
                      className="flex-1 border-none bg-transparent focus:ring-0 text-lg placeholder:text-gray-400 py-3"
                    />
                    <Button
                      size="lg"
                      onClick={runFetch}
                      disabled={!store.videoId || store.steps.fetch.status === 'running'}
                      className="rounded-xl px-8"
                    >
                      {store.steps.fetch.status === 'running' ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                      Analyze
                    </Button>
                  </div>
                </div>
              </section>

              {/* Pipeline Controls */}
              {/* Only show controls if analyzed or manual ID input provided */}
              <Card className="overflow-hidden border-0 shadow-xl shadow-indigo-100/50 ring-1 ring-gray-100">
                <CardHeader className="bg-white/50 border-b border-gray-100">
                  <CardTitle>Processing Pipeline</CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="flex flex-wrap gap-4 justify-center">
                    {/* Fetch step handled above, but can repeat status here */}

                    <StepCard
                      icon={<Download className="w-5 h-5" />}
                      label="Download Source"
                      status={store.steps.download.status}
                      onClick={runDownload}
                      disabled={!store.replayedParts.length}
                    />

                    <StepCard
                      icon={<Scissors className="w-5 h-5" />}
                      label="Cut Segments"
                      status={store.steps.cut.status}
                      onClick={runCut}
                      disabled={!store.downloadedFilePath}
                    />

                    <StepCard
                      icon={<Crop className="w-5 h-5" />}
                      label="Smart Crop"
                      status={store.steps.crop.status}
                      onClick={runCrop}
                      disabled={store.steps.cut.status !== 'success'}
                    />

                    <StepCard
                      icon={<FileText className="w-5 h-5" />}
                      label="Auto Captions"
                      status={store.steps.subtitles.status}
                      onClick={runSubtitles}
                      disabled={store.steps.crop.status !== 'success'}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Editor */}
              {store.replayedParts.length > 0 && store.downloadedFilePath && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                  <h3 className="text-xl font-bold text-gray-900 mb-4 px-1">Clip Editor</h3>
                  <VideoPartEditor
                    parts={store.replayedParts}
                    onPartsChange={store.setReplayedParts}
                    videoUrl={`http://localhost:8001/outputs/${store.downloadedFilePath.split('processing_output')[1]?.replace(/^[\\/]/, '')}`}
                  />
                </div>
              )}

              {/* Outputs List */}
              <div className="space-y-4">
                {Object.entries(store.steps).map(([stepId, state]) => {
                  if (stepId === 'fetch' || !state.outputs && !state.result?.outputs && !state.result?.parts) return null;

                  const items = state.result?.outputs || state.result?.parts || [];
                  if (!items.length) return null;

                  return (
                    <Card key={stepId} className="overflow-hidden animate-in fade-in">
                      <CardHeader className="py-4 bg-gray-50/50 border-b border-gray-100 flex flex-row items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="capitalize">{stepId}</Badge>
                          <h4 className="font-medium text-gray-700">Generated Files</h4>
                        </div>
                        <Badge variant="secondary">{items.length} files</Badge>
                      </CardHeader>
                      <div className="divide-y divide-gray-100">
                        {items.map((item: any, i: number) => (
                          <div key={i} className="px-6 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors group">
                            <div className="flex items-center gap-3 overflow-hidden">
                              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg group-hover:bg-indigo-100 transition-colors">
                                <FileText className="w-4 h-4" />
                              </div>
                              <div className="text-sm font-medium text-gray-700 truncate max-w-md">
                                {item.path.split(/[\\/]/).pop()}
                              </div>
                            </div>
                            <Button size="sm" variant="ghost" className="text-gray-400 hover:text-indigo-600">
                              Open
                            </Button>
                          </div>
                        ))}
                      </div>
                    </Card>
                  );
                })}
              </div>

              <div className="h-32"></div> {/* Spacer */}
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

function StepCard({ icon, label, status, onClick, disabled }: any) {
  const isRunning = status === 'running';
  const isSuccess = status === 'success';
  const isFailed = status === 'failed';

  return (
    <button
      onClick={onClick}
      disabled={disabled || isRunning}
      className={clsx(
        "relative flex flex-col items-center gap-3 p-6 rounded-2xl border transition-all duration-200 w-40",
        isSuccess
          ? "bg-emerald-50 border-emerald-200 text-emerald-900 ring-1 ring-emerald-100"
          : isFailed
            ? "bg-red-50 border-red-200 text-red-900 ring-1 ring-red-100"
            : disabled
              ? "bg-gray-50 border-gray-100 text-gray-300 cursor-not-allowed"
              : "bg-white border-gray-200 text-gray-600 hover:border-indigo-300 hover:shadow-lg hover:-translate-y-1 hover:text-indigo-600"
      )}
    >
      {isSuccess && (
        <div className="absolute top-2 right-2 text-emerald-600">
          <CheckCircle2 className="w-4 h-4" />
        </div>
      )}
      {isFailed && (
        <div className="absolute top-2 right-2 text-red-600">
          <AlertCircle className="w-4 h-4" />
        </div>
      )}

      <div className={clsx(
        "p-3 rounded-xl transition-colors",
        isSuccess ? "bg-emerald-100 text-emerald-700" :
          isFailed ? "bg-red-100 text-red-700" :
            disabled ? "bg-gray-100 text-gray-300" :
              "bg-indigo-50 text-indigo-600 group-hover:bg-indigo-100"
      )}>
        {isRunning ? <Loader2 className="w-6 h-6 animate-spin" /> : icon}
      </div>

      <span className="font-semibold text-sm">{label}</span>

      {/* Progress Bar for running state */}
      {isRunning && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-indigo-100 rounded-b-2xl overflow-hidden">
          <div className="h-full bg-indigo-500 animate-progress origin-left"></div>
        </div>
      )}
    </button>
  );
}

export default App;
