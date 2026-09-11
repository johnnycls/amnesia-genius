import { app } from 'electron';
import { existsSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { join } from 'node:path';
import { spawn, type ChildProcess } from 'node:child_process';
import { SseParser } from './src/shared/sse.js';
import type { ServerEvent, ServerHealth, ServerState } from './src/shared/types.js';

export const HOST = '127.0.0.1';
export const PORT = 8765;
const STARTUP_TIMEOUT_MS = 15_000;

type StatusListener = (state: ServerState) => void;

export class LocalServerProcess {
  private child: ChildProcess | null = null;
  private state: ServerState = { status: 'stopped' };
  private readonly listeners = new Set<StatusListener>();
  private instanceId: string | null = null;
  private startPromise: Promise<ServerState> | null = null;

  onStatus(listener: StatusListener): () => void {
    this.listeners.add(listener);
    listener(this.state);
    return () => this.listeners.delete(listener);
  }

  getState(): ServerState {
    return this.state;
  }

  async start(): Promise<ServerState> {
    if (this.state.status === 'ready') return this.state;
    if (this.startPromise) return this.startPromise;
    this.startPromise = this.startInternal();
    try {
      return await this.startPromise;
    } finally {
      this.startPromise = null;
    }
  }

  private async startInternal(): Promise<ServerState> {
    this.setState({ status: 'starting' });
    this.instanceId = randomUUID();
    const command = this.resolveCommand();
    try {
      this.child = spawn(command.file, command.args, {
        cwd: app.getAppPath(),
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
        stdio: ['ignore', 'ignore', 'pipe'],
        windowsHide: true,
      });
      this.child.stderr?.on('data', (chunk: Buffer) => {
        console.warn(`[local-server] ${chunk.toString().trim()}`);
      });
      this.child.once('exit', () => {
        if (this.state.status !== 'stopped') this.setState({ status: 'error', error: 'Local server exited.' });
      });
      const health = await this.waitForHealth();
      this.setState({ status: 'ready', health });
      return this.state;
    } catch (error) {
      await this.killChild();
      const message = error instanceof Error ? error.message : String(error);
      this.setState({ status: 'error', error: message });
      throw error;
    }
  }

  async stop(): Promise<void> {
    if (!this.child) {
      this.setState({ status: 'stopped' });
      return;
    }
    this.setState({ status: 'stopped' });
    try {
      await fetch(this.url('/v1/shutdown'), { method: 'POST', signal: AbortSignal.timeout(1000) });
    } catch {
      // The process may already have exited; the kill below is still scoped to our child.
    }
    await this.killChild();
  }

  async request<T>(method: 'GET' | 'PUT' | 'POST', path: string, body?: unknown): Promise<T> {
    if (!path.startsWith('/v1/')) throw new Error('Only /v1 API paths are allowed.');
    const response = await fetch(this.url(path), {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const raw = await response.text();
    let payload: unknown = {};
    try {
      payload = raw ? JSON.parse(raw) : {};
    } catch {
      throw new Error(`Server returned invalid JSON (${response.status}).`);
    }
    if (!response.ok) {
      const detail = payload && typeof payload === 'object' && 'detail' in payload ? String(payload.detail) : response.statusText;
      throw new Error(detail || `Server request failed (${response.status}).`);
    }
    return payload as T;
  }

  async startTurn(text: string, send: (event: ServerEvent) => void, signal: AbortSignal): Promise<void> {
    const response = await fetch(this.url('/v1/turn'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream', 'Cache-Control': 'no-cache' },
      body: JSON.stringify({ text }),
      signal,
    });
    if (!response.ok || !response.body) {
      const raw = await response.text();
      throw new Error(raw || `Turn request failed (${response.status}).`);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const parser = new SseParser();
    try {
      while (true) {
        const result = await reader.read();
        parser.push(decoder.decode(result.value, { stream: !result.done })).forEach(send);
        if (result.done) break;
      }
      parser.finish().forEach(send);
    } finally {
      reader.releaseLock();
    }
  }

  private async waitForHealth(): Promise<ServerHealth> {
    const deadline = Date.now() + STARTUP_TIMEOUT_MS;
    let lastError = 'Local server did not become ready.';
    while (Date.now() < deadline) {
      if (this.child?.exitCode !== null && this.child?.exitCode !== undefined) throw new Error('Local server exited before becoming ready.');
      try {
        const health = await this.request<ServerHealth>('GET', '/v1/health');
        if (health.instance_id !== this.instanceId) throw new Error(`Port ${PORT} is occupied by another local server.`);
        return health;
      } catch (error) {
        lastError = error instanceof Error ? error.message : String(error);
        await new Promise((resolve) => setTimeout(resolve, 150));
      }
    }
    throw new Error(lastError);
  }

  private resolveCommand(): { file: string; args: string[] } {
    const sidecar = this.sidecarPath();
    if (existsSync(sidecar)) return { file: sidecar, args: ['--host', HOST, '--port', String(PORT), '--instance-id', this.instanceId!] };
    const python = process.env.AMNESIA_AGENT_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
    return { file: python, args: ['-m', 'amnesia_agent_local_server', '--host', HOST, '--port', String(PORT), '--instance-id', this.instanceId!] };
  }

  private sidecarPath(): string {
    const executable = process.platform === 'win32' ? 'amnesia-agent-local-server.exe' : 'amnesia-agent-local-server';
    const root = app.isPackaged ? process.resourcesPath : join(app.getAppPath(), 'resources', 'server');
    return app.isPackaged ? join(root, 'server', executable) : join(root, executable);
  }

  private url(path: string): string {
    return `http://${HOST}:${PORT}${path}`;
  }

  private setState(state: ServerState): void {
    this.state = state;
    this.listeners.forEach((listener) => listener(state));
  }

  private async killChild(): Promise<void> {
    const child = this.child;
    this.child = null;
    if (!child || child.exitCode !== null) return;
    child.kill();
    await new Promise<void>((resolve) => {
      const timer = setTimeout(() => { child.kill('SIGKILL'); resolve(); }, 2000);
      child.once('exit', () => { clearTimeout(timer); resolve(); });
    });
  }
}
