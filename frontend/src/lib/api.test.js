// Run: node --test src/lib/   (from frontend/; no dependencies, no network: fetch is stubbed)
import assert from 'node:assert/strict'
import { afterEach, describe, it } from 'node:test'

import {
  API_BASE_URL,
  ApiError,
  CLIENT_ERROR_CODES,
  downloadUrl,
  generateDocument,
  listTemplates,
  resolveApiBaseUrl,
  sendChatMessage,
} from './api.js'

const realFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = realFetch
})

function jsonResponse(status, body) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

/** Replace fetch with a stub that records calls and answers with `respond(call)`. */
function stubFetch(respond) {
  const calls = []
  globalThis.fetch = async (url, init) => {
    const call = { url, init }
    calls.push(call)
    return respond(call)
  }
  return calls
}

describe('resolveApiBaseUrl', () => {
  it('defaults to the local backend when unset', () => {
    assert.equal(resolveApiBaseUrl(undefined), 'http://localhost:8000')
    assert.equal(resolveApiBaseUrl({}), 'http://localhost:8000')
    assert.equal(resolveApiBaseUrl({ VITE_API_BASE_URL: '   ' }), 'http://localhost:8000')
  })

  it('uses the env value without trailing slashes', () => {
    assert.equal(resolveApiBaseUrl({ VITE_API_BASE_URL: 'https://api.example.com/' }), 'https://api.example.com')
    assert.equal(resolveApiBaseUrl({ VITE_API_BASE_URL: ' https://x.com/backend// ' }), 'https://x.com/backend')
  })

  it('module constant falls back outside Vite', () => {
    assert.equal(API_BASE_URL, 'http://localhost:8000')
  })
})

describe('downloadUrl', () => {
  const rel = '/api/v1/documents/download/1b2c.pdf'

  it('joins a relative path to the base URL', () => {
    assert.equal(downloadUrl(rel), `http://localhost:8000${rel}`)
    assert.equal(downloadUrl(rel, 'https://api.example.com/'), `https://api.example.com${rel}`)
  })

  it('keeps a path inside the base URL', () => {
    assert.equal(downloadUrl(rel, 'https://x.com/backend'), `https://x.com/backend${rel}`)
  })

  it('returns absolute http(s) URLs unchanged', () => {
    assert.equal(downloadUrl('https://cdn.example.com/a.pdf'), 'https://cdn.example.com/a.pdf')
    assert.equal(downloadUrl('HTTP://host/a.docx'), 'HTTP://host/a.docx')
  })

  it('rejects protocol-relative, relative-without-slash and empty input', () => {
    for (const bad of ['//evil.example/a.pdf', 'api/v1/x.pdf', '', '   ', undefined, null, 42]) {
      assert.throws(() => downloadUrl(bad), TypeError, String(bad))
    }
  })
})

describe('requests', () => {
  it('sendChatMessage posts the contract body as JSON without credentials', async () => {
    const body = {
      intent: 'question_answering',
      answer: 'TBK m. 344 ...',
      citations: [{ article_id: 'TBK-344', law_name: 'TBK', text_snippet: '...' }],
      extracted_params: {},
      missing_fields: [],
      suggested_template_id: null,
      disclaimer: 'Bu sistem bir AI asistanıdır; avukatlık hizmeti vermez.',
    }
    const calls = stubFetch(() => jsonResponse(200, body))

    const result = await sendChatMessage('s-1', 'Kira artışı ne kadar olabilir?')

    assert.deepEqual(result, body) // returned untouched
    assert.equal(calls.length, 1)
    const { url, init } = calls[0]
    assert.equal(url, 'http://localhost:8000/api/v1/chat/message')
    assert.equal(init.method, 'POST')
    assert.equal(init.credentials, 'omit')
    assert.equal(init.headers['Content-Type'], 'application/json')
    assert.equal(init.headers.Accept, 'application/json')
    assert.deepEqual(JSON.parse(init.body), { session_id: 's-1', message: 'Kira artışı ne kadar olabilir?' })
  })

  it('listTemplates sends a GET without body or Content-Type', async () => {
    const calls = stubFetch(() => jsonResponse(200, { templates: [] }))
    assert.deepEqual(await listTemplates(), { templates: [] })
    const { url, init } = calls[0]
    assert.equal(url, 'http://localhost:8000/api/v1/documents/templates')
    assert.equal(init.method, 'GET')
    assert.equal(init.body, undefined)
    assert.equal(init.headers['Content-Type'], undefined)
    assert.equal(init.credentials, 'omit')
  })

  it('generateDocument maps arguments to template_id / case_params / pii', async () => {
    const response = {
      file_id: 'abc',
      docx_url: '/api/v1/documents/download/abc.docx',
      pdf_url: '/api/v1/documents/download/abc.pdf',
      expires_at: '2026-11-01T12:00:00Z',
      disclaimer: 'Bu sistem bir AI asistanıdır; avukatlık hizmeti vermez.',
    }
    const calls = stubFetch(() => jsonResponse(200, response))
    const result = await generateDocument('kira_artis_itiraz_ihtarname', { tufe_oran: 62.51 }, { kiraci_ad_soyad: 'Örnek Kişi' })

    assert.deepEqual(result, response)
    assert.equal(calls[0].url, 'http://localhost:8000/api/v1/documents/generate')
    assert.deepEqual(JSON.parse(calls[0].init.body), {
      template_id: 'kira_artis_itiraz_ihtarname',
      case_params: { tufe_oran: 62.51 },
      pii: { kiraci_ad_soyad: 'Örnek Kişi' },
    })
  })

  it('passes the caller signal through', async () => {
    const calls = stubFetch(() => jsonResponse(200, { templates: [] }))
    const controller = new AbortController()
    await listTemplates({ signal: controller.signal })
    assert.equal(calls[0].init.signal, controller.signal)
  })
})

