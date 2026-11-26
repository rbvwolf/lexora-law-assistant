import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, BookOpen, Briefcase, Building2, Clock, FileText, Info, Landmark, MessageSquare, Scale, ShoppingBag, Wallet } from 'lucide-react';
import { KIRA_ARTIS_TEMPLATE_ID } from '../lib/fields';

/**
 * Fixed, rule-based guides for the in-scope topics (roadmap idea 4, "1-2 sabit akış").
 * Article summaries are paraphrases, not quotations; mentors should review the wording.
 */
const GUIDES = [
  {
    id: 'kira-artisi',
    icon: Building2,
    domain: 'Kira Hukuku',
    title: 'Ev sahibi kirayı ne kadar artırabilir?',
    lead: 'Konut ve çatılı işyeri kiralarında yenilenen kira dönemi için yapılacak artışın kanuni bir üst sınırı vardır.',
    summary: [
      'Yeni kira döneminde artış, bir önceki kira yılındaki TÜFE on iki aylık ortalama değişim oranını geçemez.',
      'Bu sınırı aşan bir artış talebinin, sınırı aşan kısmını kabul etmek zorunda değilsiniz.',
      'Beş yılı dolduran kira ilişkilerinde yeni kira bedeli, dava açılırsa hâkim tarafından hakkaniyete göre belirlenebilir.',
    ],
    articles: [['TBK m. 344', 'Kira bedelinin belirlenmesi ve artış sınırı']],
    steps: [
      'Sözleşme başlangıç tarihinizi ve mevcut kira bedelinizi belirleyin.',
      'TÜİK tarafından ilan edilen ilgili aya ait TÜFE on iki aylık ortalama değişim oranını öğrenin.',
      'Talep edilen artış bu oranı aşıyorsa, itirazınızı yazılı olarak (genellikle noter aracılığıyla) bildirin.',
    ],
    question: 'Ev sahibim kirayı yasal sınırın üzerinde artırmak istiyor, ne yapabilirim?',
    templateId: KIRA_ARTIS_TEMPLATE_ID,
  },
  {
    id: 'kira-temerrut',
    icon: Wallet,
    domain: 'Kira Hukuku',
    title: 'Kira ödenmezse ne olur?',
    lead: 'Kiracı muaccel kira bedelini ödemezse kiraya veren yazılı bir ihtarla ödeme süresi vererek sözleşmeyi feshetme yoluna gidebilir.',
    summary: [
      'Kiraya veren, kiracıya yazılı olarak bir ödeme süresi verir ve bu süre içinde ödeme yapılmazsa sözleşmeyi feshedeceğini bildirir.',
      'Konut ve çatılı işyeri kiralarında bu süre en az otuz gündür.',
      'Süre içinde ödeme yapılmazsa kiraya veren sözleşmeyi feshedebilir ve tahliye yoluna gidebilir.',
    ],
    articles: [['TBK m. 315', 'Kiracının ödeme borcunda temerrüdü']],
    steps: [
      'Ödenmeyen ayları ve tutarları belirleyin.',
      'Kiracıya en az 30 günlük süre veren yazılı bir ihtarname gönderin.',
      'Süre sonunda ödeme yapılmazsa izlenecek yol için bir avukata danışın.',
    ],
    question: 'Kiracım iki aydır kira ödemiyor, ne yapabilirim?',
    templateId: null, // kira_ihtarname_temerrut is still a placeholder on the backend
  },
  {
    id: 'ayipli-mal',
    icon: ShoppingBag,
    domain: 'Tüketici Hukuku',
    title: 'Aldığım ürün ayıplı çıktı, haklarım neler?',
    lead: 'Tüketici, ayıplı mal durumunda kanunda sayılan seçimlik haklardan birini kullanabilir.',
    summary: [
      'Sözleşmeden dönme, ayıp oranında bedelden indirim, ücretsiz onarım veya ayıpsız bir misliyle değiştirme haklarından birini seçebilirsiniz.',
      'Satıcı, seçtiğiniz hakkı yerine getirmekle yükümlüdür; bazı durumlarda orantısızlık gerekçesiyle başka bir hakkı önerebilir.',
      'Ayıplı maldan doğan sorumluluk için genel kural, teslimden itibaren iki yıllık zamanaşımı süresidir.',
    ],
    articles: [['TKHK m. 11', 'Tüketicinin seçimlik hakları'], ['TKHK m. 12', 'Zamanaşımı']],
    steps: [
      'Fatura, teslim tarihi ve ayıbı gösteren belgeleri (fotoğraf, servis raporu) saklayın.',
      'Kullanmak istediğiniz seçimlik hakkı satıcıya yazılı olarak bildirin.',
      'Sonuç alamazsanız parasal sınıra göre Tüketici Hakem Heyeti veya tüketici mahkemesine başvurabilirsiniz.',
    ],
    question: 'Aldığım ürün kısa sürede bozuldu, satıcıdan bedel iadesi isteyebilir miyim?',
    templateId: null,
  },
  {
    id: 'ihbar-suresi',
    icon: Briefcase,
    domain: 'İş Hukuku',
    title: 'İşten çıkarılırken bildirim süresi',
    lead: 'Belirsiz süreli iş sözleşmesini feshetmek isteyen taraf, kıdeme göre değişen bildirim sürelerine uymak zorundadır.',
    summary: [
      'Bildirim süresi, iş ilişkisinin süresine göre iki ila sekiz hafta arasında değişir.',
      'İşveren bu süreye uymazsa, süreye ait ücret tutarında ihbar tazminatı ödemekle yükümlüdür.',
      'İşveren, bildirim süresine ait ücreti peşin ödeyerek sözleşmeyi hemen sona erdirebilir.',
    ],
    articles: [['İş Kanunu m. 17', 'Süreli fesih ve bildirim süreleri']],
    steps: [
      'İşe giriş tarihinizi ve fesih bildiriminin size ulaştığı tarihi not edin.',
      'Çalışma sürenize karşılık gelen bildirim süresini kontrol edin.',
      'İşe iade gibi talepler için arabuluculuğa başvuru sürelerinin kısa olduğunu unutmayın; vakit kaybetmeden bir avukata danışın.',
    ],
    question: 'İşverenim ihbar süresi vermeden beni işten çıkardı, haklarım nelerdir?',
    templateId: null,
  },
];

