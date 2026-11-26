import { Eye } from 'lucide-react';
import {
  KIRA_ARTIS_TEMPLATE_ID,
  TEMERRUT_TEMPLATE_ID,
  formatTrDate,
  formatTrNumber,
  hesaplaKiraArtisi,
  isBlank,
  maskSensitive,
  parseNumber,
} from '../../lib/fields';
import { DISCLAIMER_TEXT } from '../../lib/constants';

/**
 * Live A4 preview built in the browser from the form values. Nothing here is sent anywhere.
 * The kira artışı and temerrüt texts mirror backend/app/services/doc_layouts.py; the downloaded file is the
 * authoritative version.
 */

const Slot = ({ value, label, bold = false }) =>
  isBlank(value)
    ? <span className="bg-amber-100 text-amber-800 px-1 rounded not-italic">[{label}]</span>
    : <span className={bold ? 'font-bold' : undefined}>{value}</span>;

const today = () => new Date().toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' });

function KiraArtisPreview({ caseValues: c, piiValues: p }) {
  const calc = hesaplaKiraArtisi(c.mevcut_kira_tutari, c.talep_edilen_kira_tutari, c.tufe_oran);
  const money = (v) => (Number.isFinite(parseNumber(v)) ? formatTrNumber(parseNumber(v)) : '');
  const tc = (v) => (isBlank(v) ? '' : ` (T.C. Kimlik No: ${maskSensitive(v)})`);
  const date = isBlank(c.kira_baslangic_tarihi) ? '' : formatTrDate(c.kira_baslangic_tarihi);

  return (
    <>
      <p className="text-center font-bold"><Slot value={c.noter_ili} label="Noterlik ili" /> Nöbetçi Noterliğine</p>
      <p className="text-center font-bold tracking-[0.3em] my-3">İHTARNAME</p>
      <p><b>KEŞİDECİ (Kiracı): </b><Slot value={p.kiraci_ad_soyad} label="Kiracı adı" />{tc(p.kiraci_tc)}</p>
      <p><b>Adres: </b><Slot value={p.kiraci_adres} label="Kiracı adresi" /></p>
      <p><b>MUHATAP (Kiraya Veren): </b><Slot value={p.kiraya_veren_ad_soyad} label="Kiraya veren adı" />{tc(p.kiraya_veren_tc)}</p>
      <p><b>Adres: </b><Slot value={p.kiraya_veren_adres} label="Kiraya veren adresi" /></p>
      <p><b>KİRALANAN: </b><Slot value={p.tasinmaz_adresi} label="Taşınmaz adresi" /></p>
      <p className="text-justify"><b>KONU: </b><Slot value={date} label="Başlangıç tarihi" /> başlangıç tarihli kira sözleşmesine ilişkin olarak talep edilen kira artışının, 6098 sayılı Türk Borçlar Kanunu m. 344 uyarınca yasal sınırı aştığının ve bu sınırı aşan kısmın kabul edilmediğinin bildirilmesidir.</p>
      <p className="font-bold mt-2">AÇIKLAMALAR:</p>
      <p className="indent-6 text-justify">1. Yukarıda adresi belirtilen taşınmazı, <Slot value={date} label="Başlangıç tarihi" /> başlangıç tarihli kira sözleşmesi uyarınca kiracı sıfatıyla kullanmaktayım. Mevcut aylık kira bedeli <Slot value={money(c.mevcut_kira_tutari)} label="Mevcut kira" bold /> <b>TL</b>&apos;dir.</p>
      <p className="indent-6 text-justify">2. Tarafınızca yeni kira dönemi için aylık <Slot value={money(c.talep_edilen_kira_tutari)} label="Talep edilen kira" bold /> <b>TL</b> kira bedeli talep edilmiştir. Bu talep, mevcut kira bedeline göre %<Slot value={calc ? formatTrNumber(calc.talepArtisOrani) : ''} label="oran" /> oranında bir artışa karşılık gelmektedir.</p>
      <p className="indent-6 text-justify">3. 6098 sayılı Türk Borçlar Kanunu&apos;nun 344. maddesinin birinci fıkrası uyarınca, tarafların yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin anlaşmaları, bir önceki kira yılında tüketici fiyat endeksindeki on iki aylık ortalamalara göre değişim oranını geçmemek koşuluyla geçerlidir. Bu oran %<Slot value={money(c.tufe_oran)} label="TÜFE oranı" /> olup, buna göre yeni kira döneminde uygulanabilecek azami aylık kira bedeli <Slot value={calc ? formatTrNumber(calc.azami) : ''} label="Yasal azami kira" bold /> <b>TL</b>&apos;dir.</p>
      <p className="indent-6 text-justify">4. Açıklanan nedenlerle, yasal sınırı aşan kira artışı talebinizi kabul etmediğimi; yeni kira döneminde aylık kira bedelini yasal sınır olan <Slot value={calc ? formatTrNumber(calc.azami) : ''} label="Yasal azami kira" bold /> <b>TL</b> üzerinden ödeyeceğimi bildiririm.</p>
      <p className="font-bold mt-2">SONUÇ:</p>
      <p className="indent-6 text-justify">İşbu ihtarnamenin bir suretinin muhataba tebliğini, bir suretinin dairenizde saklanmasını ve tebliğ şerhini havi bir suretinin tarafıma verilmesini saygılarımla talep ederim.</p>
      <div className="text-right mt-3 space-y-0.5">
        <p>{today()}</p>
        <p className="font-bold">Keşideci</p>
        <p><Slot value={p.kiraci_ad_soyad} label="Kiracı adı" /></p>
        <p>İmza</p>
      </div>
    </>
  );
}

