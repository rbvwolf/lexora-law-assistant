import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  Search, ChevronRight, BookOpen, ShieldCheck, FileText, Scale, CheckCircle2, XCircle, AlertTriangle, ArrowRight, Lock, Download, MessageSquare, Bot, ChevronDown, Mail, MessageCircle, File, Server, EyeOff, FileCheck, Network, Database, Shield, Send, MapPin, Check, Eye, LogIn, UserPlus, Landmark, Building2, Info, CreditCard, LayoutDashboard, Briefcase, FolderOpen, HelpCircle, Headphones, User, Calculator, Calendar, Gavel, Clock, ArrowLeft, Plus, Mic, Paperclip, MoreVertical, ExternalLink, RefreshCw, FileLock2, AlertOctagon, History, Loader2
} from 'lucide-react';

const LexoraLogo = ({ className = "h-12", light = false }) => (
  <svg viewBox="0 0 240 70" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
    <text x="0" y="50" fontFamily="Georgia, serif" fontSize="54" fill={light ? "#ffffff" : "#1a2542"} letterSpacing="-1">le</text>
    <g transform="translate(52, 10)">
      <line x1="38" y1="0" x2="2" y2="46" stroke="#c4a77d" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="4" y1="2" x2="36" y2="44" stroke={light ? "#ffffff" : "#1a2542"} strokeWidth="8" strokeLinecap="round" />
      <g transform="translate(10, 26)"><path d="M-6 8 Q0 12 6 8 L0 14 Z" fill="#c4a77d" /><line x1="-6" y1="8" x2="0" y2="0" stroke="#c4a77d" strokeWidth="1" /><line x1="6" y1="8" x2="0" y2="0" stroke="#c4a77d" strokeWidth="1" /><circle cx="0" cy="0" r="1.5" fill="#c4a77d" /></g>
      <g transform="translate(30, 26)"><path d="M-6 8 Q0 12 6 8 L0 14 Z" fill="#c4a77d" /><line x1="-6" y1="8" x2="0" y2="0" stroke="#c4a77d" strokeWidth="1" /><line x1="6" y1="8" x2="0" y2="0" stroke="#c4a77d" strokeWidth="1" /><circle cx="0" cy="0" r="1.5" fill="#c4a77d" /></g>
    </g>
    <text x="96" y="50" fontFamily="Georgia, serif" fontSize="54" fill={light ? "#ffffff" : "#1a2542"} letterSpacing="-1">ora</text>
  </svg>
);

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow text-left">
      <div className="w-10 h-10 rounded-lg bg-slate-50 flex items-center justify-center mb-4 border border-slate-100">{icon}</div>
      <h3 className="text-navy font-semibold text-sm mb-2">{title}</h3>
      <p className="text-slate-500 text-xs leading-relaxed">{desc}</p>
    </div>
  );
}

