'use client'
import { Thermometer, Droplets, Zap, TrendingUp, TrendingDown, AlertTriangle, Shield } from 'lucide-react'
import { Card, SectionLabel, Badge, RiskFlag, Gauge, Divider } from '@/components/ui/Primitives'
import { REGIONS } from '@/lib/data'

const SEVERITY_VARIANT = { HIGH: 'red', MED: 'amber', LOW: 'cyan', INFO: 'info' }
const EVENT_ICON = {
  HEATWAVE: '🌡',
  INDUSTRIAL: '🏭',
  EVENT: '🎪',
  FESTIVAL: '🎆',
  MARKET: '📊',
  SUPPLY: '⚡',
  RAIN: '🌧',
  SOLAR: '☀️',
  EXPORT: '📤',
}

export function RegionCard({ regionId, data }) {
  if (!data) return null
  const region = REGIONS.find(r => r.id === regionId)
  const { multipliers, risk_flags, detected_events, weather } = data

  const hasAnyRisk = Object.values(risk_flags).some(Boolean)

  return (
    <Card className={`relative ${hasAnyRisk ? 'glow-amber' : ''}`}>
      {/* Color accent bar */}
      <div
        className="absolute top-0 left-0 right-0 h-0.5 rounded-t-xl"
        style={{ background: `linear-gradient(90deg, ${region.color}, transparent)` }}
      />

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div
            className="text-xl font-bold tracking-wider"
            style={{ fontFamily: 'Rajdhani, sans-serif', color: region.color }}
          >
            {regionId}
          </div>
          <div className="text-xs text-grid-textDim">{region.fullName}</div>
        </div>
        <div className="text-right">
          <div className="text-2xl">{weather.forecast[0]}</div>
          <div className="text-xs text-grid-textDim">{weather.condition}</div>
        </div>
      </div>

      {/* Weather row */}
      <div className="flex items-center gap-4 mb-4 p-2.5 rounded-lg bg-white/3">
        <div className="flex items-center gap-1.5 text-sm">
          <Thermometer className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-white font-medium">{weather.temp}°C</span>
        </div>
        <div className="flex items-center gap-1.5 text-sm">
          <Droplets className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-grid-textDim">{weather.humidity}%</span>
        </div>
        <div className="flex gap-1 ml-auto">
          {weather.forecast.map((icon, i) => (
            <span key={i} className="text-sm opacity-70">{icon}</span>
          ))}
        </div>
      </div>

      <Divider className="mb-4" />

      {/* Multiplier Gauges */}
      <SectionLabel>Intelligence Multipliers</SectionLabel>
      <div className="flex justify-around py-2 mb-4">
        <Gauge
          value={multipliers.edm}
          label="EDM"
          color={region.color}
        />
        <div className="w-px bg-grid-border/50 self-stretch" />
        <Gauge
          value={multipliers.gcm}
          label="GCM"
          color={region.color}
        />
      </div>

      <Divider className="mb-3" />

      {/* Risk Flags */}
      <SectionLabel>Risk Assessment</SectionLabel>
      <div className="flex flex-col gap-1.5 mb-4">
        <RiskFlag label="Demand Spike Risk" active={risk_flags.demand_spike_risk} />
        <RiskFlag label="Pre-Event Hoarding" active={risk_flags.pre_event_hoard} />
        <RiskFlag label="Supply Crunch" active={risk_flags.supply_crunch} />
      </div>

      <Divider className="mb-3" />

      {/* Detected Events */}
      <SectionLabel>Detected Events</SectionLabel>
      <div className="flex flex-col gap-2">
        {detected_events.map((event, i) => (
          <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-white/3">
            <span className="text-sm mt-0.5">{EVENT_ICON[event.type] || '📌'}</span>
            <div className="flex-1 min-w-0">
              <div className="text-xs text-white font-medium truncate">{event.label}</div>
              <div className="text-[10px] text-grid-textDim" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                {event.timestamp}
              </div>
            </div>
            <Badge variant={SEVERITY_VARIANT[event.severity] || 'default'}>
              {event.severity}
            </Badge>
          </div>
        ))}
      </div>
    </Card>
  )
}
