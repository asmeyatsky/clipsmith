'use client';

import { useRef } from 'react';

interface TimelineProps {
    duration: number;
    playhead: number;
    onPlayheadChange: (newPlayhead: number) => void;
}

export function Timeline({ duration, playhead, onPlayheadChange }: TimelineProps) {
    const timelineRef = useRef<HTMLDivElement>(null);

    const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!timelineRef.current) return;
        const rect = timelineRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const newPlayhead = (x / rect.width) * duration;
        onPlayheadChange(newPlayhead);

        const handleMouseMove = (e: MouseEvent) => {
            if (!timelineRef.current) return;
            const rect = timelineRef.current.getBoundingClientRect();
            const x = e.clientX - rect.left;
            let newPlayhead = (x / rect.width) * duration;
            if (newPlayhead < 0) newPlayhead = 0;
            if (newPlayhead > duration) newPlayhead = duration;
            onPlayheadChange(newPlayhead);
        };

        const handleMouseUp = () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    const formatTime = (seconds: number) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    // Hardcode 3 tracks for now
    const tracks = [1, 2, 3];

    return (
        <div className="w-full h-full flex flex-col p-2 bg-gray-200 dark:bg-gray-700 rounded-lg">
            {/* Time Ruler */}
            <div className="relative h-6 mb-1">
                <div className="absolute top-0 left-0 w-full h-full flex justify-between px-2 text-xs text-gray-500">
                    {[...Array(Math.floor(duration / 10) + 1)].map((_, i) => (
                        <span key={i} style={{ left: `${(i * 10 / duration) * 100}%`, position: 'absolute' }}>
                            {formatTime(i * 10)}
                        </span>
                    ))}
                </div>
            </div>

            {/* Tracks Container */}
            <div className="relative flex-1" ref={timelineRef} onMouseDown={handleMouseDown}>
                {tracks.map(trackNum => (
                    <div key={trackNum} className="relative w-full h-1/3 border-b border-gray-300 dark:border-gray-600 last:border-b-0 flex items-center px-2">
                        <span className="text-xs text-gray-500 mr-2">Track {trackNum}</span>
                        {/* Placeholder for clips */}
                        {trackNum === 1 && ( // Example clip on first track
                            <div
                                className="absolute bg-green-500 opacity-70 rounded-md h-3/4"
                                style={{
                                    left: `${(0.5 / duration) * 100}%`,
                                    width: `${(5 / duration) * 100}%`,
                                }}
                            ></div>
                        )}
                    </div>
                ))}
                
                {/* Playhead */}
                <div
                    className="absolute top-0 bottom-0 w-0.5 bg-red-500 pointer-events-none"
                    style={{ left: `${(playhead / duration) * 100}%` }}
                ></div>
            </div>
            {/* Current Time Display */}
            <div className="text-xs text-center text-gray-500 mt-1">
                Current Time: {formatTime(playhead)}
            </div>
        </div>
    );
}
