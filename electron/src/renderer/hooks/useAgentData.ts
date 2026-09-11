import { useCallback, useState } from 'react';
import type { Config, HistoryRecord } from '../../shared/types';
import { configToForm, emptySettings, type SettingsForm } from '../lib/settings';

export function useAgentData() {
  const [config, setConfig] = useState<Config | null>(null);
  const [settings, setSettings] = useState<SettingsForm>(emptySettings);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [memory, setMemory] = useState('');
  const [dates, setDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [historyRecords, setHistoryRecords] = useState<HistoryRecord[]>([]);
  const [workspaceBusy, setWorkspaceBusy] = useState(false);

  const loadWorkspace = useCallback(async () => {
    const [prompt, storedMemory, history] = await Promise.all([
      window.desktop.api.request<{ content: string }>('GET', '/v1/workspace/system-prompt'),
      window.desktop.api.request<{ content: string }>('GET', '/v1/workspace/memory'),
      window.desktop.api.request<{ dates: string[] }>('GET', '/v1/workspace/history'),
    ]);
    setSystemPrompt(prompt.content); setMemory(storedMemory.content); setDates(history.dates);
  }, []);
  const loadAppData = useCallback(async () => { const [loadedConfig] = await Promise.all([window.desktop.api.request<Config>('GET', '/v1/config'), loadWorkspace()]); setConfig(loadedConfig); setSettings(configToForm(loadedConfig)); }, [loadWorkspace]);
  const loadHistory = useCallback(async (date: string) => { const result = await window.desktop.api.request<{ date: string; messages: HistoryRecord[] }>('GET', `/v1/workspace/history/${date}`); setSelectedDate(result.date); setHistoryRecords(result.messages); }, []);
  return { config, setConfig, settings, setSettings, systemPrompt, setSystemPrompt, memory, setMemory, dates, setDates, selectedDate, setSelectedDate, historyRecords, setHistoryRecords, workspaceBusy, setWorkspaceBusy, loadWorkspace, loadAppData, loadHistory };
}
