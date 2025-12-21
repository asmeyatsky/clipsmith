'use client';

import { useParams } from 'next/navigation';
import { Video, Layers, Scissors, Music, Type, Subtitles, Palette, Volume2, Camera } from 'lucide-react'; // Import Camera
import { Timeline } from '@/components/editor/timeline';
import { useEffect, useState, useRef } from 'react';
import { videoService } from '@/lib/api/video';
import { VideoResponseDTO } from '@/lib/types';
import { useRouter } from 'next/navigation';

export default function EditorPage() {
    const params = useParams();
    const videoId = params.videoId as string;
    const [video, setVideo] = useState<VideoResponseDTO | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const [playhead, setPlayhead] = useState(0);
    const router = useRouter();
    const [isChromaKeyEnabled, setIsChromaKeyEnabled] = useState(false);
    const [selectedPreset, setSelectedPreset] = useState<string | null>(null); // New state for color grading
    const [mainVolume, setMainVolume] = useState(100);
    const [musicVolume, setMusicVolume] = useState(50);
    const [sfxVolume, setSfxVolume] = useState(70);

    useEffect(() => {
        const fetchVideo = async () => {
            if (!videoId) return;
            try {
                setLoading(true);
                const data = await videoService.getById(videoId);
                setVideo(data);
            } catch (err: any) {
                setError(err.message || 'Failed to load video');
            } finally {
                setLoading(false);
            }
        };

        fetchVideo();
    }, [videoId]);

    useEffect(() => {
        const videoElement = videoRef.current;
        if (!videoElement) return;

        const handleTimeUpdate = () => {
            setPlayhead(videoElement.currentTime);
        };

        videoElement.addEventListener('timeupdate', handleTimeUpdate);

        return () => {
            videoElement.removeEventListener('timeupdate', handleTimeUpdate);
        };
    }, [video]);

    const handlePlayheadChange = (newPlayhead: number) => {
        if (videoRef.current) {
            videoRef.current.currentTime = newPlayhead;
            setPlayhead(newPlayhead);
        }
    };

    const handleGenerateCaptions = async () => {
        if (!videoId) return;
        try {
            alert("Generating captions... This may take a moment.");
            await videoService.generateCaptions(videoId);
            alert("Captions generation initiated successfully!");
        } catch (err: any) {
            console.error("Failed to generate captions:", err);
            alert(`Failed to generate captions: ${err.message || 'Unknown error'}`);
        }
    };

    const toggleChromaKey = () => {
        setIsChromaKeyEnabled(prev => !prev);
        alert(`Chroma Key ${isChromaKeyEnabled ? 'disabled' : 'enabled'} (simulated)`);
    };

    const applyPreset = (presetName: string) => {
        setSelectedPreset(presetName);
        alert(`Color Grading Preset "${presetName}" applied (simulated)`);
    };

    return (
        <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
            {/* Sidebar */}
            <aside className="w-16 bg-white dark:bg-gray-800 flex flex-col items-center py-4">
                <div className="flex flex-col items-center space-y-4">
                    <button className="p-2 rounded-lg bg-blue-500 text-white">
                        <Layers size={24} />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">
                        <Scissors size={24} />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">
                        <Music size={24} />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">
                        <Type size={24} />
                    </button>
                </div>
            </aside>

            <main className="flex-1 flex flex-col">
                {/* Top Bar */}
                <div className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4">
                    <h1 className="text-lg font-bold">Video Editor</h1>
                    <div className="flex items-center space-x-4">
                        <button className="px-4 py-2 text-sm rounded-lg bg-gray-200 dark:bg-gray-700">
                            Export
                        </button>
                        <button
                            className="px-4 py-2 text-sm rounded-lg bg-blue-500 text-white flex items-center gap-2"
                            onClick={handleGenerateCaptions}
                            disabled={!video || loading}
                        >
                            <Subtitles size={16} />
                            Generate Captions
                        </button>
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 flex p-4">
                    {/* Video Preview */}
                    <div className="w-2/3 bg-black rounded-lg flex items-center justify-center">
                        {loading && <p>Loading...</p>}
                        {error && <p>{error}</p>}
                        {video && (
                            <video
                                ref={videoRef}
                                src={video.url!}
                                controls
                                className="w-full h-full"
                            />
                        )}
                    </div>

                    {/* Properties Panel */}
                    <div className="w-1/3 bg-white dark:bg-gray-800 ml-4 rounded-lg p-4">
                        <h2 className="text-lg font-bold mb-4">Properties</h2>
                        <p className="text-sm text-gray-500 mb-4">Select an element to edit its properties.</p>

                        {/* Simulated Chroma Key Section */}
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
                            <h3 className="text-md font-semibold mb-2 flex items-center gap-2">
                                <Palette size={18} /> Chroma Key (Simulated)
                            </h3>
                            <button
                                onClick={toggleChromaKey}
                                className={`w-full px-4 py-2 rounded-lg text-white font-semibold transition-colors
                                    ${isChromaKeyEnabled ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'}`}
                            >
                                {isChromaKeyEnabled ? 'Disable Chroma Key' : 'Enable Chroma Key'}
                            </button>
                            <p className="text-xs text-gray-500 mt-2">
                                This is a simulated toggle. Full functionality requires advanced video processing.
                            </p>
                        </div>

                        {/* Simulated Color Grading Section */}
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
                            <h3 className="text-md font-semibold mb-2 flex items-center gap-2">
                                <Palette size={18} /> Color Grading (Simulated)
                            </h3>
                            <div className="flex flex-wrap gap-2">
                                {['Vibrant', 'Monochrome', 'Cinematic', 'Warm', 'Cool'].map(preset => (
                                    <button
                                        key={preset}
                                        onClick={() => applyPreset(preset)}
                                        className={`px-4 py-2 text-sm rounded-lg border transition-colors
                                            ${selectedPreset === preset
                                                ? 'bg-blue-500 border-blue-500 text-white'
                                                : 'bg-gray-100 border-gray-200 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600'}`}
                                    >
                                        {preset}
                                    </button>
                                ))}
                                <button
                                    onClick={() => applyPreset('None')}
                                    className={`px-4 py-2 text-sm rounded-lg border transition-colors
                                        ${selectedPreset === 'None'
                                            ? 'bg-red-500 border-red-500 text-white'
                                            : 'bg-gray-100 border-gray-200 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600'}`}
                                >
                                    Reset
                                </button>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                Apply various color filters. Full functionality requires advanced video processing.
                            </p>
                        </div>

                        {/* Simulated Audio Mixing Section */}
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
                            <h3 className="text-md font-semibold mb-2 flex items-center gap-2">
                                <Volume2 size={18} /> Audio Mixing (Simulated)
                            </h3>
                            <div className="space-y-3">
                                <div>
                                    <label htmlFor="mainVolume" className="text-sm text-gray-700 dark:text-gray-300">
                                        Main Volume: {mainVolume}%
                                    </label>
                                    <input
                                        type="range"
                                        id="mainVolume"
                                        min="0"
                                        max="100"
                                        value={mainVolume}
                                        onChange={(e) => {
                                            setMainVolume(parseInt(e.target.value));
                                            alert(`Main Volume set to ${e.target.value}% (simulated)`);
                                        }}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="musicVolume" className="text-sm text-gray-700 dark:text-gray-300">
                                        Music Volume: {musicVolume}%
                                    </label>
                                    <input
                                        type="range"
                                        id="musicVolume"
                                        min="0"
                                        max="100"
                                        value={musicVolume}
                                        onChange={(e) => {
                                            setMusicVolume(parseInt(e.target.value));
                                            alert(`Music Volume set to ${e.target.value}% (simulated)`);
                                        }}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="sfxVolume" className="text-sm text-gray-700 dark:text-gray-300">
                                        SFX Volume: {sfxVolume}%
                                    </label>
                                    <input
                                        type="range"
                                        id="sfxVolume"
                                        min="0"
                                        max="100"
                                        value={sfxVolume}
                                        onChange={(e) => {
                                            setSfxVolume(parseInt(e.target.value));
                                            alert(`SFX Volume set to ${e.target.value}% (simulated)`);
                                        }}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                                    />
                                </div>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                Adjust audio levels for different tracks. Full functionality requires advanced audio processing.
                            </p>
                        </div>

                        {/* Simulated AI Scene Detection */}
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
                            <h3 className="text-md font-semibold mb-2 flex items-center gap-2">
                                <Camera size={18} /> AI Scene Detection (Simulated)
                            </h3>
                            <button
                                onClick={() => alert("AI Scene Detection triggered (simulated)! Auto-cutting would happen here.")}
                                className="w-full px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white font-semibold transition-colors"
                            >
                                Detect Scenes & Auto-Cut
                            </button>
                            <p className="text-xs text-gray-500 mt-2">
                                Analyze video content to automatically detect scene changes and create cuts.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Timeline */}
                <div className="h-48 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
                    <h2 className="text-lg font-bold mb-4">Timeline</h2>
                    <Timeline
                        duration={video?.duration || 0}
                        playhead={playhead}
                        onPlayheadChange={handlePlayheadChange}
                    />
                </div>
            </main>
        </div>
    );
}
