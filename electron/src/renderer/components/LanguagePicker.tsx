import { Globe } from 'lucide-react';
import { useState } from 'react';
import { IconButton } from './IconButton';
import { localeOptions, useI18n, type Locale } from '../i18n/i18n';

export function LanguagePicker() {
  const [open, setOpen] = useState(false);
  const { t, locale, setLocale } = useI18n();
  return <div className="relative">
    <IconButton label={t('switchLanguage')} aria-expanded={open} onClick={() => setOpen((value) => !value)} className="text-slate-400 hover:bg-slate-800 hover:text-slate-100"><Globe size={17} /></IconButton>
    {open && <div className="absolute right-0 top-11 z-50 min-w-40 rounded-md border border-slate-700 bg-slate-900 p-1 shadow-xl">
      {localeOptions.map((option) => <button key={option.code} onClick={() => { setLocale(option.code as Locale); setOpen(false); }} className={`flex w-full items-center rounded px-3 py-2 text-left text-xs ${locale === option.code ? 'bg-slate-800 text-cyan-300' : 'text-slate-300 hover:bg-slate-800'}`}>
        {option.name}
      </button>)}
    </div>}
  </div>;
}
