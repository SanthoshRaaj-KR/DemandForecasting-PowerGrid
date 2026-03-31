'use client'
import { Brain, Radar, AlertTriangle } from 'lucide-react'
import { useIntelligence } from '@/hooks/useApi'
import { RegionCard } from '@/components/agents/RegionCard'
import { Card, SectionLabel, Badge, Skeleton } from '@/components/ui/Primitives'
import { REGIONS } from '@/lib/gridMeta'

function getRegionData(data, id) {
  if (!data || typeof data !== 'object') return null
  return data[id] || null
}

function countRisks(regionData) {
  if (!regionData) return 0
  const gm = regionData.grid_multipliers || {}
  const flags = [
    ['HIGH', 'MEDIUM'].includes(String(gm.demand_spike_risk || '').toUpperCase()),
    ['HIGH', 'MEDIUM'].includes(String(gm.supply_shortfall_risk || '').toUpperCase()),
    Boolean(gm.pre_event_hoard),
  ]
  return flags.filter(Boolean).length
}

function topSummary(data) {
  if (!data) return 'Intelligence feed unavailable.'
  const rows = REGIONS.map(region => {
    const item = data[region.id]
    if (!item) return null
    const gm = item.grid_multipliers || {}
    const delta = Number(gm.seven_day_demand_forecast_mw_delta || 0)
    return {
      id: region.id,
      delta,
      driver: gm.key_driver || 'n/a',
      risks: countRisks(item),
      color: region.color,
    }
  }).filter(Boolean)

  const highest = [...rows].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)).slice(0, 2)
  if (!highest.length) return 'No intelligence summary available.'

  return highest.map(r => `${r.id}: ${r.delta >= 0 ? '+' : ''}${r.delta.toFixed(0)} MW | ${r.driver}`).join('  |  ')
}

export default function IntelligencePage() {
  const { data, loading } = useIntelligence()
  const summary = topSummary(data)

  return (
    <div className="pt-14">
      <div className="relative border-b border-grid-border/50 overflow-hidden">
        <div className="absolute inset-0 grid-dots opacity-40" />
        <div className="max-w-7xl mx-auto px-6 py-10 relative z-10">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="h-px w-6 bg-cyan-400" />
                <span className="text-[10px] uppercase tracking-[0.3em] text-cyan-400" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                  Intelligence Command Deck
                </span>
              </div>
              <h1 className="text-4xl font-bold text-white mb-1" style={{ fontFamily: 'Rajdhani, sans-serif', letterSpacing: '0.05em' }}>
                REGIONAL INTELLIGENCE
              </h1>
              <p className="text-grid-textDim text-sm max-w-2xl">
                Clean regional cards with demand drivers, seasonal demand factors, key vulnerabilities, fuel supply routes, and primary fuel sources.
              </p>
            </div>
            <Badge variant="cyan"><Brain className="w-3 h-3" />AGENTS ONLINE</Badge>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <Card className="glow-cyan">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
              <Radar className="w-4.5 h-4.5 text-cyan-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <SectionLabel>Priority Snapshot</SectionLabel>
                <Badge variant="cyan">LIVE CACHE</Badge>
              </div>
              {loading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              ) : (
                <p className="text-sm text-grid-text leading-relaxed">{summary}</p>
              )}
            </div>
          </div>
        </Card>

        {!loading && data && (
          <div className="flex flex-wrap gap-3">
            {REGIONS.map(region => {
              const count = countRisks(getRegionData(data, region.id))
              return (
                <div key={region.id} className="flex items-center gap-2 px-3 py-2 rounded-lg border" style={{
                  background: count > 0 ? 'rgba(245,158,11,0.07)' : 'rgba(16,185,129,0.07)',
                  borderColor: count > 0 ? 'rgba(245,158,11,0.25)' : 'rgba(16,185,129,0.2)',
                }}>
                  <span className="text-xs font-bold" style={{ color: region.color, fontFamily: 'Rajdhani, sans-serif', letterSpacing: '0.1em' }}>{region.id}</span>
                  {count === 0 ? (
                    <span className="text-[10px] text-green-400" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>No active risks</span>
                  ) : (
                    <span className="text-[10px] text-amber-400 flex items-center gap-1" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                      <AlertTriangle className="w-3 h-3" />
                      {count} risk{count > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {loading ? (
          <div className="grid md:grid-cols-2 gap-6 items-start">
            {[1, 2, 3, 4].map(i => (
              <Card key={i}><Skeleton className="h-[360px] w-full" /></Card>
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6 items-start">
            {REGIONS.map(region => (
              <RegionCard key={region.id} regionId={region.id} data={getRegionData(data, region.id)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
