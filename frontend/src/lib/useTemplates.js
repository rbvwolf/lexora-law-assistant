import { useCallback, useEffect, useState } from 'react';
import { ApiError, listTemplates } from './api';

// One request per page load shared by every screen; reset on failure so "Tekrar dene" refetches
let cached = null;

function fetchTemplates() {
  if (!cached) {
    cached = listTemplates().then((res) => res.templates ?? []);
    cached.catch(() => {
      cached = null;
    });
  }
  return cached;
}

/**
 * Active document templates from GET /api/v1/documents/templates.
 * @returns {{ templates: import('./api').TemplateSchema[], loading: boolean, error: string | null, retry: () => void }}
 */
export function useTemplates() {
  const [state, setState] = useState({ templates: [], loading: true, error: null });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    fetchTemplates().then(
      (templates) => active && setState({ templates, loading: false, error: null }),
      (error) => active && setState({
        templates: [],
        loading: false,
        error: error instanceof ApiError ? error.message : 'Şablonlar yüklenemedi.',
      }),
    );
    return () => {
      active = false;
    };
  }, [attempt]);

  const retry = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    setAttempt((n) => n + 1);
  }, []);

  return { ...state, retry };
}
