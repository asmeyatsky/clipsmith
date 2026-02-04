'use client';

import { useState } from 'react';
import { VideoEditor } from './video-editor';
import { ProjectGallery } from './project-gallery';

export function EditorApp() {
    const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
    const [view, setView] = useState<'gallery' | 'editor'>('gallery');

    const handleProjectSelect = (projectId: string) => {
        setCurrentProjectId(projectId);
        setView('editor');
    };

    const handleBackToGallery = () => {
        setCurrentProjectId(null);
        setView('gallery');
    };

    const handleCreateNew = () => {
        // This will be handled by ProjectGallery creating a new project
        // then automatically switching to editor view
    };

    if (view === 'editor' && currentProjectId) {
        return (
            <div className="relative">
                {/* Back Button */}
                <div className="absolute top-4 left-4 z-10">
                    <button
                        onClick={handleBackToGallery}
                        className="flex items-center space-x-2 px-3 py-2 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        <span>Back to Projects</span>
                    </button>
                </div>
                
                <VideoEditor projectId={currentProjectId} />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <ProjectGallery
                onProjectSelect={handleProjectSelect}
                onCreateNew={handleCreateNew}
            />
        </div>
    );
}