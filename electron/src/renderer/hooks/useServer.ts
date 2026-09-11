import { useEffect, useState } from 'react';
import type { ServerState } from '../../shared/types';

export function useServer(onReady: () => Promise<void>) {
  const [server, setServer] = useState<ServerState>({ status: 'starting' });
  const [notice, setNotice] = useState('');
  useEffect(() => {
    const remove = window.desktop.server.onStatus((state) => { setServer(state); if (state.status === 'error') setNotice(state.error ?? 'The local server could not start.'); });
    void window.desktop.server.start().then((state) => { setServer(state); if (state.status === 'ready') void onReady().catch((error: unknown) => setNotice(error instanceof Error ? error.message : String(error))); }).catch((error: unknown) => setNotice(error instanceof Error ? error.message : String(error)));
    return remove;
  }, [onReady]);
  return { server, setServer, notice, setNotice };
}
