export type View = 'chat' | 'workspace' | 'history' | 'settings';

export type ServerStatus = 'stopped' | 'starting' | 'ready' | 'error';

export interface ServerHealth {
  status: string;
  active_turn: boolean;
  api_version: string;
  instance_id: string | null;
}

export interface ServerState {
  status: ServerStatus;
  error?: string;
  health?: ServerHealth;
}

export interface Config {
  model: string;
  api_key: null;
  api_key_set: boolean;
  base_url: string | null;
  provider_params: Record<string, unknown>;
  command_timeout_seconds: number;
  max_command_output_bytes: number;
  max_context_message_chars: number;
}

export interface ServerEvent {
  type: 'delta' | 'assistant' | 'tool_call' | 'tool_result' | 'error' | 'done';
  data: Record<string, unknown>;
}

export interface HistoryRecord {
  role?: string;
  content?: string;
  [key: string]: unknown;
}

export interface DesktopApi {
  server: {
    start(): Promise<ServerState>;
    stop(): Promise<void>;
    status(): Promise<ServerState>;
    onStatus(listener: (state: ServerState) => void): () => void;
  };
  api: {
    request<T = Record<string, unknown>>(
      method: 'GET' | 'PUT' | 'POST',
      path: string,
      body?: unknown,
    ): Promise<T>;
    startTurn(text: string): Promise<void>;
    cancelTurn(): Promise<void>;
    onTurnEvent(listener: (event: ServerEvent) => void): () => void;
  };
}

declare global {
  interface Window {
    desktop: DesktopApi;
  }
}
