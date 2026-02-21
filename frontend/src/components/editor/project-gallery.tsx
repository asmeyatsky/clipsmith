'use client';

import { useState, useEffect } from 'react';
import { sanitizeForReact } from '@/lib/utils/sanitize';
import { apiClient } from '@/lib/api/client';

interface VideoProject {
    id: string;
    title: string;
    description?: string;
    status: string;
    duration: number;
    created_at: string;
    updated_at?: string;
    thumbnail_url?: string;
}

interface ProjectGalleryProps {
    onProjectSelect: (projectId: string) => void;
    onCreateNew: () => void;
}

export function ProjectGallery({ onProjectSelect, onCreateNew }: ProjectGalleryProps) {
    const [projects, setProjects] = useState<VideoProject[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [filter, setFilter] = useState('all'); // all, draft, published, archived

    useEffect(() => {
        loadProjects();
    }, [filter]);

    const loadProjects = async () => {
        try {
            const url = filter === 'all' 
                ? '/api/editor/projects'
                : `/api/editor/projects?status=${filter}`;

            const data = await apiClient<{ projects: VideoProject[] }>(url);
            setProjects(data.projects);

        } catch (error) {
            console.error('Error loading projects:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const createNewProject = async () => {
        try {
            const data = await apiClient<{ project: VideoProject }>('/api/editor/projects', {
                method: 'POST',
                body: JSON.stringify({ title: 'New Project' }),
            });
            setProjects(prev => [data.project, ...prev]);
            onProjectSelect(data.project.id);

        } catch (error) {
            console.error('Error creating project:', error);
        }
    };

    const deleteProject = async (projectId: string) => {
        if (!confirm('Are you sure you want to delete this project?')) return;

        try {
            await apiClient(`/api/editor/projects/${projectId}`, {
                method: 'DELETE',
            });
            setProjects(prev => prev.filter(p => p.id !== projectId));

        } catch (error) {
            console.error('Error deleting project:', error);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString();
    };

    const formatDuration = (seconds: number) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-lg">Loading projects...</div>
            </div>
        );
    }

    return (
        <div className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Video Editor</h1>
                <button
                    onClick={createNewProject}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                    New Project
                </button>
            </div>

            {/* Filters */}
            <div className="flex space-x-4 mb-6">
                {['all', 'draft', 'published', 'archived'].map(status => (
                    <button
                        key={status}
                        onClick={() => setFilter(status)}
                        className={`px-4 py-2 rounded capitalize ${
                            filter === status
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
                        }`}
                    >
                        {status}
                    </button>
                ))}
            </div>

            {/* Projects Grid */}
            {projects.length === 0 ? (
                <div className="text-center py-12">
                    <div className="text-gray-500 mb-4">
                        {filter === 'all' ? 'No projects yet' : `No ${filter} projects`}
                    </div>
                    <button
                        onClick={createNewProject}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                        Create your first project
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {projects.map(project => (
                        <div
                            key={project.id}
                            className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow cursor-pointer"
                        >
                            {/* Thumbnail */}
                            <div
                                className="h-40 bg-gradient-to-br from-blue-400 to-purple-600 relative"
                                onClick={() => onProjectSelect(project.id)}
                            >
                                {project.thumbnail_url ? (
                                    <img
                                        src={project.thumbnail_url}
                                        alt={project.title}
                                        className="w-full h-full object-cover"
                                    />
                                ) : (
                                    <div className="flex items-center justify-center h-full">
                                        <div className="text-white text-center">
                                            <div className="text-4xl mb-2">🎬</div>
                                            <div className="text-sm">No thumbnail</div>
                                        </div>
                                    </div>
                                )}
                                
                                {/* Status Badge */}
                                <div className="absolute top-2 right-2">
                                    <span className={`px-2 py-1 text-xs rounded ${
                                        project.status === 'published' 
                                            ? 'bg-green-500 text-white'
                                            : project.status === 'archived'
                                            ? 'bg-gray-500 text-white'
                                            : 'bg-yellow-500 text-white'
                                    }`}>
                                        {project.status}
                                    </span>
                                </div>
                            </div>

                            {/* Project Info */}
                            <div className="p-4">
                                <h3 
                                    className="font-semibold text-lg mb-1 truncate"
                                    dangerouslySetInnerHTML={{ __html: sanitizeForReact(project.title) }}
                                />
                                
                                {project.description && (
                                    <p 
                                        className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-2"
                                        dangerouslySetInnerHTML={{ __html: sanitizeForReact(project.description) }}
                                    />
                                )}

                                <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                                    <span>{formatDuration(project.duration)}</span>
                                    <span>{formatDate(project.created_at)}</span>
                                </div>

                                {/* Actions */}
                                <div className="flex space-x-2">
                                    <button
                                        onClick={() => onProjectSelect(project.id)}
                                        className="flex-1 px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                                    >
                                        Open
                                    </button>
                                    
                                    {project.status !== 'published' && (
                                        <button className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600">
                                            Publish
                                        </button>
                                    )}
                                    
                                    <button
                                        onClick={() => deleteProject(project.id)}
                                        className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}