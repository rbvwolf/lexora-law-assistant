import { useState } from 'react';
import { Routes, Route, Link, NavLink, Navigate, useLocation } from 'react-router-dom';
import { AlertTriangle, BookOpen, Bot, ChevronRight, FileText, FolderOpen, Home, Menu, ShieldCheck, X } from 'lucide-react';
import DashboardWizard from './components/DashboardWizard';
import DashboardArsiv from './components/DashboardArsiv';
import DashboardRehber from './components/DashboardRehber';
import DashboardDanisAI from './components/DashboardDanisAI';
import DisclaimerBanner from './components/common/DisclaimerBanner';
import ErrorBoundary from './components/common/ErrorBoundary';
import NotFound from './components/common/NotFound';
import BackendStatus from './components/common/BackendStatus';
import LexoraLogo from './components/common/LexoraLogo';
import HomePage from './app/HomePage';
import FeaturesPage from './app/FeaturesPage';
import FaqPage from './app/FaqPage';
import KvkkPage from './app/KvkkPage';

const APP_LINKS = [
  { to: '/app/danis-ai', label: 'Danış AI', icon: Bot },
  { to: '/app/sihirbaz', label: 'Belge Sihirbazı', icon: FileText },
  { to: '/app/arsiv', label: 'Belgelerim', icon: FolderOpen },
  { to: '/app/rehber', label: 'Hak Rehberi', icon: BookOpen },
];

const PUBLIC_LINKS = [
  { to: '/ozellikler', label: 'Nasıl Çalışır' },
  { to: '/app/rehber', label: 'Hak Rehberi' },
  { to: '/sss', label: 'Sıkça Sorulanlar' },
  { to: '/kvkk', label: 'Kişisel Veriler' },
];

// =====================================================================
// DASHBOARD (KULLANICI PANELİ)
// =====================================================================