// =====================================================================
// 1. PUBLIC SAYFALAR (DIŞ YÜZ)
// =====================================================================
function Home() {
  return (
    <main className="flex-1 flex flex-col items-center text-center px-4 pt-16 pb-20 relative z-10">
      <div className="mb-6 scale-150 transform"><LexoraLogo className="h-20" /></div>
      <h2 className="text-navy font-semibold tracking-widest text-sm mb-4">YAPAY ZEKÂ DESTEKLİ HUKUK ASİSTANI</h2>
      <p className="text-slate-500 max-w-2xl text-lg mb-10 leading-relaxed">Hukuki dilekçe, sözleşme ve ihtarname taslaklarınızı saniyeler <br className="hidden md:block"/> içinde hazırlayın; haklarınızı güncel kanun maddeleriyle öğrenin.</p>
      <div className="w-full max-w-3xl relative mb-8 group">
        <div className="absolute inset-0 bg-teal/20 blur-xl rounded-full opacity-50 group-hover:opacity-80 transition-opacity"></div>
        <div className="relative bg-white rounded-full p-2 flex items-center shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-slate-100">
          <Search className="text-teal ml-4 mr-2" size={20} /><input type="text" placeholder="Hangi dilekçeyi veya hukuki konuyu hazırlamak istersiniz?" className="flex-1 bg-transparent border-none outline-none text-sm text-slate-700 placeholder:text-slate-400 py-3"/>
          <Link to="/app/sihirbaz" className="bg-teal hover:bg-teal/90 text-white px-6 py-3 rounded-full text-sm font-medium transition-colors flex items-center gap-2 ml-2">Oluştur <ChevronRight size={16} /></Link>
        </div>
      </div>
      <div className="flex flex-wrap justify-center gap-3 max-w-3xl mb-24">
        {['İhtarname', 'Kira Sözleşmesi & İtiraz', 'İtiraz Dilekçesi', 'Tüketici Başvurusu', 'İşçi Alacağı'].map((t) => (<button key={t} className="bg-white border border-slate-200 text-slate-600 px-4 py-2 rounded-full text-xs font-medium hover:border-teal hover:text-teal shadow-sm">{t}</button>))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl w-full px-4">
        <FeatureCard icon={<BookOpen size={20} className="text-navy" />} title="Güncel Mevzuat Dayanağı" desc="TBK, TKHK, İİK ve HMK güncel kanun maddeleriyle tam uyumlu referanslar." />
        <FeatureCard icon={<ShieldCheck size={20} className="text-teal" />} title="KVKK & Gizlilik Maskeleme" desc="T.C. Kimlik ve kişisel verileriniz tarayıcınızdan çıkmadan otomatik anonimleşir." />
        <FeatureCard icon={<FileText size={20} className="text-amber-600" />} title="UYAP & Noter Standartı" desc="A4 formatına tam uyumlu, resmi adli makam başlık düzeni ve Word/UDF çıktısı." />
        <FeatureCard icon={<Scale size={20} className="text-purple-600" />} title="Adli Yardım Yönlendirmesi" desc="Maddi imkânı kısıtlı vatandaşlar için Baro Adli Yardım başvuru kılavuzu." />
      </div>
    </main>
  );
}

function Features() {
  return (
    <div className="w-full relative z-10 bg-[#fafafa]">
      <div className="max-w-7xl mx-auto px-6 pt-12 pb-20">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-10">
          <div className="max-w-2xl">
            <span className="bg-teal/10 text-teal px-3 py-1 rounded-full text-[10px] font-bold tracking-widest mb-6 inline-flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-teal"></div> LEXORA TEKNOLOJİ ALTYAPISI</span>
            <h1 className="text-4xl md:text-[42px] font-bold text-navy mb-6 leading-tight tracking-tight">Yapay Zekâ Destekli Hukuk Teknolojisi ile Tanışın</h1>
            <p className="text-slate-500 text-lg leading-relaxed">Vatandaşlar ve profesyoneller için mevzuata tam uyumlu, hızlı ve güvenilir hukuki teknoloji altyapısı. Hata payını sıfıra indiren kurumsal veri doğrulama motoru.</p>
          </div>
          <div className="bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 flex gap-8 w-full lg:w-auto">
            <div><p className="text-[10px] font-bold tracking-widest text-slate-400 mb-2">SİSTEM PERFORMANSI</p><p className="text-3xl font-bold text-navy mb-1">14.500+</p><p className="text-xs text-slate-500 font-medium">Üretilen Belge</p></div>
            <div className="w-px bg-slate-100"></div>
            <div><p className="text-[10px] font-bold tracking-widest text-teal mb-2 flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse"></div> ÇEVRİMİÇİ</p><p className="text-3xl font-bold text-navy mb-1">42 sn</p><p className="text-xs text-slate-500 font-medium">Ortalama Üretim</p></div>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="flex flex-col lg:flex-row gap-16 items-center">
          <div className="flex-1">
            <span className="bg-slate-200 text-slate-600 px-3 py-1 rounded-md text-[10px] font-bold mb-6 inline-block tracking-widest">01 ÇEKİRDEK ÇÖZÜM</span>
            <h2 className="text-3xl font-bold text-navy mb-4 tracking-tight">Akıllı Dilekçe ve İhtarname Motoru</h2>
            <p className="text-slate-500 mb-8 leading-relaxed">Türk Borçlar Kanunu, İş Kanunu ve Tüketici Kanunu ile eğitilmiş, olayın detaylarına göre resmi dilekçe taslağı üreten sistem. UYAP ve Noter e-imza standartlarında DOCX ve UDF indirme imkânı.</p>
            <div className="space-y-4 mb-8">
              <div className="flex gap-4 p-4 bg-white rounded-2xl border border-slate-100 shadow-sm"><div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center shrink-0"><FileText className="text-blue-600" size={20} /></div><div><h4 className="font-semibold text-navy text-sm mb-1">UYAP Formatına Tam Uyum (A4)</h4><p className="text-xs text-slate-500 leading-relaxed">Kenar boşlukları ve satır aralıkları Adalet Bakanlığı standartlarında (Times New Roman 12pt).</p></div></div>
              <div className="flex gap-4 p-4 bg-white rounded-2xl border border-slate-100 shadow-sm"><div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center shrink-0"><Shield className="text-amber-600" size={20} /></div><div><h4 className="font-semibold text-navy text-sm mb-1">Noter Formatı İhtarname Kurgusu</h4><p className="text-xs text-slate-500 leading-relaxed">Muhatap tebliğ şerhi ve yasal ihtarat sonları hesaplanarak otomatik oluşturulur.</p></div></div>
            </div>
          </div>
          <div className="flex-1 bg-indigo-50/50 p-6 md:p-10 rounded-[40px] w-full border border-indigo-50 relative overflow-hidden">
             <div className="bg-white rounded-xl shadow-[0_20px_50px_rgb(0,0,0,0.05)] p-8 border border-slate-100 relative z-10 w-full max-w-md mx-auto">
                <div className="absolute top-0 left-0 w-full h-1.5 bg-teal rounded-t-xl"></div>
                <div className="flex items-center gap-2 mb-6 pb-4 border-b border-slate-100"><CheckCircle2 className="text-teal" size={16} /><span className="text-[10px] font-bold text-slate-400 tracking-widest">KİRA ARTIŞ İHTARNAMESİ TASLAĞI</span></div>
                <div className="text-center font-serif text-sm font-bold mb-6 tracking-widest">İHTARNAME</div>
                <p className="text-[11px] text-slate-600 leading-relaxed font-serif mb-6 text-justify"><span className="font-bold text-navy">KEŞİDECİ:</span> Ahmet Y***<br/><span className="font-bold text-navy">MUHATAP:</span> Mehmet K***<br/><br/><span className="font-bold text-navy">KONU:</span> Kira sözleşmesinin feshi ve tahliye talebimiz hk.<br/><br/>Sayın Muhatap; mülkiyeti müvekkilime ait bulunan taşınmazda akdedilen 01.06.2024 tarihli kira sözleşmesi uyarınca kiracı olarak bulunmaktasınız...</p>
             </div>
          </div>
        </div>
      </div>
      <div className="bg-white border-y border-slate-100">
        <div className="max-w-7xl mx-auto px-6 py-20">
          <div className="flex flex-col lg:flex-row-reverse gap-16 items-center">
             <div className="flex-1">
                <span className="bg-slate-200 text-slate-600 px-3 py-1 rounded-md text-[10px] font-bold mb-6 inline-block tracking-widest">02 GÜVENLİK STANDARTI</span>
                <h2 className="text-3xl font-bold text-navy mb-4 tracking-tight">Otomatik KVKK & Kişisel Veri Maskeleme</h2>
                <p className="text-slate-500 mb-8 leading-relaxed">T.C. Kimlik Numarası, IBAN, tapu ada parsel ve iletişim bilgileri gibi hassas veriler tarayıcınızdan çıkmadan sistem tarafından anonimleştirilir.</p>
                <ul className="space-y-4">
                  <li className="flex gap-3 text-sm text-slate-600 font-medium items-center"><CheckCircle2 className="text-teal shrink-0" size={18} /> %100 algoritma tabanlı lokal maskeleme.</li>
                  <li className="flex gap-3 text-sm text-slate-600 font-medium items-center"><CheckCircle2 className="text-teal shrink-0" size={18} /> Türkiye sunucuları & SSL formatı ile uçtan uca şifreleme.</li>
                  <li className="flex gap-3 text-sm text-slate-600 font-medium items-center"><CheckCircle2 className="text-teal shrink-0" size={18} /> Avukat-Müvekkil gizliliği standartı.</li>
                </ul>
             </div>
             <div className="flex-1 bg-slate-50 p-6 md:p-10 rounded-[40px] w-full border border-slate-100">
                <div className="space-y-4 w-full max-w-md mx-auto">
                   <div className="bg-white p-4 rounded-xl border border-red-100 shadow-sm relative"><span className="absolute -top-3 right-4 bg-red-100 text-red-600 text-[9px] font-bold px-2 py-1 rounded-full">GİRDİ (RİSKLİ)</span><p className="text-[11px] font-mono text-slate-500 leading-relaxed">Ahmet Yılmaz (T.C. <span className="bg-red-50 text-red-600 font-bold px-1 rounded">12345678901</span>), TR12 0006 1004... numaralı hesaba ödemeyi yaptı.</p></div>
                   <div className="flex justify-center"><ArrowRight className="text-slate-300" /></div>
                   <div className="bg-navy p-4 rounded-xl border border-navy shadow-lg relative"><span className="absolute -top-3 right-4 bg-teal text-white text-[9px] font-bold px-2 py-1 rounded-full flex items-center gap-1"><Lock size={10}/> LEXORA MASKESİ</span><p className="text-[11px] font-mono text-slate-300 leading-relaxed">Ahmet Yılmaz (T.C. <span className="bg-teal/20 text-teal font-bold px-1 rounded">[T.C. KİMLİK NO]</span>), <span className="bg-teal/20 text-teal font-bold px-1 rounded">[IBAN NO]</span> numaralı hesaba ödemeyi yaptı.</p></div>
                </div>
             </div>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-6 py-16 grid grid-cols-1 md:grid-cols-2 gap-8">
         <div className="bg-white border border-slate-200 rounded-[32px] p-8 md:p-12 shadow-sm"><span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-md text-[10px] font-bold mb-6 inline-block tracking-widest">03 GÜVENİLİR DAYANAK</span><h3 className="text-2xl font-bold text-navy mb-4">Resmi Mevzuat ve İçtihat Doğrulama</h3><p className="text-slate-500 mb-8 text-sm leading-relaxed">Yargıtay, BAM (İstinaf) emsal kararları ile anlık eşleştirme, halüsinasyonsuz kanun maddesi referansları sunar.</p></div>
         <div className="bg-white border border-slate-200 rounded-[32px] p-8 md:p-12 shadow-sm"><span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-md text-[10px] font-bold mb-6 inline-block tracking-widest">04 SÜRE YÖNETİMİ</span><h3 className="text-2xl font-bold text-navy mb-4">Hak Düşürücü Süre Takvimi</h3><p className="text-slate-500 mb-8 text-sm leading-relaxed">İtiraz, istinaf ve zamanaşımı sürelerini otomatik hesaplayarak acil geri sayım başlatır.</p></div>
      </div>
    </div>
  );
}

function FAQ() {
  const [openQ, setOpenQ] = useState(0);
  const faqs = [
    { tag: "1136 Sayılı Kanun Uyumlu", q: "Lexora resmi bir avukatlık hizmeti sunar mı?", a: "Hayır. Lexora bir yapay zekâ asistanıdır ve resmi avukatlık hizmeti yerine geçmez. Bilgilendirme ve taslak üretimi sağlar." },
    { tag: "UYAP & Adli Standart", q: "Üretilen dilekçeler UYAP'ta geçerli midir?", a: "Evet, belgeler UYAP ve adli makam standartlarına uygun DOCX/UDF formatında teknik olarak tam uyumlu üretilir." },
    { tag: "RAG & Mevzuat Doğrulama", q: "Yapay zekâ yanıtları uydurabilir mi?", a: "Lexora, kapalı devre RAG mimarisi ile sadece sisteme yüklü güncel resmi mevzuat üzerinden yanıt üretir." },
    { tag: "6698 Sayılı KVKK Uyumlu", q: "Kişisel bilgilerim güvende mi?", a: "Verileriniz tarayıcınızda maskelenir ve sunucularımızda saklanmaz. AI model eğitiminde kesinlikle kullanılmaz." }
  ];
  return (
    <div className="w-full relative z-10 bg-[#fafafa] pb-24">
      <div className="bg-gradient-to-b from-blue-50/50 to-transparent pt-16 pb-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="max-w-2xl text-left">
            <span className="text-teal font-bold text-xs flex items-center gap-1 mb-4"><ShieldCheck size={14}/> Şeffaf Hukuk Teknolojisi & Bilgi Tabanı</span>
            <h1 className="text-3xl md:text-4xl font-bold text-navy mb-4 leading-tight">Aklınıza Takılan Sorular ve Şeffaf Yanıtlar</h1>
            <p className="text-slate-500 leading-relaxed mb-6">Yapay zekâ destekli hukuk asistanımızın çalışma prensipleri, mevzuat güvenliği, adli uyumluluk ve veri mahremiyeti standartlarına dair merak ettiğiniz tüm detaylar.</p>
            <div className="relative w-full max-w-lg"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} /><input type="text" placeholder="Soru ara..." className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-slate-200 shadow-sm text-sm outline-none" /></div>
          </div>
          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4"><div className="bg-teal/10 p-3 rounded-xl text-teal"><FileText size={24}/></div><div><p className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">SON MEVZUAT</p><p className="font-bold text-navy text-sm">T.C. Resmi Gazete 32.540</p><p className="text-xs text-teal font-medium flex items-center gap-1 mt-1"><div className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse"></div> Canlı Kaynak</p></div></div>
        </div>
      </div>
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex flex-col lg:flex-row gap-8">
          <div className="flex-1 space-y-4">
            {faqs.map((faq, idx) => (
              <div key={idx} className="bg-white border border-slate-200 rounded-2xl overflow-hidden transition-all">
                <button onClick={() => setOpenQ(openQ === idx ? null : idx)} className="w-full text-left p-6 flex justify-between items-center gap-4"><div><span className="text-[10px] font-bold text-teal bg-teal/10 px-2 py-1 rounded-md mb-2 inline-block">{faq.tag}</span><h3 className="text-navy font-semibold text-sm">{faq.q}</h3></div><ChevronDown className={`text-slate-400 transition-transform ${openQ === idx ? 'rotate-180' : ''}`} size={20} /></button>
                {openQ === idx && (<div className="px-6 pb-6 text-slate-500 text-sm leading-relaxed border-t border-slate-50 pt-4">{faq.a}</div>)}
              </div>
            ))}
          </div>
          <div className="w-full lg:w-80 space-y-6">
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm"><div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mb-4"><MessageCircle size={20}/></div><h4 className="font-bold text-navy mb-2">Sorunuzu Bulamadınız mı?</h4><p className="text-xs text-slate-500 mb-6">Destek ekibimiz sorularınızı yanıtlamak için hazır.</p><button className="w-full bg-teal text-white py-3 rounded-xl text-sm font-medium hover:bg-teal/90 flex justify-center items-center gap-2"><MessageSquare size={16}/> Canlı Destek</button></div>
            <div className="bg-navy rounded-2xl p-6 text-white text-center shadow-lg relative overflow-hidden"><div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl"></div><span className="text-[10px] font-bold text-teal tracking-widest mb-2 block relative z-10">HEMEN DENEYİN</span><h4 className="font-bold text-lg mb-3 relative z-10">İlk Dilekçenizi Ücretsiz Oluşturun</h4><Link to="/app/sihirbaz" className="bg-white text-navy px-6 py-2.5 rounded-full text-sm font-bold inline-flex items-center gap-2 relative z-10">Sihirbazı Aç <ArrowRight size={16}/></Link></div>
          </div>
        </div>
      </div>
    </div>
  );
}