function TemerrutPreview({ caseValues: c, piiValues: p }) {
  const money = (v) => (Number.isFinite(parseNumber(v)) ? formatTrNumber(parseNumber(v)) : '');
  const tc = (v) => (isBlank(v) ? '' : ` (T.C. Kimlik No: ${maskSensitive(v)})`);
  const date = isBlank(c.kira_baslangic_tarihi) ? '' : formatTrDate(c.kira_baslangic_tarihi);
  const sure = Number.isFinite(parseNumber(c.odeme_suresi_gun)) ? String(parseNumber(c.odeme_suresi_gun)) : '';
  const toplam = money(c.odenmeyen_toplam_tutar);

  return (
    <>
      <p className="text-center font-bold"><Slot value={c.noter_ili} label="Noterlik ili" /> Nöbetçi Noterliğine</p>
      <p className="text-center font-bold tracking-[0.3em] my-3">İHTARNAME</p>
      <p><b>KEŞİDECİ (Kiraya Veren): </b><Slot value={p.kiraya_veren_ad_soyad} label="Kiraya veren adı" />{tc(p.kiraya_veren_tc)}</p>
      <p><b>Adres: </b><Slot value={p.kiraya_veren_adres} label="Kiraya veren adresi" /></p>
      <p><b>MUHATAP (Kiracı): </b><Slot value={p.kiraci_ad_soyad} label="Kiracı adı" />{tc(p.kiraci_tc)}</p>
      <p><b>Adres: </b><Slot value={p.kiraci_adres} label="Kiracı adresi" /></p>
      <p><b>KİRALANAN: </b><Slot value={p.tasinmaz_adresi} label="Taşınmaz adresi" /></p>
      <p className="text-justify"><b>KONU: </b>Ödenmeyen kira bedellerinin 6098 sayılı Türk Borçlar Kanunu m. 315 uyarınca verilen süre içinde ödenmesi, aksi halde kira sözleşmesinin feshedileceğinin ihtarıdır.</p>
      <p className="font-bold mt-2">AÇIKLAMALAR:</p>
      <p className="indent-6 text-justify">1. Yukarıda adresi belirtilen taşınmaz, <Slot value={date} label="Başlangıç tarihi" /> başlangıç tarihli kira sözleşmesi ile tarafınıza kiralanmıştır. Aylık kira bedeli <Slot value={money(c.kira_tutari)} label="Aylık kira" bold /> <b>TL</b>&apos;dir.</p>
      <p className="indent-6 text-justify">2. Kira sözleşmesi uyarınca ödenmesi gereken <Slot value={isBlank(c.gecikilen_aylar) ? '' : String(c.gecikilen_aylar).trim()} label="Ödenmeyen aylar" bold /> dönemlerine ait kira bedelleri, muaccel olmasına rağmen tarafınızca ödenmemiştir. Ödenmeyen kira bedellerinin toplamı <Slot value={toplam} label="Toplam borç" bold /> <b>TL</b>&apos;dir.</p>
      <p className="indent-6 text-justify">3. 6098 sayılı Türk Borçlar Kanunu&apos;nun 315. maddesi uyarınca, kiracı kiralananın tesliminden sonra muaccel olan kira bedelini ödeme borcunu ifa etmezse kiraya veren, kiracıya yazılı olarak bir süre verip bu sürede de ifa etmeme durumunda sözleşmeyi feshedeceğini bildirebilir. Konut ve çatılı işyeri kiralarında bu süre en az otuz gündür ve yazılı bildirimin yapıldığı tarihi izleyen günden itibaren işlemeye başlar.</p>
      <p className="indent-6 text-justify">4. Açıklanan nedenlerle, ödenmeyen <Slot value={toplam} label="Toplam borç" bold /> <b>TL</b> tutarındaki kira bedelini işbu ihtarnamenin tebliğini izleyen günden itibaren <Slot value={sure} label="Süre" bold /> <b>gün</b> içinde aşağıda belirtilen banka hesabına ödemenizi; bu süre içinde ödeme yapmamanız halinde kira sözleşmesini feshedeceğimi ve tahliye için yasal yollara başvuracağımı ihtar ederim.</p>
      <p><b>Ödeme Yapılacak Hesap (IBAN): </b><Slot value={isBlank(p.iban) ? '' : maskSensitive(p.iban)} label="IBAN" /></p>
      <p><b>Hesap Sahibi: </b><Slot value={p.kiraya_veren_ad_soyad} label="Kiraya veren adı" /></p>
      <p className="font-bold mt-2">SONUÇ:</p>
      <p className="indent-6 text-justify">İşbu ihtarnamenin bir suretinin muhataba tebliğini, bir suretinin dairenizde saklanmasını ve tebliğ şerhini havi bir suretinin tarafıma verilmesini saygılarımla talep ederim.</p>
      <div className="text-right mt-3 space-y-0.5">
        <p>{today()}</p>
        <p className="font-bold">Keşideci</p>
        <p><Slot value={p.kiraya_veren_ad_soyad} label="Kiraya veren adı" /></p>
        <p>İmza</p>
      </div>
    </>
  );
}

