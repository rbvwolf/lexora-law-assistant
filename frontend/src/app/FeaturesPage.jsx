import { Link } from 'react-router-dom';
import { ArrowRight, BookOpen, Calculator, CheckCircle2, FileText, Lock, MessageSquare, Scale } from 'lucide-react';

const Section = ({ no, tag, title, children }) => (
  <div>
    <span className="bg-slate-200 text-slate-600 px-3 py-1 rounded-md text-[10px] font-bold mb-6 inline-block tracking-widest">{no} {tag}</span>
    <h2 className="text-2xl md:text-3xl font-bold text-navy mb-4 tracking-tight">{title}</h2>
    {children}
  </div>
);

const Point = ({ children }) => (
  <li className="flex gap-3 text-sm text-slate-600 items-start"><CheckCircle2 className="text-teal shrink-0 mt-0.5" size={18} /> <span>{children}</span></li>
);

const FeaturesPage = () => (
  <div className="w-full relative z-10 bg-[#fafafa]">
    <div className="max-w-7xl mx-auto px-6 pt-12 pb-12">
      <span className="bg-teal/10 text-teal px-3 py-1 rounded-full text-[10px] font-bold tracking-widest mb-6 inline-block">NASIL ÇALIŞIR</span>
      <h1 className="text-3xl md:text-[42px] font-bold text-navy mb-6 leading-tight tracking-tight max-w-3xl">Sorunuzu anlatın, ilgili kanun maddelerini görün, gerekiyorsa belgenizi hazırlayın</h1>
      <p className="text-slate-500 text-lg leading-relaxed max-w-2xl">Lexora kira, tüketici ve iş hukukundaki yaygın sorunlar için bilgi veren ve ihtarname taslağı hazırlayan bir yapay zekâ asistanıdır. Avukatlık hizmeti yerine geçmez.</p>
    </div>

    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="flex flex-col lg:flex-row gap-12 lg:gap-16 items-center">
        <div className="flex-1">
          <Section no="01" tag="DANIŞ AI" title="Kanun maddesine dayanan yanıtlar">
            <p className="text-slate-500 mb-6 leading-relaxed">Sorunuz önce sınıflandırılır: bilgi mi istiyorsunuz, belge mi hazırlamak istiyorsunuz, yoksa konu kapsam dışında mı? Bilgi sorularında sistem, yüklü kanun metinlerinde madde bazında arama yapar ve yanıtı bu maddelere atıfla verir.</p>
            <ul className="space-y-3">
              <Point>Kaynaklar: TBK kira ve temerrüt hükümleri, Tüketicinin Korunması Hakkında Kanun, İş Kanunu.</Point>
              <Point>Her yanıtın altında dayanak madde numaraları ve ilgili metin parçası gösterilir.</Point>
              <Point>Belge gerektiren durumlarda uygun şablon önerilir ve sihirbaza geçilir.</Point>
            </ul>
          </Section>
        </div>
        <div className="flex-1 w-full bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
          <div className="bg-navy text-white text-sm rounded-2xl rounded-tr-none p-4 ml-auto max-w-[85%] mb-4">Ev sahibim kirayı %100 artırmak istiyor, bu yasal mı?</div>
          <div className="border border-slate-200 rounded-2xl rounded-tl-none p-4 max-w-[90%]">
            <p className="text-xs text-slate-600 leading-relaxed mb-3">Konut kiralarında yenilenen dönem için kira artışı, bir önceki kira yılındaki TÜFE on iki aylık ortalama değişim oranını geçemez...</p>
            <span className="text-[11px] font-bold text-teal bg-teal/5 border border-teal/10 px-2 py-1 rounded-lg inline-flex items-center gap-1"><Scale size={12} /> TBK m. 344</span>
          </div>
        </div>
      </div>
    </div>

    <div className="bg-white border-y border-slate-100">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="flex flex-col lg:flex-row-reverse gap-12 lg:gap-16 items-center">
          <div className="flex-1">
            <Section no="02" tag="BELGE SİHİRBAZI" title="Kira artışına itiraz ihtarnamesi">
              <p className="text-slate-500 mb-6 leading-relaxed">Olay bilgilerini ve taraf bilgilerini dört adımda girersiniz. Sistem TBK m. 344&apos;e göre yasal azami kirayı hesaplar ve belgeyi aynı veriden hem Word (.docx) hem PDF olarak üretir.</p>
              <ul className="space-y-3">
                <Point>Sohbette anlattığınız bilgiler forma otomatik aktarılır, eksik alanlar sorulur.</Point>
                <Point>Canlı önizlemede belgenin son halini indirmeden görürsünüz.</Point>
                <Point>Temerrüt ihtarnamesi ve ayıplı mal başvurusu şablonları geliştirme aşamasındadır.</Point>
              </ul>
            </Section>
          </div>
          <div className="flex-1 w-full bg-slate-50 p-6 rounded-3xl border border-slate-100">
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center gap-2 text-teal font-bold text-sm mb-4"><Calculator size={16} /> TBK m. 344 yasal tavan hesabı</div>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div><p className="text-[10px] text-slate-500 font-bold">Mevcut kira</p><p className="font-bold text-navy">12.000 TL</p></div>
                <div><p className="text-[10px] text-slate-500 font-bold">TÜFE ort.</p><p className="font-bold text-navy">%62,51</p></div>
                <div><p className="text-[10px] text-teal font-bold">Yasal azami</p><p className="font-bold text-navy">19.501,20 TL</p></div>
              </div>
              <p className="text-[10px] text-slate-400 mt-4">Örnek değerlerdir. TÜFE oranını kullanıcı girer; sistem tahmin etmez.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div className="max-w-7xl mx-auto px-6 py-16">
      <div className="flex flex-col lg:flex-row gap-12 lg:gap-16 items-center">
        <div className="flex-1">
          <Section no="03" tag="KİŞİSEL VERİ" title="Kişisel veriler yapay zekâya ulaşmaz">
            <p className="text-slate-500 mb-6 leading-relaxed">Ad, T.C. kimlik no, IBAN ve adres gibi bilgiler sohbete değil, sihirbazdaki ayrı forma girilir ve yalnızca belge üretiminde kullanılır. Sohbete yanlışlıkla yazılan kimlik numarası, IBAN, telefon ve e-posta ise sunucuda, yapay zekâya gönderilmeden önce maskelenir.</p>
            <ul className="space-y-3">
              <Point>Oluşturulan belgeler kalıcı saklanmaz, kısa bir süre sonra sunucudan otomatik silinir.</Point>
              <Point>İzleme kayıtlarına da maskelenmiş metin yazılır.</Point>
            </ul>
          </Section>
        </div>
        <div className="flex-1 w-full bg-slate-50 p-6 rounded-3xl border border-slate-100 space-y-4">
          <div className="bg-white p-4 rounded-xl border border-red-100 shadow-sm relative"><span className="absolute -top-3 right-4 bg-red-100 text-red-600 text-[9px] font-bold px-2 py-1 rounded-full">GELEN MESAJ</span><p className="text-[11px] font-mono text-slate-500 leading-relaxed">T.C. no&apos;m <span className="bg-red-50 text-red-600 font-bold px-1 rounded">12345678901</span>, kirayı <span className="bg-red-50 text-red-600 font-bold px-1 rounded">TR12 0006 ...</span> hesabına yatırıyorum.</p></div>
          <div className="bg-navy p-4 rounded-xl shadow-lg relative"><span className="absolute -top-3 right-4 bg-teal text-white text-[9px] font-bold px-2 py-1 rounded-full flex items-center gap-1"><Lock size={10} /> YAPAY ZEKÂYA GİDEN</span><p className="text-[11px] font-mono text-slate-300 leading-relaxed">T.C. no&apos;m <span className="bg-teal/20 text-teal font-bold px-1 rounded">[TC_NO]</span>, kirayı <span className="bg-teal/20 text-teal font-bold px-1 rounded">[IBAN]</span> hesabına yatırıyorum.</p></div>
        </div>
      </div>
    </div>

    <div className="max-w-7xl mx-auto px-6 pb-20">
      <div className="bg-navy rounded-3xl p-8 md:p-10 text-white flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h2 className="text-xl md:text-2xl font-bold mb-2">Hemen deneyin</h2>
          <p className="text-sm text-slate-400">Üyelik gerekmez. Sorunuzu yazın ya da doğrudan belge sihirbazını açın.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link to="/app/danis-ai" className="bg-teal hover:bg-teal/90 text-white text-sm font-bold px-5 py-3 rounded-xl flex items-center gap-2"><MessageSquare size={16} /> Danış AI</Link>
          <Link to="/app/sihirbaz" className="bg-white text-navy text-sm font-bold px-5 py-3 rounded-xl flex items-center gap-2"><FileText size={16} /> Belge sihirbazı <ArrowRight size={16} /></Link>
          <Link to="/app/rehber" className="text-white/80 hover:text-white text-sm font-bold px-3 py-3 flex items-center gap-2"><BookOpen size={16} /> Hak rehberi</Link>
        </div>
      </div>
    </div>
  </div>
);

export default FeaturesPage;
