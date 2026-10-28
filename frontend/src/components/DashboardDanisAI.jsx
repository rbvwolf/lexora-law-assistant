import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Plus, FolderOpen, ShieldCheck, FileText, Eye, Database, 
  Network, Lock, Download, Scale, Mail, Landmark, Paperclip, 
  Mic, Send, Bot, BookOpen, CheckCircle2, ArrowRight 
} from 'lucide-react';

const DashboardDanisAI = () => {
  return (
    <div className="flex-1 bg-[#f8fafc] flex overflow-hidden">
      <div className="w-72 bg-white border-r border-slate-200 flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-200"><button className="w-full bg-navy text-white text-sm font-bold py-2.5 rounded-xl flex justify-center items-center gap-2 hover:bg-navy/90"><Plus size={16}/> Yeni Hukuki Soru Başlat</button></div>
        <div className="p-4 flex-1 overflow-y-auto custom-scrollbar">
           <div className="flex justify-between items-center mb-4"><span className="text-[10px] font-bold text-slate-400 tracking-widest">HUKUKİ OTURUMLAR</span><span className="text-[10px] font-bold text-teal">3 Aktif Dosya</span></div>
           <div className="space-y-2 mb-6">
             <div className="bg-teal/5 border border-teal/20 p-3 rounded-xl cursor-pointer"><div className="flex justify-between items-center mb-1"><span className="text-[10px] font-bold text-teal bg-teal/10 px-2 py-0.5 rounded flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-teal"></div> Kira Hukuku</span><span className="text-[10px] text-slate-400">14 dk önce</span></div><p className="text-xs font-bold text-navy mb-1 truncate">Kira Artış Oranı ve Sözle...</p><p className="text-[10px] text-slate-500 truncate">TBK m. 344 artış limiti ve...</p></div>
             <div className="bg-slate-50 border border-slate-100 p-3 rounded-xl cursor-pointer hover:bg-slate-100"><div className="flex justify-between items-center mb-1"><span className="text-[10px] font-bold text-slate-500 bg-slate-200 px-2 py-0.5 rounded">İş Hukuku</span><span className="text-[10px] text-slate-400">Dün</span></div><p className="text-xs font-bold text-navy mb-1 truncate">İhbar Süresi Kullandırıl...</p><p className="text-[10px] text-slate-500 truncate">4857 SK m. 17 tazminat...</p></div>
           </div>
           <div className="bg-teal/5 border border-teal/20 p-4 rounded-xl mb-6"><div className="flex items-center gap-2 mb-2"><ShieldCheck className="text-teal" size={18}/><span className="text-xs font-bold text-navy">Uçtan Uca Maskeleme Açık</span></div><p className="text-[10px] text-slate-500 mb-3">TCKN, IBAN ve isimler sunucuya iletilmeden istemci tarafında filtrelenir.</p></div>
           <div className="mb-2"><span className="text-[10px] font-bold text-slate-400 tracking-widest flex items-center gap-1"><FolderOpen size={12}/> İlişkili Dosyalar (1)</span></div>
           <div className="bg-white border border-slate-200 p-2.5 rounded-lg flex justify-between items-center text-xs"><div className="flex items-center gap-2"><FileText size={14} className="text-red-500"/><span className="text-navy font-medium truncate w-32">Kira_Sozlesmesi_2024.pdf</span></div><Eye size={14} className="text-slate-400 cursor-pointer"/></div>
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-[#f8fafc]">
        <div className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-6 shrink-0">
          <div className="flex gap-4 text-xs font-bold text-slate-500"><span className="flex items-center gap-1"><Database size={14} className="text-teal"/> Mevzuat Veritabanı: <span className="text-navy">Resmi Gazete v2025.02 (Güncel)</span></span><span className="flex items-center gap-1"><Network size={14} className="text-teal"/> UYAP Emsal Karar Ağı Entegre</span></div>
          <div className="flex gap-4 text-xs font-bold"><span className="flex items-center gap-1 text-teal"><Lock size={14}/> Gizlilik Kalkanı: Aktif</span><span className="flex items-center gap-1 text-slate-500 hover:text-navy cursor-pointer"><Download size={14}/> Mütalaayı İndir</span></div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
           <div className="flex justify-end">
             <div className="max-w-[80%]">
               <div className="flex justify-end items-center gap-2 mb-1"><span className="text-xs font-bold text-slate-500">Siz (Müvekkil Modu)</span><div className="w-6 h-6 rounded-full bg-navy text-white text-[10px] font-bold flex justify-center items-center">K</div></div>
               <div className="bg-navy text-white p-4 rounded-2xl rounded-tr-none text-sm leading-relaxed shadow-md">Ev sahibim kira sözleşmemin 1 yılı dolduğu için kiramı 12.000 TL'den 25.000 TL'ye çıkarmak istiyor. Kabul etmezsem haftaya çıkmamı söyledi. Ne yapmalıyım?</div>
             </div>
           </div>

           <div className="flex justify-start">
             <div className="max-w-[90%]">
               <div className="flex items-center gap-2 mb-2"><div className="w-8 h-8 rounded-full bg-teal flex justify-center items-center text-white"><Scale size={16}/></div><span className="text-xs font-bold text-navy">Danış AI Hukuk Mütalaası</span><span className="text-[10px] text-slate-400">• Motor v4.2</span><span className="text-[10px] font-bold text-teal bg-teal/10 px-2 py-0.5 rounded ml-2">Kesin Hukuki Koruma</span></div>
               <div className="bg-white border border-slate-200 p-5 rounded-2xl rounded-tl-none shadow-sm space-y-5">
                  <div>
                    <h4 className="text-sm font-bold text-navy mb-2 flex items-center gap-2"><div className="w-5 h-5 rounded-full bg-navy text-white text-[10px] flex justify-center items-center">1</div> Hukuki Durum Tespiti & Tahliye Geçersizliği</h4>
                    <p className="text-sm text-slate-600 leading-relaxed pl-7"><span className="font-bold text-navy">TBK m. 347</span> gereğince, konut ve çatılı işyeri kira sözleşmelerinde sözleşme süresinin (1 yılın) dolması gerekçesiyle <span className="font-bold">kiraya verenin tek taraflı fesih ve tahliye hakkı bulunmamaktadır.</span> Ev sahibinizin <i>"haftaya evi boşaltın"</i> ihtarı kanunen hükümsüzdür.</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-navy mb-2 flex items-center gap-2"><div className="w-5 h-5 rounded-full bg-navy text-white text-[10px] flex justify-center items-center">2</div> Kira Artış Oranı Tavanı</h4>
                    <p className="text-sm text-slate-600 leading-relaxed pl-7 mb-3"><span className="font-bold text-navy">TBK m. 344/1</span> hükmünce yenilenen kira dönemlerinde uygulanabilecek azami zam oranı, <span className="font-bold">TÜİK tarafından açıklanan son 12 aylık TÜFE ortalamasıdır.</span></p>
                    <div className="ml-7 bg-slate-50 border border-slate-100 rounded-xl p-4 flex justify-between items-center">
                      <div><p className="text-[10px] font-bold text-slate-500 mb-1">Mevcut Kira Bedeli</p><p className="text-lg font-bold text-navy">12.000 ₺</p></div>
                      <div><p className="text-[10px] font-bold text-teal mb-1">Yasal Tavan Tahmini (%62,5)</p><p className="text-lg font-bold text-teal">~19.501 ₺</p></div>
                      <div className="text-right"><p className="text-[10px] font-bold text-red-500 mb-1">Ev Sahibinin Talebi</p><p className="text-lg font-bold text-red-500 line-through">25.000 ₺</p></div>
                    </div>
                  </div>
                  <div className="pl-7">
                    <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-2">DAYANAK KANUN MADDELERİ</p>
                    <div className="flex gap-2 flex-wrap">
                      <span className="text-xs font-bold text-teal bg-teal/5 border border-teal/10 px-2 py-1.5 rounded-lg flex items-center gap-1"><Scale size={12}/> TBK Madde 344</span>
                      <span className="text-xs font-bold text-teal bg-teal/5 border border-teal/10 px-2 py-1.5 rounded-lg flex items-center gap-1"><Scale size={12}/> TBK Madde 347</span>
                    </div>
                  </div>
                  <div className="pl-7 border-t border-slate-100 pt-4">
                    <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-3">TAVSİYE EDİLEN SOMUT HUKUKİ ADIMLAR:</p>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-blue-50/50 border border-blue-100 p-4 rounded-xl"><h5 className="text-xs font-bold text-navy mb-1 flex items-center gap-1"><Mail size={14} className="text-blue-600"/> 1. İtiraz İhtarnamesi Keşide Edin</h5><p className="text-[11px] text-slate-600 leading-relaxed">Fahiş kira artışını kabul etmediğinizi noter kanalıyla veya yazılı bildirin.</p></div>
                      <div className="bg-teal/5 border border-teal/10 p-4 rounded-xl"><h5 className="text-xs font-bold text-navy mb-1 flex items-center gap-1"><Landmark size={14} className="text-teal"/> 2. Yasal Tutarı Bankadan Ödeyin</h5><p className="text-[11px] text-slate-600 leading-relaxed">TÜFE oranlı kirayı sözleşmedeki IBAN'a '2025 Kira Bedeli' yazarak yatırın.</p></div>
                    </div>
                  </div>
               </div>
             </div>
           </div>
        </div>

        <div className="p-6 bg-white border-t border-slate-200 shrink-0">
          <div className="max-w-4xl mx-auto relative">
             <div className="absolute -top-8 left-4 text-[10px] font-bold text-teal bg-teal/10 px-2 py-1 rounded-t-lg flex items-center gap-1"><Lock size={12}/> Gizlilik Kalkanı Açık</div>
             <div className="border border-slate-200 rounded-2xl rounded-tl-none bg-slate-50 p-2 flex flex-col focus-within:border-teal focus-within:bg-white transition-colors shadow-sm">
                <textarea rows="2" placeholder="Örn: Ev sahibim sözleşmeyi elden yenilemek istiyor veya tahliye taahhüdü imzalatmak istiyor, ne yapmalıyım?..." className="w-full bg-transparent resize-none outline-none p-2 text-sm text-navy placeholder:text-slate-400"></textarea>
                <div className="flex justify-between items-center mt-2">
                   <div className="flex gap-2">
                     <button className="text-xs font-bold text-slate-500 bg-white border border-slate-200 px-3 py-1.5 rounded-lg flex items-center gap-1 hover:bg-slate-100"><Paperclip size={14}/> Belge / PDF Ekle</button>
                     <button className="text-xs font-bold text-slate-500 bg-white border border-slate-200 w-8 h-8 rounded-lg flex justify-center items-center hover:bg-slate-100"><Mic size={14}/></button>
                   </div>
                   <button className="bg-teal hover:bg-teal/90 text-white text-xs font-bold px-4 py-2 rounded-lg flex items-center gap-2 shadow-sm">Hukuki Analiz İste <Send size={14}/></button>
                </div>
             </div>
          </div>
        </div>
      </div>

      <div className="w-80 bg-white border-l border-slate-200 overflow-y-auto shrink-0 p-6 custom-scrollbar">
         <div className="bg-navy rounded-2xl p-5 text-white shadow-lg mb-6 relative overflow-hidden">
           <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl"></div>
           <div className="text-[10px] font-bold text-teal tracking-widest mb-2 flex items-center gap-1"><Bot size={12}/> HIZLI HUKUKİ AKSİYON</div>
           <h3 className="font-bold text-lg mb-2 relative z-10">Fahiş Kira Artışına İtiraz İhtarnamesi</h3>
           <p className="text-xs text-slate-400 mb-4 leading-relaxed relative z-10">Bu analize dayalı olarak resmi noter veya iadeli taahhütlü posta formatında itiraz ihtarnamenizi 30 saniyede hazırlayın.</p>
           <Link to="/app/sihirbaz" className="w-full bg-teal text-white text-xs font-bold py-2.5 rounded-xl flex justify-center items-center gap-2 hover:bg-teal/90 transition-colors relative z-10">İhtarnamemi Oluştur <ArrowRight size={14}/></Link>
         </div>

         <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 mb-6">
           <div className="flex justify-between items-center mb-3"><div className="flex items-center gap-1 text-teal"><BookOpen size={14}/><span className="text-xs font-bold text-navy">Emsal Karar Özeti</span></div><span className="text-[10px] font-bold text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">Yargıtay 3. HD</span></div>
           <div className="text-[10px] text-slate-400 font-mono mb-2 flex justify-between"><span>E. 2021/4091</span><span>K. 2022/1034</span></div>
           <h4 className="text-xs font-bold text-navy mb-2">"Sözleşme Süresinin Bitimi Sebebiyle Kiracı Tahliye Edilemez"</h4>
           <p className="text-[11px] text-slate-600 italic leading-relaxed mb-3">"...TBK'nın 347. maddesi uyarınca kiraya veren, sözleşme süresinin bitimine dayanarak sözleşmeyi sona erdiremez. 10 yıllık uzama süresi dolmadıkça tahliye davası dinlenemez..."</p>
         </div>

         <div className="bg-white border border-slate-200 rounded-2xl p-4 mb-6 shadow-sm">
           <div className="flex justify-between items-center mb-3"><span className="text-xs font-bold text-navy">Orijinal Kanun Metni</span><span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">6098 S.K.</span></div>
           <div className="h-40 overflow-y-auto text-[11px] text-slate-600 leading-relaxed pr-2 custom-scrollbar">
             <p className="font-bold text-navy mb-1">Madde 344 - Kira Bedelinin Belirlenmesi</p>
             <p className="mb-3">"Tarafların yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin anlaşmaları, bir önceki kira yılında tüketici fiyat endeksindeki oniki aylık ortalamalara göre değişim oranını geçmemek koşuluyla geçerlidir..."</p>
             <p className="font-bold text-navy mb-1">Madde 347 - Fesih Bildirimi ile Sona Erme</p>
             <p>"Konut ve çatılı işyeri kiralarında kiracı, belirli süreli sözleşmelerin süresinin bitiminden en az onbeş gün önce bildirimde bulunmadıkça, sözleşme aynı koşullarla bir yıl için uzatılmış sayılır."</p>
           </div>
         </div>

         <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
           <h4 className="text-xs font-bold text-navy mb-3 flex items-center gap-2"><CheckCircle2 size={14} className="text-teal"/> Kiracı Hakları Kontrol Listesi</h4>
           <div className="space-y-2 text-[11px] font-medium text-slate-600">
             <div className="flex items-start gap-2"><CheckCircle2 size={14} className="text-teal shrink-0 mt-0.5"/> 10 yıllık uzama süreniz dolmadı</div>
             <div className="flex items-start gap-2"><CheckCircle2 size={14} className="text-teal shrink-0 mt-0.5"/> Yazılı tahliye taahhüdü vermediniz</div>
             <div className="flex items-start gap-2"><CheckCircle2 size={14} className="text-teal shrink-0 mt-0.5"/> Kiralarınızı zamanında ödüyorsunuz</div>
           </div>
         </div>
      </div>
    </div>
  );
};

export default DashboardDanisAI;