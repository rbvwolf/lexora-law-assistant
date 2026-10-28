import React, { useState } from 'react';
import DashboardWizard from './components/DashboardWizard';
import DashboardArsiv from './components/DashboardArsiv';
import DashboardRehber from './components/DashboardRehber';
import DashboardDanisAI from './components/DashboardDanisAI';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  Search, ChevronRight, BookOpen, ShieldCheck, FileText, Scale, CheckCircle2, XCircle, AlertTriangle, ArrowRight, Lock, Download, MessageSquare, Bot, ChevronDown, Mail, MessageCircle, File, Server, EyeOff, FileCheck, Network, Database, Shield, Send, MapPin, Check, Eye, LogIn, UserPlus, Landmark, Building2, Info, CreditCard, LayoutDashboard, Briefcase, FolderOpen, HelpCircle, Headphones, User, Calculator, Calendar, Gavel, Clock, ArrowLeft, Plus, Mic, Paperclip, MoreVertical, ExternalLink, RefreshCw, FileLock2, AlertOctagon, History
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
              <div><label className="block text-xs font-bold text-navy mb-2">Şifre</label><input type="password" placeholder="••••••••••••" className="w-full pl-4 pr-4 py-3.5 rounded-xl border border-slate-200 text-sm"/></div>
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