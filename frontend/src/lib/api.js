/**
 * lexora backend API client (plain fetch, no dependencies).
 *
 * Responses are returned exactly as the backend sends them (snake_case, no renaming), so the
 * fields below always match backend/app/schemas/*. Every non-2xx answer becomes an ApiError
 * carrying the backend's { error_code, message }.
 *
 * Usage:
 *   import { sendChatMessage, ApiError } from '../lib/api'
 *   try { const res = await sendChatMessage(sessionId, text) }
 *   catch (e) { if (e instanceof ApiError && e.errorCode === 'EMPTY_MESSAGE') { ... } }
 */

const DEFAULT_API_BASE_URL = 'http://localhost:8000'

/**
 * Codes produced by this client, never by the backend. HTTP_ERROR matches the code the backend
 * itself uses for errors without a structured body.
 */
export const CLIENT_ERROR_CODES = Object.freeze({
  NETWORK_ERROR: 'NETWORK_ERROR', // backend unreachable or blocked by CORS
  HTTP_ERROR: 'HTTP_ERROR', // non-2xx without a JSON { error_code, message } body
  INVALID_RESPONSE: 'INVALID_RESPONSE', // 2xx whose body is not JSON
})

// ---------------------------------------------------------------------------
// Types (copied from backend/app/schemas; keep in sync)
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} Citation
 * @property {string} article_id
 * @property {string} law_name
 * @property {string} text_snippet
 */

/**
 * @typedef {Object} ChatResponse
 * @property {'question_answering' | 'document_generation' | 'out_of_scope'} intent
 * @property {string} answer
 * @property {Citation[]} citations
 * @property {Object<string, *>} extracted_params
 * @property {string[]} missing_fields
 * @property {string | null} suggested_template_id
 * @property {string} disclaimer
 */

/**
 * @typedef {Object} TemplateFieldSchema
 * @property {string} field_name
 * @property {string} label
 * @property {'string' | 'number' | 'date' | 'tc_id' | 'iban'} field_type
 * @property {boolean} required
 * @property {string | null} description
 */

/**
 * @typedef {Object} TemplateSchema
 * @property {string} template_id
 * @property {string} title
 * @property {string} domain
 * @property {string} description
 * @property {TemplateFieldSchema[]} case_param_fields
 * @property {TemplateFieldSchema[]} pii_fields
 */

/**
 * @typedef {Object} TemplateListResponse
 * @property {TemplateSchema[]} templates
 */

/**
 * @typedef {Object} DocumentGenerateResponse
 * @property {string} file_id
 * @property {string} docx_url Relative, e.g. "/api/v1/documents/download/<uuid>.docx"; see downloadUrl()
 * @property {string} pdf_url Relative; see downloadUrl()
 * @property {string} expires_at ISO 8601 timestamp
 * @property {string} disclaimer
 */

/**
 * @typedef {Object} RequestOptions
 * @property {AbortSignal} [signal] Lets the caller cancel or time out the request
 */

// ---------------------------------------------------------------------------
// Base URL and download links (pure functions)
// ---------------------------------------------------------------------------

/**
 * Backend base URL from Vite env (VITE_API_BASE_URL, baked in at build time), without a
 * trailing slash. Falls back to the local uvicorn default.
 * @param {Record<string, string | undefined> | undefined} env
 * @returns {string}
 */
export function resolveApiBaseUrl(env) {
  const configured = env?.VITE_API_BASE_URL?.trim()
  return (configured || DEFAULT_API_BASE_URL).replace(/\/+$/, '')
}

// Outside Vite (e.g. node --test) import.meta.env is undefined; resolveApiBaseUrl handles that
export const API_BASE_URL = resolveApiBaseUrl(import.meta.env)