const DashboardRehber = () => {
  const navigate = useNavigate();
  const [activeId, setActiveId] = useState(GUIDES[0].id);
  const guide = GUIDES.find((g) => g.id === activeId) ?? GUIDES[0];

  const ask = () => navigate('/app/danis-ai', { state: { initialMessage: guide.question } });
  const prepare = () => navigate('/app/sihirbaz', { state: { templateId: guide.templateId, extractedParams: {}, source: 'rehber' } });

  return (
    <div className="flex-1 bg-[#f8fafc] overflow-y-auto custom-scrollbar">
      <div className="p-6 max-w-7xl mx-auto flex flex-col lg:flex-row gap-6">
        <nav className="w-full lg:w-72 shrink-0" aria-label="Rehber konuları">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 lg:sticky lg:top-0">
            <h2 className="text-xs font-bold text-slate-500 mb-4 flex items-center gap-2"><BookOpen size={16} /> Hak Rehberi</h2>
            <ul className="space-y-1">
              {GUIDES.map((g) => {
                const Icon = g.icon;
                const active = g.id === activeId;
                return (
                  <li key={g.id}>
                    <button type="button" onClick={() => setActiveId(g.id)} aria-current={active ? 'page' : undefined}
                      className={`w-full text-left flex items-start gap-2 px-3 py-2.5 rounded-lg text-sm ${active ? 'bg-teal/5 text-teal font-bold border border-teal/10' : 'text-slate-600 hover:bg-slate-50 font-medium'}`}>
                      <Icon size={16} className="shrink-0 mt-0.5" />
                      <span><span className="block text-[10px] text-slate-400 font-bold">{g.domain}</span>{g.title}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </nav>

        <article className="flex-1 min-w-0">
          <p className="text-[10px] font-bold text-teal mb-2">{guide.domain}</p>
          <h1 className="text-2xl md:text-3xl font-bold text-navy mb-3">{guide.title}</h1>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">{guide.lead}</p>

          <section className="bg-white border-l-4 border-navy shadow-sm rounded-r-2xl p-6 mb-6">
            <h2 className="font-bold text-navy mb-3">Kısaca</h2>
            <ol className="list-decimal pl-5 space-y-2 text-sm text-slate-600 leading-relaxed">
              {guide.summary.map((item) => <li key={item}>{item}</li>)}
            </ol>
          </section>

          <section className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm mb-6">
            <h2 className="font-bold text-navy mb-3 flex items-center gap-2"><Clock size={18} className="text-teal" /> Ne yapabilirsiniz?</h2>
            <ol className="space-y-3">
              {guide.steps.map((step, i) => (
                <li key={step} className="flex gap-3 text-sm text-slate-600 leading-relaxed">
                  <span className="w-6 h-6 rounded-full bg-navy text-white text-[11px] font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </section>

          <div className="bg-navy rounded-2xl p-6 md:p-8 text-white flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-lg">
            <div>
              <h2 className="font-bold text-lg mb-1">Durumunuza özel yanıt alın</h2>
              <p className="text-xs text-slate-400">Danış AI sorunuzu ilgili kanun maddeleriyle yanıtlar.</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button type="button" onClick={ask} className="bg-teal hover:bg-teal/90 text-white text-sm font-bold py-3 px-5 rounded-xl flex items-center gap-2"><MessageSquare size={16} /> Danış AI&apos;a sor</button>
              {guide.templateId && (
                <button type="button" onClick={prepare} className="bg-white text-navy text-sm font-bold py-3 px-5 rounded-xl flex items-center gap-2"><FileText size={16} /> İhtarnameyi hazırla <ArrowRight size={16} /></button>
              )}
            </div>
          </div>
        </article>

        <aside className="w-full lg:w-72 shrink-0 space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
            <h2 className="font-bold text-navy text-sm flex items-center gap-2 mb-3"><Scale size={16} className="text-teal" /> İlgili kanun maddeleri</h2>
            <ul className="space-y-2">
              {guide.articles.map(([no, name]) => (
                <li key={no} className="text-xs"><span className="font-bold text-teal">{no}</span> <span className="text-slate-500">· {name}</span></li>
              ))}
            </ul>
          </div>
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5">
            <h2 className="font-bold text-navy text-sm flex items-center gap-2 mb-2"><Landmark size={16} className="text-teal" /> Avukata ihtiyacınız varsa</h2>
            <p className="text-xs text-slate-600 leading-relaxed">Maddi imkânınız yoksa bulunduğunuz ilin barosundaki adli yardım bürosuna başvurarak ücretsiz avukat desteği isteyebilirsiniz.</p>
          </div>
          <p className="text-[11px] text-slate-500 flex items-start gap-1.5 leading-relaxed"><Info size={13} className="shrink-0 mt-px" /> Bu sayfa genel bilgilendirme amaçlıdır; somut durumunuzun değerlendirilmesi yerine geçmez.</p>
        </aside>
      </div>
    </div>
  );
};

export default DashboardRehber;
