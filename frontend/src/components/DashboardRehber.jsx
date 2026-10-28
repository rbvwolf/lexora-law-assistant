import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, ShieldCheck, Network, Building2, Briefcase, Scale, 
  Landmark, Info, Clock, AlertTriangle, Gavel, Calendar, 
  Calculator, ArrowRight, FileText 
} from 'lucide-react';

const DashboardRehber = () => {
  return (
    <div className="flex-1 bg-[#f8fafc] overflow-y-auto custom-scrollbar">
       <div className="bg-white border-b border-slate-200 px-6 py-8">
          <div className="max-w-7xl mx-auto text-center">
             <span className="text-[10px] font-bold text-teal bg-teal/10 border border-teal/20 px-3 py-1 rounded-full mb-4 inline-flex items-center gap-1"><ShieldCheck size={12}/> T.C. Mevzuatı ve Güncel Yargıtay İçtihatları Rehberi</span>
             <div className="relative max-w-2xl mx-auto mb-4">
               <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
               <input type="text" placeholder="Hangi konudaki haklarınızı öğrenmek istiyorsunuz? (Örn: İşten çıkarılma)" className="w-full pl-12 pr-32 py-4 rounded-xl border border-slate-200 shadow-sm text-sm outline-none focus:border-teal" />
               <button className="absolute right-2 top-1/2 -translate-y-1/2 bg-navy text-white px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1">Rehberde Ara <ArrowRight size={14}/></button>
             </div>
             <div className="flex flex-wrap justify-center gap-2 text-[10px] font-bold">
                <span className="text-slate-400">Öne Çıkan Başlıklar:</span>
                <span className="text-teal bg-teal/5 px-2 py-1 rounded"># KiraHukuku</span>
                <span className="text-slate-500 bg-slate-100 px-2 py-1 rounded"># İşçiHakları</span>
                <span className="text-slate-500 bg-slate-100 px-2 py-1 rounded"># TüketiciMevzuatı</span>
             </div>
          </div>
       </div>

       <div className="p-6 max-w-7xl mx-auto flex flex-col lg:flex-row gap-6">
          <div className="w-full lg:w-64 shrink-0">
             <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 sticky top-6">
                <h3 className="text-xs font-bold text-slate-500 mb-4 flex items-center gap-2"><Network size={16}/> Hukuk Konu Ağacı</h3>
                <nav className="space-y-1">
                  <a href="#" className="flex justify-between items-center px-3 py-2.5 rounded-lg bg-teal/5 text-teal font-bold text-sm border border-teal/10"><span className="flex items-center gap-2"><Building2 size={16}/> Kiracı & Ev Sahibi</span><span className="bg-teal/20 px-2 py-0.5 rounded text-[10px]">18</span></a>
                  <a href="#" className="flex justify-between items-center px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 text-sm font-medium"><span className="flex items-center gap-2"><Briefcase size={16}/> İşten Çıkarma</span><span className="bg-slate-100 px-2 py-0.5 rounded text-[10px]">14</span></a>
                  <a href="#" className="flex justify-between items-center px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 text-sm font-medium"><span className="flex items-center gap-2"><Scale size={16}/> Arabuluculuk Şartı</span><span className="bg-slate-100 px-2 py-0.5 rounded text-[10px]">8</span></a>
                  <a href="#" className="flex justify-between items-center px-3 py-2.5 rounded-lg text-slate-600 hover:bg-slate-50 text-sm font-medium"><span className="flex items-center gap-2"><Landmark size={16}/> Baro Adli Yardım</span><span className="bg-slate-100 px-2 py-0.5 rounded text-[10px]">Rehber</span></a>
                </nav>
                <div className="mt-6 bg-blue-50 border border-blue-100 p-3 rounded-xl"><p className="text-[10px] font-bold text-blue-800 flex items-center gap-1 mb-1"><Info size={12}/> Biliyor muydunuz?</p><p className="text-[10px] text-blue-700 leading-relaxed">WhatsApp veya e-posta mesajları, HMK m. 199 uyarınca "belge" delili niteliği taşır.</p></div>
             </div>
          </div>
          <div className="flex-1">
             <div className="text-[10px] font-bold text-slate-400 mb-4 flex gap-2"><span>Rehberler</span> {'>'} <span>Kira Hukuku</span> {'>'} <span className="text-teal">Tahliye Şartları</span></div>
             <h1 className="text-2xl md:text-3xl font-bold text-navy mb-4">Ev Sahibi Kiracıyı Hangi Şartlarda Çıkarabilir?</h1>
             <p className="text-sm text-slate-500 mb-8">Türk Borçlar Kanunu kapsamında konut ve çatılı işyeri kira sözleşmelerinin sona erdirilmesi ve tahliye davası açma kuralları.</p>
             <div className="bg-white border-l-4 border-navy shadow-sm rounded-r-2xl p-6 mb-8 flex gap-4 items-start">
                <div className="bg-slate-100 w-8 h-8 rounded flex justify-center items-center font-bold text-navy shrink-0">=</div>
                <div>
                  <h4 className="font-bold text-navy mb-2">3 Cümlede Durumunuz (Sade Özet)</h4>
                  <ol className="list-decimal pl-4 space-y-2 text-sm text-slate-600 leading-relaxed">
                    <li>Sözleşme süresi bitti diye ev sahibi kiracıyı <strong>hemen kapıya koyamaz</strong>; kiracı çıkmak istemezse sözleşme her yıl otomatik uzar.</li>
                    <li>Ev sahibi ancak <strong>kendisi veya 1. derece yakınının samimi konut ihtiyacı</strong> varsa veya aynı kira yılında <strong>2 haklı ihtar</strong> çekmişse dava açabilir.</li>
                    <li>Kiracı 10 yıllık uzama süresini doldurmuşsa, ev sahibi herhangi bir sebep göstermeksizin en az 3 ay önceden bildirim yaparak sözleşmeyi feshedebilir.</li>
                  </ol>
                </div>
             </div>
             <h4 className="font-bold text-navy flex items-center gap-2 mb-4"><ShieldCheck size={18} className="text-teal"/> Kritik Kanun Maddeleri ve Yargıtay Kararları</h4>
             <div className="space-y-4 mb-8">
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                  <div className="flex justify-between items-start mb-2"><h5 className="font-bold text-sm text-navy">TBK M. 350 / 1 — İHTİYAÇ SEBEBİYLE TAHLİYE</h5><Info size={16} className="text-slate-400"/></div>
                  <p className="text-xs text-slate-600 mb-3">"Kiraya veren, kiralananı kendisi, eşi, altsoyu, üstsoyu veya kanun gereği bakmakla yükümlü olduğu diğer kişiler için konut gereksinimi sebebiyle kullanma zorunluluğu varsa..."</p>
                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 text-xs text-slate-500 italic"><strong>Emsal Yargıtay 3. H.D. (2022/4119 E.):</strong> İhtiyaç iddiasının samimi, zorunlu ve devamlı olması gerekir. Henüz doğmamış şüpheli ihtiyaçlar tahliye gerekçesi yapılamaz.</div>
                </div>
             </div>
             <div className="bg-navy rounded-2xl p-8 text-white flex justify-between items-center shadow-lg">
               <div><h4 className="font-bold text-lg mb-2">Bu Konuda Dilekçenizi Hazırlayın</h4><p className="text-xs text-slate-400">Lexora AI ile T.C. HMK standartlarına uygun Tahliye veya Cevap Dilekçenizi oluşturun.</p></div>
               <Link to="/app/sihirbaz" className="bg-teal hover:bg-teal/90 text-white font-bold py-3 px-6 rounded-xl flex items-center gap-2 transition-colors shrink-0"><FileText size={18}/> Dilekçeyi Hazırla</Link>
             </div>
          </div>
          <div className="w-full lg:w-72 shrink-0 space-y-6">
             <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
               <h3 className="font-bold text-navy text-sm flex items-center gap-2 mb-4"><Clock size={16} className="text-red-500"/> Hak Düşürücü Süreler</h3>
               <p className="text-xs text-slate-500 mb-4">Hukukta sürelerin kaçırılması hak kaybına ve davanın usulden reddine neden olur.</p>
               <div className="space-y-3">
                 <div className="bg-red-50 border border-red-100 p-3 rounded-lg"><div className="flex justify-between items-center mb-1"><span className="text-[10px] font-bold text-red-600 flex items-center gap-1"><AlertTriangle size={12}/> İŞÇİ HAKLARI</span><span className="text-[10px] font-bold text-red-600 bg-white px-2 py-0.5 rounded">30 Gün</span></div><p className="text-[10px] text-red-800">Fesih bildiriminin tebliğinden itibaren 30 gün içinde zorunlu arabulucuya başvurulmalıdır.</p></div>
                 <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg"><div className="flex justify-between items-center mb-1"><span className="text-[10px] font-bold text-navy flex items-center gap-1"><Gavel size={12}/> İCRA & TAKİP</span><span className="text-[10px] font-bold text-navy bg-white px-2 py-0.5 rounded border">7 Gün</span></div><p className="text-[10px] text-slate-600">Ödeme emri tebliğ edildiği günden sonraki 7 gün içinde icra dairesine itiraz verilmelidir.</p></div>
               </div>
             </div>
             <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
               <h3 className="font-bold text-navy text-sm flex items-center gap-2 mb-4"><Calendar size={16} className="text-teal"/> Akıllı Süre Hesaplayıcı</h3>
               <div className="space-y-3">
                 <div><label className="text-[10px] font-bold text-slate-500 block mb-1">Uyuşmazlık Türü</label><select className="w-full text-xs border rounded-lg p-2 outline-none bg-slate-50"><option>İlamsız İcra Ödeme Emri (7 Gün)</option></select></div>
                 <div><label className="text-[10px] font-bold text-slate-500 block mb-1">Tebliğ Tarihi</label><input type="date" className="w-full text-xs border rounded-lg p-2 outline-none bg-slate-50" /></div>
                 <button className="w-full bg-navy text-white text-xs font-bold py-2.5 rounded-lg flex justify-center items-center gap-2"><Calculator size={14}/> Son Günü Hesapla</button>
               </div>
             </div>
          </div>
       </div>
    </div>
  );
};

export default DashboardRehber;