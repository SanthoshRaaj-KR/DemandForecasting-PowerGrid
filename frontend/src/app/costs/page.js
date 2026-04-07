'use client'

import { CostSavingsChart, CostSummaryCard } from '@/components/charts/CostSavingsChart'
import { Card } from '@/components/ui/Primitives'
import { useCostTracking } from '@/hooks/useCostTracking'

export default function CostsPage() {
  const { data, loading, error } = useCostTracking()

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-6 pt-20">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-800 rounded w-1/3" />
            <div className="h-64 bg-gray-800 rounded" />
          </div>
        </div>
      </div>
    )
  }

  const avgBaselinePerDay =
    data?.total_baseline_cost_inr && data?.total_days
      ? (Number(data.total_baseline_cost_inr) / Number(data.total_days)).toFixed(2)
      : '20.00'

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 pt-20">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Cost Savings Dashboard</h1>
          <p className="text-gray-400">
            Track how much the sleep/wake system saves by skipping full orchestration on normal days.
          </p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400">
            Error loading cost data: {error}
          </div>
        )}

        <CostSummaryCard summary={data} />

        <Card>
          <h2 className="text-lg font-semibold mb-4">Daily Savings</h2>
          <p className="text-sm text-gray-400 mb-4">
            Green bars are SLEEP days (savings achieved). Red bars are WAKE days (LLM agents ran).
          </p>
          <CostSavingsChart dailyMetrics={data?.daily_metrics || []} />
        </Card>

        <Card className="bg-gray-800/30">
          <h3 className="font-semibold mb-2">How Savings Work</h3>
          <div className="text-sm text-gray-400 space-y-2">
            <p>
              <span className="text-green-400 font-medium">SLEEP Days:</span> When anomaly Delta is below threshold
              (50 MW), the system uses baseline and avoids heavy orchestration. Estimated savings: about INR{' '}
              {avgBaselinePerDay}/day.
            </p>
            <p>
              <span className="text-red-400 font-medium">WAKE Days:</span> On major anomaly days (storm, outage, demand
              spike), full multi-agent orchestration is activated.
            </p>
            <p>
              <span className="text-purple-400 font-medium">Target:</span> About 70% sleep rate under normal conditions.
            </p>
          </div>
        </Card>

        {Number(data?.total_savings_inr || 0) > 0 && (
          <div className="text-center py-6">
            <p className="text-sm text-gray-500 uppercase">Total Savings This Period</p>
            <p className="text-4xl font-bold text-green-400">
              INR {Number(data.total_savings_inr).toLocaleString('en-IN')}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
