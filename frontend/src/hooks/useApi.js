'use client'
import { useState, useEffect, useCallback } from 'react'
import { INTELLIGENCE_DATA, GRID_STATUS, DISPATCH_RESULTS, SIM_LOGS } from '@/lib/data'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generic fetch with fallback to mock data
async function apiFetch(path, mock) {
  try {
    const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
    if (!res.ok) throw new Error('API error')
    return await res.json()
  } catch {
    return mock
  }
}

export function useIntelligence() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch('/api/intelligence', INTELLIGENCE_DATA).then(d => {
      setData(d)
      setLoading(false)
    })
  }, [])

  return { data, loading }
}

export function useGridStatus() {
  const [data, setData] = useState(GRID_STATUS)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch('/api/grid-status', GRID_STATUS).then(d => {
      setData(d)
      setLoading(false)
    })
  }, [])

  return { data, loading }
}

export function useSimulation() {
  const [logs, setLogs] = useState([])
  const [results, setResults] = useState(null)
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)

  const runSimulation = useCallback(async () => {
    setLogs([])
    setResults(null)
    setRunning(true)
    setDone(false)

    // Try real SSE stream, fall back to mock
    try {
      const res = await fetch(`${API_BASE}/api/run-simulation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: 'default' }),
        signal: AbortSignal.timeout(3000),
      })
      if (!res.ok || !res.body) throw new Error()

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done: streamDone, value } = await reader.read()
        if (streamDone) break
        buffer += decoder.decode(value)
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const text = line.slice(6)
            setLogs(prev => [...prev, { text, agent: 'STREAM', delay: 0 }])
          }
        }
      }
    } catch {
      // Mock simulation with delays
      for (const log of SIM_LOGS) {
        await new Promise(r => setTimeout(r, log.delay > 0
          ? (logs.length === 0 ? log.delay : 600)
          : 100))
        setLogs(prev => [...prev, log])
      }
    }

    // Load results
    const res = await apiFetch('/api/simulation-result', DISPATCH_RESULTS)
    setResults(res)
    setRunning(false)
    setDone(true)
  }, [])

  return { logs, results, running, done, runSimulation }
}
