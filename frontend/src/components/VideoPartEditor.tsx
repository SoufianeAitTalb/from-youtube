import { useRef, useState } from 'react';
import type { ReplayedPart } from '../api/client';
import { Play, Pause, Trash2, Plus, RefreshCw, Clock } from 'lucide-react';
import clsx from 'clsx';

interface VideoPartEditorProps {
    parts: ReplayedPart[];
    onPartsChange: (parts: ReplayedPart[]) => void;
    videoUrl?: string; // URL to the downloaded video for preview
}

// Helper to format S.MS into HH:MM:SS.MS
const formatTime = (seconds: number): string => {
    if (isNaN(seconds)) return "00:00.0";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);

    if (h > 0) {
        return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}.${ms}`;
};

export const VideoPartEditor = ({ parts, onPartsChange, videoUrl }: VideoPartEditorProps) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const rangeEndRef = useRef<number | null>(null);
    const [playingPartIndex, setPlayingPartIndex] = useState<number | null>(null);

    // Monitor video time to stop at range end
    const handleTimeUpdate = () => {
        if (videoRef.current && rangeEndRef.current !== null) {
            if (videoRef.current.currentTime >= rangeEndRef.current) {
                videoRef.current.pause();
                rangeEndRef.current = null;
                setPlayingPartIndex(null);
            }
        }
    };

    const handleSeek = (time: number) => {
        if (videoRef.current) {
            videoRef.current.currentTime = time;
            // videoRef.current.play(); // Don't auto play on seek
            rangeEndRef.current = null;
            setPlayingPartIndex(null);
        }
    };

    const playRange = (index: number, start: number, end: number) => {
        if (videoRef.current) {
            if (playingPartIndex === index) {
                // Toggle Pause
                videoRef.current.pause();
                setPlayingPartIndex(null);
                rangeEndRef.current = null;
                return;
            }

            videoRef.current.currentTime = start;
            rangeEndRef.current = end;
            setPlayingPartIndex(index);
            videoRef.current.play();
        }
    };

    const updatePart = (index: number, field: keyof ReplayedPart, value: number) => {
        const newParts = [...parts];
        newParts[index] = { ...newParts[index], [field]: value };
        onPartsChange(newParts);
    };

    const removePart = (index: number) => {
        const newParts = parts.filter((_, i) => i !== index);
        // Re-index positions
        onPartsChange(newParts.map((p, i) => ({ ...p, position: i + 1 })));
    };

    const addPart = () => {
        const lastPart = parts[parts.length - 1];
        const newPart: ReplayedPart = {
            position: parts.length + 1,
            start: lastPart ? lastPart.end : 0,
            end: lastPart ? lastPart.end + 10 : 10,
            duration: 10
        };
        onPartsChange([...parts, newPart]);
    };

    return (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden flex flex-col h-[800px]"> {/* Increased height */}
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <RefreshCw className="w-5 h-5 text-indigo-600" />
                    Review & Edit Parts
                </h2>
                <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded border border-gray-200">
                    {parts.length} parts defined
                </span>
            </div>

            <div className="flex-1 overflow-hidden p-6 grid grid-cols-1 lg:grid-cols-3 gap-8"> {/* Changed grid to 3 columns */}
                {/* Video Preview - Takes 2 columns (Larger) */}
                <div className="lg:col-span-2 flex flex-col h-full overflow-hidden">
                    <div className="flex-1 bg-gray-900 rounded-lg overflow-hidden relative shadow-inner ring-1 ring-gray-200 flex items-center justify-center">
                        {videoUrl ? (
                            <video
                                ref={videoRef}
                                src={videoUrl}
                                controls
                                className="w-full h-full object-contain"
                                onTimeUpdate={handleTimeUpdate}
                                onPause={() => setPlayingPartIndex(null)}
                            />
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-2">
                                <div className="w-8 h-8 rounded-full border-2 border-gray-600 border-t-transparent animate-spin"></div>
                                <span className="text-sm">Waiting for video...</span>
                            </div>
                        )}
                    </div>
                    {videoUrl && (
                        <div className="flex justify-between text-xs text-gray-500 px-1 mt-2">
                            <span>Source Preview</span>
                            <span>{videoUrl.split(/[\\/]/).pop()}</span>
                        </div>
                    )}
                </div>

                {/* Parts List - Takes 1 column */}
                <div className="flex flex-col h-full overflow-hidden bg-gray-50 rounded-lg border border-gray-200">
                    <div className="p-3 border-b border-gray-200 bg-white">
                        <h3 className="text-sm font-medium text-gray-700">Segments</h3>
                    </div>

                    <div className="flex-1 overflow-y-auto p-3 space-y-3">
                        {parts.map((part, idx) => {
                            const isPlaying = playingPartIndex === idx;
                            return (
                                <div
                                    key={idx}
                                    className={clsx(
                                        "group relative bg-white rounded-lg border p-3 transition-all",
                                        isPlaying ? "border-indigo-500 ring-1 ring-indigo-500 shadow-md" : "border-gray-200 hover:border-indigo-300 hover:shadow-sm"
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={clsx(
                                            "flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full font-bold text-xs transition-colors mt-1",
                                            isPlaying ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-500"
                                        )}>
                                            {isPlaying ? <Play className="w-3 h-3 fill-current animate-pulse" /> : `#${part.position}`}
                                        </div>

                                        <div className="flex-1 space-y-3">
                                            {/* Time Inputs */}
                                            <div className="grid grid-cols-2 gap-3">
                                                <div>
                                                    <label className="flex items-center justify-between text-[10px] uppercase tracking-wide text-gray-400 font-semibold mb-1">
                                                        Start <Clock className="w-3 h-3" />
                                                    </label>
                                                    <input
                                                        type="number"
                                                        value={part.start}
                                                        onChange={e => updatePart(idx, 'start', Number(e.target.value))}
                                                        className="w-full bg-gray-50 border border-gray-200 rounded px-2 py-1 text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
                                                        step="0.1"
                                                    />
                                                    <div className="text-[10px] text-gray-400 text-right mt-0.5 font-mono">
                                                        {formatTime(part.start)}
                                                    </div>
                                                </div>

                                                <div>
                                                    <label className="flex items-center justify-between text-[10px] uppercase tracking-wide text-gray-400 font-semibold mb-1">
                                                        End <Clock className="w-3 h-3" />
                                                    </label>
                                                    <input
                                                        type="number"
                                                        value={part.end}
                                                        onChange={e => updatePart(idx, 'end', Number(e.target.value))}
                                                        className="w-full bg-gray-50 border border-gray-200 rounded px-2 py-1 text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
                                                        step="0.1"
                                                    />
                                                    <div className="text-[10px] text-gray-400 text-right mt-0.5 font-mono">
                                                        {formatTime(part.end)}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Duration & Controls */}
                                            <div className="flex items-center justify-between pt-2 border-t border-gray-50">
                                                <span className="text-[10px] font-medium text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                                                    {(part.end - part.start).toFixed(1)}s
                                                </span>

                                                <div className="flex items-center gap-1">
                                                    <button
                                                        onClick={() => playRange(idx, part.start, part.end)}
                                                        className={clsx(
                                                            "p-1.5 rounded-md transition-colors",
                                                            isPlaying
                                                                ? "text-white bg-indigo-600 hover:bg-indigo-700"
                                                                : "text-indigo-600 bg-indigo-50 hover:bg-indigo-100"
                                                        )}
                                                        title={isPlaying ? "Pause" : "Play Segment"}
                                                    >
                                                        {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                                                    </button>
                                                    <button
                                                        onClick={() => removePart(idx)}
                                                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                                                        title="Remove Part"
                                                    >
                                                        <Trash2 className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <div className="p-3 border-t border-gray-200 bg-white">
                        <button
                            onClick={addPart}
                            className="w-full flex items-center justify-center gap-2 py-2 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50 transition-all font-medium"
                        >
                            <Plus className="w-3.5 h-3.5" />
                            Add Segment
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