/**
 * Turn a backend-relative path (docx_url / pdf_url from generateDocument) into a full URL for
 * an <a href>. Plain concatenation keeps any path in the base URL (new URL() would drop it).
 * Absolute http(s) URLs are returned unchanged; protocol-relative ("//host") or empty input is
 * rejected so a download link can never silently point at another site.
 * @param {string} relativeUrl
 * @param {string} [baseUrl]
 * @returns {string}
 */
export function downloadUrl(relativeUrl, baseUrl = API_BASE_URL) {
  if (typeof relativeUrl !== 'string' || relativeUrl.trim() === '') {
    throw new TypeError('downloadUrl: relativeUrl must be a non-empty string')
  }
  if (/^https?:\/\//i.test(relativeUrl)) {
    return relativeUrl
  }
  if (!relativeUrl.startsWith('/') || relativeUrl.startsWith('//')) {
    throw new TypeError('downloadUrl: expected a path starting with a single "/"')
  }
  return `${baseUrl.replace(/\/+$/, '')}${relativeUrl}`
}

// ---------------------------------------------------------------------------
// Errors and the shared request helper
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  /**
   * @param {number} status HTTP status, or 0 when no response was received
   * @param {string} errorCode Backend error_code, or one of CLIENT_ERROR_CODES
   * @param {string} message Backend message (contains no PII by backend contract)
   */
  constructor(status, errorCode, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.errorCode = errorCode
  }
}

async function readJson(response) {
  try {
    return await response.json()
  } catch {
    return undefined
  }
}

/**
 * @param {string} path Path under the base URL, e.g. "/api/v1/chat/message"
 * @param {{ method?: string, body?: unknown, signal?: AbortSignal }} [options]
 */
async function request(path, { method = 'GET', body, signal } = {}) {
  const headers = { Accept: 'application/json' }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      // Backend sets allow_credentials=False; no cookies are ever sent
      credentials: 'omit',
      signal,
    })
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw error // cancelled by the caller: let it tell this apart from a failure
    }
    throw new ApiError(0, CLIENT_ERROR_CODES.NETWORK_ERROR, 'Sunucuya ulaşılamadı.')
  }

  const data = await readJson(response)

  if (!response.ok) {
    if (data && typeof data.error_code === 'string') {
      throw new ApiError(response.status, data.error_code, String(data.message ?? ''))
    }
    throw new ApiError(response.status, CLIENT_ERROR_CODES.HTTP_ERROR, `Beklenmeyen sunucu cevabı (HTTP ${response.status}).`)
  }
  if (data === undefined) {
    throw new ApiError(response.status, CLIENT_ERROR_CODES.INVALID_RESPONSE, 'Sunucu cevabı okunamadı.')
  }
  return data
}

// ---------------------------------------------------------------------------
// Endpoints (AGENTS.md §4)
// ---------------------------------------------------------------------------

/**
 * POST /api/v1/chat/message
 * @param {string} sessionId
 * @param {string} message
 * @param {RequestOptions} [options]
 * @returns {Promise<ChatResponse>}
 */
export function sendChatMessage(sessionId, message, { signal } = {}) {
  return request('/api/v1/chat/message', {
    method: 'POST',
    body: { session_id: sessionId, message },
    signal,
  })
}

/**
 * GET /api/v1/documents/templates
 * @param {RequestOptions} [options]
 * @returns {Promise<TemplateListResponse>}
 */
export function listTemplates({ signal } = {}) {
  return request('/api/v1/documents/templates', { signal })
}

/**
 * POST /api/v1/documents/generate
 * PII goes only here (mini-form -> doc_service), never into sendChatMessage.
 * @param {string} templateId
 * @param {Object<string, *>} caseParams
 * @param {Object<string, string>} pii Keys per the template's pii_fields
 * @param {RequestOptions} [options]
 * @returns {Promise<DocumentGenerateResponse>}
 */
export function generateDocument(templateId, caseParams, pii, { signal } = {}) {
  return request('/api/v1/documents/generate', {
    method: 'POST',
    body: { template_id: templateId, case_params: caseParams, pii },
    signal,
  })
}
