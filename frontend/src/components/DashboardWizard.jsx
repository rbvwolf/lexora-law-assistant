import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  AlertCircle, ArrowLeft, ArrowRight, Check, CheckCircle2, Clock, Download, FileText,
  FolderOpen, Loader2, Lock, MessageSquare, RefreshCw, Scale, ShieldCheck, User,
} from 'lucide-react';
import { ApiError, downloadUrl, generateDocument } from '../lib/api';
import {
  KIRA_ARTIS_TEMPLATE_ID, READY_TEMPLATE_IDS, formatIban, formatRemaining, formatTrDate,
  isBlank, kiraArtisCrossErrors, maskSensitive, parseFieldErrorMessage, parseNumber, prefillFromExtracted,
  toPayload, validateFields,
} from '../lib/fields';
import { saveDocument } from '../lib/documentStore';
import { useTemplates } from '../lib/useTemplates';
import FieldInput from './document/FieldInput';
import DocumentPreview from './document/DocumentPreview';
import KiraArtisCalculator from './document/KiraArtisCalculator';
import DisclaimerBanner from './common/DisclaimerBanner';

const STEPS = [
  { no: 1, title: 'Belge Türü' },
  { no: 2, title: 'Olay Bilgileri' },
  { no: 3, title: 'Kişisel Bilgiler' },
  { no: 4, title: 'Kontrol & İndir' },
];

const currentTime = () => Date.now();

const caseErrorsFor = (template, values) => ({
  ...validateFields(template.case_param_fields, values),
  // Cross-field rules only once the individual values are valid (same order as the backend)
  ...(template.template_id === KIRA_ARTIS_TEMPLATE_ID ? kiraArtisCrossErrors(values) : {}),
});

const StepIndicator = ({ current, maxReached, onGo }) => (
  <ol className="flex gap-2 mb-6 overflow-x-auto pb-1" aria-label="Sihirbaz adımları">
    {STEPS.map((s) => {
      const done = s.no < current;
      const active = s.no === current;
      const reachable = s.no <= maxReached && !active;
      return (
        <li key={s.no} className="flex-1 min-w-[150px]">
          <button
            type="button"
            disabled={!reachable}
            onClick={() => onGo(s.no)}
            aria-current={active ? 'step' : undefined}
            className={`w-full text-left rounded-xl p-3 flex items-center gap-3 transition-colors ${active ? 'bg-navy text-white shadow-md' : done ? 'bg-white border-2 border-teal hover:bg-teal/5' : 'bg-white border border-slate-200 opacity-60'} disabled:cursor-default`}
          >
            <span className={`w-8 h-8 rounded-full flex justify-center items-center font-bold text-sm shrink-0 ${active ? 'bg-white text-navy' : done ? 'bg-teal text-white' : 'bg-slate-100 text-slate-400'}`}>
              {done ? <Check size={16} /> : s.no}
            </span>
            <span>
              <span className={`block text-[10px] font-bold ${active || done ? 'text-teal' : 'text-slate-400'}`}>{active ? 'AKTİF ADIM' : `${s.no}. ADIM`}</span>
              <span className={`block text-xs font-bold ${active ? 'text-white' : 'text-navy'}`}>{s.title}</span>
            </span>
          </button>
        </li>
      );
    })}
  </ol>
);

const Card = ({ icon, title, badge, children }) => (
  <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
    <div className="flex flex-wrap justify-between items-center gap-2 mb-5">
      <h3 className="font-bold text-navy flex items-center gap-2">{icon} {title}</h3>
      {badge}
    </div>
    {children}
  </section>
);

