import { useId } from 'react';
import { AlertCircle, Lock } from 'lucide-react';
import { formatIban } from '../../lib/fields';

const INPUT_BASE = 'w-full border rounded-lg p-2.5 text-sm outline-none transition-colors focus:border-teal focus:bg-white';

const SUFFIX = {
  number: (name) => (/oran/.test(name) ? '%' : /tutar|kira|bedel/.test(name) ? '₺' : null),
};

/**
 * One form input generated from a TemplateFieldSchema.
 * Sensitive fields (tc_id, iban) get autocomplete off and a lock badge; their values stay in
 * component state and go only to /documents/generate.
 */
const FieldInput = ({ field, value, error, onChange, onBlur, sensitive = false }) => {
  const id = useId();
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const suffix = SUFFIX[field.field_type]?.(field.field_name);
  const isSensitiveType = field.field_type === 'tc_id' || field.field_type === 'iban';
  const isLong = field.field_type === 'string' && /adres|ozet|özet|aciklama|açıklama|durum/.test(field.field_name);

  const common = {
    id,
    name: field.field_name,
    value: value ?? '',
    onBlur,
    required: field.required,
    'aria-invalid': error ? true : undefined,
    'aria-describedby': [error ? errorId : null, field.description ? hintId : null].filter(Boolean).join(' ') || undefined,
    className: `${INPUT_BASE} ${error ? 'border-red-300 bg-red-50' : 'border-slate-200 bg-slate-50'} ${suffix ? 'pr-10' : ''}`,
  };

  let control;
  if (field.field_type === 'date') {
    control = <input type="date" {...common} onChange={(e) => onChange(e.target.value)} />;
  } else if (field.field_type === 'number') {
    control = <input type="text" inputMode="decimal" autoComplete="off" {...common} onChange={(e) => onChange(e.target.value)} />;
  } else if (field.field_type === 'tc_id') {
    control = (
      <input type="text" inputMode="numeric" autoComplete="off" maxLength={11} placeholder="11 haneli" {...common}
        onChange={(e) => onChange(e.target.value.replace(/\D/g, '').slice(0, 11))} />
    );
  } else if (field.field_type === 'iban') {
    control = (
      <input type="text" autoComplete="off" spellCheck={false} placeholder="TR00 0000 0000 0000 0000 0000 00" maxLength={32} {...common}
        value={formatIban(value ?? '')}
        onChange={(e) => onChange(e.target.value.replace(/\s+/g, '').toUpperCase().slice(0, 26))} />
    );
  } else if (isLong) {
    control = <textarea rows={2} maxLength={500} {...common} className={`${common.className} resize-y`} onChange={(e) => onChange(e.target.value)} />;
  } else {
    control = <input type="text" maxLength={500} autoComplete={sensitive ? 'off' : undefined} {...common} onChange={(e) => onChange(e.target.value)} />;
  }

  return (
    <div className={isLong ? 'sm:col-span-2' : undefined}>
      <label htmlFor={id} className="text-[11px] font-bold text-slate-500 mb-1 flex items-center gap-1">
        {field.label}
        {field.required ? <span className="text-red-500" aria-hidden="true">*</span> : <span className="font-normal text-slate-400">(isteğe bağlı)</span>}
        {isSensitiveType && <Lock size={11} className="text-teal ml-auto" aria-label="Hassas veri" />}
      </label>
      <div className="relative">
        {control}
        {suffix && <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs pointer-events-none">{suffix}</span>}
      </div>
      {field.description && <p id={hintId} className="text-[10px] text-slate-400 mt-1 leading-relaxed">{field.description}</p>}
      {error && <p id={errorId} className="text-[11px] text-red-600 mt-1 flex items-center gap-1"><AlertCircle size={12} className="shrink-0" /> {error}</p>}
    </div>
  );
};

export default FieldInput;
