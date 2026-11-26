// Run: npm test   (node --test, no dependencies)
import assert from 'node:assert/strict'
import { describe, it } from 'node:test'

import { ApiError, LLM_RATE_LIMITED } from './api.js'
import { AUTO_RETRY_MAX_WAIT_SECONDS, autoRetryDelay, countdown } from './retry.js'

const rateLimited = (seconds) => new ApiError(503, LLM_RATE_LIMITED, 'Şu anda çok yoğunuz.', seconds)

describe('autoRetryDelay', () => {
  it('retries a rate limit once, rounding the wait up', () => {
    assert.equal(autoRetryDelay(rateLimited(12.2), 0), 13)
    assert.equal(autoRetryDelay(rateLimited(AUTO_RETRY_MAX_WAIT_SECONDS), 0), AUTO_RETRY_MAX_WAIT_SECONDS)
  })
  it('does not retry a second time', () => {
    assert.equal(autoRetryDelay(rateLimited(5), 1), null)
  })
  it('does not retry waits longer than the limit or without a wait', () => {
    assert.equal(autoRetryDelay(rateLimited(AUTO_RETRY_MAX_WAIT_SECONDS + 1), 0), null)
    assert.equal(autoRetryDelay(rateLimited(null), 0), null)
  })
  it('does not retry other errors', () => {
    assert.equal(autoRetryDelay(new ApiError(503, 'LLM_UNAVAILABLE', 'x'), 0), null)
    assert.equal(autoRetryDelay(new ApiError(400, 'PROMPT_INJECTION_DETECTED', 'x'), 0), null)
    assert.equal(autoRetryDelay(new Error('x'), 0), null)
  })
})

describe('countdown', () => {
  it('ticks every second down to 1, then resolves', async () => {
    const ticks = []
    await countdown(3, { tickMs: 1, onTick: (n) => ticks.push(n) })
    assert.deepEqual(ticks, [3, 2, 1])
  })
  it('rejects with AbortError when aborted', async () => {
    const controller = new AbortController()
    const waiting = countdown(5, { signal: controller.signal, tickMs: 50 })
    controller.abort()
    await assert.rejects(waiting, { name: 'AbortError' })
  })
  it('rejects at once when already aborted', async () => {
    const controller = new AbortController()
    controller.abort()
    await assert.rejects(countdown(1, { signal: controller.signal }), { name: 'AbortError' })
  })
})