const DashboardWizard = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { templates, loading, error: templatesError, retry } = useTemplates();

  // Prefill handed over by the chat or guide screen: { templateId, extractedParams, source }. Never contains PII.
  const handoff = useRef(location.state ?? null);
  const [templateId, setTemplateId] = useState(null);
  const [fromChat, setFromChat] = useState(false);
  const [step, setStep] = useState(1);
  const [maxReached, setMaxReached] = useState(1);
  const [caseValues, setCaseValues] = useState({});
  const [piiValues, setPiiValues] = useState({});
  const [caseErrors, setCaseErrors] = useState({});
  const [piiErrors, setPiiErrors] = useState({});
  const [generating, setGenerating] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [result, setResult] = useState(null);
  const [now, setNow] = useState(currentTime);
  const abortRef = useRef(null);
  const topRef = useRef(null);

  const template = useMemo(() => templates.find((t) => t.template_id === templateId), [templates, templateId]);

  // Apply the chat handoff once the templates are known, then clear it from history so a
  // reload does not re-apply stale values
  useEffect(() => {
    const data = handoff.current;
    if (!data || loading || templates.length === 0) return;
    handoff.current = null;
    const target = templates.find((t) => t.template_id === data.templateId);
    navigate(location.pathname, { replace: true, state: null });
    if (!target) return;
    setTemplateId(target.template_id);
    setCaseValues(prefillFromExtracted(target, data.extractedParams));
    setFromChat(data.source === 'chat');
    setStep(2);
    setMaxReached(2);
  }, [loading, templates, navigate, location.pathname]);

  // Leaving the screen cancels a pending generation
  useEffect(() => () => abortRef.current?.abort(), []);

  // Expiry countdown while a result is shown
  useEffect(() => {
    if (!result) return undefined;
    const timer = setInterval(() => setNow(currentTime()), 30000);
    return () => clearInterval(timer);
  }, [result]);

  const goTo = (next) => {
    setStep(next);
    setMaxReached((m) => Math.max(m, next));
    topRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const chooseTemplate = (id) => {
    if (id !== templateId) {
      setTemplateId(id);
      setCaseValues({});
      setPiiValues({});
      setCaseErrors({});
      setPiiErrors({});
      setResult(null);
      setSubmitError(null);
      setFromChat(false);
      setMaxReached(2);
    }
    goTo(2);
  };

  // Any edit makes an earlier result stale
  const updateCase = (name, value) => {
    setCaseValues((v) => ({ ...v, [name]: value }));
    setCaseErrors((e) => (e[name] ? { ...e, [name]: undefined } : e));
    setResult(null);
  };
  const updatePii = (name, value) => {
    setPiiValues((v) => ({ ...v, [name]: value }));
    setPiiErrors((e) => (e[name] ? { ...e, [name]: undefined } : e));
    setResult(null);
  };

  const nextFromCase = () => {
    const errors = caseErrorsFor(template, caseValues);
    setCaseErrors(errors);
    if (Object.keys(errors).length === 0) goTo(3);
  };

  const nextFromPii = () => {
    const errors = validateFields(template.pii_fields, piiValues);
    setPiiErrors(errors);
    if (Object.keys(errors).length === 0) goTo(4);
  };

  const handleGenerate = async () => {
    if (!template || generating) return;
    // Re-check both groups: the user may have jumped back via the step bar
    const cErr = caseErrorsFor(template, caseValues);
    const pErr = validateFields(template.pii_fields, piiValues);
    setCaseErrors(cErr);
    setPiiErrors(pErr);
    if (Object.keys(cErr).length) return goTo(2);
    if (Object.keys(pErr).length) return goTo(3);

    const controller = new AbortController();
    abortRef.current = controller;
    setGenerating(true);
    setSubmitError(null);
    try {
      const response = await generateDocument(
        template.template_id,
        toPayload(template.case_param_fields, caseValues),
        toPayload(template.pii_fields, piiValues),
        { signal: controller.signal, timeoutMs: 60000 },
      );
      setResult(response);
      setSubmitError(null);
      setNow(currentTime());
      saveDocument(response, template);
    } catch (err) {
      if (err?.name === 'AbortError') return;
      if (err instanceof ApiError && err.errorCode === 'TEMPLATE_FIELDS_INVALID') {
        // Backend message lists field names only; put them back on the form
        const parsed = parseFieldErrorMessage(err.message);
        const caseNames = new Set(template.case_param_fields.map((f) => f.field_name));
        const nextCase = {};
        const nextPii = {};
        for (const name of parsed.missing) (caseNames.has(name) ? nextCase : nextPii)[name] = 'Bu alan zorunludur.';
        for (const name of parsed.invalid) (caseNames.has(name) ? nextCase : nextPii)[name] = 'Sunucu bu değeri kabul etmedi; lütfen kontrol edin.';
        setCaseErrors(nextCase);
        setPiiErrors(nextPii);
        setSubmitError('Bazı alanlar sunucu tarafından reddedildi. İlgili adıma yönlendirildiniz.');
        if (Object.keys(nextCase).length) goTo(2);
        else if (Object.keys(nextPii).length) goTo(3);
      } else if (err instanceof ApiError && err.errorCode === 'TEMPLATE_NOT_FOUND') {
        setSubmitError('Bu belge türü artık mevcut değil. Lütfen başka bir belge türü seçin.');
        retry();
      } else {
        setSubmitError(err instanceof ApiError ? err.message : 'Belge oluşturulamadı. Lütfen tekrar deneyin.');
      }
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
        setGenerating(false);
      }
    }
  };

  const startOver = () => {
    setTemplateId(null);
    setCaseValues({});
    setPiiValues({});
    setCaseErrors({});
    setPiiErrors({});
    setResult(null);
    setSubmitError(null);
    setFromChat(false);
    setStep(1);
    setMaxReached(1);
  };

  const summaryValue = (field, values) => {
    const raw = values[field.field_name];
    if (isBlank(raw)) return <span className="text-slate-400">—</span>;
    if (field.field_type === 'tc_id') return maskSensitive(raw);
    if (field.field_type === 'iban') return maskSensitive(formatIban(raw).replace(/\s/g, ''));
    if (field.field_type === 'date') return formatTrDate(raw);
    if (field.field_type === 'number' && Number.isFinite(parseNumber(raw))) return parseNumber(raw).toLocaleString('tr-TR');
    return String(raw);
  };

  const remaining = result ? formatRemaining(result.expires_at, now) : '';
  const expired = remaining === 'süresi doldu';

  return (
    <div className="flex-1 bg-[#f8fafc] overflow-y-auto p-6 custom-scrollbar">
      <div className="max-w-7xl mx-auto" ref={topRef}>
        <div className="bg-teal/10 border border-teal/20 rounded-xl p-4 flex flex-wrap justify-between items-center gap-3 mb-6">
          <div className="flex items-center gap-3 text-teal">
            <FileText size={22} />
            <div>
              <h1 className="font-bold text-sm">Dilekçe & İhtarname Sihirbazı</h1>
              <p className="text-xs text-teal/80">Belge türünü seçin, olay ve taraf bilgilerini girin; Word (.docx) ve PDF taslağınızı indirin.</p>
            </div>
          </div>
          <span className="flex items-center gap-1 text-xs font-bold text-teal"><Lock size={14} /> Kişisel bilgiler yapay zekâya gönderilmez</span>
        </div>

        <StepIndicator current={step} maxReached={template ? maxReached : 1} onGo={goTo} />

        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1 space-y-6 min-w-0">
            {fromChat && step === 2 && (
              <div className="bg-blue-50 border border-blue-100 text-blue-800 text-xs rounded-xl p-3 flex items-start gap-2">
                <MessageSquare size={14} className="shrink-0 mt-px" />
                <span>Danış AI sohbetinde tespit edilen bilgiler forma aktarıldı. Lütfen doğruluğunu kontrol edin ve eksik alanları tamamlayın.</span>
              </div>
            )}

            {submitError && (
              <div role="alert" className="text-xs font-medium text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex items-center gap-2"><AlertCircle size={14} className="shrink-0" /> {submitError}</div>
            )}

            {/* STEP 1: template */}
            {step === 1 && (
              <Card icon={<Scale size={18} />} title="Hangi belgeyi hazırlamak istiyorsunuz?">
                {loading && <p className="text-sm text-slate-500 flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Belge türleri yükleniyor...</p>}
                {templatesError && (
                  <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-4 flex flex-wrap items-center gap-3">
                    <AlertCircle size={16} /> <span className="flex-1">Belge türleri yüklenemedi: {templatesError}</span>
                    <button type="button" onClick={retry} className="text-xs font-bold bg-white border border-red-200 px-3 py-1.5 rounded-lg flex items-center gap-1 hover:bg-red-100"><RefreshCw size={12} /> Tekrar dene</button>
                  </div>
                )}
                {!loading && !templatesError && templates.length === 0 && <p className="text-sm text-slate-500">Şu anda kullanılabilir belge türü yok.</p>}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[...templates].sort((a, b) => Number(READY_TEMPLATE_IDS.includes(b.template_id)) - Number(READY_TEMPLATE_IDS.includes(a.template_id))).map((t) => {
                    const ready = READY_TEMPLATE_IDS.includes(t.template_id);
                    const selected = t.template_id === templateId;
                    return (
                      <button key={t.template_id} type="button" onClick={() => chooseTemplate(t.template_id)} aria-pressed={selected}
                        className={`text-left rounded-xl border p-4 transition-all hover:border-teal hover:shadow-sm ${selected ? 'border-teal ring-2 ring-teal/20 bg-teal/5' : 'border-slate-200 bg-white'}`}>
                        <div className="flex justify-between items-start gap-2 mb-2">
                          <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">{t.domain}</span>
                          {ready
                            ? <span className="text-[10px] font-bold text-teal bg-teal/10 px-2 py-0.5 rounded flex items-center gap-1"><CheckCircle2 size={10} /> Hazır</span>
                            : <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">Geliştiriliyor</span>}
                        </div>
                        <p className="text-sm font-bold text-navy mb-1">{t.title}</p>
                        <p className="text-xs text-slate-500 leading-relaxed">{t.description}</p>
                      </button>
                    );
                  })}
                </div>
                <p className="text-xs text-slate-500 mt-5 flex items-center gap-1.5">
                  <MessageSquare size={14} className="text-teal" /> Hangi belgeye ihtiyacınız olduğundan emin değil misiniz?
                  <Link to="/app/danis-ai" className="font-bold text-teal hover:underline">Danış AI&apos;a durumunuzu anlatın</Link>
                </p>
              </Card>
            )}

            {/* STEP 2: case params */}
            {step === 2 && template && (
              <Card icon={<FileText size={18} />} title={`Olay bilgileri — ${template.title}`}
                badge={!READY_TEMPLATE_IDS.includes(template.template_id) && <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-1 rounded">Bu şablon henüz geliştiriliyor; indirilen dosya örnek çıktıdır</span>}>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {template.case_param_fields.map((field) => (
                    <FieldInput key={field.field_name} field={field} value={caseValues[field.field_name]} error={caseErrors[field.field_name]}
                      onChange={(v) => updateCase(field.field_name, v)} />
                  ))}
                </div>
                {template.template_id === KIRA_ARTIS_TEMPLATE_ID && <div className="mt-6"><KiraArtisCalculator values={caseValues} /></div>}
              </Card>
            )}

            {/* STEP 3: PII mini-form */}
            {step === 3 && template && (
              <Card icon={<User size={18} />} title="Taraf ve kişisel bilgiler"
                badge={<span className="text-[10px] font-bold text-teal bg-teal/10 px-2 py-1 rounded flex items-center gap-1"><ShieldCheck size={12} /> KVKK korumalı form</span>}>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-[11px] text-slate-600 leading-relaxed mb-5 flex items-start gap-2">
                  <Lock size={14} className="text-teal shrink-0 mt-px" />
                  <span>Bu bilgiler yapay zekâya gönderilmez; yalnızca belgeyi oluşturmak için kullanılır. Oluşturulan dosyalar süre dolunca sunucudan otomatik olarak silinir ve tarayıcınızda saklanmaz.</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {template.pii_fields.map((field) => (
                    <FieldInput key={field.field_name} field={field} value={piiValues[field.field_name]} error={piiErrors[field.field_name]}
                      onChange={(v) => updatePii(field.field_name, v)} sensitive />
                  ))}
                </div>
              </Card>
            )}

            {/* STEP 4: review + generate + download */}
            {step === 4 && template && (
              <Card icon={<CheckCircle2 size={18} />} title="Kontrol edin ve belgenizi oluşturun">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  {[['Olay bilgileri', template.case_param_fields, caseValues, 2], ['Kişisel bilgiler', template.pii_fields, piiValues, 3]].map(([title, fields, values, back]) => (
                    <div key={title}>
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="text-[11px] font-bold text-slate-400 tracking-widest uppercase">{title}</h4>
                        <button type="button" onClick={() => goTo(back)} className="text-[11px] font-bold text-teal hover:underline">Düzenle</button>
                      </div>
                      <dl className="space-y-1.5">
                        {fields.map((f) => (
                          <div key={f.field_name} className="flex justify-between gap-3 text-xs border-b border-slate-50 pb-1.5">
                            <dt className="text-slate-500">{f.label}</dt>
                            <dd className="font-bold text-navy text-right break-words min-w-0">{summaryValue(f, values)}</dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  ))}
                </div>

                <DisclaimerBanner variant="inline" />

                {!result ? (
                  <button type="button" onClick={handleGenerate} disabled={generating}
                    className="mt-5 w-full bg-teal hover:bg-teal/90 text-white font-bold py-3.5 rounded-xl flex justify-center items-center gap-2 shadow-sm disabled:opacity-60 disabled:cursor-wait">
                    {generating ? <><Loader2 size={18} className="animate-spin" /> Belge oluşturuluyor...</> : <><FileText size={18} /> Belgeyi oluştur (.docx + .pdf)</>}
                  </button>
                ) : (
                  <div className="mt-5 border border-teal/30 bg-teal/5 rounded-xl p-5" aria-live="polite">
                    <p className="text-sm font-bold text-navy flex items-center gap-2 mb-1"><CheckCircle2 size={18} className="text-teal" /> Belgeniz hazır</p>
                    <p className={`text-xs mb-4 flex items-center gap-1 ${expired ? 'text-red-600 font-bold' : 'text-slate-500'}`}>
                      <Clock size={12} />
                      {expired
                        ? 'İndirme süresi doldu. Belgeyi yeniden oluşturabilirsiniz.'
                        : `Dosyalar KVKK gereği ${remaining} sonra sunucudan silinecek; şimdi indirmeniz önerilir.`}
                    </p>
                    {!expired ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <a href={downloadUrl(result.docx_url)} download className="bg-navy hover:bg-navy/90 text-white text-sm font-bold py-3 rounded-xl flex justify-center items-center gap-2"><Download size={16} /> Word (.docx) indir</a>
                        <a href={downloadUrl(result.pdf_url)} download className="bg-white hover:bg-slate-50 border border-slate-200 text-navy text-sm font-bold py-3 rounded-xl flex justify-center items-center gap-2"><Download size={16} /> PDF indir</a>
                      </div>
                    ) : (
                      <button type="button" onClick={() => { setResult(null); handleGenerate(); }} className="w-full bg-teal text-white text-sm font-bold py-3 rounded-xl flex justify-center items-center gap-2"><RefreshCw size={16} /> Yeniden oluştur</button>
                    )}
                    <div className="flex flex-wrap gap-4 mt-4 text-xs font-bold">
                      <Link to="/app/arsiv" className="text-teal hover:underline flex items-center gap-1"><FolderOpen size={14} /> Belgelerim</Link>
                      <button type="button" onClick={startOver} className="text-slate-500 hover:text-navy">Yeni belge hazırla</button>
                    </div>
                  </div>
                )}
              </Card>
            )}

            {step > 1 && template && (
              <div className="flex justify-between items-center">
                <button type="button" onClick={() => goTo(step - 1)}
                  className="bg-white border border-slate-200 text-navy font-bold py-3 px-6 rounded-xl flex items-center gap-2 hover:bg-slate-50">
                  <ArrowLeft size={16} /> Geri
                </button>
                {step === 2 && <button type="button" onClick={nextFromCase} className="bg-navy text-white font-bold py-3 px-8 rounded-xl flex items-center gap-2 shadow-md hover:bg-navy/90">Kişisel bilgilere geç <ArrowRight size={16} /></button>}
                {step === 3 && <button type="button" onClick={nextFromPii} className="bg-navy text-white font-bold py-3 px-8 rounded-xl flex items-center gap-2 shadow-md hover:bg-navy/90">Kontrol et <ArrowRight size={16} /></button>}
              </div>
            )}
          </div>

          <aside className="w-full lg:w-[440px] shrink-0">
            <div className="lg:sticky lg:top-0 space-y-3">
              <DocumentPreview template={template} caseValues={caseValues} piiValues={piiValues} />
              <DisclaimerBanner variant="inline" />
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default DashboardWizard;
