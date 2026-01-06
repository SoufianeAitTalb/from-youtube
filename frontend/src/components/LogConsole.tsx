import React, { useRef, useEffect, useState } from 'react';
import { useStore } from '../store';
import type { StepName } from '../store';
import { Terminal, Copy, ChevronDown, ChevronUp } from 'lucide-react';

interface LogConsoleProps {
    isExpanded?: boolean;
    onToggleExpand?: () => void;
}

export const LogConsole = ({ isExpanded: controlledIsExpanded, onToggleExpand }: LogConsoleProps = {}) => {
    const { steps } = useStore();
    const scrollRef = useRef<HTMLDivElement>(null);
    const [filterStep, setFilterStep] = useState<StepName | 'all'>('all');
    const [internalIsExpanded, setInternalIsExpanded] = useState(true);

    const isExpanded = controlledIsExpanded !== undefined ? controlledIsExpanded : internalIsExpanded;
    const toggleExpand = () => {
        if (onToggleExpand) {
            onToggleExpand();
        } else {
            setInternalIsExpanded(!isExpanded);
        }
    };


    const logs = React.useMemo(() => {
        if (filterStep !== 'all') {
            return steps[filterStep].logs.map(l => `[${filterStep}] ${l}`);
        }
        return Object.entries(steps).flatMap(([name, step]) =>
            step.logs.map(l => `[${name}] ${l}`)
        );
    }, [steps, filterStep]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className={`flex flex-col bg-gray-900 text-gray-100 border-t border-gray-700 transition-all duration-300 ${isExpanded ? 'h-64' : 'h-10'}`}>
            <div
                className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700 cursor-pointer hover:bg-gray-750"
                onClick={toggleExpand}
            >
                <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-gray-400" />
                    <span className="text-sm font-medium">Console Output</span>
                </div>
                <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                    <select
                        className="bg-gray-700 text-xs rounded px-2 py-1 border border-gray-600 focus:outline-none"
                        value={filterStep}
                        onChange={e => setFilterStep(e.target.value as any)}
                    >
                        <option value="all">All Steps</option>
                        <option value="fetch">Fetch</option>
                        <option value="download">Download</option>
                        <option value="cut">Cut</option>
                        <option value="crop">Crop</option>
                        <option value="subtitles">Subtitles</option>
                    </select>
                    <button
                        className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
                        title="Copy Logs"
                        onClick={() => navigator.clipboard.writeText(logs.join('\n'))}
                    >
                        <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button
                        className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white ml-2"
                        onClick={toggleExpand}
                    >
                        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
                    </button>
                </div>
            </div>
            {isExpanded && (
                <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-1">
                    {logs.length === 0 ? (
                        <div className="text-gray-600 italic">No logs yet...</div>
                    ) : (
                        logs.map((log, i) => (
                            <div key={i} className="break-all whitespace-pre-wrap">{log}</div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};
