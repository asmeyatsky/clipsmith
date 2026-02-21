'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { 
  Sliders, Volume2, Sparkles, Key, Palette, 
  ChevronDown, ChevronUp, Play, Pause
} from 'lucide-react';

interface ColorGradeSettings {
  brightness: number;
  contrast: number;
  saturation: number;
  temperature: number;
  tint: number;
  highlights: number;
  shadows: number;
  vibrance: number;
  filters: string[];
}

interface AudioMixSettings {
  volume: number;
  pan: number;
  mute: boolean;
  solo: boolean;
  fade_in: number;
  fade_out: number;
  equalizer: { low: number; mid: number; high: number };
  audio_effects: string[];
  duck_others: boolean;
}

interface ChromaKeySettings {
  enabled: boolean;
  key_color: string;
  similarity: number;
  smoothness: number;
  spill_suppression: number;
  background_type: string;
  background_value: string;
}

interface Keyframe {
  id: string;
  property_name: string;
  time: number;
  value: number | number[];
  easing: string;
}

interface Effect {
  id: string;
  effect_type: string;
  parameters: Record<string, unknown>;
  start_time: number;
  end_time: number;
  enabled: boolean;
}

interface AdvancedEditorPanelsProps {
  projectId: string;
  trackId: string;
}

export function AdvancedEditorPanels({ projectId, trackId }: AdvancedEditorPanelsProps) {
  const [activePanel, setActivePanel] = useState<string | null>(null);
  const [colorGrade, setColorGrade] = useState<ColorGradeSettings>({
    brightness: 0, contrast: 0, saturation: 0, temperature: 0,
    tint: 0, highlights: 0, shadows: 0, vibrance: 0, filters: []
  });
  const [audioMix, setAudioMix] = useState<AudioMixSettings>({
    volume: 1, pan: 0, mute: false, solo: false,
    fade_in: 0, fade_out: 0,
    equalizer: { low: 0, mid: 0, high: 0 },
    audio_effects: [], duck_others: false
  });
  const [chromaKey, setChromaKey] = useState<ChromaKeySettings>({
    enabled: false, key_color: '#00FF00', similarity: 0.4,
    smoothness: 0.1, spill_suppression: 0.1,
    background_type: 'none', background_value: ''
  });
  const [keyframes, setKeyframes] = useState<Keyframe[]>([]);
  const [effects, setEffects] = useState<Effect[]>([]);

  useEffect(() => {
    if (trackId && projectId) {
      loadColorGrade();
      loadAudioMix();
      loadChromaKey();
      loadKeyframes();
      loadEffects();
    }
  }, [trackId, projectId]);

  const loadColorGrade = async () => {
    try {
      const data = await apiClient<ColorGradeSettings>(
        `/api/editor/projects/${projectId}/tracks/${trackId}/color-grade`
      );
      setColorGrade(data);
    } catch (e) { console.error('Error loading color grade:', e); }
  };

  const saveColorGrade = async () => {
    try {
      await apiClient(`/api/editor/projects/${projectId}/tracks/${trackId}/color-grade`, {
        method: 'POST',
        body: JSON.stringify(colorGrade)
      });
    } catch (e) { console.error('Error saving color grade:', e); }
  };

  const loadAudioMix = async () => {
    try {
      const data = await apiClient<AudioMixSettings>(
        `/api/editor/projects/${projectId}/tracks/${trackId}/audio-mix`
      );
      setAudioMix(data);
    } catch (e) { console.error('Error loading audio mix:', e); }
  };

  const saveAudioMix = async () => {
    try {
      await apiClient(`/api/editor/projects/${projectId}/tracks/${trackId}/audio-mix`, {
        method: 'POST',
        body: JSON.stringify(audioMix)
      });
    } catch (e) { console.error('Error saving audio mix:', e); }
  };

  const loadChromaKey = async () => {
    try {
      const data = await apiClient<ChromaKeySettings>(
        `/api/editor/projects/${projectId}/tracks/${trackId}/chroma-key`
      );
      setChromaKey(data);
    } catch (e) { console.error('Error loading chroma key:', e); }
  };

  const saveChromaKey = async () => {
    try {
      await apiClient(`/api/editor/projects/${projectId}/tracks/${trackId}/chroma-key`, {
        method: 'POST',
        body: JSON.stringify(chromaKey)
      });
    } catch (e) { console.error('Error saving chroma key:', e); }
  };

  const loadKeyframes = async () => {
    try {
      const data = await apiClient<{ keyframes: Keyframe[] }>(
        `/api/editor/projects/${projectId}/tracks/${trackId}/keyframes`
      );
      setKeyframes(data.keyframes || []);
    } catch (e) { console.error('Error loading keyframes:', e); }
  };

  const loadEffects = async () => {
    try {
      const data = await apiClient<{ effects: Effect[] }>(
        `/api/editor/projects/${projectId}/tracks/${trackId}/effects`
      );
      setEffects(data.effects || []);
    } catch (e) { console.error('Error loading effects:', e); }
  };

  const addKeyframe = async (property: string, time: number, value: number) => {
    try {
      await apiClient(`/api/editor/projects/${projectId}/tracks/${trackId}/keyframes`, {
        method: 'POST',
        body: JSON.stringify({ property_name: property, time, value })
      });
      loadKeyframes();
    } catch (e) { console.error('Error adding keyframe:', e); }
  };

  const addEffect = async (effectType: string) => {
    try {
      await apiClient(`/api/editor/projects/${projectId}/tracks/${trackId}/effects`, {
        method: 'POST',
        body: JSON.stringify({
          effect_type: effectType,
          parameters: {},
          start_time: 0,
          end_time: 10
        })
      });
      loadEffects();
    } catch (e) { console.error('Error adding effect:', e); }
  };

  const SliderControl = ({ label, value, min, max, onChange, onCommit }: {
    label: string; value: number; min: number; max: number;
    onChange: (v: number) => void; onCommit: () => void
  }) => (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-500">{label}</span>
        <span className="text-gray-700 dark:text-gray-300">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        onMouseUp={onCommit}
        onTouchEnd={onCommit}
        className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
      />
    </div>
  );

  const Panel = ({ id, title, icon: Icon, children }: {
    id: string; title: string; icon: React.ElementType; children: React.ReactNode
  }) => (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setActivePanel(activePanel === id ? null : id)}
        className="w-full flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700"
      >
        <div className="flex items-center gap-2">
          <Icon size={16} />
          <span className="font-medium text-sm">{title}</span>
        </div>
        {activePanel === id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {activePanel === id && (
        <div className="p-3 space-y-3 bg-white dark:bg-gray-900">
          {children}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-2">
      <Panel id="color" title="Color Grading" icon={Palette}>
        <SliderControl
          label="Brightness" value={colorGrade.brightness} min={-100} max={100}
          onChange={(v) => setColorGrade({ ...colorGrade, brightness: v })}
          onCommit={saveColorGrade}
        />
        <SliderControl
          label="Contrast" value={colorGrade.contrast} min={-100} max={100}
          onChange={(v) => setColorGrade({ ...colorGrade, contrast: v })}
          onCommit={saveColorGrade}
        />
        <SliderControl
          label="Saturation" value={colorGrade.saturation} min={-100} max={100}
          onChange={(v) => setColorGrade({ ...colorGrade, saturation: v })}
          onCommit={saveColorGrade}
        />
        <SliderControl
          label="Temperature" value={colorGrade.temperature} min={-100} max={100}
          onChange={(v) => setColorGrade({ ...colorGrade, temperature: v })}
          onCommit={saveColorGrade}
        />
        <SliderControl
          label="Highlights" value={colorGrade.highlights} min={-100} max={100}
          onChange={(v) => setColorGrade({ ...colorGrade, highlights: v })}
          onCommit={saveColorGrade}
        />
        <SliderControl
          label="Shadows" value={colorGrade.shadows} min={-100} max={100}
          onChange={(v) => setColorGrade({ ...colorGrade, shadows: v })}
          onCommit={saveColorGrade}
        />
      </Panel>

      <Panel id="audio" title="Audio Mixing" icon={Volume2}>
        <SliderControl
          label="Volume" value={audioMix.volume} min={0} max={2}
          onChange={(v) => setAudioMix({ ...audioMix, volume: v })}
          onCommit={saveAudioMix}
        />
        <SliderControl
          label="Pan" value={audioMix.pan} min={-1} max={1}
          onChange={(v) => setAudioMix({ ...audioMix, pan: v })}
          onCommit={saveAudioMix}
        />
        <SliderControl
          label="Fade In" value={audioMix.fade_in} min={0} max={5}
          onChange={(v) => setAudioMix({ ...audioMix, fade_in: v })}
          onCommit={saveAudioMix}
        />
        <SliderControl
          label="Fade Out" value={audioMix.fade_out} min={0} max={5}
          onChange={(v) => setAudioMix({ ...audioMix, fade_out: v })}
          onCommit={saveAudioMix}
        />
        <div className="flex gap-2">
          <button
            onClick={() => { setAudioMix({ ...audioMix, mute: !audioMix.mute }); saveAudioMix(); }}
            className={`px-3 py-1 text-xs rounded ${audioMix.mute ? 'bg-red-500 text-white' : 'bg-gray-200 dark:bg-gray-700'}`}
          >
            Mute
          </button>
          <button
            onClick={() => { setAudioMix({ ...audioMix, solo: !audioMix.solo }); saveAudioMix(); }}
            className={`px-3 py-1 text-xs rounded ${audioMix.solo ? 'bg-yellow-500 text-white' : 'bg-gray-200 dark:bg-gray-700'}`}
          >
            Solo
          </button>
          <button
            onClick={() => { setAudioMix({ ...audioMix, duck_others: !audioMix.duck_others }); saveAudioMix(); }}
            className={`px-3 py-1 text-xs rounded ${audioMix.duck_others ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-700'}`}
          >
            Duck
          </button>
        </div>
      </Panel>

      <Panel id="chroma" title="Chroma Key" icon={Key}>
        <div className="flex items-center justify-between">
          <span className="text-sm">Enable Chroma Key</span>
          <input
            type="checkbox"
            checked={chromaKey.enabled}
            onChange={(e) => { setChromaKey({ ...chromaKey, enabled: e.target.checked }); saveChromaKey(); }}
            className="rounded"
          />
        </div>
        {chromaKey.enabled && (
          <>
            <div className="space-y-1">
              <label className="text-xs text-gray-500">Key Color</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={chromaKey.key_color}
                  onChange={(e) => setChromaKey({ ...chromaKey, key_color: e.target.value })}
                  className="w-8 h-8 rounded"
                />
                <input
                  type="text"
                  value={chromaKey.key_color}
                  onChange={(e) => setChromaKey({ ...chromaKey, key_color: e.target.value })}
                  className="flex-1 px-2 py-1 text-sm border rounded"
                />
              </div>
            </div>
            <SliderControl
              label="Similarity" value={chromaKey.similarity} min={0} max={1}
              onChange={(v) => setChromaKey({ ...chromaKey, similarity: v })}
              onCommit={saveChromaKey}
            />
            <SliderControl
              label="Smoothness" value={chromaKey.smoothness} min={0} max={1}
              onChange={(v) => setChromaKey({ ...chromaKey, smoothness: v })}
              onCommit={saveChromaKey}
            />
            <div className="space-y-1">
              <label className="text-xs text-gray-500">Background</label>
              <select
                value={chromaKey.background_type}
                onChange={(e) => setChromaKey({ ...chromaKey, background_type: e.target.value })}
                className="w-full px-2 py-1 text-sm border rounded"
              >
                <option value="none">None (Transparent)</option>
                <option value="color">Solid Color</option>
                <option value="image">Image</option>
                <option value="video">Video</option>
              </select>
            </div>
          </>
        )}
      </Panel>

      <Panel id="keyframes" title="Keyframes" icon={Key}>
        <div className="space-y-2">
          <div className="flex gap-2">
            <select id="kf-property" className="flex-1 px-2 py-1 text-sm border rounded">
              <option value="opacity">Opacity</option>
              <option value="scale">Scale</option>
              <option value="position">Position</option>
              <option value="rotation">Rotation</option>
            </select>
            <button
              onClick={() => {
                const prop = (document.getElementById('kf-property') as HTMLSelectElement).value;
                addKeyframe(prop, 0, 100);
              }}
              className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Add
            </button>
          </div>
          {keyframes.length > 0 ? (
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {keyframes.map((kf) => (
                <div key={kf.id} className="flex justify-between text-xs p-1 bg-gray-100 dark:bg-gray-800 rounded">
                  <span>{kf.property_name}</span>
                  <span>{kf.time}s: {JSON.stringify(kf.value)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500">No keyframes added yet</p>
          )}
        </div>
      </Panel>

      <Panel id="effects" title="Effects" icon={Sparkles}>
        <div className="grid grid-cols-2 gap-2">
          {['blur', 'sharpen', 'glow', 'vignette', 'noise', 'pixelate'].map((effect) => (
            <button
              key={effect}
              onClick={() => addEffect(effect)}
              className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600 capitalize"
            >
              {effect}
            </button>
          ))}
        </div>
        {effects.length > 0 && (
          <div className="space-y-1 mt-2 max-h-32 overflow-y-auto">
            {effects.map((eff) => (
              <div key={eff.id} className="flex justify-between text-xs p-1 bg-gray-100 dark:bg-gray-800 rounded">
                <span className="capitalize">{eff.effect_type}</span>
                <span className={eff.enabled ? 'text-green-500' : 'text-gray-400'}>
                  {eff.enabled ? 'Active' : 'Disabled'}
                </span>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
