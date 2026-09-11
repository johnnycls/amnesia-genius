import { app, BrowserWindow, ipcMain } from 'electron';
import { join } from 'node:path';
import { LocalServerProcess } from './server.js';
import type { ServerEvent } from './src/shared/types.js';

let window: BrowserWindow | null = null;
let quitting = false;
let turnAbort: AbortController | null = null;
const server = new LocalServerProcess();

function createWindow(): void {
  window = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 560,
    minHeight: 520,
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  const devUrl = process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:5173';
  if (!app.isPackaged) void window.loadURL(devUrl);
  else void window.loadFile(join(app.getAppPath(), 'dist', 'index.html'));
  window.on('closed', () => { window = null; });
}

function sendTurnEvent(event: ServerEvent): void {
  window?.webContents.send('turn:event', event);
}

server.onStatus((state) => window?.webContents.send('server:status-changed', state));

ipcMain.handle('server:start', () => server.start());
ipcMain.handle('server:stop', () => server.stop());
ipcMain.handle('server:status', () => server.getState());
ipcMain.handle('api:request', (_event, request: { method: 'GET' | 'PUT' | 'POST'; path: string; body?: unknown }) => server.request(request.method, request.path, request.body));
ipcMain.handle('turn:start', async (_event, text: string) => {
  if (turnAbort) throw new Error('A turn is already active.');
  turnAbort = new AbortController();
  const active = turnAbort;
  void server.startTurn(text, sendTurnEvent, active.signal)
    .catch((error: unknown) => {
      if (!active.signal.aborted) {
        const message = error instanceof Error ? error.message : String(error);
        sendTurnEvent({ type: 'error', data: { error_type: 'ClientError', message } });
      }
    })
    .finally(() => { if (turnAbort === active) turnAbort = null; });
});
ipcMain.handle('turn:cancel', () => { turnAbort?.abort(); turnAbort = null; });

app.whenReady().then(() => {
  createWindow();
  if (process.env.AMNESIA_AGENT_AUTOSTART !== 'false') void server.start().catch(() => undefined);
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('before-quit', (event) => {
  if (quitting) return;
  event.preventDefault();
  quitting = true;
  turnAbort?.abort();
  void server.stop().finally(() => app.exit(0));
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
