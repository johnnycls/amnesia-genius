import { contextBridge, ipcRenderer } from 'electron';
import type { DesktopApi, ServerEvent, ServerState } from './src/shared/types.js';

const api: DesktopApi = {
  server: {
    start: () => ipcRenderer.invoke('server:start'),
    stop: () => ipcRenderer.invoke('server:stop'),
    status: () => ipcRenderer.invoke('server:status'),
    onStatus: (listener: (state: ServerState) => void) => {
      const handler = (_event: Electron.IpcRendererEvent, state: ServerState) => listener(state);
      ipcRenderer.on('server:status-changed', handler);
      return () => ipcRenderer.removeListener('server:status-changed', handler);
    },
  },
  api: {
    request: (method, path, body) => ipcRenderer.invoke('api:request', { method, path, body }),
    startTurn: (text: string) => ipcRenderer.invoke('turn:start', text),
    cancelTurn: () => ipcRenderer.invoke('turn:cancel'),
    onTurnEvent: (listener: (event: ServerEvent) => void) => {
      const handler = (_event: Electron.IpcRendererEvent, value: ServerEvent) => listener(value);
      ipcRenderer.on('turn:event', handler);
      return () => ipcRenderer.removeListener('turn:event', handler);
    },
  },
};

contextBridge.exposeInMainWorld('desktop', api);
