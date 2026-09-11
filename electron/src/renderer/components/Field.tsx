export function Field({ label, value, onChange, placeholder, type = 'text' }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; type?: string }) {
  return <label className="block"><span className="mb-1.5 block text-xs text-slate-400">{label}</span><input type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className="field w-full" /></label>;
}