function KVKK() {
  return (
    <div className="w-full relative z-10 bg-[#fafafa]">
      <div className="max-w-7xl mx-auto px-6 pt-16 pb-16">
        <div className="flex flex-col lg:flex-row justify-between items-start gap-10">
          <div className="max-w-3xl">
            <span className="bg-teal/10 text-teal px-3 py-1 rounded-full text-[10px] font-bold tracking-widest mb-6 inline-flex items-center gap-1"><ShieldCheck size={12}/> 6698 SAYILI KANUN & GDPR UYUMLU</span>
            <h1 className="text-4xl md:text-5xl font-bold text-navy mb-6 leading-tight">Kişisel Verileriniz ve Hukuki Mahremiyetiniz Korunur</h1>
            <p className="text-slate-500 text-lg leading-relaxed">Lexora, avukatlık meslek sırrı ilkeleri ve KVKK mevzuatı uyarınca geliştirilmiş çok katmanlı veri koruma kalkanıyla donatılmıştır. Hukuki taslaklarınız cihazınızdan çıkmadan önce taranır, anonimleştirilir.</p>
          </div>
          <div className="flex flex-col gap-3 w-full lg:w-auto">
             <div className="bg-white border border-slate-200 p-4 rounded-2xl flex items-center gap-4 shadow-sm"><div className="bg-blue-50 p-2 rounded-lg text-blue-600"><FileCheck size={20}/></div><div><p className="text-[10px] font-bold text-slate-400">VERBİS KAYIT NO</p><p className="font-semibold text-navy text-sm">T.C. KVKK - 2026/18402</p></div></div>
             <div className="bg-white border border-slate-200 p-4 rounded-2xl flex items-center gap-4 shadow-sm"><div className="bg-indigo-50 p-2 rounded-lg text-indigo-600"><Server size={20}/></div><div><p className="text-[10px] font-bold text-slate-400">VERİ MERKEZİ KONUMU</p><p className="font-semibold text-navy text-sm">İstanbul & Ankara (Tier III)</p></div></div>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-6 pb-20">
         <h2 className="text-[10px] font-bold text-slate-400 tracking-widest mb-6">KREDİT GÜVENLİK MİMARİSİ</h2>
         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm"><div className="w-12 h-12 bg-teal/10 text-teal rounded-xl flex items-center justify-center mb-6"><Lock size={24}/></div><span className="text-[10px] font-bold text-slate-400 mb-2 block">KATMAN 01</span><h4 className="font-bold text-navy text-lg mb-3">Uçtan Uca Maskeleme</h4><p className="text-xs text-slate-500 mb-6">Hassas veriler yapay zekâ motoruna gönderilmeden önce cihazınızda değiştirilir.</p></div>
            <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm"><div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mb-6"><Server size={24}/></div><span className="text-[10px] font-bold text-slate-400 mb-2 block">KATMAN 02</span><h4 className="font-bold text-navy text-lg mb-3">256-Bit SSL Şifreleme</h4><p className="text-xs text-slate-500 mb-6">KVKK uyumu için tüm sunucularımız Türkiye'de barındırılır.</p></div>
            <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm"><div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center mb-6"><EyeOff size={24}/></div><span className="text-[10px] font-bold text-slate-400 mb-2 block">KATMAN 03</span><h4 className="font-bold text-navy text-lg mb-3">Model Eğitimi Yasağı</h4><p className="text-xs text-slate-500 mb-6">Kullanıcı girdileri yapay zekâ modelinin eğitilmesinde kullanılamaz.</p></div>
            <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm"><div className="w-12 h-12 bg-purple-50 text-purple-600 rounded-xl flex items-center justify-center mb-6"><FileCheck size={24}/></div><span className="text-[10px] font-bold text-slate-400 mb-2 block">KATMAN 04</span><h4 className="font-bold text-navy text-lg mb-3">Veri İmha Hakkı</h4><p className="text-xs text-slate-500 mb-6">Dilediğiniz an panelinizden belge geçmişinizi kalıcı olarak silebilirsiniz.</p></div>
         </div>
      </div>
    </div>
  );
}

