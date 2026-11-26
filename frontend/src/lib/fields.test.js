// Run: npm test   (node --test, no dependencies)
import assert from 'node:assert/strict'
import { describe, it } from 'node:test'

import {
  READY_TEMPLATE_IDS,
  TEMERRUT_TEMPLATE_ID,
  crossFieldErrors,
  fieldLabel,
  formatIban,
  formatRemaining,
  formatTrDate,
  formatTrNumber,
  hesaplaKiraArtisi,
  kiraArtisCrossErrors,
  maskSensitive,
  parseFieldErrorMessage,
  parseNumber,
  prefillFromExtracted,
  temerrutCrossErrors,
  toPayload,
  validateField,
  validateFields,
} from './fields.js'
import { clearDocuments, loadDocuments, pruneExpired, saveDocument } from './documentStore.js'

const f = (field_name, field_type = 'string', required = true) => ({ field_name, label: field_name, field_type, required, description: null })

const TEMPLATE = {
  template_id: 'kira_artis_itiraz_ihtarname',
  title: 'Fahiş Kira Artışına İtiraz İhtarnamesi',
  domain: 'Kira Hukuku',
  description: '',
  case_param_fields: [
    f('kira_baslangic_tarihi', 'date'),
    f('mevcut_kira_tutari', 'number'),
    f('talep_edilen_kira_tutari', 'number'),
    f('tufe_oran', 'number'),
    f('noter_ili'),
  ],
  pii_fields: [f('kiraci_ad_soyad'), f('kiraci_tc', 'tc_id', false), f('iban', 'iban')],
}

describe('parseNumber', () => {
  it('reads Turkish and plain notations', () => {
    assert.equal(parseNumber('12.000,50'), 12000.5)
    assert.equal(parseNumber('12,000.50'), 12000.5)
    assert.equal(parseNumber('12000'), 12000)
    assert.equal(parseNumber('12.000'), 12000)
    assert.equal(parseNumber('62,51'), 62.51)
    assert.equal(parseNumber('62.51'), 62.51)
    assert.equal(parseNumber('15.000 TL'), 15000)
    assert.equal(parseNumber(48), 48)
  })
  it('rejects text', () => {
    assert.ok(Number.isNaN(parseNumber('on bin')))
    assert.ok(Number.isNaN(parseNumber('')))
    assert.ok(Number.isNaN(parseNumber(null)))
  })
})

describe('validateField', () => {
  it('required and optional blanks', () => {
    assert.equal(validateField(f('a'), '  '), 'Bu alan zorunludur.')
    assert.equal(validateField(f('a', 'string', false), ''), null)
  })
  it('tc_id is 11 digits', () => {
    assert.equal(validateField(f('tc', 'tc_id'), '12345678901'), null)
    assert.ok(validateField(f('tc', 'tc_id'), '1234567890'))
    assert.ok(validateField(f('tc', 'tc_id'), '1234567890a'))
  })
  it('iban accepts spaces and lower case, like the backend after normalising', () => {
    assert.equal(validateField(f('iban', 'iban'), 'tr12 0006 1000 0000 1234 5678 90'), null)
    assert.ok(validateField(f('iban', 'iban'), 'DE12000610000000123456789'))
  })
  it('date must be a real ISO date', () => {
    assert.equal(validateField(f('d', 'date'), '2024-02-29'), null)
    assert.ok(validateField(f('d', 'date'), '2023-02-29'))
    assert.ok(validateField(f('d', 'date'), '01.09.2024'))
  })
  it('validateFields collects per-field errors', () => {
    const errors = validateFields(TEMPLATE.pii_fields, { kiraci_ad_soyad: 'A', kiraci_tc: '1', iban: '' })
    assert.deepEqual(Object.keys(errors).sort(), ['iban', 'kiraci_tc'])
  })
})

