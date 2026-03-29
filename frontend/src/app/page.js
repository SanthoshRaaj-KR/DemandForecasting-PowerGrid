'use client'
import { useState, useEffect } from 'react'
import { Activity, Cpu, GitBranch, Zap, Wind, BarChart2, CloudLightning, ChevronRight } from 'lucide-react'
import Link from 'next/link'
import { ForecastChart } from '@/components/charts/ForecastChart'
import { GridMap } from '@/components/grid/GridMap'
import { Card, SectionLabel, StatBlock, ProgressBar, Badge } from '@/components/ui/Primitives'
import { GRID_STATUS, REGIONS, FORECAST_DATA } from '@/lib/data'

const FEATURE_CARDS = [
  {
    icon: Cpu,
    color: '#00d4ff',
    title: 'Hybrid ML/AI Forecasting',
    body: 'LightGBM models trained on 5-year NLDC data, climate indices, and industrial calendars. 7-day rolling horizon with climate-adjusted confidence bands.',
  },
  {
    icon: GitBranch,
    color: '#0066ff',
    title: 'Agentic Market Clearing',
    body: 'State Agents, Routing Agent, and Fusion Agent negotiate energy trades in real-time using LLM reasoning — mimicking India\'s actual DEEP portal dynamics.',
  },
  {
    icon: CloudLightning,
    color: '#10b981',
    title: 'Climate-Aware Dispatch',
    body: 'Carbon tax optimization at ₹850/tonne. Solar surplus routing from Karnataka HVDC corridors. Pre-monsoon generation scheduling for WB thermal offsets.',
  },
]

function LiveStatRow() {
  const regions = Object.entries(GRID_STATUS)
  const totalDemand = regions.reduce((s, [, v]) => s + v.demand, 0)
  const totalSupply = regions.reduce((s, [, v]) => s + v.supply, 0)
  const netBalance = totalSupply - totalDemand

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {[
        { label: 'Total Demand', value: (totalDemand / 1000).toFixed(1), unit: 'GW', color: 'text-amber-400' },
        { label: 'Total Supply', value: (totalSupply / 1000).toFixed(1), unit: 'GW', color: 'text-green-400' },
        { label: 'Net Balance', value: (netBalance > 0 ? '+' : '') + netBalance, unit: 'MW', color: netBalance >= 0 ? 'text-cyan-400' : 'text-red-400' },
        { label: 'Active Regions', value: '4', unit: 'nodes', color: 'text-purple-400' },
      ].map(s => (
        <Card key={s.label} className="py-4">
          <StatBlock {...s} />
        </Card>
      ))}
    </div>
  )
}

function RegionStatusRow() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {REGIONS.map(region => {
        const status = GRID_STATUS[region.id]
        const isDeficit = status.deficit < 0
        const socPct = Math.round(status.battery_soc * 100)

        return (
          <Card key={region.id} className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm font-bold tracking-widest"
                  style={{ fontFamily: 'Rajdhani, sans-serif', color: region.color }}>
                  {region.id}
                </div>
                <div className="text-[10px] text-grid-textDim">{region.name}</div>
              </div>
              <Badge variant={isDeficit ? 'red' : 'green'}>
                {isDeficit ? `▼${Math.abs(status.deficit)}` : `▲${status.deficit}`} MW
              </Badge>
            </div>

            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-[10px] text-grid-textDim mb-1">
                  <span>Supply / Demand</span>
                  <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                    {status.supply} / {status.demand} MW
                  </span>
                </div>
                <ProgressBar
                  value={status.supply}
                  max={Math.max(status.supply, status.demand)}
                  color={region.color}
                />
              </div>
              <div>
                <div className="flex justify-between text-[10px] text-grid-textDim mb-1">
                  <span>Battery SoC</span>
                  <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{socPct}%</span>
                </div>
                <ProgressBar
                  value={socPct}
                  max={100}
                  color={socPct > 60 ? '#10b981' : socPct > 30 ? '#f59e0b' : '#ef4444'}
                />
              </div>
            </div>
          </Card>
        )
      })}
    </div>
  )
}

