import React, { useState } from 'react';
import { 
  CheckCircle2, Lock, Check, User, Shield, ShieldCheck, 
  Calendar, Calculator, ArrowLeft, ArrowRight, Download, FileText 
} from 'lucide-react';

const DashboardWizard = () => {
  // Sihirbaz adım mantığını kuruyoruz (Başlangıçta 2. adımda olduğumuzu varsayıyoruz)
  const [currentStep, setCurrentStep] = useState(2);

  const handleNextStep = () => {
    if (currentStep < 4) setCurrentStep(prev => prev + 1);
  };

  const handlePrevStep = () => {
    if (currentStep > 1) setCurrentStep(prev => prev - 1);
  };

  return (
    <div className="flex-1 bg-[#f8fafc] overflow-y-auto p-6">
       <div className="max-w-7xl mx-auto">
          {/* Üst Bilgi Uyarı Alanı */}
          <div className="bg-teal/10 border border-teal/20 rounded-xl p-4 flex justify-between items-center mb-6">
             <div className="flex items-center gap-3 text-teal">
                 <CheckCircle2 size={24} className="fill-teal text-white"/>
                 <div>
                     <h3 className="font-bold text-sm">Resmi Dilekçe & Belge Sihirbazı</h3>
                     <p className="text-xs text-teal/80">Adalet Bakanlığı UYAP ve Noterler Birliği (TNB) e-işlem format standartlarıyla %100 uyumludur.</p>
                 </div>
             </div>
             <div className="flex gap-4 text-xs font-bold text-teal">
                 <span className="flex items-center gap-1"><Lock size={14}/> 256-Bit Uçtan Uca</span>
                 <span className="bg-white px-2 py-1 rounded text-navy">Belge Kodu: LX-2024-KIR-8421</span>
             </div>
          </div>

          {/* Dinamik Adım Göstergeleri */}
          <div className="flex gap-2 mb-8 overflow-x-auto">
             <div className={`flex-1 rounded-xl p-3 flex items-center gap-3 shrink-0 ${currentStep >= 1 ? 'bg-white border-2 border-teal' : 'bg-white border border-slate-200 opacity-60'}`}>
                 <div className={`w-8 h-8 rounded-full flex justify-center items-center ${currentStep >= 1 ? 'bg-teal text-white' : 'bg-slate-100 text-slate-400 font-bold'}`}>
                     {currentStep > 1 ? <Check size={16}/> : '1'}
                 </div>
                 <div>
                     <p className={`text-[10px] font-bold ${currentStep >= 1 ? 'text-teal' : 'text-slate-400'}`}>1. ADIM</p>
                     <p className="text-xs font-bold text-navy">Kategori & Şablon</p>
                 </div>
             </div>
             
             <div className={`flex-1 rounded-xl p-3 flex items-center gap-3 shrink-0 ${currentStep >= 2 ? (currentStep === 2 ? 'bg-navy text-white shadow-md' : 'bg-white border-2 border-teal') : 'bg-white border border-slate-200 opacity-60'}`}>
                 <div className={`w-8 h-8 rounded-full flex justify-center items-center font-bold ${currentStep === 2 ? 'bg-white text-navy' : (currentStep > 2 ? 'bg-teal text-white' : 'bg-slate-100 text-slate-400')}`}>
                     {currentStep > 2 ? <Check size={16}/> : '2'}
                 </div>
                 <div>
                     <p className={`text-[10px] font-bold ${currentStep === 2 ? 'text-teal' : (currentStep > 2 ? 'text-teal' : 'text-slate-400')}`}>{currentStep === 2 ? 'AKTİF ADIM' : '2. ADIM'}</p>
                     <p className={`text-xs font-bold ${currentStep === 2 ? 'text-white' : 'text-navy'}`}>Taraf & Uyuşmazlık</p>
                 </div>
             </div>

             <div className={`flex-1 rounded-xl p-3 flex items-center gap-3 shrink-0 ${currentStep >= 3 ? (currentStep === 3 ? 'bg-navy text-white shadow-md' : 'bg-white border-2 border-teal') : 'bg-white border border-slate-200 opacity-60'}`}>
                 <div className={`w-8 h-8 rounded-full flex justify-center items-center font-bold ${currentStep === 3 ? 'bg-white text-navy' : (currentStep > 3 ? 'bg-teal text-white' : 'bg-slate-100 text-slate-400')}`}>
                    {currentStep > 3 ? <Check size={16}/> : '3'}
                 </div>
                 <div>
                     <p className={`text-[10px] font-bold ${currentStep === 3 ? 'text-teal' : (currentStep > 3 ? 'text-teal' : 'text-slate-400')}`}>{currentStep === 3 ? 'AKTİF ADIM' : '3. ADIM'}</p>
                     <p className={`text-xs font-bold ${currentStep === 3 ? 'text-white' : 'text-navy'}`}>Deliller & Dayanaklar</p>
                 </div>
             </div>

             <div className={`flex-1 rounded-xl p-3 flex items-center gap-3 shrink-0 ${currentStep === 4 ? 'bg-navy text-white shadow-md' : 'bg-white border border-slate-200 opacity-60'}`}>
                 <div className={`w-8 h-8 rounded-full flex justify-center items-center font-bold ${currentStep === 4 ? 'bg-white text-navy' : 'bg-slate-100 text-slate-400'}`}>
                     4
                 </div>
                 <div>
                     <p className={`text-[10px] font-bold ${currentStep === 4 ? 'text-teal' : 'text-slate-400'}`}>4. ADIM</p>
                     <p className={`text-xs font-bold ${currentStep === 4 ? 'text-white' : 'text-navy'}`}>UYAP / Noter Çıktısı</p>
                 </div>
             </div>
          </div>

          <div className="flex flex-col lg:flex-row gap-6">
             <div className="flex-1 space-y-6">
                
                {/* Şimdilik sadece 2. adımdaki formları gösteriyoruz */}
                {currentStep === 2 ? (
                    <>
                        {/* Taraf Bilgileri Formu */}
                        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="font-bold text-navy flex items-center gap-2"><User size={18}/> 1. Taraf Bilgileri</h3>
                                <span className="text-[10px] font-bold text-teal bg-teal/10 px-2 py-1 rounded flex items-center gap-1"><Shield size={12}/> KVKK Otomatik Maskeleme Açık</span>
                            </div>
                            <div className="mb-6">
                                <p className="text-xs font-bold text-slate-500 mb-3">Muhatap (Ev Sahibi / Kiraya Veren)</p>
                                <div className="grid grid-cols-2 gap-4">
                                    <div><label className="text-[10px] text-slate-400 block mb-1">Ad Soyad / Unvan</label><input type="text" defaultValue="Hikmet Çetin" className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50"/></div>
                                    <div><label className="text-[10px] text-slate-400 block mb-1">T.C. Kimlik / Vergi No</label><div className="relative"><input type="text" defaultValue="38291048214" className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50"/><ShieldCheck className="absolute right-3 top-1/2 -translate-y-1/2 text-teal" size={16}/></div></div>
                                </div>
                            </div>
                            <div>
                                <p className="text-xs font-bold text-slate-500 mb-3 flex justify-between">Keşideci (Kiracı) <span className="text-teal">Profilinizden Aktarıldı</span></p>
                                <div className="grid grid-cols-2 gap-4">
                                    <div><label className="text-[10px] text-slate-400 block mb-1">Ad Soyad</label><input type="text" defaultValue="Av. Tolga Yılmaz" className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50"/></div>
                                    <div><label className="text-[10px] text-slate-400 block mb-1">T.C. Kimlik No</label><input type="text" defaultValue="19482910382" className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50"/></div>
                                </div>
                            </div>
                        </div>

                        {/* Kira Artış Hesaplayıcı */}
                        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                            <h3 className="font-bold text-navy flex items-center gap-2 mb-6"><FileText size={18}/> 2. Kira Sözleşmesi ve Artış Değerleri</h3>
                            <div className="grid grid-cols-3 gap-4 mb-6">
                                <div><label className="text-[10px] text-slate-400 block mb-1">Kira Başlangıç Tarihi</label><div className="relative"><input type="text" defaultValue="09/01/2022" className="w-full border rounded-lg p-2.5 text-sm outline-none bg-slate-50"/><Calendar className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" size={16}/></div></div>
                                <div><label className="text-[10px] text-slate-400 block mb-1">Mevcut Ödenen Kira</label><div className="relative"><input type="text" defaultValue="12000" className="w-full border rounded-lg p-2.5 text-sm outline-none font-bold"/><span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">₺ / ay</span></div></div>
                                <div><label className="text-[10px] text-slate-400 block mb-1">Talep Edilen Kira</label><div className="relative"><input type="text" defaultValue="24000" className="w-full border border-red-300 bg-red-50 text-red-600 rounded-lg p-2.5 text-sm outline-none font-bold"/><span className="absolute right-3 top-1/2 -translate-y-1/2 text-red-400 text-xs">₺ / ay</span></div></div>
                            </div>
                            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 relative overflow-hidden">
                                <div className="flex justify-between items-center mb-4"><div className="flex items-center gap-2 text-teal font-bold text-sm"><Calculator size={16}/> TBK m. 344 Yasal Tavan Artış Hesaplayıcı</div><div className="text-[10px] font-bold text-slate-500 bg-white px-2 py-1 rounded border">TÜFE 12 Aylık Ort.: %62,51</div></div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="bg-white p-3 rounded-lg border"><p className="text-[10px] text-slate-500 font-bold mb-1">Yasal Azami Artış Tutarı</p><p className="text-lg font-bold text-navy">19.501,20 TL</p><p className="text-[10px] text-teal font-bold">+7.501,20 ₺</p></div>
                                    <div className="bg-red-50 p-3 rounded-lg border border-red-200"><p className="text-[10px] text-red-500 font-bold mb-1">Geçersiz Fahiş Fark</p><p className="text-lg font-bold text-red-600">-4.498,80 TL</p><p className="text-[10px] text-red-500 font-bold">Hukuken Hükümsüz Talep</p></div>
                                    <div className="bg-teal/10 p-3 rounded-lg border border-teal/20"><p className="text-[10px] text-teal font-bold mb-1">İhtarda Ödeneceği Bildirilen</p><p className="text-lg font-bold text-navy">19.501,20 TL</p><p className="text-[10px] text-teal font-bold">Yasal Oranda Havale</p></div>
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center text-slate-500">
                        {currentStep}. Adım İçeriği Buraya Gelecek
                    </div>
                )}
                
                {/* DİNAMİK BUTONLAR BURADA */}
                <div className="flex justify-between items-center mt-6">
                  <button 
                    onClick={handlePrevStep}
                    disabled={currentStep === 1}
                    className="bg-white border border-slate-200 text-navy font-bold py-3 px-6 rounded-xl flex items-center gap-2 hover:bg-slate-50 disabled:opacity-50 transition-all"
                  >
                    <ArrowLeft size={16}/> {currentStep > 1 ? `${currentStep - 1}. Adıma Dön` : 'Geri Dönülemez'}
                  </button>
                  
                  <button 
                    onClick={handleNextStep}
                    disabled={currentStep === 4}
                    className="bg-navy text-white font-bold py-3 px-8 rounded-xl flex items-center gap-2 shadow-md hover:bg-navy/90 disabled:opacity-50 transition-all"
                  >
                    {currentStep < 4 ? `${currentStep + 1}. Adıma İlerle` : 'Tamamlandı'} <ArrowRight size={16}/>
                  </button>
                </div>
             </div>

             {/* Canlı A4 Önizleme */}
             <div className="w-full lg:w-[450px] shrink-0">
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 sticky top-6">
                   <div className="flex justify-between items-center mb-4">
                     <h3 className="font-bold text-navy text-sm flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-teal animate-pulse"></div> Canlı Önizleme (A4)</h3>
                     <div className="flex gap-2"><button className="text-[10px] font-bold text-navy bg-slate-100 px-2 py-1 rounded">.UDF</button><button className="text-[10px] font-bold text-navy bg-slate-100 px-2 py-1 rounded">.DOCX</button><button className="bg-teal text-white text-[10px] font-bold px-3 py-1 rounded flex items-center gap-1"><Download size={12}/> İndir</button></div>
                   </div>
                   
                   <div className="w-full aspect-[1/1.414] bg-white border border-slate-200 shadow-inner p-6 overflow-y-auto text-[8px] sm:text-[9px] font-serif text-slate-800 leading-relaxed custom-scrollbar">
                      <div className="flex justify-between mb-8 text-slate-400 border-b border-slate-100 pb-2"><span>LEXORA RESMİ İHTARNAME PROTOKOLÜ</span><span>TARİH: 24.10.2026</span></div>
                      <div className="text-center font-bold mb-6"><p className="text-sm">ANKARA NÖBETÇİ NOTERLİĞİNE</p><p className="italic font-normal">(Muhataba tebliğ edilmek üzere bir nüshası talep edilmektedir)</p></div>
                      <div className="text-center font-bold tracking-[0.3em] mb-8 text-sm">İ H T A R N A M E</div>
                      <table className="w-full mb-6">
                        <tbody>
                          <tr><td className="font-bold w-24 align-top pb-2">KEŞİDECİ:</td><td className="pb-2">Av. Tolga Yılmaz (T.C. Kimlik: 194*****382)</td></tr>
                          <tr><td className="font-bold align-top pb-2">ADRES:</td><td className="pb-2">Ayrancı Mah. Güvenlik Cad. 24/5 Çankaya / ANKARA</td></tr>
                          <tr><td className="font-bold align-top pb-2">MUHATAP:</td><td className="pb-2">Hikmet Çetin (T.C. Kimlik: 382*****214)</td></tr>
                          <tr><td className="font-bold align-top pb-2">KONU:</td><td className="pb-2 font-bold">01/09/2022 başlangıç tarihli kira akdi gereğince talep edilen fahiş kira artışının reddi ile 6098 sayılı TBK m. 344 uyarınca TÜFE 12 aylık ortalamalar tavanı olan %62,51 oranında yasal artış yapılacağının bildirimidir.</td></tr>
                        </tbody>
                      </table>
                      <p className="font-bold mb-2">SAYIN MUHATAP;</p>
                      <p className="mb-2 indent-4 text-justify">1. Tarafınızla akdedilen yukarıda adresi belirtilen taşınmaza ilişkin kira sözleşmesi uyarınca aylık kira bedeli <span className="font-bold underline">12.000,00 TL</span> olarak düzenli biçimde banka hesabınıza eksiksiz yatırılmaktadır.</p>
                      <p className="mb-2 indent-4 text-justify">2. Tarafımıza şahsınızca şifahen iletilen aylık <span className="font-bold text-red-600">24.000,00 TL</span> kira bedeli talebi (%100 artış), 6098 sayılı Türk Borçlar Kanunu'nun (TBK) emredici nitelikteki <span className="font-bold">344/2. fıkrasına</span> açıkça aykırıdır. İlgili kanun maddesi uyarınca yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin anlaşmalar, bir önceki kira yılında Türkiye İstatistik Kurumu (TÜİK) tarafından açıklanan tüketici fiyat endeksindeki on iki aylık ortalamalara göre değişim oranını geçmemek koşuluyla geçerlidir.</p>
                   </div>
                   <div className="mt-4 bg-teal/10 border border-teal/20 rounded-lg p-3 flex items-center gap-3"><CheckCircle2 className="text-teal" size={20}/><div><p className="text-xs font-bold text-navy">UYAP Şablon Doğrulaması Başarılı</p><p className="text-[10px] text-slate-500">UYAP Döküman Editörü (.udf) v4.4 Uyumlu</p></div></div>
                </div>
             </div>
          </div>
       </div>
    </div>
  );
};

export default DashboardWizard;