describe('toPayload', () => {
  it('converts types and drops blank optional fields', () => {
    const payload = toPayload([...TEMPLATE.case_param_fields, ...TEMPLATE.pii_fields], {
      mevcut_kira_tutari: '15.000',
      tufe_oran: '48,5',
      noter_ili: '  İstanbul ',
      kiraci_tc: '',
      iban: 'tr12 0006 1000 0000 1234 5678 90',
    })
    assert.deepEqual(payload, {
      mevcut_kira_tutari: 15000,
      tufe_oran: 48.5,
      noter_ili: 'İstanbul',
      iban: 'TR120006100000001234567890',
    })
  })
})

describe('prefillFromExtracted', () => {
  it('keeps only the template case fields, never PII keys', () => {
    const values = prefillFromExtracted(TEMPLATE, {
      mevcut_kira_tutari: 15000,
      tufe_oran: 48.0,
      noter_ili: 'İstanbul',
      kiraci_ad_soyad: 'should not be copied',
      uyusmazlik_turu: 'x',
      kira_baslangic_tarihi: 'geçen eylül',
    })
    assert.deepEqual(values, { mevcut_kira_tutari: '15000', tufe_oran: '48', noter_ili: 'İstanbul' })
  })
  it('joins lists', () => {
    const t = { ...TEMPLATE, case_param_fields: [f('gecikilen_aylar')] }
    assert.deepEqual(prefillFromExtracted(t, { gecikilen_aylar: ['Eylül 2026', 'Ekim 2026'] }), { gecikilen_aylar: 'Eylül 2026, Ekim 2026' })
  })
})

describe('parseFieldErrorMessage', () => {
  it('splits the backend message into field names', () => {
    assert.deepEqual(parseFieldErrorMessage('Eksik: kiraci_adres, noter_ili; Geçersiz: iban'), {
      missing: ['kiraci_adres', 'noter_ili'],
      invalid: ['iban'],
      unknown: [],
    })
    assert.deepEqual(parseFieldErrorMessage('garbage'), { missing: [], invalid: [], unknown: [] })
  })
})

describe('kira artışı (TBK m. 344)', () => {
  it('matches doc_service rounding', () => {
    const r = hesaplaKiraArtisi('12000', '24000', '62,51')
    assert.equal(r.azami, 19501.2)
    assert.equal(r.fazlaTutar, 4498.8)
    assert.equal(r.talepArtisOrani, 100)
    assert.equal(r.asiyor, true)
  })
  it('returns null for incomplete input', () => {
    assert.equal(hesaplaKiraArtisi('', '24000', '62'), null)
    assert.equal(hesaplaKiraArtisi('0', '24000', '62'), null)
  })
  it('cross errors mirror _check_kira_artis', () => {
    assert.deepEqual(Object.keys(kiraArtisCrossErrors({ mevcut_kira_tutari: '10000', talep_edilen_kira_tutari: '14000', tufe_oran: '48' })), ['talep_edilen_kira_tutari'])
    assert.deepEqual(kiraArtisCrossErrors({ mevcut_kira_tutari: '10000', talep_edilen_kira_tutari: '20000', tufe_oran: '48' }), {})
    assert.ok(kiraArtisCrossErrors({ mevcut_kira_tutari: '10000', talep_edilen_kira_tutari: '20000', tufe_oran: '250' }).tufe_oran)
  })
})

