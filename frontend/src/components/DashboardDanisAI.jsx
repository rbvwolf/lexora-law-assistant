import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  AlertCircle, AlertTriangle, ArrowRight, BookOpen, Bot, CheckCircle2, Database, FileText,
  HelpCircle, Landmark, Lock, Plus, Scale, Send, ShieldCheck,
} from 'lucide-react';
import { ApiError, sendChatMessage } from '../lib/api';
import { DISCLAIMER_TEXT } from '../lib/constants';
import { fieldLabel } from '../lib/fields';
import { autoRetryDelay, countdown } from '../lib/retry';
import { useTemplates } from '../lib/useTemplates';
import RichText from './common/RichText';

// Same limit as backend ChatRequest.message (max_length=4000)
const MAX_MESSAGE_LENGTH = 4000;

// Laws loaded into the RAG corpus (data/laws/)
const CORPUS = ['TBK — Kira', 'TBK — Temerrüt', 'TKHK — Tüketici', 'İş Kanunu'];

const EXAMPLES = [
  'Ev sahibim kirayı TÜFE oranının üzerinde artırmak istiyor, yasal sınır nedir?',
  'Ev sahibim kirayı %100 artırdı, itiraz ihtarnamesi hazırlamak istiyorum.',
  'Aldığım telefon iki haftada bozuldu, satıcıdan bedel iadesi isteyebilir miyim?',
];