function Sidebar({ onNavigate }) {
  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${isActive ? 'bg-teal/10 text-teal font-bold' : 'text-slate-500 hover:bg-slate-100 hover:text-navy'}`;
  return (
    <aside className="w-64 bg-slate-50 border-r border-slate-200 h-full flex flex-col">
      <div className="p-6 border-b border-slate-200">
        <Link to="/" onClick={onNavigate} aria-label="Ana sayfa"><LexoraLogo className="h-8" /></Link>
      </div>
      <nav className="flex-1 overflow-y-auto py-6 px-4 custom-scrollbar space-y-1 text-sm font-medium" aria-label="Panel menüsü">
        {APP_LINKS.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={linkClass} onClick={onNavigate}><Icon size={18} /> {label}</NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-200 text-[11px] text-slate-500 leading-relaxed flex items-start gap-2">
        <ShieldCheck size={14} className="text-teal shrink-0 mt-px" />
        <span>Üyelik gerekmez. Kişisel bilgileriniz yapay zekâya gönderilmez.</span>
      </div>
    </aside>
  );
}

function DashboardLayout() {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const close = () => setMenuOpen(false);

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-navy overflow-hidden">
      <div className="hidden md:block shrink-0 h-screen"><Sidebar /></div>

      {menuOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex" role="dialog" aria-modal="true" aria-label="Menü">
          <div className="h-full shadow-xl"><Sidebar onNavigate={close} /></div>
          <button type="button" className="flex-1 bg-navy/40" onClick={close} aria-label="Menüyü kapat" />
        </div>
      )}

      <div className="flex-1 flex flex-col h-screen overflow-hidden min-w-0">
        <header className="bg-white border-b border-slate-200 h-14 md:h-16 flex items-center justify-between px-4 md:px-6 shrink-0 gap-3">
          <div className="flex items-center gap-3 md:gap-4 text-sm font-bold text-navy min-w-0">
            <button type="button" className="md:hidden p-1.5 -ml-1.5 rounded-lg hover:bg-slate-100" onClick={() => setMenuOpen(true)} aria-label="Menüyü aç"><Menu size={20} /></button>
            <span className="truncate">Lexora</span>
            <span className="text-teal font-normal text-xs bg-teal/10 px-2 py-0.5 rounded">Beta</span>
            <BackendStatus />
          </div>
          <Link to="/" className="text-sm text-slate-500 font-medium hover:text-navy flex items-center gap-1 shrink-0"><Home size={16} /> <span className="hidden sm:inline">Ana sayfa</span></Link>
        </header>
        <DisclaimerBanner />
        <ErrorBoundary resetKey={location.pathname}>
          <Routes>
            <Route path="/app" element={<Navigate to="/app/danis-ai" replace />} />
            <Route path="/app/sihirbaz" element={<DashboardWizard />} />
            <Route path="/app/rehber" element={<DashboardRehber />} />
            <Route path="/app/danis-ai" element={<DashboardDanisAI />} />
            <Route path="/app/arsiv" element={<DashboardArsiv />} />
            <Route path="*" element={<NotFound homePath="/app/danis-ai" />} />
          </Routes>
        </ErrorBoundary>
      </div>
    </div>
  );
}

// =====================================================================
// PUBLIC SAYFALAR
// =====================================================================

function PublicLayout() {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const linkClass = ({ isActive }) => `transition-colors ${isActive ? 'text-teal font-bold' : 'hover:text-teal'}`;

  return (
    <div className="min-h-screen relative flex flex-col font-sans text-navy bg-[#fafafa]">
      {location.pathname === '/' && <div className="bg-grid-pattern"></div>}

      <div className="bg-navy text-white text-[11px] py-2 px-4 flex justify-center items-center gap-2 text-center">
        <span className="bg-teal px-2 py-0.5 rounded text-[10px] font-bold tracking-wide shrink-0">YASAL UYARI</span>
        <span className="opacity-90">Lexora bir yapay zekâ asistanıdır; avukatlık hizmeti vermez.</span>
      </div>

      <nav className="max-w-7xl mx-auto w-full px-6 py-4 flex items-center justify-between relative z-20" aria-label="Ana menü">
        <div className="flex items-center gap-8">
          <Link to="/" aria-label="Ana sayfa"><LexoraLogo className="h-10" /></Link>
          <div className="hidden lg:flex items-center gap-6 text-sm font-medium">
            {PUBLIC_LINKS.map(({ to, label }) => <NavLink key={to} to={to} className={linkClass}>{label}</NavLink>)}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/app/danis-ai" className="bg-navy hover:bg-navy/90 text-white text-sm font-medium px-4 md:px-5 py-2.5 rounded-full transition-all flex items-center gap-2">Hemen Başla <ChevronRight size={16} /></Link>
          <button type="button" className="lg:hidden p-2 rounded-lg hover:bg-slate-100" onClick={() => setMenuOpen((o) => !o)} aria-expanded={menuOpen} aria-label="Menü">
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
        {menuOpen && (
          <div className="lg:hidden absolute top-full left-4 right-4 bg-white border border-slate-200 rounded-2xl shadow-lg p-4 flex flex-col gap-3 text-sm font-medium">
            {PUBLIC_LINKS.map(({ to, label }) => <NavLink key={to} to={to} className={linkClass} onClick={() => setMenuOpen(false)}>{label}</NavLink>)}
          </div>
        )}
      </nav>

      <ErrorBoundary resetKey={location.pathname}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/ozellikler" element={<FeaturesPage />} />
          <Route path="/sss" element={<FaqPage />} />
          <Route path="/kvkk" element={<KvkkPage />} />
          {/* No accounts yet: old login links land in the app */}
          <Route path="/giris" element={<Navigate to="/app/danis-ai" replace />} />
          <Route path="/kayit" element={<Navigate to="/app/danis-ai" replace />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </ErrorBoundary>

      <footer className="border-t border-slate-200 bg-white pt-10 pb-6 mt-auto relative z-20">
        <div className="max-w-7xl mx-auto px-6 mb-10">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-4 items-start">
            <AlertTriangle className="text-amber-500 shrink-0 mt-0.5" size={20} />
            <div>
              <h2 className="text-xs font-bold text-amber-800 mb-1">Yasal bildirim</h2>
              <p className="text-[11px] text-amber-700 leading-relaxed">Lexora&apos;nın sunduğu bilgiler ve belge taslakları avukatlık hizmeti yerine geçmez. Üretilen metinleri kullanmadan önce kontrol etmek kullanıcının sorumluluğundadır.</p>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-8 text-xs text-slate-500 mb-10">
          <div>
            <div className="mb-4"><LexoraLogo className="h-8" /></div>
            <p className="leading-relaxed">Kira, tüketici ve iş hukukunda kanun maddesine dayalı bilgi veren ve ihtarname taslağı hazırlayan yapay zekâ asistanı.</p>
          </div>
          <div>
            <h2 className="font-bold text-navy text-sm mb-4">Araçlar</h2>
            <ul className="space-y-2">
              <li><Link to="/app/danis-ai" className="hover:text-teal">Danış AI</Link></li>
              <li><Link to="/app/sihirbaz" className="hover:text-teal">Belge Sihirbazı</Link></li>
              <li><Link to="/app/rehber" className="hover:text-teal">Hak Rehberi</Link></li>
            </ul>
          </div>
          <div>
            <h2 className="font-bold text-navy text-sm mb-4">Bilgi</h2>
            <ul className="space-y-2">
              <li><Link to="/ozellikler" className="hover:text-teal">Nasıl Çalışır</Link></li>
              <li><Link to="/sss" className="hover:text-teal">Sıkça Sorulan Sorular</Link></li>
              <li><Link to="/kvkk" className="hover:text-teal">Kişisel Verilerin Korunması</Link></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 text-xs text-slate-400 border-t border-slate-100 pt-6">© 2026 Lexora</div>
      </footer>
    </div>
  );
}

function App() {
  const location = useLocation();
  return location.pathname.startsWith('/app') ? <DashboardLayout /> : <PublicLayout />;
}

export default App;
