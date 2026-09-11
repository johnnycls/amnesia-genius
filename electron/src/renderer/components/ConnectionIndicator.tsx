import { LoaderCircle, Wifi, WifiOff } from 'lucide-react';
import type { ServerState } from '../../shared/types';
import { useI18n } from '../i18n/i18n';
import { Tooltip } from './Tooltip';

export function ConnectionIndicator({ state }: { state: ServerState }) {
  const { t } = useI18n();
  const ready = state.status === 'ready';
  const starting = state.status === 'starting';
  const label = ready ? t('serverReady') : starting ? t('serverStarting') : state.status === 'error' ? t('serverError') : t('serverStopped');
  return <Tooltip label={label}><span aria-label={label} className={`grid size-9 place-items-center rounded-md border ${ready ? 'border-emerald-900 bg-emerald-950/40 text-emerald-300' : state.status === 'error' ? 'border-rose-900 bg-rose-950/40 text-rose-300' : 'border-slate-700 bg-slate-900 text-slate-400'}`}>
    {ready ? <Wifi size={15} /> : starting ? <LoaderCircle size={15} className="animate-spin" /> : <WifiOff size={15} />}
  </span></Tooltip>;
}
