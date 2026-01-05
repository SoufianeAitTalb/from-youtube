
import { useStore } from '../store';
import type { StepName, StepState } from '../store';
import { CheckCircle, Circle, Loader2, XCircle } from 'lucide-react';
import clsx from 'clsx';

const STEPS: { id: StepName; label: string }[] = [
    { id: 'fetch', label: 'Fetch Replayed Parts' },
    { id: 'download', label: 'Download Video' },
    { id: 'cut', label: 'Cut Video Parts' },
    { id: 'crop', label: 'Crop Vertical' },
    { id: 'subtitles', label: 'Add Subtitles' },
];

const StatusIcon = ({ status }: { status: StepState['status'] }) => {
    switch (status) {
        case 'success': return <CheckCircle className="w-5 h-5 text-green-500" />;
        case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
        case 'running': return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
        default: return <Circle className="w-5 h-5 text-gray-300" />;
    }
};

export const Timeline = () => {
    const { steps } = useStore();

    return (
        <div className="w-64 bg-white border-r border-gray-200 h-full flex flex-col shrink-0">
            <div className="p-4 border-b border-gray-200 font-bold text-gray-700">Pipeline Steps</div>
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {STEPS.map((step, idx) => {
                    const stepState = steps[step.id];
                    const isLast = idx === STEPS.length - 1;

                    return (
                        <div key={step.id} className="relative flex gap-3">
                            {!isLast && (
                                <div className="absolute left-[9px] top-6 w-0.5 h-full bg-gray-100 -z-10" />
                            )}
                            <div className="mt-1">
                                <StatusIcon status={stepState.status} />
                            </div>
                            <div className="flex-1">
                                <h3 className={clsx("font-medium", {
                                    "text-gray-900": stepState.status !== 'idle',
                                    "text-gray-500": stepState.status === 'idle'
                                })}>{step.label}</h3>
                                <div className="text-xs text-gray-500 mt-1 capitalize">
                                    {stepState.status}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
