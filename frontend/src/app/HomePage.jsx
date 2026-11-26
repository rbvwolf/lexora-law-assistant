import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, ChevronRight, FileText, Scale, Search, ShieldCheck } from 'lucide-react';
import LexoraLogo from '../components/common/LexoraLogo';

const TOPICS = [
  ['Kira artışına itiraz', 'Ev sahibim kirayı yasal sınırın üzerinde artırdı, itiraz ihtarnamesi hazırlamak istiyorum.'],
  ['Kira temerrüt ihtarı', 'Kiracım iki aydır kira ödemiyor, ne yapabilirim?'],
  ['Ayıplı mal iadesi', 'Aldığım ürün kısa sürede bozuldu, satıcıdan bedel iadesi isteyebilir miyim?'],
  ['İşçi hakları', 'İşverenim ihbar süresi vermeden beni işten çıkardı, haklarım nelerdir?'],
];

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-left">
      <div className="w-10 h-10 rounded-lg bg-slate-50 flex items-center justify-center mb-4 border border-slate-100">{icon}</div>
      <h3 className="text-navy font-semibold text-sm mb-2">{title}</h3>
      <p className="text-slate-500 text-xs leading-relaxed">{desc}</p>
    </div>
  );
}

const HomePage = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const ask = (text) => navigate('/app/danis-ai', { state: { initialMessage: text } });
  const handleSubmit = (event) => {
    event.preventDefault();
    if (query.trim()) ask(query.trim());
    else navigate('/app/danis-ai');
  };

  return (
    <main className="flex-1 flex flex-col items-center text-center px-4 pt-12 md:pt-16 pb-20 relative z-10">
      <div className="mb-6 md:scale-150 transform"><LexoraLogo className="h-16 md:h-20" /></div>
      <h1 className="text-navy font-semibold tracking-widest text-sm mb-4">YAPAY ZEKÂ DESTEKLİ HUKUK ASİSTANI</h1>
      <p className="text-slate-500 max-w-2xl text-base md:text-lg mb-10 leading-relaxed">Hukuki sorunuzu kanun maddeleriyle öğrenin, gerekiyorsa ihtarname taslağınızı birkaç adımda hazırlayıp Word ve PDF olarak indirin.</p>
      <div className="w-full max-w-3xl relative mb-8 group">
        <div className="absolute inset-0 bg-teal/20 blur-xl rounded-full opacity-50 group-hover:opacity-80 transition-opacity"></div>
        <form onSubmit={handleSubmit} role="search" className="relative bg-white rounded-full p-2 flex items-center shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-slate-100">
          <Search className="text-teal ml-4 mr-2 shrink-0" size={20} aria-hidden="true" />
          <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} maxLength={4000} aria-label="Hukuki sorunuz" placeholder="Durumunuzu kısaca yazın..." className="flex-1 min-w-0 bg-transparent border-none outline-none text-sm text-slate-700 placeholder:text-slate-400 py-3" />
          <button type="submit" className="bg-teal hover:bg-teal/90 text-white px-5 md:px-6 py-3 rounded-full text-sm font-medium transition-colors flex items-center gap-2 ml-2 shrink-0">Sor <ChevronRight size={16} /></button>
        </form>
      </div>
      <div className="flex flex-wrap justify-center gap-3 max-w-3xl mb-20">
        {TOPICS.map(([title, question]) => (
          <button type="button" key={title} onClick={() => ask(question)} className="bg-white border border-slate-200 text-slate-600 px-4 py-2 rounded-full text-xs font-medium hover:border-teal hover:text-teal shadow-sm">{title}</button>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl w-full px-4">
        <FeatureCard icon={<BookOpen size={20} className="text-navy" />} title="Kanun maddesi dayanaklı yanıtlar" desc="Yanıtlar TBK (kira ve temerrüt), Tüketicinin Korunması Hakkında Kanun ve İş Kanunu maddelerine atıfla verilir." />
        <FeatureCard icon={<FileText size={20} className="text-amber-600" />} title="Word ve PDF taslak" desc="Kira artışına itiraz ihtarnamesini adım adım doldurun, yasal sınırı otomatik hesaplayın ve iki formatta indirin." />
        <FeatureCard icon={<ShieldCheck size={20} className="text-teal" />} title="Kişisel veri koruması" desc="Kimlik ve iletişim bilgileriniz yapay zekâya gönderilmez; oluşturulan dosyalar kısa süre sonra sunucudan silinir." />
        <FeatureCard icon={<Scale size={20} className="text-purple-600" />} title="Kapsam dışında yönlendirme" desc="Lexora'nın yardımcı olamadığı konularda avukata veya baro adli yardım bürosuna başvurmanızı önerir." />
      </div>
    </main>
  );
};

export default HomePage;
