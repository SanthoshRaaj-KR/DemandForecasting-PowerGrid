'use client'
import { ArrowRight, CheckCircle, Zap, Leaf } from 'lucide-react'
import { REGIONS } from '@/lib/data'
import { Badge } from '@/components/ui/Primitives'

const regionColor = (id) => REGIONS.find(r => r.id === id)?.color || '#94a3b8'

export function DispatchTable({ results }) {
  if (!results || results.length === 0) {
    return (
      <div className="text-center text-grid-textDim text-sm py-8">
        Run simulation to see dispatch results
      </div>
    )
  }

  const totalValue = results.reduce((s, r) => s + r.total_value, 0)
  const totalSavings = results.reduce((s, r) => s + r.carbon_savings, 0)

  return (
    <div>
      {/* Summary row */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { label: 'Total Trades', value: results.length, unit: '', color: 'text-cyan-400' },
          { label: 'Total Value', value: `₹${(totalValue / 1000).toFixed(1)}k`, unit: '', color: 'text-green-400' },
          { label: 'Carbon Savings', value: `₹${(totalSavings / 100000).toFixed(2)}L`, unit: '', color: 'text-emerald-400' },
        ].map(s => (
          <div key={s.label} className="p-3 rounded-lg bg-white/3 border border-grid-border/50 text-center">
            <div className={`text-xl font-bold ${s.color}`}
              style={{ fontFamily: 'Rajdhani, sans-serif' }}>
              {s.value}
            </div>
            <div className="text-[10px] text-grid-textDim uppercase tracking-wider mt-0.5"
              style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
              {s.label}
            </div>
          </div>
        ))}
      </div>

      {/* Trades */}
      <div className="flex flex-col gap-3">
        {results.map((trade, i) => (
          <div
            key={trade.id}
            className="p-4 rounded-xl border border-grid-border/60 bg-white/2"
            style={{
              borderLeft: `3px solid ${trade.type === 'SYNDICATE' ? '#ef4444' : '#00d4ff'}`,
              animation: `count-up 0.3s ease-out ${i * 0.1}s both`,
            }}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Badge variant={trade.type === 'SYNDICATE' ? 'red' : 'cyan'}>
                  {trade.type}
                </Badge>
                <span className="text-[10px] text-grid-textDim"
                  style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                  {trade.id}
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-green-400 text-xs">
                <CheckCircle className="w-3 h-3" />
                <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{trade.status}</span>
              </div>
            </div>

            {/* Flow: Seller → Path → Buyer */}
            <div className="flex items-center gap-2 mb-3">
              <div className="flex items-center gap-1.5">
                <div
                  className="px-2 py-1 rounded text-xs font-bold"
                  style={{
                    background: `${regionColor(trade.seller)}15`,
                    color: regionColor(trade.seller),
                    fontFamily: 'Rajdhani, sans-serif',
                    letterSpacing: '0.1em',
                  }}
                >
                  {trade.seller}
                </div>
              </div>
              {/* Path arrows */}
              {trade.path.slice(1, -1).map((node, j) => (
                <div key={j} className="flex items-center gap-1">
                  <ArrowRight className="w-3 h-3 text-grid-textDim" />
                  <div
                    className="px-1.5 py-0.5 rounded text-[10px]"
                    style={{
                      background: `${regionColor(node)}10`,
                      color: regionColor(node),
                      fontFamily: 'IBM Plex Mono, monospace',
                    }}
                  >
                    {node}
                  </div>
                </div>
              ))}
              <ArrowRight className="w-3 h-3 text-grid-textDim" />
              <div
                className="px-2 py-1 rounded text-xs font-bold"
                style={{
                  background: `${regionColor(trade.buyer)}15`,
                  color: regionColor(trade.buyer),
                  fontFamily: 'Rajdhani, sans-serif',
                  letterSpacing: '0.1em',
                }}
              >
                {trade.buyer}
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-4 gap-2 text-center">
              {[
                { label: 'Quantity', value: `${trade.quantity_mw} MW`, icon: <Zap className="w-3 h-3" />, color: 'text-cyan-400' },
                { label: 'Price', value: `₹${trade.price_kwh}/kWh`, icon: null, color: 'text-white' },
                { label: 'Value', value: `₹${(trade.total_value / 1000).toFixed(1)}k`, icon: null, color: 'text-green-400' },
                { label: 'Carbon Tax', value: `₹${(trade.carbon_tax / 1000).toFixed(1)}k`, icon: <Leaf className="w-3 h-3" />, color: 'text-emerald-400' },
              ].map(stat => (
                <div key={stat.label} className="p-2 rounded bg-white/3">
                  <div className={`text-sm font-bold flex items-center justify-center gap-1 ${stat.color}`}
                    style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                    {stat.icon}
                    {stat.value}
                  </div>
                  <div className="text-[9px] text-grid-textDim mt-0.5 uppercase tracking-wider"
                    style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
