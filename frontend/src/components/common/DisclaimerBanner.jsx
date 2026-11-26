import { ShieldAlert } from 'lucide-react';
import { DISCLAIMER_TEXT } from '../../lib/constants';

/**
 * Legal disclaimer, required on every output screen.
 * variant="bar": full-width strip under the dashboard header (always visible).
 * variant="inline": compact note inside a card (document preview, download result).
 */
const DisclaimerBanner = ({ variant = 'bar', text = DISCLAIMER_TEXT }) => {
  if (variant === 'inline') {
    return (
      <p role="note" className="text-[11px] text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 flex items-start gap-2">
        <ShieldAlert size={14} className="shrink-0 mt-px" aria-hidden="true" />
        <span>{text} Üretilen belge bir taslaktır; göndermeden önce bir avukata kontrol ettirmeniz önerilir.</span>
      </p>
    );
  }
  return (
    <div role="note" className="bg-amber-50 border-b border-amber-200 text-amber-800 text-xs px-6 py-2 flex items-center gap-2 shrink-0">
      <ShieldAlert size={14} className="shrink-0" aria-hidden="true" />
      <span className="font-bold">Yasal uyarı:</span>
      <span>{text}</span>
    </div>
  );
};

export default DisclaimerBanner;