function Login() {
  const [showPassword, setShowPassword] = useState(false);
  return (
    <div className="min-h-screen w-full flex bg-white font-sans absolute top-0 left-0 z-50">
      <div className="hidden lg:flex w-[45%] bg-navy flex-col justify-between p-12 text-white relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-teal/20 via-navy to-navy pointer-events-none"></div>
        <div className="relative z-10">
          <div className="flex justify-between items-center mb-16"><div className="flex items-center gap-2"><div className="bg-teal/20 p-2 rounded-lg"><Scale size={20} className="text-teal"/></div><div className="font-serif font-bold text-xl">Lexora <span className="text-teal text-sm">.ai</span></div></div></div>
          <h1 className="text-4xl xl:text-5xl font-bold mb-6 leading-tight">Hukuki Süreçlerinizde<br/>Yapay Zekâ Güvencesi</h1>
          <p className="text-slate-400 text-sm leading-relaxed mb-12 max-w-md">Türk hukuk mevzuatına tam uyumlu, içtihat tarayan yeni nesil platform.</p>
        </div>
      </div>
      <div className="w-full lg:w-[55%] flex flex-col items-center justify-center p-6 md:p-12">
         <div className="w-full max-w-md mt-10">
            <h2 className="text-2xl md:text-3xl font-bold text-navy mb-2">Lexora Portalı'na Hoş Geldiniz</h2>
            <p className="text-slate-500 text-sm mb-8">Hukuki işlemlerinizi güvenle yönetmek için hesabınıza erişin</p>
            <form className="space-y-5">
              <div><label className="block text-xs font-bold text-navy mb-2">E-posta Adresi</label><input type="email" placeholder="ornek@alanadi.com" className="w-full pl-4 pr-4 py-3.5 rounded-xl border border-slate-200 text-sm"/></div>
              <div><label className="block text-xs font-bold text-navy mb-2">Şifre</label><input type={showPassword ? "text" : "password"} placeholder="••••••••••••" className="w-full pl-4 pr-4 py-3.5 rounded-xl border border-slate-200 text-sm"/></div>
              <Link to="/app/sihirbaz" className="w-full bg-navy hover:bg-navy/90 text-white font-bold py-4 rounded-xl flex justify-center items-center gap-2 transition-colors shadow-md">Giriş Yap <ArrowRight size={18}/></Link>
            </form>
         </div>
      </div>
    </div>
  );
}

// =====================================================================
// 2. DASHBOARD BİLEŞENLERİ (KULLANICI PANELİ)
// =====================================================================

function Sidebar() {
  const location = useLocation();
  const isActive = (path) => location.pathname === path ? 'bg-teal/10 text-teal font-bold' : 'text-slate-500 hover:bg-slate-100 hover:text-navy';
  return (
    <aside className="w-64 bg-slate-50/50 border-r border-slate-200 h-screen flex flex-col shrink-0 sticky top-0">
      <div className="p-6 border-b border-slate-200"><LexoraLogo className="h-8" /><div className="mt-4 flex items-center gap-2 text-[10px] font-bold text-teal bg-teal/10 border border-teal/20 px-2 py-1.5 rounded-md"><ShieldCheck size={12}/> KVKK Güvenli Mod</div></div>
      <div className="flex-1 overflow-y-auto py-6 px-4 custom-scrollbar">
        <div className="mb-6">
          <h4 className="text-[10px] font-bold text-slate-400 tracking-widest mb-3 px-2">HUKUK İŞLEMLERİ</h4>
          <nav className="space-y-1 text-sm font-medium">
            <Link to="/app/sihirbaz" className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${isActive('/app/sihirbaz')}`}><FileText size={18}/> Dilekçe Sihirbazı</Link>
            <Link to="/app/danis-ai" className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${isActive('/app/danis-ai')}`}><Bot size={18}/> Danış AI Co-Pilot</Link>
            <Link to="/app/arsiv" className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${isActive('/app/arsiv')}`}><FolderOpen size={18}/> Belgelerim & Arşiv</Link>
            <Link to="/app/rehber" className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${isActive('/app/rehber')}`}><BookOpen size={18}/> Hak Rehberi</Link>
          </nav>
        </div>
        <div>
          <h4 className="text-[10px] font-bold text-slate-400 tracking-widest mb-3 px-2">BİLGİ & DESTEK</h4>
          <nav className="space-y-1 text-sm font-medium">
            <Link to="/ozellikler" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-500 hover:bg-slate-100"><LayoutDashboard size={18}/> Özellikler</Link>
            <Link to="/sss" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-500 hover:bg-slate-100"><MessageCircle size={18}/> Sıkça Sorulanlar</Link>
          </nav>
        </div>
      </div>
      <div className="p-4 border-t border-slate-200"><div className="bg-slate-100 p-3 rounded-xl flex items-center gap-3"><div className="w-8 h-8 rounded-full bg-slate-300 flex items-center justify-center text-navy font-bold text-xs">AV</div><div><p className="text-xs font-bold text-navy">Av. T. Yılmaz</p><p className="text-[10px] text-slate-500">Hesabım • Kurumsal</p></div></div></div>
    </aside>
  );
}

