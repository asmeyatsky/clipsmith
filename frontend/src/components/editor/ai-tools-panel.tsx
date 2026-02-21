'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { 
  Sparkles, Video, MessageSquare, Voice, 
  Loader2, Check, X, Play, Image, Wand2
} from 'lucide-react';

interface AITemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  style: string;
  thumbnail_url: string;
  is_premium: boolean;
  price: number;
  tags: string[];
}

interface AIVoice {
  id: string;
  name: string;
  language: string;
  gender: string;
}

interface CaptionJob {
  id: string;
  status: string;
  language: string;
  captions: { text: string; start: number; end: number }[];
}

export function AIToolsPanel({ projectId }: { projectId?: string }) {
  const [activeTab, setActiveTab] = useState<'captions' | 'templates' | 'video' | 'voiceover'>('captions');
  const [templates, setTemplates] = useState<AITemplate[]>([]);
  const [voices, setVoices] = useState<AIVoice[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  
  // Caption settings
  const [captionLanguage, setCaptionLanguage] = useState('en');
  const [captions, setCaptions] = useState<{ text: string; start: number; end: number }[]>([]);
  
  // Video generation settings
  const [videoPrompt, setVideoPrompt] = useState('');
  const [videoType, setVideoType] = useState<'text_to_video' | 'image_to_video'>('text_to_video');
  const [videoDuration, setVideoDuration] = useState(5);
  
  // Voice-over settings
  const [voiceText, setVoiceText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('default');
  const [voiceSpeed, setVoiceSpeed] = useState(1.0);

  useEffect(() => {
    loadVoices();
    loadTemplates();
  }, []);

  const loadVoices = async () => {
    try {
      const data = await apiClient<{ voices: AIVoice[] }>('/api/ai/voices');
      setVoices(data.voices);
    } catch (e) {
      console.error('Error loading voices:', e);
    }
  };

  const loadTemplates = async () => {
    try {
      const data = await apiClient<{ templates: AITemplate[] }>('/api/ai/templates?limit=20');
      setTemplates(data.templates);
    } catch (e) {
      console.error('Error loading templates:', e);
    }
  };

  const generateCaptions = async () => {
    if (!projectId) return;
    setIsLoading(true);
    setJobStatus('pending');
    try {
      const result = await apiClient<{ job_id: string }>('/api/ai/captions/generate', {
        method: 'POST',
        body: JSON.stringify({ project_id: projectId, video_asset_id: projectId, language: captionLanguage })
      });
      
      // Poll for completion
      const pollJob = async () => {
        const job = await apiClient<CaptionJob>(`/api/ai/captions/${result.job_id}`);
        if (job.status === 'completed') {
          setCaptions(job.captions || []);
          setJobStatus('completed');
          setIsLoading(false);
        } else if (job.status === 'failed') {
          setJobStatus('failed');
          setIsLoading(false);
        } else {
          setTimeout(pollJob, 2000);
        }
      };
      setTimeout(pollJob, 2000);
    } catch (e) {
      console.error('Error generating captions:', e);
      setIsLoading(false);
      setJobStatus('failed');
    }
  };

  const generateVideo = async () => {
    if (!projectId || !videoPrompt) return;
    setIsLoading(true);
    try {
      await apiClient('/api/ai/video/generate', {
        method: 'POST',
        body: JSON.stringify({
          project_id: projectId,
          generation_type: videoType,
          prompt: videoPrompt,
          duration: videoDuration
        })
      });
      setIsLoading(false);
      alert('Video generation started! This may take a few minutes.');
    } catch (e) {
      console.error('Error generating video:', e);
      setIsLoading(false);
    }
  };

  const generateVoiceOver = async () => {
    if (!projectId || !voiceText) return;
    setIsLoading(true);
    try {
      await apiClient('/api/ai/voiceover/generate', {
        method: 'POST',
        body: JSON.stringify({
          project_id: projectId,
          text: voiceText,
          voice_id: selectedVoice,
          speed: voiceSpeed
        })
      });
      setIsLoading(false);
      alert('Voice-over generation started!');
    } catch (e) {
      console.error('Error generating voiceover:', e);
      setIsLoading(false);
    }
  };

  const useTemplate = async (templateId: string) => {
    try {
      const result = await apiClient<{ project_id: string }>(`/api/ai/templates/${templateId}/use`, {
        method: 'POST',
        body: JSON.stringify({ title: 'New Project from Template' })
      });
      alert(`Project created! ID: ${result.project_id}`);
    } catch (e) {
      console.error('Error using template:', e);
    }
  };

  const tabs = [
    { id: 'captions', label: 'Captions', icon: MessageSquare },
    { id: 'templates', label: 'Templates', icon: Sparkles },
    { id: 'video', label: 'AI Video', icon: Video },
    { id: 'voiceover', label: 'Voice Over', icon: Voice },
  ] as const;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-2 p-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="p-4">
        {activeTab === 'captions' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Language</label>
              <select
                value={captionLanguage}
                onChange={(e) => setCaptionLanguage(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="ja">Japanese</option>
                <option value="zh">Chinese</option>
              </select>
            </div>
            
            <button
              onClick={generateCaptions}
              disabled={!projectId || isLoading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? <Loader2 className="animate-spin" size={16} /> : <Wand2 size={16} />}
              Generate Captions
            </button>
            
            {jobStatus && (
              <div className={`flex items-center gap-2 p-2 rounded ${
                jobStatus === 'completed' ? 'bg-green-50 text-green-600' :
                jobStatus === 'failed' ? 'bg-red-50 text-red-600' :
                'bg-yellow-50 text-yellow-600'
              }`}>
                {jobStatus === 'completed' && <Check size={16} />}
                {jobStatus === 'failed' && <X size={16} />}
                {jobStatus === 'pending' && <Loader2 className="animate-spin" size={16} />}
                <span className="text-sm capitalize">{jobStatus}</span>
              </div>
            )}
            
            {captions.length > 0 && (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                <h4 className="text-sm font-medium">Generated Captions</h4>
                {captions.map((cap, i) => (
                  <div key={i} className="p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
                    <span className="text-xs text-gray-500">{cap.start}s - {cap.end}s</span>
                    <p>{cap.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'templates' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:border-blue-500 transition-colors cursor-pointer"
                  onClick={() => useTemplate(template.id)}
                >
                  {template.thumbnail_url ? (
                    <img src={template.thumbnail_url} alt={template.name} className="w-full h-24 object-cover" />
                  ) : (
                    <div className="w-full h-24 bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                      <Sparkles className="text-gray-400" />
                    </div>
                  )}
                  <div className="p-2">
                    <h4 className="text-sm font-medium truncate">{template.name}</h4>
                    <p className="text-xs text-gray-500 capitalize">{template.category}</p>
                    {template.is_premium && (
                      <span className="text-xs bg-yellow-500 text-white px-1 rounded">Premium</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'video' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Generation Type</label>
              <select
                value={videoType}
                onChange={(e) => setVideoType(e.target.value as 'text_to_video' | 'image_to_video')}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              >
                <option value="text_to_video">Text to Video</option>
                <option value="image_to_video">Image to Video</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Prompt</label>
              <textarea
                value={videoPrompt}
                onChange={(e) => setVideoPrompt(e.target.value)}
                placeholder="Describe the video you want to generate..."
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700 h-24 resize-none"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Duration: {videoDuration}s</label>
              <input
                type="range"
                min="3"
                max="10"
                value={videoDuration}
                onChange={(e) => setVideoDuration(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
            
            <button
              onClick={generateVideo}
              disabled={!projectId || !videoPrompt || isLoading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {isLoading ? <Loader2 className="animate-spin" size={16} /> : <Video size={16} />}
              Generate Video
            </button>
          </div>
        )}

        {activeTab === 'voiceover' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Voice</label>
              <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              >
                {voices.map((voice) => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name} ({voice.gender})
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Text</label>
              <textarea
                value={voiceText}
                onChange={(e) => setVoiceText(e.target.value)}
                placeholder="Enter the text to convert to voice..."
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700 h-32 resize-none"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Speed: {voiceSpeed}x</label>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                value={voiceSpeed}
                onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
            
            <button
              onClick={generateVoiceOver}
              disabled={!projectId || !voiceText || isLoading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {isLoading ? <Loader2 className="animate-spin" size={16} /> : <Voice size={16} />}
              Generate Voice Over
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
