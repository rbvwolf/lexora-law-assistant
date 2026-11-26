import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Download, FileText, FolderOpen, Info, Plus, ShieldCheck, Trash2 } from 'lucide-react';
import { downloadUrl } from '../lib/api';
import { clearDocuments, pruneExpired } from '../lib/documentStore';
import { formatRemaining } from '../lib/fields';
import DisclaimerBanner from './common/DisclaimerBanner';

const formatCreated = (iso) => {
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? ''
    : date.toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
};

/**
 * Documents generated in this browser tab (lib/documentStore). The backend deletes files after
 * DOCUMENT_TTL_MINUTES, so entries disappear from here when they expire.
 */
const DashboardArsiv = () => {
  const [documents, setDocuments] = useState(() => pruneExpired());
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(Date.now());
      setDocuments(pruneExpired());
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  const handleClear = () => {
    clearDocuments();
    setDocuments([]);
  };

  return (
    <div className="flex-1 bg-[#f8fafc] overflow-y-auto p-6 custom-scrollbar">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex flex-wrap justify-between items-start gap-4">
          <div>
            <h1 className="text-2xl font-bold text-navy flex items-center gap-2"><FolderOpen size={24} className="text-teal"/> Belgelerim</h1>
            <p className="text-sm text-slate-500 mt-1">Bu oturumda oluşturduğunuz belgeler. Dosyalar süre dolunca sunucudan otomatik silinir.</p>
          </div>
          <Link to="/app/sihirbaz" className="bg-navy text-white text-xs font-bold px-4 py-2.5 rounded-lg flex items-center gap-2 hover:bg-navy/90"><Plus size={14}/> Yeni belge oluştur</Link>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 text-xs text-slate-600 flex items-start gap-2">
          <ShieldCheck size={16} className="text-teal shrink-0"/>
          <span>KVKK gereği kişisel verileriniz kalıcı olarak saklanmaz. Bu listede yalnızca belge türü ve indirme bağlantısı tutulur; sekmeyi kapattığınızda liste de silinir.</span>
        </div>

        {documents.length === 0 ? (
          <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center">
            <div className="w-12 h-12 rounded-full bg-teal/10 text-teal flex items-center justify-center mx-auto mb-3"><FileText size={22}/></div>
            <p className="text-sm font-bold text-navy mb-1">Henüz belge oluşturmadınız</p>
            <p className="text-xs text-slate-500 mb-5">Sihirbazla oluşturduğunuz belgeler indirme süreleri boyunca burada görünür.</p>
            <Link to="/app/sihirbaz" className="inline-flex bg-teal text-white text-xs font-bold px-5 py-2.5 rounded-xl items-center gap-2 hover:bg-teal/90"><Plus size={14}/> Belge sihirbazını aç</Link>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="flex justify-between items-center px-4 py-3 border-b border-slate-100 bg-slate-50/50">
              <h3 className="text-sm font-bold text-navy">{documents.length} belge</h3>
              <button type="button" onClick={handleClear} className="text-[11px] font-bold text-slate-500 hover:text-red-600 flex items-center gap-1"><Trash2 size={12}/> Listeyi temizle</button>
            </div>
            <ul>
              {documents.map((doc) => {
                const remaining = formatRemaining(doc.expires_at, now);
                const soon = Date.parse(doc.expires_at) - now < 15 * 60000;
                return (
                  <li key={doc.file_id} className="flex flex-wrap items-center gap-4 px-4 py-4 border-b border-slate-50 last:border-b-0">
                    <div className="bg-teal/10 p-2 rounded-lg text-teal shrink-0"><FileText size={18}/></div>
                    <div className="flex-1 min-w-[200px]">
                      <p className="text-sm font-bold text-navy">{doc.title}</p>
                      <p className="text-[11px] text-slate-400">Oluşturuldu: {formatCreated(doc.created_at)}</p>
                    </div>
                    <span className={`text-[11px] font-bold px-2 py-1 rounded-full flex items-center gap-1 ${soon ? 'bg-red-50 text-red-600' : 'bg-slate-100 text-slate-600'}`}>
                      <Clock size={12}/> {remaining === 'süresi doldu' ? remaining : `${remaining} kaldı`}
                    </span>
                    <div className="flex gap-2">
                      <a href={downloadUrl(doc.docx_url)} download className="bg-navy hover:bg-navy/90 text-white text-[11px] font-bold px-3 py-2 rounded-lg flex items-center gap-1"><Download size={12}/> DOCX</a>
                      <a href={downloadUrl(doc.pdf_url)} download className="bg-white hover:bg-slate-50 border border-slate-200 text-navy text-[11px] font-bold px-3 py-2 rounded-lg flex items-center gap-1"><Download size={12}/> PDF</a>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5">
          <h4 className="text-sm font-bold text-navy mb-3 flex items-center gap-2"><Info size={16} className="text-teal"/> İhtarnamenizi nasıl gönderirsiniz?</h4>
          <ol className="space-y-2 text-xs text-slate-600 list-decimal pl-5 leading-relaxed">
            <li>Belgeyi indirip bilgileri kontrol edin; gerekirse Word dosyası üzerinde düzenleyin.</li>
            <li>İhtarnameyi imzalayıp bir noter aracılığıyla karşı tarafa tebliğ ettirin.</li>
            <li>Tebliğ şerhli nüshayı saklayın; ileride delil olarak gerekebilir.</li>
          </ol>
        </div>

        <DisclaimerBanner variant="inline" />
      </div>
    </div>
  );
};

export default DashboardArsiv;
