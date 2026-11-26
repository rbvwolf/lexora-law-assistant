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
  TIMEOUT: 'TIMEOUT', // no answer within the request timeout
})

/** Backend error code for a Groq rate limit (503 + retry_after_seconds). */
export const LLM_RATE_LIMITED = 'LLM_RATE_LIMITED'

/** Default per-request timeout. The target is p95 < 10 s; this leaves room for a cold start. */
export const DEFAULT_TIMEOUT_MS = 30000

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
 * @typedef {Object} HealthResponse
 * @property {string} status "healthy" | "degraded"
 * @property {string} environment
 * @property {Object<string, string>} dependencies
 */

/**
 * @typedef {Object} RequestOptions
 * @property {AbortSignal} [signal] Lets the caller cancel the request
 * @property {number} [timeoutMs] Overrides DEFAULT_TIMEOUT_MS; 0 disables the timeout
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
   * @param {number | null} [retryAfterSeconds] Set on 503 LLM_RATE_LIMITED: when a retry can succeed
   */
  constructor(status, errorCode, message, retryAfterSeconds = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.errorCode = errorCode
    this.retryAfterSeconds = retryAfterSeconds
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
 * @param {{ method?: string, body?: unknown, signal?: AbortSignal, timeoutMs?: number }} [options]
 */
async function request(path, { method = 'GET', body, signal, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const headers = { Accept: 'application/json' }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  // One controller aborts the fetch for both reasons; timedOut tells them apart afterwards
  const controller = new AbortController()
  let timedOut = false
  const onCallerAbort = () => controller.abort()
  if (signal?.aborted) controller.abort()
  else signal?.addEventListener('abort', onCallerAbort, { once: true })
  const timer = timeoutMs > 0
    ? setTimeout(() => { timedOut = true; controller.abort() }, timeoutMs)
    : undefined

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      // Backend sets allow_credentials=False; no cookies are ever sent
      credentials: 'omit',
      signal: controller.signal,
    })
  } catch (error) {
    if (timedOut) {
      throw new ApiError(0, CLIENT_ERROR_CODES.TIMEOUT, 'Sunucu zamanında cevap vermedi. Lütfen tekrar deneyin.')
    }
    if (error?.name === 'AbortError') {
      throw error // cancelled by the caller: let it tell this apart from a failure
    }
    throw new ApiError(0, CLIENT_ERROR_CODES.NETWORK_ERROR, 'Sunucuya ulaşılamadı.')
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', onCallerAbort)
  }

  const data = await readJson(response)

  if (!response.ok) {
    if (data && typeof data.error_code === 'string') {
      const retryAfter = Number(data.retry_after_seconds)
      throw new ApiError(
        response.status,
        data.error_code,
        String(data.message ?? ''),
        Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : null,
      )
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
export function sendChatMessage(sessionId, message, { signal, timeoutMs } = {}) {
  return request('/api/v1/chat/message', {
    method: 'POST',
    body: { session_id: sessionId, message },
    signal,
    timeoutMs,
  })
}

/**
 * GET /api/v1/documents/templates
 * @param {RequestOptions} [options]
 * @returns {Promise<TemplateListResponse>}
 */
export function listTemplates({ signal, timeoutMs } = {}) {
  return request('/api/v1/documents/templates', { signal, timeoutMs })
}

/**
 * GET /api/v1/health
 * @param {RequestOptions} [options]
 * @returns {Promise<HealthResponse>}
 */
export function getHealth({ signal, timeoutMs = 5000 } = {}) {
  return request('/api/v1/health', { signal, timeoutMs })
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
export function generateDocument(templateId, caseParams, pii, { signal, timeoutMs } = {}) {
  return request('/api/v1/documents/generate', {
    method: 'POST',
    body: { template_id: templateId, case_params: caseParams, pii },
    signal,
    timeoutMs,
  })
}
