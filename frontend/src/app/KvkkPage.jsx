import { Clock, EyeOff, FileLock2, Lock, ShieldCheck } from 'lucide-react';

const LAYERS = [
  {
    icon: <FileLock2 size={24} />, tone: 'bg-teal/10 text-teal',
    title: 'Ayrı kişisel bilgi formu',
    text: 'Ad, T.C. kimlik no, IBAN ve adres yalnızca belge sihirbazındaki forma girilir ve doğrudan belge üretimine gider; yapay zekâ modeline gönderilmez.',
  },
  {
    icon: <EyeOff size={24} />, tone: 'bg-blue-50 text-blue-600',
    title: 'Sohbette maskeleme',
    text: 'Sohbete yanlışlıkla yazılan T.C. kimlik no, IBAN, telefon ve e-posta, mesaj yapay zekâya iletilmeden önce sunucuda [TC_NO], [IBAN] gibi etiketlerle değiştirilir.',
  },
  {
    icon: <Clock size={24} />, tone: 'bg-amber-50 text-amber-600',
    title: 'Kalıcı saklama yok',
    text: 'Oluşturulan Word ve PDF dosyaları geçici olarak tutulur ve süre dolunca sunucudan otomatik silinir. Tarayıcıdaki belge listesi de sekme kapanınca silinir.',
  },
  {
    icon: <Lock size={24} />, tone: 'bg-purple-50 text-purple-600',
    title: 'Maskelenmiş kayıtlar',
    text: 'Sistemin izleme ve hata kayıtlarına kişisel veriler maskelenmiş olarak yazılır; doğrulama hata mesajlarında yalnızca alan adları yer alır, değerler yer almaz.',
  },
];

const KvkkPage = () => (
  <div className="w-full relative z-10 bg-[#fafafa]">
    <div className="max-w-7xl mx-auto px-6 pt-12 md:pt-16 pb-12">
      <span className="bg-teal/10 text-teal px-3 py-1 rounded-full text-[10px] font-bold tracking-widest mb-6 inline-flex items-center gap-1"><ShieldCheck size={12} /> KİŞİSEL VERİLERİN KORUNMASI</span>
      <h1 className="text-3xl md:text-5xl font-bold text-navy mb-6 leading-tight max-w-3xl">Kişisel verilerinizi nasıl koruyoruz?</h1>
      <p className="text-slate-500 text-lg leading-relaxed max-w-3xl">Lexora, 6698 sayılı Kişisel Verilerin Korunması Kanunu&apos;nun veri minimizasyonu ilkesi gözetilerek tasarlanmıştır: belge için gereken bilgiler dışında kişisel veri toplanmaz ve hiçbir kişisel veri kalıcı olarak saklanmaz.</p>
    </div>
    <div className="max-w-7xl mx-auto px-6 pb-12">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {LAYERS.map((layer, i) => (
          <div key={layer.title} className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-6 ${layer.tone}`}>{layer.icon}</div>
            <span className="text-[10px] font-bold text-slate-400 mb-2 block">KATMAN 0{i + 1}</span>
            <h2 className="font-bold text-navy text-lg mb-3">{layer.title}</h2>
            <p className="text-xs text-slate-500 leading-relaxed">{layer.text}</p>
          </div>
        ))}
      </div>
    </div>
    <div className="max-w-7xl mx-auto px-6 pb-20">
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-sm text-amber-900 leading-relaxed">
        <p className="font-bold mb-1">Önerimiz</p>
        <p>Sohbette kişisel bilgilerinizi paylaşmayın; durumunuzu genel ifadelerle anlatın. Belge için gereken bilgileri yalnızca sihirbazdaki kişisel bilgi formuna girin.</p>
      </div>
    </div>
  </div>
);

export default KvkkPage;