describe('temerrut (TBK m. 315)', () => {
  const ok = { kira_tutari: '18.000', odenmeyen_toplam_tutar: '36000', odeme_suresi_gun: '30' }
  it('accepts a valid payment period and amounts', () => {
    assert.deepEqual(temerrutCrossErrors(ok), {})
    assert.deepEqual(temerrutCrossErrors({ ...ok, odeme_suresi_gun: '365' }), {})
  })
  it('rejects periods below 30 days, fractions and over 365, like _check_temerrut', () => {
    for (const sure of ['29', '10', '0', '30,5', '366']) {
      assert.deepEqual(Object.keys(temerrutCrossErrors({ ...ok, odeme_suresi_gun: sure })), ['odeme_suresi_gun'], sure)
    }
  })
  it('rejects non-positive amounts', () => {
    assert.deepEqual(Object.keys(temerrutCrossErrors({ ...ok, kira_tutari: '0' })), ['kira_tutari'])
    assert.deepEqual(Object.keys(temerrutCrossErrors({ ...ok, odenmeyen_toplam_tutar: '-5' })), ['odenmeyen_toplam_tutar'])
  })
  it('leaves blank or unparsable values to the per-field check', () => {
    assert.deepEqual(temerrutCrossErrors({ odeme_suresi_gun: '', kira_tutari: 'abc' }), {})
  })
  it('is wired into crossFieldErrors and marked ready', () => {
    assert.ok(crossFieldErrors(TEMERRUT_TEMPLATE_ID, { ...ok, odeme_suresi_gun: '15' }).odeme_suresi_gun)
    assert.deepEqual(crossFieldErrors('tuketici_ayipli_mal_ihtarname', { odeme_suresi_gun: '15' }), {})
    assert.ok(READY_TEMPLATE_IDS.includes(TEMERRUT_TEMPLATE_ID))
  })
})

describe('formatting', () => {
  it('numbers, dates, IBAN, masking', () => {
    assert.equal(formatTrNumber(19501.2), '19.501,20')
    assert.equal(formatTrDate('2024-09-01'), '01.09.2024')
    assert.equal(formatIban('TR120006100000001234567890'), 'TR12 0006 1000 0000 1234 5678 90')
    assert.equal(maskSensitive('12345678901'), '123*****901')
  })
  it('remaining time', () => {
    const now = Date.parse('2026-11-26T10:00:00Z')
    assert.equal(formatRemaining('2026-11-26T11:30:00Z', now), '1 sa 30 dk')
    assert.equal(formatRemaining('2026-11-26T10:05:00Z', now), '5 dk')
    assert.equal(formatRemaining('2026-11-26T09:00:00Z', now), 'süresi doldu')
  })
  it('field labels fall back to a readable key', () => {
    assert.equal(fieldLabel([TEMPLATE], 'noter_ili'), 'noter_ili')
    assert.equal(fieldLabel([], 'olay_tarihi'), 'Olay tarihi')
  })
})

describe('documentStore', () => {
  const memory = () => {
    const data = new Map()
    return { getItem: (k) => data.get(k) ?? null, setItem: (k, v) => data.set(k, v), removeItem: (k) => data.delete(k), data }
  }
  const response = (id, expires) => ({ file_id: id, docx_url: `/d/${id}.docx`, pdf_url: `/d/${id}.pdf`, expires_at: expires, disclaimer: 'x' })

  it('stores only non-personal keys, newest first, without duplicates', () => {
    const store = memory()
    saveDocument(response('a', '2099-01-01T00:00:00Z'), { template_id: 't', title: 'T', pii: { tc: '1' } }, store)
    saveDocument(response('b', '2099-01-01T00:00:00Z'), { template_id: 't', title: 'T' }, store)
    saveDocument(response('a', '2099-01-01T00:00:00Z'), { template_id: 't', title: 'T' }, store)
    const docs = loadDocuments(store)
    assert.deepEqual(docs.map((d) => d.file_id), ['a', 'b'])
    assert.deepEqual(Object.keys(docs[0]).sort(), ['created_at', 'docx_url', 'expires_at', 'file_id', 'pdf_url', 'template_id', 'title'])
  })
  it('prunes expired entries and survives broken JSON', () => {
    const store = memory()
    saveDocument(response('old', '2000-01-01T00:00:00Z'), { template_id: 't', title: 'T' }, store)
    saveDocument(response('new', '2099-01-01T00:00:00Z'), { template_id: 't', title: 'T' }, store)
    assert.deepEqual(pruneExpired(store).map((d) => d.file_id), ['new'])
    store.setItem('lexora.generatedDocuments.v1', '{broken')
    assert.deepEqual(loadDocuments(store), [])
    clearDocuments(store)
    assert.equal(store.data.size, 0)
  })
})
