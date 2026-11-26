import { Calculator, CheckCircle2, AlertTriangle } from 'lucide-react';
import { formatTrNumber, hesaplaKiraArtisi } from '../../lib/fields';

/** TBK m. 344 ceiling from the values the user typed (same formula and rounding as doc_service). */
const KiraArtisCalculator = ({ values }) => {
  const calc = hesaplaKiraArtisi(values.mevcut_kira_tutari, values.talep_edilen_kira_tutari, values.tufe_oran);

  return (
    <div className="bg-slate-50 rounded-xl p-4 border border-slate-200" aria-live="polite">
      <div className="flex flex-wrap justify-between items-center gap-2 mb-4">
        <div className="flex items-center gap-2 text-teal font-bold text-sm"><Calculator size={16} /> TBK m. 344 yasal tavan hesabı</div>
        {calc && <div className="text-[10px] font-bold text-slate-500 bg-white px-2 py-1 rounded border">TÜFE 12 aylık ort.: %{formatTrNumber(calc.tufe)}</div>}
      </div>
      {!calc ? (
        <p className="text-xs text-slate-500">Mevcut kira, talep edilen kira ve TÜFE oranını girdiğinizde yasal azami kira burada hesaplanır.</p>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-white p-3 rounded-lg border">
              <p className="text-[10px] text-slate-500 font-bold mb-1">Yasal azami kira</p>
              <p className="text-lg font-bold text-navy">{formatTrNumber(calc.azami)} TL</p>
              <p className="text-[10px] text-teal font-bold">+{formatTrNumber(calc.azami - calc.mevcut)} TL</p>
            </div>
            <div className={`p-3 rounded-lg border ${calc.asiyor ? 'bg-red-50 border-red-200' : 'bg-white'}`}>
              <p className={`text-[10px] font-bold mb-1 ${calc.asiyor ? 'text-red-500' : 'text-slate-500'}`}>Sınırı aşan kısım</p>
              <p className={`text-lg font-bold ${calc.asiyor ? 'text-red-600' : 'text-navy'}`}>{formatTrNumber(Math.max(calc.fazlaTutar, 0))} TL</p>
              <p className="text-[10px] text-slate-500 font-bold">Talep edilen artış: %{formatTrNumber(calc.talepArtisOrani)}</p>
            </div>
            <div className="bg-teal/10 p-3 rounded-lg border border-teal/20">
              <p className="text-[10px] text-teal font-bold mb-1">İhtarda bildirilecek kira</p>
              <p className="text-lg font-bold text-navy">{formatTrNumber(calc.azami)} TL</p>
            </div>
          </div>
          <p className={`mt-3 text-xs font-medium flex items-center gap-1.5 ${calc.asiyor ? 'text-teal' : 'text-amber-700'}`}>
            {calc.asiyor
              ? <><CheckCircle2 size={14} /> Talep yasal sınırı aşıyor; itiraz ihtarnamesi hazırlanabilir.</>
              : <><AlertTriangle size={14} /> Talep yasal sınırın altında; bu ihtarname bu durumda uygun değildir.</>}
          </p>
        </>
      )}
    </div>
  );
};

export default KiraArtisCalculator;
