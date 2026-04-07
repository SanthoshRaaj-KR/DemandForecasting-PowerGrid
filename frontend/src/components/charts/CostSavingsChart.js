'use client'

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const toNumber = (v) => {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null

  const data = payload[0].payload
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
      <p className="font-medium text-white">{data.date}</p>
      <p className={`text-sm ${data.llm_agents_enabled ? 'text-red-400' : 'text-green-400'}`}>
        {data.llm_agents_enabled ? 'WAKE (LLM Active)' : 'SLEEP (Baseline)'}
      </p>
      <div className="mt-2 text-xs text-gray-400 space-y-1">
        <p>Baseline Cost: INR {toNumber(data.baseline_cost_inr).toFixed(2)}</p>
        <p>Actual Cost: INR {toNumber(data.actual_cost_inr).toFixed(2)}</p>
        <p className="font-medium text-green-400">
          Savings: INR {toNumber(data.savings_inr).toFixed(2)} ({toNumber(data.savings_pct).toFixed(1)}%)
        </p>
      </div>
    </div>
  )
}

export function CostSavingsChart({ dailyMetrics = [] }) {
  if (!dailyMetrics.length) {
    return <div className="h-64 flex items-center justify-center text-gray-500">No cost data available</div>
  }

  const chartData = dailyMetrics.map((m, idx) => ({
    ...m,
    day: idx + 1,
    displaySavings: toNumber(m.savings_inr),
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <XAxis
          dataKey="day"
          tick={{ fill: '#9CA3AF', fontSize: 11 }}
          axisLine={{ stroke: '#374151' }}
          label={{ value: 'Day', position: 'bottom', fill: '#9CA3AF', fontSize: 12 }}
        />
        <YAxis
          tick={{ fill: '#9CA3AF', fontSize: 11 }}
          axisLine={{ stroke: '#374151' }}
          label={{ value: 'Savings (INR)', angle: -90, position: 'insideLeft', fill: '#9CA3AF', fontSize: 12 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="displaySavings" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, idx) => (
            <Cell key={`cell-${idx}`} fill={entry.llm_agents_enabled ? '#EF4444' : '#22C55E'} fillOpacity={0.8} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function CostSummaryCard({ summary }) {
  if (!summary) return null

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-gray-800/50 rounded-lg p-4 text-center">
        <p className="text-2xl font-bold text-white">{toNumber(summary.total_days)}</p>
        <p className="text-sm text-gray-400">Total Days</p>
      </div>
      <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
        <p className="text-2xl font-bold text-green-400">{toNumber(summary.sleep_days)}</p>
        <p className="text-sm text-green-400/70">Sleep Days</p>
      </div>
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-center">
        <p className="text-2xl font-bold text-red-400">{toNumber(summary.wake_days)}</p>
        <p className="text-sm text-red-400/70">Wake Days</p>
      </div>
      <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4 text-center">
        <p className="text-2xl font-bold text-purple-400">{toNumber(summary.savings_pct).toFixed(1)}%</p>
        <p className="text-sm text-purple-400/70">Cost Savings</p>
      </div>
    </div>
  )
}
