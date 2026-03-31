'use client'
import { useMemo, useState } from 'react'
import { AlertTriangle, Route, Factory, CalendarClock, Zap, Thermometer, Battery, ArrowDownRight, ShieldCheck, Brain } from 'lucide-react'
import { Card, SectionLabel, Badge, RiskFlag } from '@/components/ui/Primitives'
import { REGION_BY_ID } from '@/lib/gridMeta'

const SEVERITY_VARIANT = { HIGH: 'red', MEDIUM: 'amber', MED: 'amber', LOW: 'cyan', INFO: 'info', UNKNOWN: 'default' }

function normalizeRiskLevel(level) {
  return String(level || 'UNKNOWN').toUpperCase()
}

function normalizeEvents(events = []) {
  return events.map((event, index) => {
    if (typeof event === 'string') {
      return { label: event, severity: 'INFO' }
    }

    return {
      label: event.event_name || event.label || event.title || event.event || `Event ${index + 1}`,
      severity: normalizeRiskLevel(event.severity || event.confidence || event.risk || 'INFO'),
    }
  })
}

function clean(text = '') {
  if (!text) return ''
  return String(text).replace(/\s+/g, ' ').trim()
}

function compact(items = []) {
  return items.map(clean).filter(Boolean)
}

function short(text = '', max = 96) {
  const t = clean(text)
  if (!t) return ''
  return t.length > max ? `${t.slice(0, max).trim()}...` : t
}