describe('errors', () => {
  it('backend { error_code, message } becomes ApiError with that code', async () => {
    stubFetch(() => jsonResponse(422, { error_code: 'TEMPLATE_FIELDS_INVALID', message: 'Eksik: kiraci_adres' }))
    await assert.rejects(generateDocument('t', {}, {}), (error) => {
      assert.ok(error instanceof ApiError)
      assert.ok(error instanceof Error)
      assert.equal(error.status, 422)
      assert.equal(error.errorCode, 'TEMPLATE_FIELDS_INVALID')
      assert.equal(error.message, 'Eksik: kiraci_adres')
      return true
    })
  })

  it('400 / 404 / 500 keep their backend codes', async () => {
    for (const [status, code] of [
      [400, 'EMPTY_MESSAGE'],
      [404, 'TEMPLATE_NOT_FOUND'],
      [500, 'INTERNAL_SERVER_ERROR'],
    ]) {
      stubFetch(() => jsonResponse(status, { error_code: code, message: 'x' }))
      await assert.rejects(sendChatMessage('s', 'm'), { name: 'ApiError', status, errorCode: code })
    }
  })

  it('non-JSON error body (e.g. proxy HTML 502) becomes HTTP_ERROR', async () => {
    stubFetch(() => new Response('<html>Bad Gateway</html>', { status: 502, headers: { 'Content-Type': 'text/html' } }))
    await assert.rejects(listTemplates(), { status: 502, errorCode: CLIENT_ERROR_CODES.HTTP_ERROR })
  })

  it('JSON error body without error_code becomes HTTP_ERROR', async () => {
    stubFetch(() => jsonResponse(503, { detail: 'down' }))
    await assert.rejects(listTemplates(), { status: 503, errorCode: CLIENT_ERROR_CODES.HTTP_ERROR })
  })

  it('rejected fetch (backend down / CORS) becomes NETWORK_ERROR with status 0', async () => {
    globalThis.fetch = async () => {
      throw new TypeError('Failed to fetch')
    }
    await assert.rejects(listTemplates(), { status: 0, errorCode: CLIENT_ERROR_CODES.NETWORK_ERROR })
  })

  it('2xx with a non-JSON body becomes INVALID_RESPONSE', async () => {
    stubFetch(() => new Response('ok', { status: 200 }))
    await assert.rejects(listTemplates(), { status: 200, errorCode: CLIENT_ERROR_CODES.INVALID_RESPONSE })
  })

  it('caller abort is rethrown as the original AbortError', async () => {
    const controller = new AbortController()
    globalThis.fetch = async (_url, init) => {
      init.signal.throwIfAborted()
      return jsonResponse(200, {})
    }
    controller.abort()
    await assert.rejects(listTemplates({ signal: controller.signal }), (error) => {
      assert.equal(error.name, 'AbortError')
      assert.ok(!(error instanceof ApiError))
      return true
    })
  })
})
