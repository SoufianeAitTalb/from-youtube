import { useRef } from 'react';
import type { ReplayedPart } from '../api/client';
import { Play, Trash2, Plus, RefreshCw } from 'lucide-react';

interface VideoPartEditorProps {
    parts: ReplayedPart[];
    onPartsChange: (parts: ReplayedPart[]) => void;
    videoUrl?: string; // URL to the downloaded video for preview
}

export const VideoPartEditor = ({ parts, onPartsChange, videoUrl }: VideoPartEditorProps) => {
    const videoRef = useRef<HTMLVideoElement>(null);

    const handleSeek = (time: number) => {
        if (videoRef.current) {
            videoRef.current.currentTime = time;
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
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
            <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
                <RefreshCw className="w-5 h-5 text-gray-500" />
                Review & Edit Parts
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Video Preview */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">Preview Source</label>
                    <div className="aspect-video bg-black rounded-lg overflow-hidden relative">
                        {videoUrl ? (
                            <video
                                ref={videoRef}
                                src={videoUrl}
                                controls
                                className="w-full h-full"
                            />
                        ) : (
                            <div className="flex items-center justify-center h-full text-gray-500">
                                No video source available
                            </div>
                        )}
                    </div>
                    {videoUrl && <p className="text-xs text-gray-500">Previewing downloaded video from server</p>}
                </div>

                {/* Parts List */}
                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                    {parts.map((part, idx) => (
                        <div key={idx} className="flex items-end gap-3 p-3 bg-gray-50 rounded border border-gray-100">
                            <div className="w-8 font-bold text-gray-400 text-center pb-2">#{part.position}</div>

                            <div>
                                <label className="block text-xs font-medium text-gray-500 mb-1">Start (s)</label>
                                <div className="flex items-center gap-1">
                                    <input
                                        type="number"
                                        value={part.start}
                                        onChange={e => updatePart(idx, 'start', Number(e.target.value))}
                                        className="w-20 rounded border-gray-300 text-sm p-1.5"
                                        step="0.1"
                                    />
                                    <button
                                        onClick={() => handleSeek(part.start)}
                                        className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                                        title="Preview Start"
                                    >
                                        <Play className="w-3 h-3" />
                                    </button>
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-gray-500 mb-1">End (s)</label>
                                <div className="flex items-center gap-1">
                                    <input
                                        type="number"
                                        value={part.end}
                                        onChange={e => updatePart(idx, 'end', Number(e.target.value))}
                                        className="w-20 rounded border-gray-300 text-sm p-1.5"
                                        step="0.1"
                                    />
                                    <button
                                        onClick={() => handleSeek(part.end)}
                                        className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                                        title="Preview End"
                                    >
                                        <Play className="w-3 h-3" />
                                    </button>
                                </div>
                            </div>

                            <button
                                onClick={() => removePart(idx)}
                                className="mb-1 p-2 text-red-500 hover:bg-red-50 rounded"
                                title="Remove Part"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    ))}

                    <button
                        onClick={addPart}
                        className="w-full flex items-center justify-center gap-2 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <Plus className="w-4 h-4" />
                        Add New Part
                    </button>
                </div>
            </div>
        </div>
    );
};
