'use client'
import { useState } from 'react'
import { Zap, Network, BarChart2, MessageSquare } from 'lucide-react'
import { useSimulation } from '@/hooks/useApi'
import { SimTerminal } from '@/components/grid/SimTerminal'
import { AgentChat } from '@/components/agents/AgentChat'
import { GridMap } from '@/components/grid/GridMap'
import { DispatchTable } from '@/components/grid/DispatchTable'
import { Card, SectionLabel, Badge } from '@/components/ui/Primitives'

const TABS = [
  { id: 'terminal', label: 'Terminal',  icon: Zap },
  { id: 'agents',   label: 'Agents',    icon: MessageSquare },
  { id: 'grid',     label: 'Grid View', icon: Network },
  { id: 'results',  label: 'Dispatch',  icon: BarChart2 },
]

export default function SimulationPage() {
  const { logs, results, running, done, runSimulation } = useSimulation()
  const [activeTab, setActiveTab] = useState('terminal')

  return (
    <div className="pt-14">
      {/* Page header */}
      <div className="relative border-b border-grid-border/50 overflow-hidden">
        <div className="absolute inset-0 grid-dots opacity-40" />
        <div className="max-w-7xl mx-auto px-6 py-10 relative z-10">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="h-px w-6 bg-red-400" />
                <span className="text-[10px] uppercase tracking-[0.3em] text-red-400"
                  style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                  Agentic Simulation
                </span>
              </div>
              <h1 className="text-4xl font-bold text-white mb-1"
                style={{ fontFamily: 'Rajdhani, sans-serif', letterSpacing: '0.05em' }}>
                THE WAR ROOM
              </h1>
              <p className="text-grid-textDim text-sm max-w-xl">
                Watch LLM State Agents negotiate energy trades in real-time. The Routing Agent finds optimal transmission paths. The Fusion Agent resolves deadlocks.
              </p>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {running && (
                <Badge variant="red">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                  SIMULATION RUNNING
                </Badge>
              )}
              {done && (
                <Badge variant="green">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                  SIMULATION COMPLETE
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">

        {/* Tab Bar */}
        <div className="flex gap-1 mb-6 border-b border-grid-border/40 pb-0">
          {TABS.map(tab => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            const hasResults = tab.id === 'results' && results
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2.5 text-sm transition-all duration-150 border-b-2 -mb-px
                  ${active
                    ? 'border-cyan-400 text-cyan-400'
                    : 'border-transparent text-grid-textDim hover:text-white'
                  }
                `}
                style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, letterSpacing: '0.05em' }}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
                {hasResults && (
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                )}
              </button>
            )
          })}
        </div>

        {/* ── Terminal Tab ───────────────────────────────────────── */}
        {activeTab === 'terminal' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <SectionLabel>Simulation Output Stream</SectionLabel>
              <span className="text-[10px] text-grid-textDim"
                style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                {logs.length} events
              </span>
            </div>
            <SimTerminal
              logs={logs}
              running={running}
              done={done}
              onRun={runSimulation}
            />
            {/* Quick info cards */}
            <div className="grid grid-cols-3 gap-3 mt-4">
              {[
                { label: 'State Agents', count: 4, color: '#00d4ff', desc: 'BHR · UP · WB · KAR' },
                { label: 'Routing Agent', count: 1, color: '#f59e0b', desc: 'Path optimization' },
                { label: 'Fusion Agent',  count: 1, color: '#ef4444', desc: 'Deadlock resolution' },
              ].map(a => (
                <Card key={a.label} className="py-3 text-center">
                  <div className="text-2xl font-bold mb-0.5"
                    style={{ fontFamily: 'Rajdhani, sans-serif', color: a.color }}>
                    {a.count}
                  </div>
                  <div className="text-xs text-white font-medium">{a.label}</div>
                  <div className="text-[10px] text-grid-textDim mt-0.5"
                    style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                    {a.desc}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* ── Agents Chat Tab ────────────────────────────────────── */}
        {activeTab === 'agents' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <SectionLabel>Agent Negotiation Feed</SectionLabel>
              {!running && !done && (
                <button
                  onClick={() => { runSimulation(); setActiveTab('agents') }}
                  className="text-xs text-cyan-400 border border-cyan-500/20 px-3 py-1 rounded hover:bg-cyan-500/10 transition-colors"
                  style={{ fontFamily: 'IBM Plex Mono, monospace' }}
                >
                  Run to see agents talk →
                </button>
              )}
            </div>
            <Card>
              <AgentChat logs={logs} />
            </Card>

            {/* Agent legend */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {[
                { avatar: '🏙', name: 'Bihar Agent',     color: '#00d4ff', role: 'Deficit buyer — seeks cheapest supply' },
                { avatar: '🌾', name: 'UP Agent',        color: '#0066ff', role: 'Surplus seller — maximizes price' },
                { avatar: '⚓', name: 'W.Bengal Agent',  color: '#8b5cf6', role: 'Critical deficit — accepts any trade' },
                { avatar: '☀️', name: 'Karnataka Agent', color: '#10b981', role: 'Solar surplus — bulk export window' },
                { avatar: '🔀', name: 'Routing Agent',   color: '#f59e0b', role: 'Finds optimal transmission path' },
                { avatar: '🧠', name: 'Fusion Agent',    color: '#ef4444', role: 'Resolves deadlocks via SYNDICATE' },
              ].map(a => (
                <div key={a.name}
                  className="flex items-start gap-2 p-2.5 rounded-lg border border-grid-border/40 bg-white/2">
                  <span className="text-base mt-0.5">{a.avatar}</span>
                  <div>
                    <div className="text-xs font-medium" style={{ color: a.color }}>
                      {a.name}
                    </div>
                    <div className="text-[10px] text-grid-textDim leading-relaxed">{a.role}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Grid View Tab ──────────────────────────────────────── */}
        {activeTab === 'grid' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <SectionLabel>Live Grid Topology</SectionLabel>
              <Badge variant={running ? 'red' : 'cyan'}>
                {running ? '⚡ ACTIVE TRADES' : 'STATIC VIEW'}
              </Badge>
            </div>
            <Card className="glow-cyan">
              <GridMap animated={running || done} className="h-96 md:h-[500px]" />
            </Card>
            {/* Congestion legend */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[
                { label: 'BHR—WB', congestion: 82, color: '#ef4444' },
                { label: 'WB—KAR', congestion: 67, color: '#f59e0b' },
                { label: 'UP—WB',  congestion: 55, color: '#f59e0b' },
                { label: 'BHR—UP', congestion: 45, color: '#00d4ff' },
                { label: 'UP—KAR', congestion: 31, color: '#00d4ff' },
              ].map(line => (
                <div key={line.label}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/3 border border-grid-border/40">
                  <span className="text-xs text-white"
                    style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                    {line.label}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1 rounded-full bg-grid-border/50">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${line.congestion}%`,
                          background: line.color,
                          boxShadow: `0 0 6px ${line.color}88`,
                        }}
                      />
                    </div>
                    <span className="text-xs font-medium w-8 text-right"
                      style={{ color: line.color, fontFamily: 'IBM Plex Mono, monospace' }}>
                      {line.congestion}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Dispatch Results Tab ───────────────────────────────── */}
        {activeTab === 'results' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <SectionLabel>Dispatch Orders & Trade Settlement</SectionLabel>
            </div>
            <Card>
              <DispatchTable results={results} />
            </Card>
            {!results && !running && (
              <div className="text-center py-4">
                <button
                  onClick={() => { runSimulation(); }}
                  className="text-sm text-cyan-400 border border-cyan-500/20 px-4 py-2 rounded-lg hover:bg-cyan-500/10 transition-colors"
                  style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 600 }}
                >
                  Run Simulation to Generate Dispatch Orders
                </button>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  )
}
