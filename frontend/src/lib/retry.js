/**
 * Automatic retry after a Groq rate limit (backend 503 LLM_RATE_LIMITED + retry_after_seconds).
 * Pure helpers, no React: the chat screen waits once with a visible countdown, then resends.
 */
import { ApiError, LLM_RATE_LIMITED } from './api.js'

/** Longest wait the chat screen takes on its own; a longer one is shown as an error instead. */
export const AUTO_RETRY_MAX_WAIT_SECONDS = 30

/**
 * @param {unknown} error
 * @param {number} retriesSoFar automatic retries already made for this message
 * @returns {number | null} seconds to wait before the retry, or null when not to retry
 */
export function autoRetryDelay(error, retriesSoFar) {
  if (!(error instanceof ApiError) || error.errorCode !== LLM_RATE_LIMITED || retriesSoFar >= 1) return null
  const seconds = error.retryAfterSeconds
  if (!Number.isFinite(seconds) || seconds <= 0 || seconds > AUTO_RETRY_MAX_WAIT_SECONDS) return null
  return Math.ceil(seconds)
}

/**
 * Wait `seconds`, calling onTick(remaining) once per second (first call with `seconds`).
 * Rejects with an AbortError when the signal aborts, like fetch does.
 * @param {number} seconds
 * @param {{ signal?: AbortSignal, onTick?: (remaining: number) => void, tickMs?: number }} [options]
 */
export function countdown(seconds, { signal, onTick, tickMs = 1000 } = {}) {
  return new Promise((resolve, reject) => {
    const abortError = () => new DOMException('Aborted', 'AbortError')
    if (signal?.aborted) {
      reject(abortError())
      return
    }
    let remaining = seconds
    let timer
    const onAbort = () => {
      clearTimeout(timer)
      reject(abortError())
    }
    signal?.addEventListener('abort', onAbort, { once: true })
    const step = () => {
      if (remaining <= 0) {
        signal?.removeEventListener('abort', onAbort)
        resolve()
        return
      }
      onTick?.(remaining)
      remaining -= 1
      timer = setTimeout(step, tickMs)
    }
    step()
  })
}
