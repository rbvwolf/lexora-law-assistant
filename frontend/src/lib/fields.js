/**
 * Template field helpers (pure functions, no React, no network).
 *
 * The rules mirror backend/app/services/doc_service.py so the user sees a problem before the
 * request is sent. The backend stays the authority: its TEMPLATE_FIELDS_INVALID answer is mapped
 * back onto the form with parseFieldErrorMessage().
 */

// Same patterns as doc_service.TC_ID_RE / IBAN_TR_RE
const TC_ID_RE = /^\d{11}$/
const IBAN_TR_RE = /^TR\d{24}$/
const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/

// doc_service.KIRA_ARTIS_TEMPLATE_ID and TUFE_ORAN_MAX
export const KIRA_ARTIS_TEMPLATE_ID = 'kira_artis_itiraz_ihtarname'
export const TUFE_ORAN_MAX = 200

/**
 * Templates whose backend output is a real rendered document. The others still produce
 * placeholder files (doc_service._RENDER_CONTEXT_BUILDERS); update this when G2 adds one.
 */
export const READY_TEMPLATE_IDS = Object.freeze([KIRA_ARTIS_TEMPLATE_ID])

/** @param {unknown} value */
export function isBlank(value) {
  return value === undefined || value === null || (typeof value === 'string' && value.trim() === '')
}

/** IBAN as the backend expects it: no spaces, upper case. */
export function normalizeIban(value) {
  return String(value ?? '').replace(/\s+/g, '').toUpperCase()
}

/** Display an IBAN in groups of four: TR12 0006 1000 ... */
export function formatIban(value) {
  return normalizeIban(value).replace(/(.{4})(?=.)/g, '$1 ')
}

/**
 * Parse a number typed by a Turkish user: "12.000,50", "12000.5", "12000". Returns NaN when the
 * text is not a number.
 * @param {unknown} value
 * @returns {number}
 */
export function parseNumber(value) {
  if (typeof value === 'number') return value
  if (typeof value !== 'string') return Number.NaN
  let text = value.trim().replace(/\s+/g, '').replace(/₺|TL|%/gi, '')
  if (text === '') return Number.NaN
  const hasComma = text.includes(',')
  const hasDot = text.includes('.')
  if (hasComma && hasDot) {
    // The last separator is the decimal one: "12.000,50" or "12,000.50"
    text = text.lastIndexOf(',') > text.lastIndexOf('.')
      ? text.replace(/\./g, '').replace(',', '.')
      : text.replace(/,/g, '')
  } else if (hasComma) {
    text = text.replace(',', '.')
  } else if (hasDot && /^\d{1,3}(\.\d{3})+$/.test(text)) {
    // "12.000" is a thousands separator, not 12.0
    text = text.replace(/\./g, '')
  }
  if (!/^-?\d+(\.\d+)?$/.test(text)) return Number.NaN
  return Number(text)
}

function isValidIsoDate(value) {
  if (typeof value !== 'string' || !ISO_DATE_RE.test(value)) return false
  const [y, m, d] = value.split('-').map(Number)
  const date = new Date(Date.UTC(y, m - 1, d))
  return date.getUTCFullYear() === y && date.getUTCMonth() === m - 1 && date.getUTCDate() === d
}

/**
 * Check one value against its field schema.
 * @param {import('./api.js').TemplateFieldSchema} field
 * @param {unknown} value
 * @returns {string | null} Turkish error text, or null when the value is acceptable
 */
export function validateField(field, value) {
  if (isBlank(value)) {
    return field.required ? 'Bu alan zorunludur.' : null
  }
  switch (field.field_type) {
    case 'tc_id':
      return TC_ID_RE.test(String(value).trim()) ? null : 'T.C. Kimlik No 11 haneli olmalıdır.'
    case 'iban':
      return IBAN_TR_RE.test(normalizeIban(value)) ? null : 'IBAN "TR" ve 24 rakamdan oluşmalıdır.'
    case 'number':
      return Number.isFinite(parseNumber(value)) ? null : 'Geçerli bir sayı girin.'
    case 'date':
      return isValidIsoDate(value) ? null : 'Geçerli bir tarih seçin.'
    default:
      return null
  }
}

/**
 * Validate every field of a group.
 * @param {import('./api.js').TemplateFieldSchema[]} fields
 * @param {Record<string, unknown>} values
 * @returns {Record<string, string>} field_name -> error text (empty when all valid)
 */
export function validateFields(fields, values) {
  const errors = {}
  for (const field of fields) {
    const error = validateField(field, values?.[field.field_name])
    if (error) errors[field.field_name] = error
  }
  return errors
}

/**
 * Convert form values into the payload types the backend checks (number -> number, IBAN without
 * spaces, trimmed strings). Blank optional values are left out.
 * @param {import('./api.js').TemplateFieldSchema[]} fields
 * @param {Record<string, unknown>} values
 * @returns {Record<string, string | number>}
 */
export function toPayload(fields, values) {
  const payload = {}
  for (const field of fields) {
    const raw = values?.[field.field_name]
    if (isBlank(raw)) continue
    if (field.field_type === 'number') {
      payload[field.field_name] = parseNumber(raw)
    } else if (field.field_type === 'iban') {
      payload[field.field_name] = normalizeIban(raw)
    } else {
      payload[field.field_name] = String(raw).trim()
    }
  }
  return payload
}

/**
 * Turn the chat's extracted_params into form values for one template: keeps only the template's
 * case fields, joins lists, drops anything the form cannot show. Never touches PII fields.
 * @param {import('./api.js').TemplateSchema | undefined} template
 * @param {Record<string, unknown> | undefined} extracted
 * @returns {Record<string, string>}
 */