function PreviewRow({ icon: Icon, label, items }) {
  const shown = items.slice(0, 2)
  return (
    <div className="rounded-lg border border-grid-border/50 bg-white/5 p-2.5">
      <div className="flex items-center gap-1.5 mb-1.5">
        <Icon className="w-3.5 h-3.5 text-cyan-300" />
        <div className="text-[10px] uppercase tracking-[0.1em] text-cyan-300" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{label}</div>
      </div>
      {shown.length ? (
        <div className="space-y-1">
          {shown.map((item, i) => (
            <div key={`${label}-${i}`} className="text-xs text-grid-textDim leading-relaxed">{item}</div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-grid-textDim">No data</div>
      )}
    </div>
  )
}

function FullList({ title, items, showAll, setShowAll }) {
  const visible = showAll ? items : items.slice(0, 2)
  return (
    <div className="rounded-lg border border-grid-border/50 bg-white/5 p-2.5">
      <div className="text-[10px] uppercase tracking-[0.1em] text-cyan-300 mb-1.5" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{title}</div>
      {visible.length ? (
        <div className="space-y-1">
          {visible.map((item, idx) => (
            <div key={`${title}-${idx}`} className="text-xs text-grid-textDim leading-relaxed">{item}</div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-grid-textDim">No data</div>
      )}
      {items.length > 2 && (
        <button
          type="button"
          onClick={() => setShowAll(!showAll)}
          className="mt-2 text-[10px] uppercase tracking-[0.1em] text-cyan-300 hover:text-cyan-200"
          style={{ fontFamily: 'IBM Plex Mono, monospace' }}
        >
          {showAll ? 'Show top 2' : `Show all (${items.length})`}
        </button>
      )}
    </div>
  )
}

function TemperatureTrend({ points = [] }) {
  if (!points.length) {
    return <div className="text-xs text-grid-textDim">No temperature forecast data.</div>
  }

  const maxVal = Math.max(...points.map(p => Number(p.max)))
  const minVal = Math.min(...points.map(p => Number(p.min)))
  const range = Math.max(1, maxVal - minVal)

  return (
    <div className="space-y-2">
      {points.slice(0, 7).map((p, idx) => {
        const maxWidth = `${((Number(p.max) - minVal) / range) * 100}%`
        const minWidth = `${((Number(p.min) - minVal) / range) * 100}%`
        return (
          <div key={`${p.date}-${idx}`}>
            <div className="flex items-center justify-between text-[10px] text-grid-textDim mb-1" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
              <span>{p.label}</span>
              <span>{Number(p.min).toFixed(1)}C - {Number(p.max).toFixed(1)}C</span>
            </div>
            <div className="h-1.5 rounded bg-[#0f1a27] border border-cyan-500/20 overflow-hidden">
              <div className="h-full bg-cyan-500/35 relative" style={{ width: maxWidth }}>
                <div className="absolute top-0 bottom-0 bg-amber-400/60" style={{ width: minWidth }} />
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function RegionCard({ regionId, data }) {
  const region = REGION_BY_ID[regionId]
  if (!region || !data) return null

  const multipliers = data?.grid_multipliers || {}
  const intel = data?.city_intelligence || {}
  const weather = data?.weather || {}
  const events = normalizeEvents(data?.detected_events || [])

  const demandRiskLevel = normalizeRiskLevel(multipliers.demand_spike_risk)
  const supplyRiskLevel = normalizeRiskLevel(multipliers.supply_shortfall_risk)
  const demandRiskActive = demandRiskLevel === 'HIGH' || demandRiskLevel === 'MEDIUM'
  const supplyRiskActive = supplyRiskLevel === 'HIGH' || supplyRiskLevel === 'MEDIUM'
  const hoardActive = Boolean(multipliers.pre_event_hoard)
  const hasRisk = demandRiskActive || supplyRiskActive || hoardActive

  const demandDrivers = compact(intel.demand_drivers || [])
  const seasonalFactors = compact(intel.seasonal_demand_factors || [])
  const vulnerabilities = compact(intel.key_vulnerabilities || [])
  const fuelRoutes = compact(intel.fuel_supply_routes || [])
  const fuelSources = compact(intel.primary_fuel_sources || [])

  const hoardDay = multipliers.hoard_day || 0
  const isHoarding = hoardActive || hoardDay > 0

  const [pinDetails, setPinDetails] = useState(false)
  const [allDrivers, setAllDrivers] = useState(false)
  const [allSeasonal, setAllSeasonal] = useState(false)
  const [allVuln, setAllVuln] = useState(false)
  const [allRoutes, setAllRoutes] = useState(false)
  const [allFuel, setAllFuel] = useState(false)

  const topEvents = useMemo(() => events.slice(0, 2), [events])
  const delta = Number(multipliers.seven_day_demand_forecast_mw_delta || 0)
  const tempPoints = useMemo(() => {
    const rows = Array.isArray(weather?.forecast_days) ? weather.forecast_days : []
    return rows
      .map((r, i) => ({
        date: String(r?.date || i),
        label: r?.date ? String(r.date).slice(5) : `D${i + 1}`,
        max: Number(r?.max_c ?? weather?.current_temp_c ?? 0),
        min: Number(r?.min_c ?? weather?.current_temp_c ?? 0),
      }))
      .filter(r => Number.isFinite(r.max) && Number.isFinite(r.min))
  }, [weather])

  return (
    <>
      {/* SIMPLIFIED PREVIEW CARD */}
      <Card className="relative overflow-visible hover:shadow-xl transition-all duration-300 cursor-pointer" onClick={() => setPinDetails(true)}>
        <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-xl" style={{ background: `linear-gradient(90deg, ${region.color}, transparent)` }} />

        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="text-2xl font-bold tracking-[0.08em]" style={{ fontFamily: 'Rajdhani, sans-serif', color: region.color }}>{regionId}</div>
            <div className="text-xs text-grid-textDim mt-0.5">{region.fullName}</div>
          </div>
          <Badge variant={hasRisk ? 'red' : 'green'}>
            {hasRisk ? 'ALERT' : 'STABLE'}
          </Badge>
        </div>

        {/* Key Metrics Only */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="p-3 rounded-lg bg-white/5 border border-grid-border/30">
            <div className="text-[9px] text-grid-textDim uppercase tracking-wider mb-1">Demand Trend</div>
            <div className={`text-lg font-bold ${delta >= 0 ? 'text-red-400' : 'text-green-400'}`}>
              {delta >= 0 ? '+' : ''}{delta.toFixed(0)} MW
            </div>
          </div>
          <div className="p-3 rounded-lg bg-white/5 border border-grid-border/30">
            <div className="text-[9px] text-grid-textDim uppercase tracking-wider mb-1">Risk Level</div>
            <div className={`text-lg font-bold ${hasRisk ? 'text-amber-400' : 'text-cyan-400'}`}>
              {demandRiskLevel}
            </div>
          </div>
        </div>

        {/* Key Driver Summary */}
        <div className="p-3 rounded-lg bg-cyan-500/5 border border-cyan-500/20 mb-4">
          <div className="text-[9px] text-cyan-300 uppercase tracking-wider mb-1.5">PRIMARY DRIVER</div>
          <div className="text-sm text-white font-medium leading-relaxed">
            {short(multipliers.key_driver || 'No key driver identified', 120)}
          </div>
        </div>

        {/* Hoarding Warning if active */}
        {isHoarding && (
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 mb-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span className="text-sm font-bold text-amber-400">Pre-Event Hoarding Active (Day {hoardDay})</span>
            </div>
          </div>
        )}

        {/* Detected Events */}
        {topEvents.length > 0 && (
          <div className="space-y-2 mb-4">
            <div className="text-[9px] text-grid-textDim uppercase tracking-wider">DETECTED EVENTS</div>
            {topEvents.map((ev, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded bg-white/5 border border-grid-border/20">
                <span className="text-xs text-white">{short(ev.label, 50)}</span>
                <Badge variant={SEVERITY_VARIANT[ev.severity] || 'default'}>{ev.severity}</Badge>
              </div>
            ))}
            {events.length > 2 && (
              <div className="text-[10px] text-cyan-400 text-center">+{events.length - 2} more events</div>
            )}
          </div>
        )}

        {/* Click to View Details */}
        <div className="pt-4 border-t border-grid-border/20">
          <div className="text-center text-xs text-cyan-400 flex items-center justify-center gap-2">
            <Route className="w-3.5 h-3.5" />
            Click for Full Intelligence Report
          </div>
        </div>
      </Card>

      {/* DETAILED VIEW MODAL - Same as before */}
      {pinDetails && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
           <div className="absolute inset-0 bg-black/90 backdrop-blur-md animate-fade-in" onClick={() => setPinDetails(false)} />
           
           <div className="relative w-full max-w-4xl max-h-[90vh] bg-[#07101a] border border-cyan-400/40 rounded-2xl shadow-[0_0_100px_rgba(0,212,255,0.2)] overflow-hidden flex flex-col scale-1 animation-bloom">
              <div className="p-6 border-b border-grid-border/30 flex items-start justify-between bg-white/2">
                 <div>
                    <h2 className="text-3xl font-bold tracking-[0.1em]" style={{ color: region.color, fontFamily: 'Rajdhani, sans-serif' }}>{regionId} Strategic Audit</h2>
                    <p className="text-grid-textDim text-sm font-mono mt-1 uppercase tracking-tighter">Regional Intelligence Analysis Packet // 7-Day Window</p>
                 </div>
                 <button onClick={() => setPinDetails(false)} className="p-2 text-grid-textDim hover:text-white transition-colors">
                    <span className="text-sm font-mono">[ CLOSE ]</span>
                 </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                 <div className="p-5 rounded-xl border border-cyan-500/20 bg-cyan-500/5">
                    <div className="flex items-center gap-2 mb-3">
                       <Brain className="w-5 h-5 text-cyan-400" />
                       <SectionLabel>AI Narrative</SectionLabel>
                    </div>
                    <p className="text-sm text-grid-text leading-relaxed font-medium italic">
                       "{multipliers.reasoning || data?.impact_narrative || 'No detailed analysis available.'}"
                    </p>
                 </div>

                 <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-4">
                       <FullList title="Demand Drivers" items={demandDrivers} showAll={allDrivers} setShowAll={setAllDrivers} />
                       <FullList title="Seasonal Factors" items={seasonalFactors} showAll={allSeasonal} setShowAll={setAllSeasonal} />
                       <div className="rounded-lg border border-cyan-500/25 bg-[#0a1826] p-4">
                          <div className="flex items-center justify-between mb-4">
                             <span className="text-[10px] uppercase tracking-[0.15em] text-cyan-300 font-bold">Temperature Forecast</span>
                             <Thermometer className="w-4 h-4 text-cyan-300" />
                          </div>
                          <TemperatureTrend points={tempPoints} />
                       </div>
                    </div>
                    <div className="space-y-4">
                       <FullList title="Key Vulnerabilities" items={vulnerabilities} showAll={allVuln} setShowAll={setAllVuln} />
                       <FullList title="Fuel Routes" items={fuelRoutes} showAll={allRoutes} setShowAll={setAllRoutes} />
                       <FullList title="Fuel Sources" items={fuelSources} showAll={allFuel} setShowAll={setAllFuel} />
                       <div className="rounded-lg border border-grid-border/50 bg-white/5 p-4">
                         <div className="text-[10px] uppercase tracking-[0.1em] text-cyan-300 mb-3">All Events ({events.length})</div>
                         {events.length ? events.map((ev, idx) => (
                           <div key={idx} className="flex items-center justify-between gap-3 py-2 border-b border-grid-border/10 last:border-0">
                             <div className="text-xs text-grid-text font-medium">{ev.label}</div>
                             <Badge variant={SEVERITY_VARIANT[ev.severity] || 'default'}>{ev.severity}</Badge>
                           </div>
                         )) : <div className="text-xs text-grid-textDim">No events</div>}
                       </div>
                    </div>
                 </div>
              </div>

              <div className="p-4 bg-black/60 border-t border-grid-border/30 flex justify-between items-center px-8">
                 <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                       <div className="w-2 h-2 rounded-full bg-cyan-400" />
                       <span className="text-[10px] text-cyan-400/80 font-mono">LIVE DATA</span>
                    </div>
                 </div>
                 <span className="text-[10px] text-grid-textDim font-mono">VERIFIED_PACKET</span>
              </div>
           </div>
        </div>
      )}
    </>
  )
}