export default function HomePage() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <div className="pt-14">
      {/* ── Hero ─────────────────────────────────────────────────── */}
      <section className="relative min-h-[85vh] flex flex-col items-center justify-center overflow-hidden grid-dots">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-5"
            style={{ background: 'radial-gradient(circle, #00d4ff, transparent)', filter: 'blur(60px)' }} />
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full opacity-4"
            style={{ background: 'radial-gradient(circle, #10b981, transparent)', filter: 'blur(60px)' }} />
        </div>

        <div className="max-w-7xl mx-auto px-6 w-full">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Copy */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="h-px w-8 bg-cyan-400" />
                <span className="text-[10px] uppercase tracking-[0.3em] text-cyan-400"
                  style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                  Digital Twin Infrastructure
                </span>
              </div>

              <h1 className="mb-6 leading-none"
                style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700 }}>
                <span className="block text-5xl lg:text-7xl text-white tracking-tight">INDIA GRID</span>
                <span className="block text-4xl lg:text-6xl tracking-tight"
                  style={{ background: 'linear-gradient(90deg, #00d4ff, #0066ff)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  DIGITAL TWIN
                </span>
              </h1>

              <p className="text-grid-textDim text-base leading-relaxed mb-8 max-w-lg">
                A real-time simulation platform fusing <strong className="text-white">LightGBM demand forecasting</strong> with <strong className="text-white">multi-agent LLM negotiation</strong> to model India's national grid — Bihar, UP, West Bengal, and Karnataka.
              </p>

              <div className="flex flex-wrap gap-3">
                <Link href="/intelligence"
                  className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105"
                  style={{ background: 'rgba(0,212,255,0.1)', color: '#00d4ff', border: '1px solid rgba(0,212,255,0.2)', fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, letterSpacing: '0.05em' }}>
                  <Activity className="w-4 h-4" />
                  View Intelligence
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
                <Link href="/simulation"
                  className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105"
                  style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)', fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, letterSpacing: '0.05em' }}>
                  <Zap className="w-4 h-4" />
                  War Room
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Tech badges */}
              <div className="flex flex-wrap gap-2 mt-6">
                {['LightGBM', 'FastAPI', 'LLM Agents', 'Real-time', 'Carbon-Aware'].map(tag => (
                  <span key={tag} className="text-[9px] px-2 py-0.5 rounded border border-grid-border/60 text-grid-textDim"
                    style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Right: Grid Map */}
            <div className="relative">
              <div className="glass rounded-2xl p-4 glow-cyan">
                <div className="flex items-center justify-between mb-3">
                  <SectionLabel>Live Grid Topology</SectionLabel>
                  <div className="flex items-center gap-1.5 text-[10px] text-green-400"
                    style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                    LIVE
                  </div>
                </div>
                {mounted && <GridMap animated={true} className="h-64 lg:h-80" />}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Live Status ───────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-4">
          <SectionLabel>Real-Time Grid Status</SectionLabel>
          <div className="flex-1 h-px bg-grid-border/30" />
          <span className="text-[10px] text-grid-textDim"
            style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
            Updated: {new Date().toLocaleTimeString('en-IN')} IST
          </span>
        </div>
        <LiveStatRow />
        <div className="mt-3">
          <RegionStatusRow />
        </div>
      </section>

      {/* ── Forecast Chart ────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-6">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-lg font-bold text-white"
                style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                7-Day Demand Forecast
              </div>
              <div className="text-xs text-grid-textDim">LightGBM · Climate-Adjusted · 4 Regions</div>
            </div>
            <Badge variant="cyan">
              <BarChart2 className="w-3 h-3" />
              ML FORECAST
            </Badge>
          </div>
          <ForecastChart />
        </Card>
      </section>

      {/* ── What We Do ────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-8">
        <div className="text-center mb-8">
          <div className="text-[10px] uppercase tracking-[0.3em] text-cyan-400 mb-2"
            style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
            Capabilities
          </div>
          <h2 className="text-3xl font-bold text-white"
            style={{ fontFamily: 'Rajdhani, sans-serif' }}>
            What This System Does
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {FEATURE_CARDS.map((card, i) => {
            const Icon = card.icon
            return (
              <Card key={i} className="group hover:scale-[1.02] transition-transform duration-200">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                  style={{ background: `${card.color}15`, border: `1px solid ${card.color}25` }}>
                  <Icon className="w-5 h-5" style={{ color: card.color }} />
                </div>
                <h3 className="text-lg font-bold text-white mb-2"
                  style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                  {card.title}
                </h3>
                <p className="text-sm text-grid-textDim leading-relaxed">{card.body}</p>
              </Card>
            )
          })}
        </div>
      </section>

      {/* ── Footer spacer ─────────────────────────────────────────── */}
      <div className="h-12" />
    </div>
  )
}