function GenericPreview({ template, caseValues, piiValues }) {
  const show = (field, values) => {
    const raw = values[field.field_name];
    if (isBlank(raw)) return '';
    if (field.field_type === 'tc_id' || field.field_type === 'iban') return maskSensitive(raw);
    if (field.field_type === 'date') return formatTrDate(raw);
    return String(raw);
  };
  return (
    <>
      <p className="text-center font-bold tracking-[0.2em] mb-3 uppercase">{template.title}</p>
      <p className="font-bold">TARAFLAR VE KİŞİSEL BİLGİLER</p>
      {template.pii_fields.map((f) => (
        <p key={f.field_name}><b>{f.label}: </b><Slot value={show(f, piiValues)} label={f.required ? 'zorunlu' : 'isteğe bağlı'} /></p>
      ))}
      <p className="font-bold mt-2">OLAY BİLGİLERİ</p>
      {template.case_param_fields.map((f) => (
        <p key={f.field_name}><b>{f.label}: </b><Slot value={show(f, caseValues)} label={f.required ? 'zorunlu' : 'isteğe bağlı'} /></p>
      ))}
      <p className="mt-3 text-slate-500 italic">Bu şablonun tam metni belge üretildiğinde oluşturulur.</p>
    </>
  );
}

const DocumentPreview = ({ template, caseValues, piiValues }) => (
  <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4">
    <div className="flex justify-between items-center mb-3">
      <h3 className="font-bold text-navy text-sm flex items-center gap-2"><Eye size={16} className="text-teal" /> Canlı Önizleme (A4)</h3>
      <span className="text-[10px] font-bold text-slate-400">Tarayıcınızda oluşturulur</span>
    </div>
    <div className="w-full aspect-[1/1.414] bg-white border border-slate-200 shadow-inner p-6 overflow-y-auto text-[9px] sm:text-[10px] font-serif text-slate-800 leading-relaxed custom-scrollbar space-y-1.5">
      {!template ? (
        <p className="h-full flex items-center justify-center text-slate-400 font-sans text-xs">Önizleme için bir belge türü seçin.</p>
      ) : template.template_id === KIRA_ARTIS_TEMPLATE_ID ? (
        <KiraArtisPreview caseValues={caseValues} piiValues={piiValues} />
      ) : template.template_id === TEMERRUT_TEMPLATE_ID ? (
        <TemerrutPreview caseValues={caseValues} piiValues={piiValues} />
      ) : (
        <GenericPreview template={template} caseValues={caseValues} piiValues={piiValues} />
      )}
      {template && <p className="pt-4 text-center text-[8px] italic text-slate-400">Taslak belge. {DISCLAIMER_TEXT}</p>}
    </div>
  </div>
);

export default DocumentPreview;
