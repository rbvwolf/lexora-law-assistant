/**
 * Documents generated in this browser tab, kept in sessionStorage so the archive screen can list
 * them until the backend deletes the files (DOCUMENT_TTL_MINUTES).
 *
 * KVKK: only the template id/title, file links and timestamps are stored. Names, TC IDs, IBANs
 * and addresses never enter storage. sessionStorage is cleared when the tab is closed.
 */

const STORAGE_KEY = 'lexora.generatedDocuments.v1'
const MAX_ENTRIES = 20

/**
 * @typedef {Object} StoredDocument
 * @property {string} file_id
 * @property {string} template_id
 * @property {string} title
 * @property {string} docx_url
 * @property {string} pdf_url
 * @property {string} expires_at
 * @property {string} created_at
 */

function getStorage(storage) {
  if (storage) return storage
  try {
    return globalThis.sessionStorage ?? null
  } catch {
    return null // blocked storage (privacy mode, sandboxed iframe)
  }
}

/** @returns {StoredDocument[]} */
export function loadDocuments(storage) {
  const store = getStorage(storage)
  if (!store) return []
  try {
    const parsed = JSON.parse(store.getItem(STORAGE_KEY) ?? '[]')
    return Array.isArray(parsed) ? parsed.filter((d) => d && typeof d.file_id === 'string') : []
  } catch {
    return []
  }
}

/**
 * Add a generated document (newest first). Extra keys are dropped so PII cannot slip in.
 * @param {import('./api.js').DocumentGenerateResponse} response
 * @param {{ template_id: string, title: string }} template
 * @returns {StoredDocument[]}
 */
export function saveDocument(response, template, storage, now = new Date()) {
  const entry = {
    file_id: String(response.file_id),
    template_id: String(template.template_id),
    title: String(template.title),
    docx_url: String(response.docx_url),
    pdf_url: String(response.pdf_url),
    expires_at: String(response.expires_at),
    created_at: now.toISOString(),
  }
  const next = [entry, ...loadDocuments(storage).filter((d) => d.file_id !== entry.file_id)].slice(0, MAX_ENTRIES)
  const store = getStorage(storage)
  try {
    store?.setItem(STORAGE_KEY, JSON.stringify(next))
  } catch {
    // Quota or blocked storage: the document is still downloadable from the wizard
  }
  return next
}

/** Remove entries whose files the backend has already deleted. */
export function pruneExpired(storage, now = Date.now()) {
  const kept = loadDocuments(storage).filter((d) => Date.parse(d.expires_at) > now)
  try {
    getStorage(storage)?.setItem(STORAGE_KEY, JSON.stringify(kept))
  } catch {
    // ignore
  }
  return kept
}

export function clearDocuments(storage) {
  try {
    getStorage(storage)?.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}
