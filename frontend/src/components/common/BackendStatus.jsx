import { useEffect, useState } from 'react';
import { getHealth } from '../../lib/api';

const POLL_MS = 60000;

const LABELS = {
  checking: { text: 'Sunucu kontrol ediliyor', dot: 'bg-slate-300', tone: 'text-slate-500' },
  healthy: { text: 'Sunucu çevrimiçi', dot: 'bg-teal', tone: 'text-teal' },
  degraded: { text: 'Sunucu kısıtlı çalışıyor', dot: 'bg-amber-500', tone: 'text-amber-700' },
  offline: { text: 'Sunucuya ulaşılamıyor', dot: 'bg-red-500', tone: 'text-red-600' },
};

/** Small header indicator backed by GET /api/v1/health, re-checked every minute. */
const BackendStatus = () => {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    let controller;
    const check = async () => {
      controller?.abort();
      controller = new AbortController();
      try {
        const res = await getHealth({ signal: controller.signal });
        setStatus(res.status === 'healthy' ? 'healthy' : 'degraded');
      } catch (error) {
        if (error?.name !== 'AbortError') setStatus('offline');
      }
    };
    check();
    const timer = setInterval(check, POLL_MS);
    return () => {
      clearInterval(timer);
      controller?.abort();
    };
  }, []);

  const label = LABELS[status];
  return (
    <span className={`flex items-center gap-1.5 text-xs font-bold ${label.tone}`} role="status" aria-live="polite">
      <span className={`w-2 h-2 rounded-full ${label.dot} ${status === 'healthy' ? 'animate-pulse' : ''}`} aria-hidden="true" />
      {label.text}
    </span>
  );
};

export default BackendStatus;