export function prefillFromExtracted(template, extracted) {
  const values = {}
  if (!template || !extracted || typeof extracted !== 'object') return values
  for (const field of template.case_param_fields) {
    const raw = extracted[field.field_name]
    if (raw === undefined || raw === null) continue
    if (Array.isArray(raw)) {
      values[field.field_name] = raw.map(String).join(', ')
    } else if (typeof raw === 'number' || typeof raw === 'string') {
      const text = String(raw).trim()
      if (field.field_type === 'date' && !isValidIsoDate(text)) continue
      values[field.field_name] = text
    }
  }
  return values
}

/**
 * Map a TEMPLATE_FIELDS_INVALID message ("Eksik: a, b; Geçersiz: c; Tanımsız: d") to field names.
 * @param {string} message
 * @returns {{ missing: string[], invalid: string[], unknown: string[] }}
 */
export function parseFieldErrorMessage(message) {
  const result = { missing: [], invalid: [], unknown: [] }
  const keys = { 'Eksik': 'missing', 'Geçersiz': 'invalid', 'Tanımsız': 'unknown' }
  for (const part of String(message ?? '').split(';')) {
    const match = part.match(/^\s*(Eksik|Geçersiz|Tanımsız)\s*:\s*(.*)$/)
    if (!match) continue
    result[keys[match[1]]].push(...match[2].split(',').map((s) => s.trim()).filter(Boolean))
  }
  return result
}

/** Human label for a field name, falling back to a readable version of the key. */
export function fieldLabel(templates, fieldName) {
  for (const template of templates ?? []) {
    for (const field of [...template.case_param_fields, ...template.pii_fields]) {
      if (field.field_name === fieldName) return field.label
    }
  }
  const text = String(fieldName).replace(/_/g, ' ').trim()
  return text.charAt(0).toLocaleUpperCase('tr-TR') + text.slice(1)
}

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

const TR_NUMBER = new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

/** 19501.2 -> "19.501,20" (same notation as doc_service._format_tr_number) */
export function formatTrNumber(value) {
  return Number.isFinite(value) ? TR_NUMBER.format(value) : ''
}

/** "2024-09-01" -> "01.09.2024"; anything else is returned unchanged. */
export function formatTrDate(value) {
  if (!isValidIsoDate(value)) return String(value ?? '')
  const [y, m, d] = value.split('-')
  return `${d}.${m}.${y}`
}

/** Mask a TC ID or IBAN for on-screen summaries: 12345678901 -> 123*****901 */
export function maskSensitive(value) {
  const text = String(value ?? '').replace(/\s+/g, '')
  if (text.length <= 6) return '*'.repeat(text.length)
  return `${text.slice(0, 3)}${'*'.repeat(text.length - 6)}${text.slice(-3)}`
}

// ---------------------------------------------------------------------------
// TBK m. 344 calculation (same rounding as doc_service._yasal_azami_kira)
// ---------------------------------------------------------------------------

const round2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100

/**
 * @param {unknown} mevcut current monthly rent
 * @param {unknown} talep requested monthly rent
 * @param {unknown} tufe 12-month average CPI change, percent
 * @returns {null | { mevcut: number, talep: number, tufe: number, azami: number, fazlaTutar: number,
 *   talepArtisOrani: number, asiyor: boolean }}
 */
export function hesaplaKiraArtisi(mevcut, talep, tufe) {
  const m = parseNumber(mevcut)
  const t = parseNumber(talep)
  const o = parseNumber(tufe)
  if (![m, t, o].every(Number.isFinite) || m <= 0 || o < 0 || o > TUFE_ORAN_MAX) return null
  const azami = round2(m * (1 + o / 100))
  return {
    mevcut: m,
    talep: t,
    tufe: o,
    azami,
    fazlaTutar: round2(t - azami),
    talepArtisOrani: round2(((t - m) / m) * 100),
    asiyor: t > azami,
  }
}

/**
 * Cross-field check for the rent-increase objection, mirroring doc_service._check_kira_artis.
 * @returns {Record<string, string>}
 */
export function kiraArtisCrossErrors(values) {
  const result = hesaplaKiraArtisi(values?.mevcut_kira_tutari, values?.talep_edilen_kira_tutari, values?.tufe_oran)
  const errors = {}
  const m = parseNumber(values?.mevcut_kira_tutari)
  const o = parseNumber(values?.tufe_oran)
  if (Number.isFinite(m) && m <= 0) errors.mevcut_kira_tutari = 'Mevcut kira sıfırdan büyük olmalıdır.'
  if (Number.isFinite(o) && (o < 0 || o > TUFE_ORAN_MAX)) errors.tufe_oran = `Oran 0 ile ${TUFE_ORAN_MAX} arasında olmalıdır.`
  if (result && !result.asiyor) {
    errors.talep_edilen_kira_tutari = 'Talep edilen kira yasal sınırın altında; bu durumda itiraz ihtarnamesi gerekmez.'
  }
  return errors
}

// ---------------------------------------------------------------------------
// Expiry
// ---------------------------------------------------------------------------

/**
 * Remaining time until an ISO timestamp, as Turkish text ("1 sa 12 dk", "süresi doldu").
 * @param {string} expiresAt
 * @param {number} [now]
 */
export function formatRemaining(expiresAt, now = Date.now()) {
  const ms = Date.parse(expiresAt) - now
  if (!Number.isFinite(ms)) return ''
  if (ms <= 0) return 'süresi doldu'
  const totalMinutes = Math.ceil(ms / 60000)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return hours > 0 ? `${hours} sa ${minutes} dk` : `${minutes} dk`
}
