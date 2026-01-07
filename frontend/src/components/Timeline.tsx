
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
        case 'success': return <CheckCircle className="w-5 h-5 text-emerald-500 fill-emerald-50" />;
        case 'failed': return <XCircle className="w-5 h-5 text-red-500 fill-red-50" />;
        case 'running': return <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" />;
        default: return <Circle className="w-5 h-5 text-gray-200" />;
    }
};

export const Timeline = () => {
    const { steps } = useStore();

    return (
        <div className="h-full flex flex-col">
            <div className="pb-4 mb-4 border-b border-gray-100">
                <h2 className="font-semibold text-gray-900">Pipeline Progress</h2>
                <p className="text-xs text-gray-500">Track extraction status</p>
            </div>

            <div className="flex-1 overflow-y-auto space-y-0">
                {STEPS.map((step, idx) => {
                    const stepState = steps[step.id];
                    const isLast = idx === STEPS.length - 1;
                    const isActive = stepState.status === 'running';
                    const isDone = stepState.status === 'success';

                    return (
                        <div key={step.id} className="relative flex gap-4 pb-8 group">
                            {!isLast && (
                                <div className={clsx(
                                    "absolute left-[9px] top-6 w-0.5 h-full -z-10 transition-colors duration-500",
                                    isDone ? "bg-emerald-200" : "bg-gray-100"
                                )} />
                            )}
                            <div className={clsx(
                                "mt-0.5 relative z-10 transition-transform duration-300",
                                isActive && "scale-110"
                            )}>
                                <StatusIcon status={stepState.status} />
                            </div>
                            <div className="flex-1 -mt-1">
                                <h3 className={clsx("text-sm font-medium transition-colors", {
                                    "text-indigo-600": isActive,
                                    "text-gray-900": isDone,
                                    "text-gray-500": stepState.status === 'idle' || stepState.status === 'failed'
                                })}>{step.label}</h3>

                                {stepState.status !== 'idle' && (
                                    <div className="mt-1 flex flex-col gap-1">
                                        <div className="text-xs text-gray-500 capitalize flex items-center gap-1.5">
                                            <span className={clsx("w-1.5 h-1.5 rounded-full", {
                                                "bg-indigo-500 animate-pulse": isActive,
                                                "bg-emerald-500": isDone,
                                                "bg-red-500": stepState.status === 'failed'
                                            })} />
                                            {stepState.status}
                                        </div>
                                        {stepState.status === 'running' && stepState.progress !== undefined && (
                                            <div className="h-1 w-full bg-gray-100 rounded-full overflow-hidden mt-1">
                                                <div
                                                    className="h-full bg-indigo-500 transition-all duration-300"
                                                    style={{ width: `${stepState.progress}%` }}
                                                />
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