// -----------------------------------------------------------------
// A. DİLEKÇE SİHİRBAZI (CANLI ÖNİZLEME VE FORM AKIŞI)
// -----------------------------------------------------------------
function DashboardWizard() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [currentStep, setCurrentStep] = useState(2);
  const [formData, setFormData] = useState({
    muhatapAd: "Hikmet Çetin",
    muhatapTc: "38291048214",
    kesideciAd: "Av. Tolga Yılmaz",
    kesideciTc: "19482910382",
    kiraBaslangic: "09/01/2022",
    mevcutKira: "12000",
    talepKira: "24000"
  });

  useEffect(() => {
    const fetchTemplates = async () => {
      setLoading(true);
      try {
        const response = await fetch('http://localhost:8000/api/v1/documents/templates');
        if (response.ok) {
          const data = await response.json();
          setTemplates(data);
        }
      } catch (error) {
        console.error("Şablonlar çekilemedi:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchTemplates();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="flex-1 bg-[#f8fafc] overflow-y-auto p-6">
       <div className="max-w-7xl mx-auto">
          <div className="bg-teal/10 border border-teal/20 rounded-xl p-4 flex justify-between items-center mb-6">
             <div className="flex items-center gap-3 text-teal"><CheckCircle2 size={24} className="fill-teal text-white"/><div><h3 className="font-bold text-sm">Resmi Dilekçe & Belge Sihirbazı</h3><p className="text-xs text-teal/80">Adalet Bakanlığı UYAP ve Noterler Birliği (TNB) e-işlem format standartlarıyla %100 uyumludur.</p></div></div>
             <div className="flex gap-4 text-xs font-bold text-teal"><span className="flex items-center gap-1"><Lock size={14}/> 256-Bit Uçtan Uca</span><span className="bg-white px-2 py-1 rounded text-navy">Belge Kodu: LX-2024-KIR-8421</span></div>
          </div>

          <div className="flex gap-2 mb-8 overflow-x-auto">
             <div className="flex-1 bg-white border-2 border-teal rounded-xl p-3 flex items-center gap-3 shrink-0 cursor-pointer" onClick={() => setCurrentStep(1)}>
               <div className="w-8 h-8 rounded-full bg-teal text-white flex justify-center items-center"><Check size={16}/></div>
               <div><p className="text-[10px] text-teal font-bold">1. ADIM - TAMAMLANDI</p><p className="text-xs font-bold text-navy">Kategori & Şablon</p></div>
             </div>
             
             <div className={`flex-1 rounded-xl p-3 flex items-center gap-3 shrink-0 shadow-md ${currentStep === 2 ? 'bg-navy text-white' : 'bg-white border-2 border-teal text-navy cursor-pointer'}`} onClick={() => setCurrentStep(2)}>
               <div className={`w-8 h-8 rounded-full flex justify-center items-center font-bold ${currentStep === 2 ? 'bg-white text-navy' : 'bg-teal text-white'}`}>{currentStep > 2 ? <Check size={16}/> : '2'}</div>
               <div><p className={`text-[10px] font-bold ${currentStep === 2 ? 'text-teal' : 'text-teal'}`}>{currentStep === 2 ? 'AKTİF ADIM' : 'TAMAMLANDI'}</p><p className="text-xs font-bold">Taraf & Uyuşmazlık</p></div>
             </div>
             
             <div className={`flex-1 rounded-xl p-3 flex items-center gap-3 shrink-0 ${currentStep === 3 ? 'bg-navy text-white shadow-md' : 'bg-white border border-slate-200 opacity-60'}`}>
               <div className={`w-8 h-8 rounded-full flex justify-center items-center font-bold ${currentStep === 3 ? 'bg-white text-navy' : 'bg-slate-100 text-slate-400'}`}>3</div>
               <div><p className={`text-[10px] font-bold ${currentStep === 3 ? 'text-teal' : 'text-slate-400'}`}>{currentStep === 3 ? 'AKTİF ADIM' : '3. ADIM'}</p><p className={`text-xs font-bold ${currentStep === 3 ? 'text-white' : 'text-navy'}`}>Deliller & Dayanaklar</p></div>
             </div>
          </div>

          <div className="flex flex-col lg:flex-row gap-6">
             <div className="flex-1 space-y-6">
                
                {currentStep === 2 && (
                  <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
                       <div className="flex justify-between items-center mb-6"><h3 className="font-bold text-navy flex items-center gap-2"><User size={18}/> 1. Taraf Bilgileri</h3><span className="text-[10px] font-bold text-teal bg-teal/10 px-2 py-1 rounded flex items-center gap-1"><Shield size={12}/> KVKK Otomatik Maskeleme Açık</span></div>
                       <div className="mb-6">
                         <p className="text-xs font-bold text-slate-500 mb-3">Muhatap (Ev Sahibi / Kiraya Veren)</p>
                         <div className="grid grid-cols-2 gap-4">
                            <div><label className="text-[10px] text-slate-400 block mb-1">Ad Soyad / Unvan</label><input type="text" name="muhatapAd" value={formData.muhatapAd} onChange={handleInputChange} className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50 focus:border-teal transition-colors"/></div>
                            <div><label className="text-[10px] text-slate-400 block mb-1">T.C. Kimlik / Vergi No</label><div className="relative"><input type="text" name="muhatapTc" value={formData.muhatapTc} onChange={handleInputChange} className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50 focus:border-teal transition-colors"/><ShieldCheck className="absolute right-3 top-1/2 -translate-y-1/2 text-teal" size={16}/></div></div>
                         </div>
                       </div>
                       <div>
                         <p className="text-xs font-bold text-slate-500 mb-3 flex justify-between">Keşideci (Kiracı) <span className="text-teal">Profilinizden Aktarıldı</span></p>
                         <div className="grid grid-cols-2 gap-4">
                            <div><label className="text-[10px] text-slate-400 block mb-1">Ad Soyad</label><input type="text" name="kesideciAd" value={formData.kesideciAd} onChange={handleInputChange} className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50 focus:border-teal transition-colors"/></div>
                            <div><label className="text-[10px] text-slate-400 block mb-1">T.C. Kimlik No</label><input type="text" name="kesideciTc" value={formData.kesideciTc} onChange={handleInputChange} className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50 focus:border-teal transition-colors"/></div>
                         </div>
                       </div>
                    </div>

                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                       <h3 className="font-bold text-navy flex items-center gap-2 mb-6"><FileText size={18}/> 2. Kira Sözleşmesi ve Artış Değerleri</h3>
                       <div className="grid grid-cols-3 gap-4 mb-6">
                          <div><label className="text-[10px] text-slate-400 block mb-1">Kira Başlangıç Tarihi</label><div className="relative"><input type="text" name="kiraBaslangic" value={formData.kiraBaslangic} onChange={handleInputChange} className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50 focus:border-teal transition-colors"/><Calendar className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" size={16}/></div></div>
                          <div><label className="text-[10px] text-slate-400 block mb-1">Mevcut Ödenen Kira</label><div className="relative"><input type="text" name="mevcutKira" value={formData.mevcutKira} onChange={handleInputChange} className="w-full border rounded-lg p-2.5 text-sm outline-none font-bold focus:border-teal transition-colors"/><span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">₺ / ay</span></div></div>
                          <div><label className="text-[10px] text-slate-400 block mb-1">Talep Edilen Kira</label><div className="relative"><input type="text" name="talepKira" value={formData.talepKira} onChange={handleInputChange} className="w-full border border-red-300 bg-red-50 text-red-600 rounded-lg p-2.5 text-sm outline-none font-bold focus:border-red-500 transition-colors"/><span className="absolute right-3 top-1/2 -translate-y-1/2 text-red-400 text-xs">₺ / ay</span></div></div>
                       </div>
                    </div>
                  </div>
                )}

                {currentStep === 3 && (
                  <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                       <h3 className="font-bold text-navy flex items-center gap-2 mb-6"><Paperclip size={18}/> 3. Ek Deliller ve Hukuki Dayanaklar</h3>
                       <p className="text-sm text-slate-500 mb-4">İhtarnamenin gücünü artırmak için sisteme kira sözleşmesini veya banka dekontlarını ekleyebilirsiniz.</p>
                       <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer mb-6">
                         <Download size={24} className="mx-auto text-slate-400 mb-2"/>
                         <p className="text-sm font-bold text-navy">Belgeleri buraya sürükleyin veya seçin</p>
                         <p className="text-xs text-slate-500">PDF, JPG veya PNG (Maks 10MB)</p>
                       </div>
                    </div>
                  </div>
                )}
                
                <div className="flex justify-between items-center mt-6">
                  {currentStep > 1 && (
                    <button onClick={() => setCurrentStep(prev => prev - 1)} className="bg-white border border-slate-200 text-navy font-bold py-3 px-6 rounded-xl flex items-center gap-2 hover:bg-slate-50 transition-colors">
                      <ArrowLeft size={16}/> Geri
                    </button>
                  )}
                  <div className="flex-1"></div>
                  {currentStep === 2 && (
                    <button onClick={() => setCurrentStep(3)} className="bg-navy hover:bg-navy/90 text-white font-bold py-3 px-8 rounded-xl flex items-center gap-2 shadow-md transition-all">
                      3. Adıma İlerle (Deliller) <ArrowRight size={16}/>
                    </button>
                  )}
                  {currentStep === 3 && (
                    <button className="bg-teal hover:bg-teal/90 text-white font-bold py-3 px-8 rounded-xl flex items-center gap-2 shadow-md transition-all">
                      Belgeyi Tamamla ve İndir <Check size={16}/>
                    </button>
                  )}
                </div>
             </div>

             <div className="w-full lg:w-[450px] shrink-0">
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 sticky top-6">
                   <div className="flex justify-between items-center mb-4">
                     <h3 className="font-bold text-navy text-sm flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-teal animate-pulse"></div> Canlı Önizleme (A4)</h3>
                     <div className="flex gap-2"><button className="text-[10px] font-bold text-navy bg-slate-100 px-2 py-1 rounded">.UDF</button><button className="bg-teal text-white text-[10px] font-bold px-3 py-1 rounded flex items-center gap-1"><Download size={12}/> İndir</button></div>
                   </div>
                   
                   <div className="w-full aspect-[1/1.414] bg-white border border-slate-200 shadow-inner p-6 overflow-y-auto text-[8px] sm:text-[9px] font-serif text-slate-800 leading-relaxed custom-scrollbar transition-all">
                      <div className="flex justify-between mb-8 text-slate-400 border-b border-slate-100 pb-2"><span>LEXORA RESMİ İHTARNAME PROTOKOLÜ</span><span>TARİH: {new Date().toLocaleDateString('tr-TR')}</span></div>
                      <div className="text-center font-bold mb-6"><p className="text-sm">ANKARA NÖBETÇİ NOTERLİĞİNE</p><p className="italic font-normal">(Muhataba tebliğ edilmek üzere bir nüshası talep edilmektedir)</p></div>
                      <div className="text-center font-bold tracking-[0.3em] mb-8 text-sm">İ H T A R N A M E</div>
                      <table className="w-full mb-6">
                        <tbody>
                          <tr><td className="font-bold w-24 align-top pb-2">KEŞİDECİ:</td><td className="pb-2"><span className="bg-teal/10">{formData.kesideciAd || '...'}</span> (T.C. Kimlik: <span className="bg-teal/10">{formData.kesideciTc || '...'}</span>)</td></tr>
                          <tr><td className="font-bold align-top pb-2">ADRES:</td><td className="pb-2">Ayrancı Mah. Güvenlik Cad. 24/5 Çankaya / ANKARA</td></tr>
                          <tr><td className="font-bold align-top pb-2">MUHATAP:</td><td className="pb-2"><span className="bg-amber-100">{formData.muhatapAd || '...'}</span> (T.C. Kimlik: <span className="bg-amber-100">{formData.muhatapTc || '...'}</span>)</td></tr>
                          <tr><td className="font-bold align-top pb-2">KONU:</td><td className="pb-2 font-bold"><span className="bg-blue-50">{formData.kiraBaslangic}</span> başlangıç tarihli kira akdi gereğince talep edilen fahiş kira artışının reddi ile 6098 sayılı TBK m. 344 uyarınca TÜFE 12 aylık ortalamalar tavanı olan %62,51 oranında yasal artış yapılacağının bildirimidir.</td></tr>
                        </tbody>
                      </table>
                      <p className="font-bold mb-2">SAYIN MUHATAP;</p>
                      <p className="mb-2 indent-4 text-justify">1. Tarafınızla akdedilen yukarıda adresi belirtilen taşınmaza ilişkin kira sözleşmesi uyarınca aylık kira bedeli <span className="font-bold underline bg-teal/10">{formData.mevcutKira || '0'} TL</span> olarak düzenli biçimde banka hesabınıza eksiksiz yatırılmaktadır.</p>
                      <p className="mb-2 indent-4 text-justify">2. Tarafımıza şahsınızca şifahen iletilen aylık <span className="font-bold text-red-600 bg-red-50">{formData.talepKira || '0'} TL</span> kira bedeli talebi, 6098 sayılı Türk Borçlar Kanunu'nun (TBK) emredici nitelikteki <span className="font-bold">344/2. fıkrasına</span> açıkça aykırıdır.</p>
                   </div>
                </div>
             </div>
          </div>
       </div>
    </div>
  );
}

// -----------------------------------------------------------------
// B. HAK REHBERİ (TAM EKRAN)
// -----------------------------------------------------------------
function DashboardRehber() {
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
}

// -----------------------------------------------------------------
// C. DANIŞ AI CO-PILOT (API ENTEGRELİ CHAT)
// -----------------------------------------------------------------
function DashboardDanisAI() {
  const [messages, setMessages] = useState([
    {
      sender: "ai",
      text: "Merhaba! Hukuki sürecinizle ilgili bir soru sorabilir veya belge şablonu oluşturmamı isteyebilirsiniz. T.C. kimlik numaranız ve diğer özel bilgileriniz otomatik maskelenecektir.",
      intent: null,
      citations: [],
      disclaimer: "Bu sistem bir AI asistanıdır; avukatlık hizmeti vermez."
    }
  ]);
  const [inputMsg, setInputMsg] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = async () => {
    if (!inputMsg.trim()) return;

    const userMessage = { sender: "user", text: inputMsg };
    setMessages((prev) => [...prev, userMessage]);
    setInputMsg("");
    setIsTyping(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "lexora-web-session-001",
          message: inputMsg
        })
      });

      if (response.ok) {
        const data = await response.json();
        const aiMessage = {
          sender: "ai",
          text: data.answer,
          intent: data.intent,
          citations: data.citations || [],
          disclaimer: data.disclaimer || "Bu sistem bir AI asistanıdır; avukatlık hizmeti vermez."
        };
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        throw new Error("Backend hatası");
      }
    } catch (error) {
      console.error("Mesaj gönderilemedi:", error);
      setMessages((prev) => [...prev, {
        sender: "ai",
        text: "Şu anda sunucuya bağlanılamıyor. (Backend açık olduğunda AI yanıtı buraya gelecektir).",
        disclaimer: "Bu sistem bir AI asistanıdır; avukatlık hizmeti vermez."
      }]);
    } finally {
      setIsTyping(false);
    }
  };

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
           {messages.map((msg, idx) => (
             msg.sender === 'user' ? (
                <div key={idx} className="flex justify-end">
                  <div className="max-w-[80%]">
                    <div className="flex justify-end items-center gap-2 mb-1"><span className="text-xs font-bold text-slate-500">Siz (Müvekkil Modu)</span><div className="w-6 h-6 rounded-full bg-navy text-white text-[10px] font-bold flex justify-center items-center">K</div></div>
                    <div className="bg-navy text-white p-4 rounded-2xl rounded-tr-none text-sm leading-relaxed shadow-md">{msg.text}</div>
                  </div>
                </div>
             ) : (
                <div key={idx} className="flex justify-start">
                  <div className="max-w-[90%]">
                    <div className="flex items-center gap-2 mb-2"><div className="w-8 h-8 rounded-full bg-teal flex justify-center items-center text-white"><Scale size={16}/></div><span className="text-xs font-bold text-navy">Danış AI Hukuk Mütalaası</span><span className="text-[10px] font-bold text-teal bg-teal/10 px-2 py-0.5 rounded ml-2">Hukuki Koruma Aktif</span></div>
                    <div className="bg-white border border-slate-200 p-5 rounded-2xl rounded-tl-none shadow-sm space-y-4">
                       <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                       
                       {msg.citations && msg.citations.length > 0 && (
                         <div className="pl-7">
                           <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-2">DAYANAK KANUN MADDELERİ</p>
                           <div className="flex gap-2 flex-wrap">
                             {msg.citations.map((cit, i) => (
                               <span key={i} className="text-xs font-bold text-teal bg-teal/5 border border-teal/10 px-2 py-1.5 rounded-lg flex items-center gap-1"><Scale size={12}/> {cit.law_name} {cit.article_id}</span>
                             ))}
                           </div>
                         </div>
                       )}

                       {msg.disclaimer && (
                          <div className="bg-amber-50 border border-amber-100 p-3 rounded-lg flex items-start gap-2 mt-4 ml-7">
                            <AlertTriangle className="text-amber-500 shrink-0 mt-0.5" size={14}/>
                            <p className="text-[10px] text-amber-800 leading-relaxed"><span className="font-bold">Yasal Uyarı:</span> {msg.disclaimer}</p>
                          </div>
                       )}
                    </div>
                  </div>
                </div>
             )
           ))}
           {isTyping && (
             <div className="flex justify-start">
               <div className="bg-white border border-slate-200 p-4 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-2">
                 <Loader2 className="animate-spin text-teal" size={16}/> <span className="text-xs text-slate-500 font-medium">Hukuki kaynaklar taranıyor...</span>
               </div>
             </div>
           )}
        </div>

        <div className="p-6 bg-white border-t border-slate-200 shrink-0">
          <div className="max-w-4xl mx-auto relative">
             <div className="absolute -top-8 left-4 text-[10px] font-bold text-teal bg-teal/10 px-2 py-1 rounded-t-lg flex items-center gap-1"><Lock size={12}/> Gizlilik Kalkanı Açık</div>
             <div className="border border-slate-200 rounded-2xl rounded-tl-none bg-slate-50 p-2 flex flex-col focus-within:border-teal focus-within:bg-white transition-colors shadow-sm">
                <textarea 
                  rows="2" 
                  value={inputMsg}
                  onChange={(e) => setInputMsg(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
                  placeholder="Hukuki sorunuzu buraya yazın..." 
                  className="w-full bg-transparent resize-none outline-none p-2 text-sm text-navy placeholder:text-slate-400"
                />
                <div className="flex justify-between items-center mt-2">
                   <div className="flex gap-2">
                     <button className="text-xs font-bold text-slate-500 bg-white border border-slate-200 px-3 py-1.5 rounded-lg flex items-center gap-1 hover:bg-slate-100"><Paperclip size={14}/> Belge / PDF Ekle</button>
                     <button className="text-xs font-bold text-slate-500 bg-white border border-slate-200 w-8 h-8 rounded-lg flex justify-center items-center hover:bg-slate-100"><Mic size={14}/></button>
                   </div>
                   <button onClick={handleSendMessage} disabled={isTyping} className="bg-teal hover:bg-teal/90 disabled:bg-teal/50 text-white text-xs font-bold px-4 py-2 rounded-lg flex items-center gap-2 shadow-sm">Hukuki Analiz İste <Send size={14}/></button>
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
      </div>
    </div>
  );
}

// -----------------------------------------------------------------
// D. BELGELERİM VE ARŞİV
// -----------------------------------------------------------------
function DashboardArsiv() {
  return (
    <div className="flex-1 bg-[#f8fafc] flex flex-col overflow-hidden">
       <div className="bg-white border-b border-slate-200 p-6 shrink-0">
          <div className="max-w-7xl mx-auto">
             <div className="flex justify-between items-center mb-6">
                <div><h1 className="text-2xl font-bold text-navy flex items-center gap-2"><FolderOpen size={24} className="text-teal"/> Hukuki Belgeler & Arşiv Yönetimi</h1><p className="text-sm text-slate-500 mt-1">Tüm UYAP (.udf), PDF ve Word dökümanlarınızı tek merkezden izleyin ve tebligat sürelerini yönetin.</p></div>
                <div className="hidden md:flex items-center gap-2 text-xs font-bold text-slate-500 bg-slate-50 border border-slate-200 px-3 py-2 rounded-lg"><FileLock2 size={16} className="text-teal"/> E-İmza Uyumlu Arşiv</div>
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

                <div className="grid grid-cols-3 gap-2 mb-8">
                  <button className="bg-teal hover:bg-teal/90 text-white text-[10px] font-bold py-2 rounded-lg flex justify-center items-center gap-1 shadow-sm"><Download size={12}/> .UDF İndir</button>
                  <button className="bg-white border border-slate-200 text-navy text-[10px] font-bold py-2 rounded-lg flex justify-center items-center gap-1"><Download size={12}/> PDF İndir</button>
                  <button className="bg-white border border-slate-200 text-navy text-[10px] font-bold py-2 rounded-lg flex justify-center items-center gap-1"><Download size={12}/> DOCX</button>
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
}


// =====================================================================
// ANA UYGULAMA (YÖNLENDİRİCİ & LAYOUT)
// =====================================================================
function App() {
  const location = useLocation();
  const isHomePage = location.pathname === '/';
  const isAuthPage = location.pathname === '/giris' || location.pathname === '/kayit';
  const isDashboard = location.pathname.startsWith('/app');

  if (isDashboard) {
    return (
      <div className="flex h-screen bg-slate-50 font-sans text-navy overflow-hidden">
         <Sidebar />
         <div className="flex-1 flex flex-col h-screen overflow-hidden">
            <header className="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-6 shrink-0">
               <div className="flex items-center gap-2 text-sm font-bold text-navy">Lexora Portal <span className="text-teal font-normal text-xs bg-teal/10 px-2 py-0.5 rounded">Beta</span></div>
               <div className="flex items-center gap-4 text-sm text-slate-500 font-medium">
                 <Link to="/" className="hover:text-navy flex items-center gap-1"><LayoutDashboard size={16}/> Ana Sayfaya Dön</Link>
                 <div className="w-px h-4 bg-slate-200"></div>
                 <Link to="/giris" className="flex items-center gap-1.5 text-red-500 hover:text-red-700"><LogIn className="rotate-180" size={16}/> Çıkış Yap</Link>
               </div>
            </header>
            <Routes>
              <Route path="/app/sihirbaz" element={<DashboardWizard />} />
              <Route path="/app/rehber" element={<DashboardRehber />} />
              <Route path="/app/danis-ai" element={<DashboardDanisAI />} />
              <Route path="/app/arsiv" element={<DashboardArsiv />} />
            </Routes>
         </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative flex flex-col font-sans text-navy bg-[#fafafa]">
      {(!isAuthPage && isHomePage) && <div className="bg-grid-pattern"></div>}

      {!isAuthPage && (
        <>
          <div className="bg-navy text-white text-[11px] py-2 px-4 flex justify-center items-center gap-2 text-center"><span className="bg-teal px-2 py-0.5 rounded text-[10px] font-bold tracking-wide">YASAL BİLGİLENDİRME</span><span className="opacity-90">Lexora yapay zekâ tabanlı bir hukuki asistan olup, resmi avukatlık hizmeti sunmaz.</span></div>
          <nav className="max-w-7xl mx-auto w-full px-6 py-4 flex items-center justify-between bg-transparent relative z-20">
            <div className="flex items-center gap-8">
              <Link to="/"><LexoraLogo className="h-10" /></Link>
              <div className="hidden lg:flex items-center gap-6 text-sm font-medium">
                <Link to="/ozellikler" className={`transition-colors ${location.pathname === '/ozellikler' ? 'text-teal font-bold' : 'hover:text-teal'}`}>Özellikler</Link>
                <div className="flex items-center gap-2"><Link to="/app/sihirbaz" className="hover:text-teal transition-colors">Dilekçe & Belge Sihirbazı</Link><span className="bg-amber-100 text-amber-700 text-[10px] px-2 py-0.5 rounded-full font-semibold">Mevzuat Uyumlu</span></div>
                <Link to="/app/rehber" className="hover:text-teal transition-colors">Hak Rehberi</Link>
                <Link to="/sss" className={`transition-colors ${location.pathname === '/sss' ? 'text-teal font-bold' : 'hover:text-teal'}`}>Sıkça Sorulanlar</Link>
              </div>
            </div>
            <div className="hidden lg:flex items-center gap-4 text-sm font-medium">
              <Link to="/kvkk" className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs transition-colors ${location.pathname === '/kvkk' ? 'bg-teal/10 text-teal font-bold' : 'text-slate-500 bg-slate-100 hover:bg-slate-200'}`}><ShieldCheck size={14} className="text-teal" /><span>KVKK Korumalı</span></Link>
              <Link to="/giris" className="hover:text-teal transition-colors">Giriş Yap</Link>
              <Link to="/giris" className="bg-navy hover:bg-navy/90 text-white px-5 py-2.5 rounded-full transition-all flex items-center gap-2">Ücretsiz Başla <ChevronRight size={16} /></Link>
            </div>
          </nav>
        </>
      )}

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/ozellikler" element={<Features />} />
        <Route path="/sss" element={<FAQ />} />
        <Route path="/kvkk" element={<KVKK />} />
        <Route path="/giris" element={<Login />} />
      </Routes>

      {!isAuthPage && (
        <footer className="border-t border-slate-200 bg-white pt-12 pb-6 mt-auto relative z-20">
          <div className="max-w-7xl mx-auto px-6 mb-12">
             <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-4 items-start"><AlertTriangle className="text-amber-500 shrink-0 mt-0.5" size={20} /><div><h4 className="text-xs font-bold text-amber-800 mb-1">TBB Gayri Resmi Hukuki Bilgilendirme Kapsamında Yasal Bildirim</h4><p className="text-[10px] text-amber-700 leading-relaxed">Lexora'nın sunduğu taslak metinler resmi avukatlık hizmeti yerine geçmez. Kullanıcı, üretilen metinleri kendi iradesiyle doğrulamakla yükümlüdür.</p></div></div>
          </div>
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-8 text-xs text-slate-500 mb-12">
            <div>
              <div className="mb-4"><LexoraLogo className="h-8" /></div><p className="leading-relaxed mb-4">Türkiye Cumhuriyet'i resmi kanun ve güncel içtihat formatlarına uygun dilekçe, ihtarname ve sözleşme taslakları hazırlayan akıllı hukuk asistanı.</p>
              <div className="flex gap-4 font-bold text-teal mt-4"><span className="flex items-center gap-1"><Lock size={14}/> Uçtan Uca Şifreli</span><span className="flex items-center gap-1"><ShieldCheck size={14}/> 6698 KVKK Uyumlu</span></div>
            </div>
            <div><h4 className="font-bold text-navy text-sm mb-4">Hukuk Araçları</h4><ul className="space-y-2"><li><Link to="/app/sihirbaz" className="hover:text-teal">Dilekçe Sihirbazı</Link></li><li><Link to="/app/sihirbaz" className="hover:text-teal">İhtarname Oluşturucu</Link></li><li><a href="#" className="hover:text-teal">Tüketici Hakem Heyeti Başvurusu</a></li></ul></div>
            <div><h4 className="font-bold text-navy text-sm mb-4">Yurttaş Hakları</h4><ul className="space-y-2"><li><Link to="/app/rehber" className="hover:text-teal">Temel Hak Rehberi</Link></li><li><a href="#" className="hover:text-teal">TBB Adli Yardım Başvurusu</a></li><li><Link to="/sss" className="hover:text-teal">Sıkça Sorulan Sorular</Link></li></ul></div>
            <div><h4 className="font-bold text-navy text-sm mb-4">Kurumsal & Yasal</h4><ul className="space-y-2"><li><Link to="/kvkk" className="hover:text-teal">KVKK Aydınlatma Metni</Link></li><li><Link to="/kvkk" className="hover:text-teal">Veri Güvenliği Standartları</Link></li><li><a href="#" className="hover:text-teal">İletişim & Destek</a></li></ul></div>
          </div>
          <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400 border-t border-slate-100 pt-6"><span>© 2026 Lexora Hukuk Teknolojileri A.Ş. Tüm hakları saklıdır.</span><div className="flex gap-4"><Link to="/kvkk" className="hover:text-navy">Gizlilik Politikası</Link><a href="#" className="hover:text-navy">Bize Ulaşın</a></div></div>
        </footer>
      )}
    </div>
  );
}

export default App;