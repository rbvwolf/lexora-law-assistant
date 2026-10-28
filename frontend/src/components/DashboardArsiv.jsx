import React from 'react';
import { Link } from 'react-router-dom';
import { 
  FolderOpen, FileLock2, FileText, Scale, History, AlertOctagon, 
  Clock, Plus, Download, RefreshCw, CheckCircle2, AlertTriangle, 
  Search, Send 
} from 'lucide-react';

const DashboardArsiv = () => {
  
  // Belge indirme simülasyon fonksiyonu
  const handleDownload = (format) => {
    alert(`Belge ${format.toUpperCase()} formatında indiriliyor...\n\n(Not: Bu bir önizleme bildirimidir, backend API'si bağlandığında dosyalar doğrudan cihazınıza inecektir.)`);
    // İleride buraya gelecek kod örneği:
    // api.downloadDocument(documentId, format);
  };

  return (
    <div className="flex-1 bg-[#f8fafc] flex flex-col overflow-hidden">
       <div className="bg-white border-b border-slate-200 p-6 shrink-0">
          <div className="max-w-7xl mx-auto">
             <div className="flex justify-between items-center mb-6">
                <div>
                  <h1 className="text-2xl font-bold text-navy flex items-center gap-2">
                    <FolderOpen size={24} className="text-teal"/> Hukuki Belgeler & Arşiv Yönetimi
                  </h1>
                  <p className="text-sm text-slate-500 mt-1">Tüm UYAP (.udf), PDF ve Word dökümanlarınızı tek merkezden izleyin ve tebligat sürelerini yönetin.</p>
                </div>
                <div className="hidden md:flex items-center gap-2 text-xs font-bold text-slate-500 bg-slate-50 border border-slate-200 px-3 py-2 rounded-lg">
                  <FileLock2 size={16} className="text-teal"/> E-İmza Uyumlu Arşiv
                </div>
             </div>

             <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm"><div className="flex justify-between items-start mb-2"><p className="text-[10px] font-bold text-slate-400 tracking-widest">TOPLAM ÜRETİLEN</p><FileText size={18} className="text-navy"/></div><div className="flex items-end gap-2 mb-2"><span className="text-3xl font-bold text-navy leading-none">18</span></div><p className="text-[10px] font-bold text-teal">+4 yeni bu ay</p></div>
                <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm"><div className="flex justify-between items-start mb-2"><p className="text-[10px] font-bold text-teal tracking-widest">UYAP HAZIR</p><Scale size={18} className="text-teal"/></div><div className="flex items-end gap-2 mb-2"><span className="text-3xl font-bold text-navy leading-none">12</span></div><p className="text-[10px] font-bold text-slate-500">UYAP Editör v5.4.1</p></div>
                <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm"><div className="flex justify-between items-start mb-2"><p className="text-[10px] font-bold text-blue-500 tracking-widest">İŞLEMDE OLAN</p><History size={18} className="text-blue-500"/></div><div className="flex items-end gap-2 mb-2"><span className="text-3xl font-bold text-navy leading-none">3</span></div><p className="text-[10px] font-bold text-slate-500">2 Taslak, 1 Noter</p></div>
                <div className="bg-red-50 border border-red-100 p-4 rounded-2xl shadow-sm relative overflow-hidden"><div className="absolute -right-4 -top-4 text-red-500/10"><AlertOctagon size={80}/></div><div className="flex justify-between items-start mb-2 relative z-10"><p className="text-[10px] font-bold text-red-600 tracking-widest">KRİTİK SÜRE</p><Clock size={18} className="text-red-600"/></div><div className="flex items-end gap-2 mb-2 relative z-10"><span className="text-3xl font-bold text-red-600 leading-none">1</span><span className="text-xs text-red-600 font-bold mb-0.5">İtiraz (Kalan: 3 Gün!)</span></div></div>
             </div>
          </div>
       </div>

       <div className="flex-1 flex overflow-hidden max-w-7xl mx-auto w-full">
          <div className="flex-1 flex flex-col p-6 border-r border-slate-200 bg-[#f8fafc] overflow-hidden">
             <div className="flex justify-between items-center mb-4 shrink-0">
                <div className="flex gap-2 overflow-x-auto custom-scrollbar pb-1">
                  <button className="bg-navy text-white text-xs font-bold px-4 py-2 rounded-full shrink-0">Tümü (18)</button>
                  <button className="bg-white border border-slate-200 text-slate-600 text-xs font-bold px-4 py-2 rounded-full shrink-0">İhtarnameler (5)</button>
                  <button className="bg-white border border-slate-200 text-slate-600 text-xs font-bold px-4 py-2 rounded-full shrink-0">Dilekçeler (6)</button>
                </div>
                <Link to="/app/sihirbaz" className="hidden md:flex bg-navy text-white text-xs font-bold px-4 py-2 rounded-lg items-center gap-2 shrink-0"><Plus size={14}/> Yeni Belge Üret</Link>
             </div>

             <div className="bg-white border border-slate-200 rounded-2xl flex-1 flex flex-col overflow-hidden shadow-sm">
                <div className="flex justify-between items-center p-4 border-b border-slate-100 bg-slate-50/50"><h3 className="text-sm font-bold text-navy">Kayıtlı Hukuki Dosyalar</h3><div className="flex gap-2 text-slate-400"><Download size={16}/><RefreshCw size={16}/></div></div>
                <div className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-slate-100 bg-slate-50 text-[10px] font-bold text-slate-400 tracking-widest shrink-0">
                  <div className="col-span-4">BELGE ADI & TÜRÜ</div><div className="col-span-3">MUHATAP / KURUM</div><div className="col-span-2">HUKUKİ DAYANAK</div><div className="col-span-1">TARİH</div><div className="col-span-2 text-right pr-2">DURUM</div>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar">
                   {/* Row 1 */}
                   <div className="grid grid-cols-12 gap-4 px-4 py-4 border-b border-slate-50 items-center bg-teal/5 border-l-2 border-l-teal">
                     <div className="col-span-4 flex items-start gap-3"><div className="bg-white border border-teal/20 p-2 rounded-lg text-teal shrink-0 mt-0.5"><FileText size={16}/></div><div><p className="text-sm font-bold text-navy mb-0.5">Kira Artış Oranına İtiraz İhtarnamesi</p><p className="text-[10px] text-slate-400">İhtarname • Noter Formatı</p></div></div>
                     <div className="col-span-3"><p className="text-xs font-bold text-navy mb-0.5">Ahmet Y***</p><p className="text-[10px] text-slate-500">(Ev Sahibi)</p></div>
                     <div className="col-span-2"><span className="bg-slate-100 text-slate-600 text-[10px] font-bold px-2 py-1 rounded">TBK m. 344</span></div>
                     <div className="col-span-1"><p className="text-xs text-slate-600 font-medium">14 Eki</p><p className="text-[10px] text-slate-400">2024</p></div>
                     <div className="col-span-2 flex justify-end"><span className="bg-teal/10 text-teal text-[10px] font-bold px-2 py-1 rounded-full flex items-center gap-1"><CheckCircle2 size={10}/> Hazır & Onaylandı</span></div>
                   </div>
                   {/* Row 2 */}
                   <div className="grid grid-cols-12 gap-4 px-4 py-4 border-b border-slate-50 items-center bg-red-50/30 cursor-pointer transition-colors">
                     <div className="col-span-4 flex items-start gap-3"><div className="bg-red-100 border border-red-200 p-2 rounded-lg text-red-600 shrink-0 mt-0.5"><AlertTriangle size={16}/></div><div><p className="text-sm font-bold text-red-700 mb-0.5">İlamsız İcra Takibine Yetki ve Borca İtiraz</p><div className="flex items-center gap-1 text-[10px] font-bold"><span className="text-slate-500">İtiraz Dilekçesi • </span><span className="bg-red-500 text-white px-1.5 py-0.5 rounded">SÜRE KRİTİK</span></div></div></div>
                     <div className="col-span-3"><p className="text-xs font-bold text-navy mb-0.5">İstanbul 14. İcra Dairesi</p></div>
                     <div className="col-span-2"><span className="bg-red-50 text-red-600 border border-red-100 text-[10px] font-bold px-2 py-1 rounded">İİK m. 62</span></div>
                     <div className="col-span-1"><p className="text-xs font-bold text-red-600">Bugün</p><p className="text-[10px] font-bold text-red-500">(Son 3 Gün)</p></div>
                     <div className="col-span-2 flex justify-end"><span className="bg-red-600 text-white text-[10px] font-bold px-3 py-1.5 rounded-full flex items-center gap-1 shadow-sm"><Clock size={12} className="animate-pulse"/> Kalan: 3 Gün</span></div>
                   </div>
                </div>
             </div>
          </div>

          <div className="w-80 lg:w-[400px] bg-white flex flex-col shrink-0 overflow-y-auto custom-scrollbar">
             <div className="p-6">
                <div className="flex justify-between items-start mb-6"><div><h2 className="text-lg font-bold text-navy flex items-center gap-2 mb-2"><FileText size={20}/> İlamsız İcra Takibine Yetki ve Borca İtiraz</h2><span className="bg-red-100 text-red-700 text-[10px] font-bold px-2 py-1 rounded inline-flex items-center gap-1"><AlertTriangle size={10}/> İCRA İTİRAZ • SÜRE KRİTİK</span></div></div>

                <div className="w-full aspect-[1/1.414] bg-slate-50 border border-slate-200 shadow-sm p-4 overflow-hidden text-[6px] font-serif text-slate-600 mb-6 relative group cursor-pointer">
                   <div className="absolute inset-0 bg-navy/50 opacity-0 group-hover:opacity-100 transition-opacity flex justify-center items-center backdrop-blur-[1px]"><span className="bg-white text-navy font-bold text-xs px-4 py-2 rounded-lg flex items-center gap-2"><Search size={14}/> Büyüt</span></div>
                   <div className="text-center font-bold mb-4 mt-2">T.C. İSTANBUL 14. İCRA MÜDÜRLÜĞÜ'NE</div>
                   <div className="flex justify-between mb-4"><div className="space-y-1 w-1/2"><p><span className="font-bold">DOSYA ESAS:</span> ESAS NO: 2024/8492 E.</p><p><span className="font-bold">İTİRAZ EDEN:</span> T. Yılmaz (T.C: 284****10)</p></div></div>
                   <p className="font-bold mb-2">KONU: Yetki, Borç, Faiz ve Tüm Fer'ilerine İtiraz</p>
                   <p className="indent-4 text-justify leading-relaxed mb-2">Müdürlüğünüzce tanzim ve tebliğ olunan mezkur ödeme emrine karşı yasal 7 günlük süre içerisinde itirazlarımızı sunuyoruz. Takip konusu borcun tamamına, faizine ve fer'ilerine açıkça itiraz etmekteyim. İkametgahımın İstanbul dışında bulunması sebebiyle ilgili icra müdürlüğü yetkisizdir.</p>
                </div>

                {/* ONCLICK EKLENEN İNDİRME BUTONLARI */}
                <div className="grid grid-cols-3 gap-2 mb-8">
                  <button onClick={() => handleDownload('udf')} className="bg-teal hover:bg-teal/90 text-white text-[10px] font-bold py-2 rounded-lg flex justify-center items-center gap-1 shadow-sm transition-colors"><Download size={12}/> .UDF İndir</button>
                  <button onClick={() => handleDownload('pdf')} className="bg-white hover:bg-slate-50 border border-slate-200 text-navy text-[10px] font-bold py-2 rounded-lg flex justify-center items-center gap-1 transition-colors"><Download size={12}/> PDF İndir</button>
                  <button onClick={() => handleDownload('docx')} className="bg-white hover:bg-slate-50 border border-slate-200 text-navy text-[10px] font-bold py-2 rounded-lg flex justify-center items-center gap-1 transition-colors"><Download size={12}/> DOCX</button>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-navy mb-4 flex items-center gap-2"><Send size={16} className="text-teal"/> Resmi Gönderim & Takip</h4>
                  <div className="space-y-4 relative before:absolute before:inset-0 before:ml-[11px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-slate-100 mb-6">
                     <div className="relative flex items-start justify-start gap-3"><div className="bg-navy text-white w-6 h-6 rounded-full flex items-center justify-center shrink-0 z-10 text-[10px] font-bold shadow-sm">1</div><div className="flex-1 bg-white border border-slate-100 rounded-xl p-3 shadow-sm z-10"><h5 className="text-xs font-bold text-navy mb-1">UYAP Vatandaş / Avukat Portalı</h5><p className="text-[10px] text-slate-500 leading-relaxed">İndirilen .udf uzantılı dosyayı portal üzerinden doğrudan sisteme yükleyip e-İmza ile imzalayabilirsiniz.</p></div></div>
                     <div className="relative flex items-start justify-start gap-3"><div className="bg-teal text-white w-6 h-6 rounded-full flex items-center justify-center shrink-0 z-10 text-[10px] font-bold shadow-sm">2</div><div className="flex-1 bg-white border border-slate-100 rounded-xl p-3 shadow-sm z-10"><h5 className="text-xs font-bold text-navy mb-1">Noter veya PTT APS Tebliği</h5><p className="text-[10px] text-slate-500 leading-relaxed">İhtarnameler için 3 nüsha çıktı alınız. En yakın Noterlik veya PTT İadeli Taahhütlü servisi barkodu sisteme işlenmelidir.</p></div></div>
                  </div>
                  <div className="bg-red-50 border border-red-100 rounded-xl p-4"><h5 className="text-xs font-bold text-red-700 flex items-center gap-1.5 mb-1"><AlertTriangle size={14}/> Hak Düşürücü Süre Hatırlatması</h5><p className="text-[10px] text-red-800 leading-relaxed">İcra tebligatı elinize ulaştığı tarihten itibaren itiraz süresi 7 gündür.</p></div>
                </div>
             </div>
          </div>
       </div>
    </div>
  );
};

export default DashboardArsiv;