// randomUUID exists only in secure contexts (https / localhost); the fallback covers plain-http LAN access
const createSessionId = () =>
  globalThis.crypto?.randomUUID?.() ?? `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;

const formatParam = (value) => {
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'number') return value.toLocaleString('tr-TR');
  return String(value);
};

// For document_generation the card below shows the details in structured form, so only the
// answer's lead paragraph is kept (the rest repeats raw field names)
const leadParagraph = (text) => String(text ?? '').split(/\n\s*\n/)[0];

const AssistantHeader = () => (
  <div className="flex items-center gap-2 mb-2"><div className="w-8 h-8 rounded-full bg-teal flex justify-center items-center text-white"><Scale size={16}/></div><span className="text-xs font-bold text-navy">Danış AI</span></div>
);

const UserBubble = ({ text }) => (
  <div className="flex justify-end">
    <div className="max-w-[80%]">
      <div className="flex justify-end items-center gap-2 mb-1"><span className="text-xs font-bold text-slate-500">Siz</span></div>
      <div className="bg-navy text-white p-4 rounded-2xl rounded-tr-none text-sm leading-relaxed shadow-md whitespace-pre-wrap break-words">{text}</div>
    </div>
  </div>
);

const Citations = ({ citations }) => (
  <div>
    <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-2">DAYANAK KANUN MADDELERİ</p>
    <div className="space-y-2">
      {citations.map((citation, index) => (
        <div key={`${citation.article_id}-${index}`} className="bg-slate-50 border border-slate-100 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs font-bold text-teal bg-teal/5 border border-teal/10 px-2 py-1.5 rounded-lg flex items-center gap-1"><Scale size={12}/> {citation.article_id}</span>
            <span className="text-[11px] font-bold text-navy">{citation.law_name}</span>
          </div>
          <p className="text-[11px] text-slate-600 leading-relaxed line-clamp-3">{citation.text_snippet}</p>
        </div>
      ))}
    </div>
  </div>
);

/** document_generation: what was understood, what is still missing, and the jump to the wizard. */
const DocumentSuggestion = ({ response, templates, onOpenWizard }) => {
  const template = templates.find((t) => t.template_id === response.suggested_template_id);
  const params = Object.entries(response.extracted_params ?? {});
  return (
    <div className="border border-teal/20 bg-teal/5 rounded-xl p-4 space-y-3">
      <div className="flex items-center gap-2">
        <FileText size={16} className="text-teal"/>
        <span className="text-[10px] font-bold text-teal tracking-widest">ÖNERİLEN BELGE</span>
      </div>
      <p className="text-sm font-bold text-navy">{template?.title ?? response.suggested_template_id ?? 'Belge'}</p>

      {params.length > 0 && (
        <div>
          <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-1.5">TESPİT EDİLEN BİLGİLER</p>
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1">
            {params.map(([key, value]) => (
              <div key={key} className="flex justify-between gap-2 text-xs border-b border-teal/10 pb-1">
                <dt className="text-slate-500">{fieldLabel(templates, key)}</dt>
                <dd className="font-bold text-navy text-right">{formatParam(value)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {response.missing_fields?.length > 0 ? (
        <div>
          <p className="text-[10px] font-bold text-amber-700 tracking-widest mb-1.5">BELGE İÇİN EKSİK BİLGİLER</p>
          <ul className="space-y-1">
            {response.missing_fields.map((name) => (
              <li key={name} className="text-xs text-slate-700 flex items-start gap-1.5">
                <HelpCircle size={13} className="text-amber-600 shrink-0 mt-px"/>
                <span><b>{fieldLabel(templates, name)}</b> nedir?</span>
              </li>
            ))}
          </ul>
          <p className="text-[11px] text-slate-500 mt-2">Bu bilgileri mesajla yazabilir ya da doğrudan sihirbazda doldurabilirsiniz.</p>
        </div>
      ) : (
        <p className="text-xs text-teal font-medium flex items-center gap-1"><CheckCircle2 size={13}/> Olay bilgileri tamam görünüyor.</p>
      )}

      <p className="text-[11px] text-slate-500 flex items-start gap-1.5"><Lock size={12} className="shrink-0 mt-px text-teal"/> Ad, T.C. kimlik no, IBAN ve adres bilgilerinizi sohbete yazmayın; sihirbazdaki güvenli formda girin.</p>

      {template ? (
        <button type="button" onClick={() => onOpenWizard(response)} className="w-full bg-navy hover:bg-navy/90 text-white text-xs font-bold py-2.5 rounded-xl flex justify-center items-center gap-2">
          Sihirbazda devam et <ArrowRight size={14}/>
        </button>
      ) : (
        <Link to="/app/sihirbaz" className="w-full bg-navy hover:bg-navy/90 text-white text-xs font-bold py-2.5 rounded-xl flex justify-center items-center gap-2">Belge sihirbazını aç <ArrowRight size={14}/></Link>
      )}
    </div>
  );
};

const OutOfScopeNote = () => (
  <div className="border border-amber-200 bg-amber-50 rounded-xl p-4 text-xs text-amber-900 space-y-1.5">
    <p className="font-bold flex items-center gap-1.5"><AlertTriangle size={14}/> Bu konu Lexora&apos;nın kapsamı dışında</p>
    <p className="leading-relaxed">Lexora şu an kira, tüketici ve iş hukuku ile borçlar hukukunun ilgili konularında bilgi verebilir. Diğer hukuki sorunlarınız için bir avukata danışmanızı öneririz; maddi imkânınız yoksa bulunduğunuz ilin barosuna adli yardım başvurusu yapabilirsiniz.</p>
  </div>
);

const AssistantBubble = ({ response, templates, onOpenWizard }) => (
  <div className="flex justify-start">
    <div className="max-w-[90%] w-full">
      <AssistantHeader />
      <div className="bg-white border border-slate-200 p-5 rounded-2xl rounded-tl-none shadow-sm space-y-5">
        <RichText text={response.intent === 'document_generation' ? leadParagraph(response.answer) : response.answer} className="text-sm text-slate-600 leading-relaxed" />
        {response.intent === 'question_answering' && response.citations?.length > 0 && <Citations citations={response.citations} />}
        {response.intent === 'document_generation' && <DocumentSuggestion response={response} templates={templates} onOpenWizard={onOpenWizard} />}
        {response.intent === 'out_of_scope' && <OutOfScopeNote />}
        <p className="text-[10px] text-slate-400 border-t border-slate-100 pt-3 flex items-center gap-1"><ShieldCheck size={12} className="shrink-0"/> {response.disclaimer || DISCLAIMER_TEXT}</p>
      </div>
    </div>
  </div>
);

const DashboardDanisAI = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { templates } = useTemplates();
  const [sessionId, setSessionId] = useState(createSessionId);
  // Text typed on the home page search box arrives as router state and is prefilled, not auto-sent
  const [input, setInput] = useState(() => String(location.state?.initialMessage ?? '').slice(0, MAX_MESSAGE_LENGTH));
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  // Seconds left before the automatic retry after a rate limit; null when not waiting
  const [retryCountdown, setRetryCountdown] = useState(null);
  const nextIdRef = useRef(0);
  const abortRef = useRef(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Leaving the screen cancels a pending request
  useEffect(() => () => abortRef.current?.abort(), []);

  // Drop the handed-over text from history so a reload does not bring it back
  useEffect(() => {
    if (location.state?.initialMessage) {
      navigate(location.pathname, { replace: true, state: null });
      inputRef.current?.focus();
    }
  }, [location.state, location.pathname, navigate]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isLoading]);

  const lastResponse = useMemo(
    () => [...messages].reverse().find((m) => m.role === 'assistant')?.response ?? null,
    [messages],
  );

  const canSend = !isLoading && input.trim() !== '';

  const handleSend = async () => {
    if (!canSend) return;
    const text = input;
    const userMessage = { id: nextIdRef.current++, role: 'user', text };
    const controller = new AbortController();
    abortRef.current = controller;

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setError(null);
    setIsLoading(true);

    try {
      let response;
      // A Groq rate limit (503 LLM_RATE_LIMITED) is waited out once with a visible countdown
      for (let retries = 0; ; retries += 1) {
        try {
          response = await sendChatMessage(sessionId, text, { signal: controller.signal, timeoutMs: 60000 });
          break;
        } catch (err) {
          const delay = autoRetryDelay(err, retries);
          if (delay === null) throw err;
          await countdown(delay, { signal: controller.signal, onTick: setRetryCountdown });
          setRetryCountdown(null);
        }
      }
      const assistantMessage = { id: nextIdRef.current++, role: 'assistant', response };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      if (err?.name === 'AbortError') return;
      // A rejected message (empty, injection, server down) leaves the conversation; its text goes back for editing
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
      setInput(text);
      setError(err instanceof ApiError ? err.message : 'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.');
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
        setIsLoading(false);
        setRetryCountdown(null);
      }
    }
  };

  const handleKeyDown = (event) => {
    // Enter sends, Shift+Enter adds a line, Enter while composing characters is ignored
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      handleSend();
    }
  };

  const startNewSession = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsLoading(false);
    setRetryCountdown(null);
    setMessages([]);
    setInput('');
    setError(null);
    setSessionId(createSessionId());
    inputRef.current?.focus();
  };

  const fillExample = (text) => {
    setInput(text);
    inputRef.current?.focus();
  };

  // Only template id and non-personal case params travel to the wizard (PII never comes from chat)
  const openWizard = (response) => {
    navigate('/app/sihirbaz', {
      state: { templateId: response.suggested_template_id, extractedParams: response.extracted_params ?? {}, source: 'chat' },
    });
  };

  const suggestedTemplate = lastResponse?.intent === 'document_generation'
    ? templates.find((t) => t.template_id === lastResponse.suggested_template_id)
    : null;
  const lastCitations = lastResponse?.intent === 'question_answering' ? lastResponse.citations ?? [] : [];

  return (
    <div className="flex-1 bg-[#f8fafc] flex overflow-hidden">
      <div className="w-72 bg-white border-r border-slate-200 hidden md:flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-200"><button type="button" onClick={startNewSession} className="w-full bg-navy text-white text-sm font-bold py-2.5 rounded-xl flex justify-center items-center gap-2 hover:bg-navy/90"><Plus size={16}/> Yeni Sohbet Başlat</button></div>
        <div className="p-4 flex-1 overflow-y-auto custom-scrollbar space-y-6">
          <div>
            <span className="text-[10px] font-bold text-slate-400 tracking-widest">ÖRNEK SORULAR</span>
            <div className="space-y-2 mt-3">
              {EXAMPLES.map((text) => (
                <button key={text} type="button" onClick={() => fillExample(text)} className="w-full text-left bg-slate-50 border border-slate-100 p-3 rounded-xl text-xs text-navy hover:bg-teal/5 hover:border-teal/20">{text}</button>
              ))}
            </div>
          </div>
          <div className="bg-teal/5 border border-teal/20 p-4 rounded-xl">
            <div className="flex items-center gap-2 mb-2"><ShieldCheck className="text-teal" size={18}/><span className="text-xs font-bold text-navy">Kişisel veri koruması</span></div>
            <p className="text-[11px] text-slate-500 leading-relaxed">Mesajınızda yanlışlıkla T.C. kimlik no veya IBAN geçerse, sunucu bunları yapay zekâya göndermeden önce maskeler. Yine de kişisel bilgilerinizi sohbete yazmayın; belge için sihirbazdaki formu kullanın.</p>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-[#f8fafc] min-w-0">
        <div className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-6 shrink-0 gap-4">
          <div className="flex gap-2 items-center text-xs font-bold text-slate-500 min-w-0 truncate"><Database size={14} className="text-teal shrink-0"/> Kapsam: <span className="text-navy truncate">{CORPUS.join(' · ')}</span></div>
          <button type="button" onClick={startNewSession} className="md:hidden text-xs font-bold text-teal flex items-center gap-1 shrink-0"><Plus size={14}/> Yeni</button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
           {messages.length === 0 && !isLoading && (
             <div className="h-full flex flex-col justify-center items-center text-center gap-3">
               <div className="w-12 h-12 rounded-full bg-teal/10 text-teal flex justify-center items-center"><Scale size={22}/></div>
               <p className="text-sm font-bold text-navy">Hukuki sorunuzu yazın</p>
               <p className="text-xs text-slate-500 max-w-sm leading-relaxed">Danış AI sorunuzu ilgili kanun maddeleriyle yanıtlar; belge gerekiyorsa sizi sihirbaza yönlendirir.</p>
               <p className="text-[10px] text-slate-400 flex items-center gap-1"><ShieldCheck size={12}/> {DISCLAIMER_TEXT}</p>
             </div>
           )}

           {messages.map((message) =>
             message.role === 'user'
               ? <UserBubble key={message.id} text={message.text} />
               : <AssistantBubble key={message.id} response={message.response} templates={templates} onOpenWizard={openWizard} />
           )}

           {isLoading && (
             <div className="flex justify-start" aria-live="polite">
               <div className="max-w-[90%]">
                 <AssistantHeader />
                 {retryCountdown === null ? (
                   <div className="bg-white border border-slate-200 p-5 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-500 animate-pulse">Danış AI ilgili kanun maddelerini inceliyor...</div>
                 ) : (
                   <div className="bg-amber-50 border border-amber-200 p-5 rounded-2xl rounded-tl-none shadow-sm text-sm text-amber-800">Şu anda yoğunluk var. Sorunuz {retryCountdown} saniye içinde otomatik olarak tekrar gönderilecek.</div>
                 )}
               </div>
             </div>
           )}
           <div ref={bottomRef} />
        </div>

        <div className="p-6 bg-white border-t border-slate-200 shrink-0">
          {error && (
            <div role="alert" className="max-w-4xl mx-auto mb-4 text-xs font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 flex items-center gap-2"><AlertCircle size={14} className="shrink-0"/> {error}</div>
          )}
          <div className="max-w-4xl mx-auto">
             <div className="border border-slate-200 rounded-2xl bg-slate-50 p-2 flex flex-col focus-within:border-teal focus-within:bg-white transition-colors shadow-sm">
                <textarea ref={inputRef} rows="2" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleKeyDown} maxLength={MAX_MESSAGE_LENGTH} aria-label="Hukuki sorunuz" placeholder="Örn: Ev sahibim kirayı %100 artırmak istiyor, ne yapabilirim?" className="w-full bg-transparent resize-none outline-none p-2 text-sm text-navy placeholder:text-slate-400"></textarea>
                <div className="flex justify-between items-center mt-2 gap-2">
                   <span className="text-[10px] text-slate-400 pl-2 flex items-center gap-1"><Lock size={11}/> Enter ile gönder, Shift+Enter yeni satır · {input.length}/{MAX_MESSAGE_LENGTH}</span>
                   <button type="button" onClick={handleSend} disabled={!canSend} className="bg-teal hover:bg-teal/90 text-white text-xs font-bold px-4 py-2 rounded-lg flex items-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed shrink-0">{isLoading ? 'Yanıt bekleniyor...' : 'Gönder'} <Send size={14}/></button>
                </div>
             </div>
          </div>
        </div>
      </div>

      <div className="w-80 bg-white border-l border-slate-200 overflow-y-auto shrink-0 p-6 custom-scrollbar hidden xl:block space-y-6">
         <div className="bg-navy rounded-2xl p-5 text-white shadow-lg relative overflow-hidden">
           <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl"></div>
           <div className="text-[10px] font-bold text-teal tracking-widest mb-2 flex items-center gap-1"><Bot size={12}/> BELGE HAZIRLA</div>
           {suggestedTemplate ? (
             <>
               <h3 className="font-bold text-lg mb-2 relative z-10">{suggestedTemplate.title}</h3>
               <p className="text-xs text-slate-400 mb-4 leading-relaxed relative z-10">Sohbette tespit edilen bilgilerle sihirbazı açın, eksikleri tamamlayıp Word ve PDF olarak indirin.</p>
               <button type="button" onClick={() => openWizard(lastResponse)} className="w-full bg-teal text-white text-xs font-bold py-2.5 rounded-xl flex justify-center items-center gap-2 hover:bg-teal/90 transition-colors relative z-10">Sihirbazda devam et <ArrowRight size={14}/></button>
             </>
           ) : (
             <>
               <h3 className="font-bold text-lg mb-2 relative z-10">İhtarname veya dilekçe mi lazım?</h3>
               <p className="text-xs text-slate-400 mb-4 leading-relaxed relative z-10">Durumunuzu anlatın, uygun belgeyi önerelim; ya da doğrudan sihirbazdan belge türünü seçin.</p>
               <Link to="/app/sihirbaz" className="w-full bg-teal text-white text-xs font-bold py-2.5 rounded-xl flex justify-center items-center gap-2 hover:bg-teal/90 transition-colors relative z-10">Sihirbazı aç <ArrowRight size={14}/></Link>
             </>
           )}
         </div>

         <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
           <h4 className="text-xs font-bold text-navy mb-3 flex items-center gap-2"><BookOpen size={14} className="text-teal"/> Son yanıtın dayanakları</h4>
           {lastCitations.length > 0 ? (
             <ul className="space-y-2">
               {lastCitations.map((c, i) => (
                 <li key={`${c.article_id}-${i}`} className="text-[11px]"><span className="font-bold text-teal">{c.article_id}</span> <span className="text-slate-500">· {c.law_name}</span></li>
               ))}
             </ul>
           ) : (
             <p className="text-[11px] text-slate-500 leading-relaxed">Bir soru sorduğunuzda yanıtın dayandığı kanun maddeleri burada listelenir.</p>
           )}
         </div>

         <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4">
           <h4 className="text-xs font-bold text-navy mb-2 flex items-center gap-2"><Landmark size={14} className="text-teal"/> Avukata ne zaman başvurmalı?</h4>
           <p className="text-[11px] text-slate-600 leading-relaxed">Dava açma, süreli itirazlar veya karşı tarafın avukatla geldiği durumlarda bir avukattan destek alın. Maddi imkânınız yoksa barolar adli yardım sağlar.</p>
         </div>
      </div>
    </div>
  );
};

export default DashboardDanisAI;
