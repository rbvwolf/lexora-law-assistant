import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ChevronDown, MessageSquare, Search } from 'lucide-react';

const FAQS = [
  {
    tag: 'Kapsam',
    q: 'Lexora avukatlık hizmeti verir mi?',
    a: 'Hayır. Lexora bir yapay zekâ asistanıdır; bilgilendirme yapar ve belge taslağı hazırlar. Hukuki temsil, dava takibi veya kesin hukuki görüş vermez. Önemli kararlardan önce bir avukata danışmanızı öneririz.',
  },
  {
    tag: 'Kapsam',
    q: 'Hangi konularda yardımcı olabilir?',
    a: 'Şu an kira hukuku (kira artışı, kira ödenmemesi), tüketici hukuku (ayıplı mal) ve iş hukukunun temel konularında bilgi verir. Ceza, aile, vergi gibi alanlar kapsam dışındadır; bu tür sorularda sizi avukata veya baro adli yardım bürosuna yönlendirir.',
  },
  {
    tag: 'Belge',
    q: 'Hangi belgeleri hazırlayabilirim?',
    a: 'Fahiş kira artışına itiraz ihtarnamesi hazırdır. Kira temerrüt ihtarnamesi ve ayıplı mal başvurusu şablonları geliştirme aşamasındadır. Belgeler Word (.docx) ve PDF olarak indirilir.',
  },
  {
    tag: 'Belge',
    q: 'Üretilen belgeyi doğrudan kullanabilir miyim?',
    a: 'Belge bir taslaktır. Göndermeden önce bilgileri kontrol edin, gerekirse Word dosyası üzerinde düzenleyin ve mümkünse bir avukata gösterin. İhtarnameler genellikle noter aracılığıyla karşı tarafa tebliğ edilir.',
  },
  {
    tag: 'Doğruluk',
    q: 'Yapay zekâ yanlış bilgi verebilir mi?',
    a: 'Verebilir. Riski azaltmak için yanıtlar yalnızca sisteme yüklü kanun maddelerine dayanır ve dayanak madde numaraları her yanıtın altında gösterilir. Yine de yanıtları ilgili madde metniyle karşılaştırmanız önerilir.',
  },
  {
    tag: 'Kişisel veri',
    q: 'Kişisel bilgilerim nasıl korunuyor?',
    a: 'Ad, T.C. kimlik no, IBAN ve adres bilgileri sihirbazdaki ayrı forma girilir ve yapay zekâya gönderilmez. Sohbete yanlışlıkla yazılan kimlik numarası, IBAN, telefon ve e-posta yapay zekâya gitmeden önce sunucuda maskelenir. Oluşturulan belgeler kısa bir süre sonra sunucudan otomatik silinir.',
  },
  {
    tag: 'Kullanım',
    q: 'Üye olmam gerekiyor mu?',
    a: 'Hayır. Sohbet ve belge sihirbazı üyelik olmadan kullanılabilir. Oluşturduğunuz belgeler yalnızca açık olan tarayıcı sekmesinde, indirme süresi boyunca "Belgelerim" ekranında listelenir.',
  },
];

const normalize = (text) => text.toLocaleLowerCase('tr-TR');

const FaqPage = () => {
  const [openQ, setOpenQ] = useState(0);
  const [query, setQuery] = useState('');

  const visible = useMemo(() => {
    const q = normalize(query.trim());
    return q ? FAQS.filter((f) => normalize(`${f.q} ${f.a} ${f.tag}`).includes(q)) : FAQS;
  }, [query]);

  return (
    <div className="w-full relative z-10 bg-[#fafafa] pb-24">
      <div className="bg-gradient-to-b from-blue-50/50 to-transparent pt-12 md:pt-16 pb-10 px-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-bold text-navy mb-4 leading-tight">Sıkça Sorulan Sorular</h1>
          <p className="text-slate-500 leading-relaxed mb-6 max-w-2xl">Lexora&apos;nın neler yapabildiği, sınırları ve kişisel verilerinizi nasıl koruduğu hakkında kısa yanıtlar.</p>
          <div className="relative w-full max-w-lg">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} aria-hidden="true" />
            <input type="search" value={query} onChange={(e) => { setQuery(e.target.value); setOpenQ(null); }} aria-label="Sorularda ara" placeholder="Soru ara..." className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-slate-200 shadow-sm text-sm outline-none focus:border-teal" />
          </div>
        </div>
      </div>
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex flex-col lg:flex-row gap-8">
          <div className="flex-1 space-y-4">
            {visible.length === 0 && <p className="text-sm text-slate-500">Aramanızla eşleşen soru bulunamadı. Sorunuzu Danış AI&apos;a sorabilirsiniz.</p>}
            {visible.map((faq, idx) => {
              const open = openQ === idx || (query.trim() !== '' && openQ === null);
              return (
                <div key={faq.q} className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
                  <button type="button" aria-expanded={open} onClick={() => setOpenQ(openQ === idx ? -1 : idx)} className="w-full text-left p-6 flex justify-between items-center gap-4">
                    <div><span className="text-[10px] font-bold text-teal bg-teal/10 px-2 py-1 rounded-md mb-2 inline-block">{faq.tag}</span><h2 className="text-navy font-semibold text-sm">{faq.q}</h2></div>
                    <ChevronDown className={`text-slate-400 transition-transform shrink-0 ${open ? 'rotate-180' : ''}`} size={20} />
                  </button>
                  {open && <div className="px-6 pb-6 text-slate-500 text-sm leading-relaxed border-t border-slate-50 pt-4">{faq.a}</div>}
                </div>
              );
            })}
          </div>
          <div className="w-full lg:w-80">
            <div className="bg-navy rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl"></div>
              <h2 className="font-bold text-lg mb-2 relative z-10">Sorunuzu bulamadınız mı?</h2>
              <p className="text-xs text-slate-400 mb-5 relative z-10">Durumunuzu Danış AI&apos;a yazın; ilgili kanun maddeleriyle yanıtlasın.</p>
              <Link to="/app/danis-ai" className="bg-teal text-white px-5 py-2.5 rounded-xl text-sm font-bold inline-flex items-center gap-2 relative z-10"><MessageSquare size={16} /> Danış AI&apos;a sor <ArrowRight size={16} /></Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FaqPage;
