'use client';

import { useState, useRef, useCallback } from 'react';
import { Timeline } from './timeline';
import { usePayment } from '@/hooks/usePayment';
import { useAnalytics } from '@/hooks/useAnalytics';
import { DollarSign, TrendingUp, Users, Eye, Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';

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
    const [showMonetizationPanel, setShowMonetizationPanel] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const animationRef = useRef<number>();

    // Initialize payment and analytics hooks
    const { sendTip, getUserWallet, getTransactionHistory } = usePayment();
    const { trackEvent, getVideoAnalytics, getCreatorAnalytics } = useAnalytics();

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

    const animate = useCallback(() => {
        if (project && playhead < project.duration) {
            setPlayhead(prev => prev + 0.016); // ~60fps
            animationRef.current = requestAnimationFrame(animate);
        } else {
            setIsPlaying(false);
        }
    }, [project, playhead]);

    // Cleanup animation frame on unmount
    useEffect(() => {
        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, []);

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
            <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-3 sm:p-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
                    <div className="flex items-center space-x-2 sm:space-x-4 min-w-0 flex-1">
                        <input
                            type="text"
                            value={project.title}
                            onChange={(e) => handleProjectTitleChange(e.target.value)}
                            className="text-lg sm:text-xl font-semibold bg-transparent border-none outline-none truncate"
                        />
                        <span className="text-xs sm:text-sm text-gray-500 whitespace-nowrap">
                            {Math.floor(project.duration / 60)}:{(project.duration % 60).toFixed(0).padStart(2, '0')}
                        </span>
                    </div>
                    
                    <div className="flex items-center space-x-2 sm:space-x-4">
                        <button
                            onClick={handlePlayPause}
                            className="px-2 sm:px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs sm:text-sm"
                        >
                            {isPlaying ? 'Pause' : 'Play'}
                        </button>
                        
                        <button
                            onClick={() => setShowMonetizationPanel(!showMonetizationPanel)}
                            className="px-2 sm:px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 flex items-center gap-1 sm:gap-2 text-xs sm:text-sm"
                        >
                            <DollarSign size={14} />
                            <span className="hidden sm:inline">Monetize</span>
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
                            className="px-2 sm:px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-xs sm:text-sm"
                        >
                            Upload
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Editor Area */}
            <div className="flex flex-1 flex-col lg:flex-row overflow-hidden">
                {/* Mobile Assets Toggle */}
                <div className="lg:hidden flex border-b border-gray-200 dark:border-gray-700">
                    <button
                        onClick={() => setShowMonetizationPanel(false)}
                        className={`flex-1 px-4 py-2 text-sm font-medium ${
                            !showMonetizationPanel 
                                ? 'bg-blue-500 text-white' 
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'
                        }`}
                    >
                        Assets
                    </button>
                    <button
                        onClick={() => setShowMonetizationPanel(true)}
                        className={`flex-1 px-4 py-2 text-sm font-medium ${
                            showMonetizationPanel 
                                ? 'bg-purple-500 text-white' 
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'
                        }`}
                    >
                        Monetization
                    </button>
                </div>

                {/* Assets Panel */}
                <div className={`${showMonetizationPanel ? 'hidden' : 'flex'} lg:block w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 overflow-y-auto`}>
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

                {/* Properties/Monetization Panel - Mobile */}
                <div className={`${showMonetizationPanel ? 'flex' : 'hidden'} lg:hidden w-full bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 overflow-y-auto`}>
                    <MonetizationPanel 
                        project={project}
                        selectedAsset={selectedAsset}
                        tracks={tracks}
                    />
                </div>

                {/* Properties Panel - Desktop */}
                <div className="hidden lg:block w-64 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-4 overflow-y-auto">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">Properties</h3>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowMonetizationPanel(!showMonetizationPanel)}
                            className="text-purple-500 hover:text-purple-600"
                        >
                            <DollarSign size={16} />
                        </Button>
                    </div>
                    
                    {showMonetizationPanel ? (
                        <MonetizationPanel 
                            project={project}
                            selectedAsset={selectedAsset}
                            tracks={tracks}
                        />
                    ) : (
                        <>
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
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

// Monetization Panel Component
interface MonetizationPanelProps {
    project: VideoProject | null;
    selectedAsset: VideoAsset | null;
    tracks: VideoTrack[];
}

function MonetizationPanel({ project, selectedAsset, tracks }: MonetizationPanelProps) {
    const [enableTips, setEnableTips] = useState(true);
    const [enableSubscriptions, setEnableSubscriptions] = useState(false);
    const [tipAmount, setTipAmount] = useState(5);
    const [subscriptionPrice, setSubscriptionPrice] = useState(9.99);
    const { sendTip, getUserWallet } = usePayment();
    const { trackEvent, getVideoAnalytics } = useAnalytics();

    const handleMonetizationToggle = async (feature: string, enabled: boolean) => {
        if (!project) return;
        
        try {
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No authentication token');

            const response = await fetch(`/api/editor/projects/${project.id}/monetization`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    feature,
                    enabled
                })
            });

            if (!response.ok) throw new Error('Failed to update monetization');

            trackEvent('monetization_updated', {
                projectId: project.id,
                feature,
                enabled
            });

        } catch (error) {
            console.error('Error updating monetization:', error);
        }
    };

    return (
        <div className="space-y-4">
            <h4 className="text-md font-semibold text-purple-600">Monetization Settings</h4>
            
            {/* Enable Tips */}
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Enable Tips</label>
                    <input
                        type="checkbox"
                        checked={enableTips}
                        onChange={(e) => {
                            setEnableTips(e.target.checked);
                            handleMonetizationToggle('tips', e.target.checked);
                        }}
                        className="rounded text-purple-500"
                    />
                </div>
                {enableTips && (
                    <div className="ml-4 space-y-2">
                        <label className="text-xs text-gray-500">Suggested Tip Amount</label>
                        <div className="flex gap-2">
                            {[1, 5, 10, 20].map(amount => (
                                <button
                                    key={amount}
                                    onClick={() => setTipAmount(amount)}
                                    className={`px-2 py-1 text-xs rounded ${
                                        tipAmount === amount
                                            ? 'bg-purple-500 text-white'
                                            : 'bg-gray-200 dark:bg-gray-700'
                                    }`}
                                >
                                    ${amount}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Enable Subscriptions */}
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Enable Subscriptions</label>
                    <input
                        type="checkbox"
                        checked={enableSubscriptions}
                        onChange={(e) => {
                            setEnableSubscriptions(e.target.checked);
                            handleMonetizationToggle('subscriptions', e.target.checked);
                        }}
                        className="rounded text-purple-500"
                    />
                </div>
                {enableSubscriptions && (
                    <div className="ml-4 space-y-2">
                        <label className="text-xs text-gray-500">Monthly Price</label>
                        <input
                            type="number"
                            value={subscriptionPrice}
                            onChange={(e) => setSubscriptionPrice(parseFloat(e.target.value))}
                            className="w-full px-2 py-1 text-sm border rounded"
                            step="0.01"
                            min="0.99"
                        />
                    </div>
                )}
            </div>

            {/* Revenue Preview */}
            <div className="mt-4 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <h5 className="text-sm font-medium mb-2 flex items-center gap-1">
                    <TrendingUp size={14} />
                    Revenue Preview
                </h5>
                <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                        <span>Estimated Tips/Month:</span>
                        <span className="font-medium">${(tipAmount * 47).toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between">
                        <span>Subscriptions:</span>
                        <span className="font-medium">${(subscriptionPrice * 12).toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between font-bold pt-1 border-t">
                        <span>Total Est. Revenue:</span>
                        <span className="text-purple-600">
                            ${(tipAmount * 47 + subscriptionPrice * 12).toFixed(0)}
                        </span>
                    </div>
                </div>
            </div>

            {/* Engagement Metrics */}
            {project && (
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <h5 className="text-sm font-medium mb-2 flex items-center gap-1">
                        <Eye size={14} />
                        Engagement Metrics
                    </h5>
                    <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                            <span>Views:</span>
                            <span className="font-medium">1,234</span>
                        </div>
                        <div className="flex justify-between">
                            <span>Engagement Rate:</span>
                            <span className="font-medium">8.5%</span>
                        </div>
                        <div className="flex justify-between">
                            <span>Conversion Rate:</span>
                            <span className="font-medium">2.3%</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Quick Actions */}
            <div className="mt-4 space-y-2">
                <button
                    onClick={() => {
                        trackEvent('editor_test_tip', {
                            projectId: project?.id,
                            amount: tipAmount
                        });
                    }}
                    className="w-full px-3 py-2 bg-purple-500 text-white rounded text-sm hover:bg-purple-600 flex items-center justify-center gap-2"
                >
                    <DollarSign size={14} />
                    Test Tip Flow
                </button>
                
                <button
                    onClick={() => {
                        trackEvent('editor_view_analytics', {
                            projectId: project?.id
                        });
                    }}
                    className="w-full px-3 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 flex items-center justify-center gap-2"
                >
                    <TrendingUp size={14} />
                    View Analytics
                </button>
            </div>
        </div>
    );
}