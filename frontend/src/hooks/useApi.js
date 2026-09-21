import { useState, useCallback } from 'react';

/**
 * Centralized API fetch hook with loading/error state management.
 *
 * Usage:
 *   const { data, loading, error, execute } = useApi();
 *   await execute('/api/firmware');
 *   await execute('/api/run', { method: 'POST', body: JSON.stringify(payload) });
 */
export function useApi() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (endpoint, options = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(endpoint, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`${res.status}: ${errText}`);
      }
      const json = await res.json();
      setData(json);
      return json;
    } catch (err) {
      setError(err.message || 'Request failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}

/**
 * Simple fetch helper that doesn't manage state — for fire-and-forget or
 * one-off calls within effects.
 */
export async function fetchApi(endpoint, options = {}) {
  const res = await fetch(endpoint, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`${res.status}: ${errText}`);
  }
  return res.json();
}
