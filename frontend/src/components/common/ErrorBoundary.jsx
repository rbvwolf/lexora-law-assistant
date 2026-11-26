import { Component } from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

/**
 * Catches render errors in a screen so one broken component does not blank the whole app.
 * Pass resetKey (e.g. the current path) to clear the error when the user navigates away.
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, resetKey: props.resetKey };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  static getDerivedStateFromProps(props, state) {
    if (props.resetKey !== state.resetKey) {
      return { hasError: false, resetKey: props.resetKey };
    }
    return null;
  }

  componentDidCatch(error, info) {
    // Only the error itself is logged: component state may hold form values (PII)
    console.error('[lexora] Ekran hatası:', error?.message, info?.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div role="alert" className="flex-1 flex flex-col items-center justify-center text-center p-10 gap-3 bg-[#f8fafc]">
        <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center"><AlertOctagon size={22} /></div>
        <h2 className="text-lg font-bold text-navy">Bu ekranda beklenmeyen bir hata oluştu</h2>
        <p className="text-sm text-slate-500 max-w-md">Sayfayı yenileyip tekrar deneyin. Sorun devam ederse farklı bir ekrandan devam edebilirsiniz.</p>
        <button type="button" onClick={() => window.location.reload()} className="mt-2 bg-navy text-white text-sm font-bold px-5 py-2.5 rounded-xl flex items-center gap-2 hover:bg-navy/90">
          <RefreshCw size={16} /> Sayfayı yenile
        </button>
      </div>
    );
  }
}

export default ErrorBoundary;
