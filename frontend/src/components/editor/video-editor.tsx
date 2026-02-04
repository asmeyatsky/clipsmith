'use client';

import { useState, useRef, useCallback } from 'react';
import { Timeline } from './timeline';

interface VideoEditorProps {
    projectId?: string;
}

interface VideoAsset {
    id: string;
    type: string;
    filename: string;
    file_size: number;
    mime_type: string;
    url: string;
    duration?: number;
    created_at: string;
}

interface VideoProject {
    id: string;
    user_id: string;
    title: string;
    description?: string;
    status: string;
    thumbnail_url?: string;
    duration: number;
    created_at: string;
    updated_at?: string;
}

interface VideoTrack {
    id: string;
    project_id: string;
    asset_id: string;
    type: string;
    start_time: number;
    end_time: number;
}

interface VideoCaption {
    id: string;
    project_id: string;
    video_asset_id: string;
    text: string;
    start_time: number;
    end_time: number;
}

export function VideoEditor({ projectId }: VideoEditorProps) {
    const [project, setProject] = useState<VideoProject | null>(null);
    const [assets, setAssets] = useState<VideoAsset[]>([]);
    const [tracks, setTracks] = useState<VideoTrack[]>([]);
    const [captions, setCaptions] = useState<VideoCaption[]>([]);
    const [playhead, setPlayhead] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [selectedAsset, setSelectedAsset] = useState<VideoAsset | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const animationRef = useRef<number>();

    const loadProject = useCallback(async () => {
        if (!projectId) return;
        
        try {
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No authentication token');
            
            // Load project
            const projectResponse = await fetch(`/api/editor/projects/${projectId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!projectResponse.ok) throw new Error('Failed to load project');
            
            const projectData = await projectResponse.json();
            setProject(projectData.project);
            
            // Load assets
            const assetsResponse = await fetch(`/api/editor/projects/${projectId}/assets`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (assetsResponse.ok) {
                const assetsData = await assetsResponse.json();
                setAssets(assetsData.assets);
            }
            
            // Load tracks
            const tracksResponse = await fetch(`/api/editor/projects/${projectId}/tracks`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (tracksResponse.ok) {
                const tracksData = await tracksResponse.json();
                setTracks(tracksData.tracks);
            }
            
        } catch (error) {
            console.error('Error loading project:', error);
        } finally {
            setIsLoading(false);
        }
    }, [projectId]);

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (!files || files.length === 0 || !project) return;

        const file = files[0];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('asset_type', file.type.startsWith('video/') ? 'video' : 'audio');
        formData.append('project_id', project.id);

        try {
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No authentication token');

            const response = await fetch(`/api/editor/projects/${project.id}/assets`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (!response.ok) throw new Error('Failed to upload asset');

            const result = await response.json();
            setAssets(prev => [...prev, result.asset]);
            
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    };

    const handlePlayPause = () => {
        if (isPlaying) {
            setIsPlaying(false);
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        } else {
            setIsPlaying(true);
            animate();
        }
    };

    const animate = () => {
        if (project && playhead < project.duration) {
            setPlayhead(prev => prev + 0.016); // ~60fps
            animationRef.current = requestAnimationFrame(animate);
        } else {
            setIsPlaying(false);
        }
    };

    const handleAddToTimeline = () => {
        if (!selectedAsset || !project) return;

        const newTrack: VideoTrack = {
            id: `track_${Date.now()}`,
            project_id: project.id,
            asset_id: selectedAsset.id,
            type: selectedAsset.type,
            start_time: playhead,
            end_time: playhead + (selectedAsset.duration || 5)
        };

        setTracks(prev => [...prev, newTrack]);
    };

    const handleProjectTitleChange = async (newTitle: string) => {
        if (!project) return;

        try {
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No authentication token');

            const response = await fetch(`/api/editor/projects/${project.id}/title`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `title=${encodeURIComponent(newTitle)}`
            });

            if (!response.ok) throw new Error('Failed to update title');

            const result = await response.json();
            setProject(result.project);

        } catch (error) {
            console.error('Error updating project title:', error);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-lg">Loading project...</div>
            </div>
        );
    }

    if (!project) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-lg text-red-500">Project not found</div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-screen bg-gray-100 dark:bg-gray-900">
            {/* Header */}
            <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <input
                            type="text"
                            value={project.title}
                            onChange={(e) => handleProjectTitleChange(e.target.value)}
                            className="text-xl font-semibold bg-transparent border-none outline-none"
                        />
                        <span className="text-sm text-gray-500">
                            Duration: {Math.floor(project.duration / 60)}:{(project.duration % 60).toFixed(0).padStart(2, '0')}
                        </span>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={handlePlayPause}
                            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                            {isPlaying ? 'Pause' : 'Play'}
                        </button>
                        
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="video/*,audio/*"
                            onChange={handleFileUpload}
                            className="hidden"
                        />
                        
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                        >
                            Upload Asset
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Editor Area */}
            <div className="flex flex-1 overflow-hidden">
                {/* Assets Panel */}
                <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 overflow-y-auto">
                    <h3 className="text-lg font-semibold mb-4">Assets</h3>
                    
                    <div className="space-y-2">
                        {assets.map(asset => (
                            <div
                                key={asset.id}
                                onClick={() => setSelectedAsset(asset)}
                                className={`p-3 rounded cursor-pointer transition-colors ${
                                    selectedAsset?.id === asset.id
                                        ? 'bg-blue-100 dark:bg-blue-900'
                                        : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                                }`}
                            >
                                <div className="text-sm font-medium">{asset.filename}</div>
                                <div className="text-xs text-gray-500">
                                    {asset.type} • {(asset.file_size / 1024 / 1024).toFixed(2)} MB
                                </div>
                            </div>
                        ))}
                    </div>
                    
                    {selectedAsset && (
                        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900 rounded">
                            <button
                                onClick={handleAddToTimeline}
                                className="w-full px-3 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                            >
                                Add to Timeline
                            </button>
                        </div>
                    )}
                </div>

                {/* Timeline Area */}
                <div className="flex-1 bg-white dark:bg-gray-800 p-4">
                    <Timeline
                        duration={project.duration}
                        playhead={playhead}
                        onPlayheadChange={setPlayhead}
                    />
                </div>

                {/* Properties Panel */}
                <div className="w-64 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-4 overflow-y-auto">
                    <h3 className="text-lg font-semibold mb-4">Properties</h3>
                    
                    {selectedAsset && (
                        <div className="space-y-3">
                            <div>
                                <label className="text-sm font-medium">File Name</label>
                                <div className="text-sm text-gray-600 dark:text-gray-400">{selectedAsset.filename}</div>
                            </div>
                            
                            <div>
                                <label className="text-sm font-medium">Type</label>
                                <div className="text-sm text-gray-600 dark:text-gray-400">{selectedAsset.type}</div>
                            </div>
                            
                            <div>
                                <label className="text-sm font-medium">Size</label>
                                <div className="text-sm text-gray-600 dark:text-gray-400">
                                    {(selectedAsset.file_size / 1024 / 1024).toFixed(2)} MB
                                </div>
                            </div>
                            
                            {selectedAsset.duration && (
                                <div>
                                    <label className="text-sm font-medium">Duration</label>
                                    <div className="text-sm text-gray-600 dark:text-gray-400">
                                        {Math.floor(selectedAsset.duration / 60)}:{(selectedAsset.duration % 60).toFixed(0).padStart(2, '0')}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                    
                    {!selectedAsset && (
                        <div className="text-sm text-gray-500">
                            Select an asset to view properties
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}