'use client'

import { useCallback, useEffect, useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const EMPTY_DATA = {
  total_days: 0,
  wake_days: 0,
  sleep_days: 0,
  sleep_rate_pct: 0,
  total_savings_inr: 0,
  savings_pct: 0,
  daily_metrics: [],
}

export function useCostTracking() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_URL}/api/cost-tracking`, { cache: 'no-store' })
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const json = await res.json()
      setData(json.data || json)
      setError(null)
    } catch (err) {
      console.error('Cost tracking fetch error:', err)
      setError(err?.message || 'Failed to load cost tracking')
      setData(EMPTY_DATA)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}
