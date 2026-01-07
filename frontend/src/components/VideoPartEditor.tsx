import { useRef, useState } from 'react';
import type { ReplayedPart } from '../api/client';
import { Play, Pause, Trash2, Plus, RefreshCw, Clock } from 'lucide-react';
import clsx from 'clsx';
import { Button } from './ui/Button';
import { Card, CardHeader, CardTitle } from './ui/Card';

interface VideoPartEditorProps {
    parts: ReplayedPart[];
    onPartsChange: (parts: ReplayedPart[]) => void;
    videoUrl?: string; // URL to the downloaded video for preview
}

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
        <Card className="flex flex-col h-[800px] border-0 shadow-xl shadow-gray-200/50 ring-1 ring-gray-200">
            <CardHeader className="py-4 bg-gray-50/50 border-b border-gray-100 flex-row items-center justify-between space-y-0">
                <CardTitle className="text-lg flex items-center gap-2">
                    <RefreshCw className="w-5 h-5 text-indigo-600" />
                    Review & Edit Parts
                </CardTitle>
                <div className="text-xs px-2 py-1 rounded bg-white border border-gray-200 text-gray-500 font-medium">
                    {parts.length} parts defined
                </div>
            </CardHeader>

            <div className="flex-1 overflow-hidden p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 bg-gray-50/30">
                {/* Video Preview - Takes 8 columns */}
                <div className="lg:col-span-8 flex flex-col h-full overflow-hidden rounded-xl border border-gray-200 bg-black shadow-inner relative group">
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

                {/* Parts List - Takes 4 columns */}
                <div className="lg:col-span-4 flex flex-col h-full overflow-hidden bg-white rounded-xl border border-gray-200 shadow-sm">
                    <div className="p-3 border-b border-gray-100 bg-gray-50/50">
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Segments</h3>
                    </div>

                    <div className="flex-1 overflow-y-auto p-3 space-y-3">
                        {parts.map((part, idx) => {
                            const isPlaying = playingPartIndex === idx;
                            return (
                                <div
                                    key={idx}
                                    className={clsx(
                                        "group relative rounded-xl border p-3 transition-all duration-200",
                                        isPlaying
                                            ? "border-indigo-500 ring-1 ring-indigo-500 shadow-md bg-indigo-50/30"
                                            : "border-gray-100 bg-white hover:border-indigo-200 hover:shadow-sm"
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={clsx(
                                            "flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full font-bold text-xs transition-colors mt-1 ring-1 ring-inset",
                                            isPlaying
                                                ? "bg-indigo-600 text-white ring-indigo-600"
                                                : "bg-gray-50 text-gray-500 ring-gray-200 group-hover:bg-indigo-50 group-hover:text-indigo-600"
                                        )}>
                                            {isPlaying ? <Play className="w-3 h-3 fill-current animate-pulse" /> : `#${part.position}`}
                                        </div>

                                        <div className="flex-1 space-y-3">
                                            {/* Time Inputs */}
                                            <div className="grid grid-cols-2 gap-2">
                                                <div className="relative">
                                                    <label className="text-[10px] uppercase tracking-wide text-gray-400 font-semibold absolute -top-1.5 left-2 bg-white px-1 z-10">Start</label>
                                                    <div className="relative">
                                                        <input
                                                            type="number"
                                                            value={part.start}
                                                            onChange={e => updatePart(idx, 'start', Number(e.target.value))}
                                                            className="w-full bg-transparent border border-gray-200 rounded-md py-1 px-2 text-sm font-medium focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                                                            step="0.1"
                                                        />
                                                    </div>
                                                </div>
                                                <div className="relative">
                                                    <label className="text-[10px] uppercase tracking-wide text-gray-400 font-semibold absolute -top-1.5 left-2 bg-white px-1 z-10">End</label>
                                                    <div className="relative">
                                                        <input
                                                            type="number"
                                                            value={part.end}
                                                            onChange={e => updatePart(idx, 'end', Number(e.target.value))}
                                                            className="w-full bg-transparent border border-gray-200 rounded-md py-1 px-2 text-sm font-medium focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                                                            step="0.1"
                                                        />
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Duration & Controls */}
                                            <div className="flex items-center justify-between pt-2">
                                                <div className="flex items-center gap-2">
                                                    <Clock className="w-3 h-3 text-gray-400" />
                                                    <span className="text-xs font-mono text-gray-600 px-1.5 py-0.5 rounded bg-gray-100">
                                                        {(part.end - part.start).toFixed(1)}s
                                                    </span>
                                                </div>

                                                <div className="flex items-center gap-1">
                                                    <Button
                                                        size="icon"
                                                        className="h-7 w-7"
                                                        variant={isPlaying ? "default" : "secondary"}
                                                        onClick={() => playRange(idx, part.start, part.end)}
                                                        title={isPlaying ? "Pause" : "Play Segment"}
                                                    >
                                                        {isPlaying ? <Pause className="w-3 h-3 fill-current" /> : <Play className="w-3 h-3 fill-current" />}
                                                    </Button>
                                                    <Button
                                                        size="icon"
                                                        className="h-7 w-7 text-gray-400 hover:text-red-600 hover:bg-red-50"
                                                        variant="ghost"
                                                        onClick={() => removePart(idx)}
                                                        title="Remove Part"
                                                    >
                                                        <Trash2 className="w-3 h-3" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <div className="p-3 border-t border-gray-100 bg-gray-50/30">
                        <Button
                            variant="outline"
                            className="w-full border-dashed"
                            onClick={addPart}
                        >
                            <Plus className="w-4 h-4 mr-2" />
                            Add Segment
                        </Button>
                    </div>
                </div>
            </div>
        </Card>
    );
};
