import { useCallback, useEffect, useRef, useState } from 'react';
import type { Config, View } from '../../shared/types';
import { useAgentData } from '../hooks/useAgentData';
import { useChat } from '../hooks/useChat';
import { useServer } from '../hooks/useServer';
import { parsePositiveInteger, parsePositiveNumber, parseProviderParams } from '../lib/validation';
import { configToForm } from '../lib/settings';
import { useI18n } from '../i18n/i18n';
import { AppShell } from '../layout/AppShell';
import { ChatView } from '../features/chat/ChatView';
import { HistoryView } from '../features/history/HistoryView';
import { SettingsView } from '../features/settings/SettingsView';
import { WorkspaceView } from '../features/workspace/WorkspaceView';

export function App() {
  const [view, setView] = useState<View>('chat');
  const { t } = useI18n();
  const data = useAgentData();
  const onReady = useCallback(() => data.loadAppData(), [data.loadAppData]);
  const { server, notice, setNotice } = useServer(onReady);
  const chat = useChat(server.status, data.loadWorkspace);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const saveContent = useCallback(async (path: string, content: string, label: string) => { data.setWorkspaceBusy(true); try { await window.desktop.api.request('PUT', path, { content }); setNotice(t('savedMessage', { name: label })); } catch (error) { setNotice(error instanceof Error ? error.message : String(error)); } finally { data.setWorkspaceBusy(false); } }, [data, setNotice, t]);
  const resetContent = useCallback(async (path: string, setter: (content: string) => void, label: string) => { if (!window.confirm(t('resetConfirm', { name: label }))) return; data.setWorkspaceBusy(true); try { const result = await window.desktop.api.request<{ content: string }>('POST', path); setter(result.content); setNotice(t('resetMessage', { name: label })); } catch (error) { setNotice(error instanceof Error ? error.message : String(error)); } finally { data.setWorkspaceBusy(false); } }, [data, setNotice, t]);
  const saveSettings = useCallback(async () => { try { const body: Record<string, unknown> = { model: data.settings.model.trim(), base_url: data.settings.baseUrl.trim() || null, provider_params: parseProviderParams(data.settings.providerParams, t('invalidJson')), command_timeout_seconds: parsePositiveNumber(data.settings.timeout, t('positiveNumber', { label: t('commandTimeout') })), max_command_output_bytes: parsePositiveInteger(data.settings.outputLimit, t('positiveInteger', { label: t('maxOutput') })), max_context_message_chars: parsePositiveInteger(data.settings.contextLimit, t('positiveInteger', { label: t('maxContext') })) }; if (data.settings.apiKey.trim()) body.api_key = data.settings.apiKey.trim(); const updated = await window.desktop.api.request<Config>('PUT', '/v1/config', body); data.setConfig(updated); data.setSettings(configToForm(updated)); setNotice(t('settingsSaved')); } catch (error) { setNotice(error instanceof Error ? error.message : String(error)); } }, [data, setNotice, t]);
  const resetSettings = useCallback(async () => { if (!window.confirm(t('resetConfirm', { name: t('settings') }))) return; try { const updated = await window.desktop.api.request<Config>('POST', '/v1/config/reset'); data.setConfig(updated); data.setSettings(configToForm(updated)); setNotice(t('settingsRestored')); } catch (error) { setNotice(error instanceof Error ? error.message : String(error)); } }, [data, setNotice, t]);
  const loadHistory = useCallback(async (date: string) => { try { await data.loadHistory(date); } catch (error) { setNotice(error instanceof Error ? error.message : String(error)); } }, [data.loadHistory, setNotice]);
  const resetHistory = useCallback(async () => { if (!window.confirm(t('clearHistoryConfirm'))) return; try { await window.desktop.api.request('POST', '/v1/workspace/history/reset'); data.setDates([]); data.setSelectedDate(''); data.setHistoryRecords([]); setNotice(t('clearHistory')); } catch (error) { setNotice(error instanceof Error ? error.message : String(error)); } }, [data, setNotice, t]);

  let content: import('react').ReactNode;
  if (view === 'chat') content = <ChatView {...chat} ready={server.status === 'ready'} inputRef={inputRef} />;
  if (view === 'workspace') content = <WorkspaceView systemPrompt={data.systemPrompt} memory={data.memory} setSystemPrompt={data.setSystemPrompt} setMemory={data.setMemory} saveContent={saveContent} resetContent={resetContent} busy={data.workspaceBusy} />;
  if (view === 'history') content = <HistoryView dates={data.dates} selectedDate={data.selectedDate} records={data.historyRecords} loadHistory={loadHistory} resetHistory={resetHistory} />;
  if (view === 'settings') content = <SettingsView form={data.settings} setForm={data.setSettings} config={data.config} save={saveSettings} reset={resetSettings} />;
  return <AppShell view={view} setView={setView} server={server} notice={notice} setNotice={setNotice}>{content}</AppShell>;
}
