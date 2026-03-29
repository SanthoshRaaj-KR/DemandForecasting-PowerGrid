'use client'
import { Brain, MessageSquare, RefreshCw, AlertTriangle } from 'lucide-react'
import { useIntelligence } from '@/hooks/useApi'
import { RegionCard } from '@/components/agents/RegionCard'
import { Card, SectionLabel, Badge, Skeleton } from '@/components/ui/Primitives'
import { REGIONS } from '@/lib/data'

export default function IntelligencePage() {
  const { data, loading } = useIntelligence()

  return (
    <div className="pt-14">
      {/* Page header */}
      <div className="relative border-b border-grid-border/50 overflow-hidden">
        <div className="absolute inset-0 grid-dots opacity-40" />
        <div className="max-w-7xl mx-auto px-6 py-10 relative z-10">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="h-px w-6 bg-cyan-400" />
                <span className="text-[10px] uppercase tracking-[0.3em] text-cyan-400"
                  style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                  LLM Agent Analysis
                </span>
              </div>
              <h1 className="text-4xl font-bold text-white mb-1"
                style={{ fontFamily: 'Rajdhani, sans-serif', letterSpacing: '0.05em' }}>
                INTELLIGENCE AGENTS
              </h1>
              <p className="text-grid-textDim text-sm max-w-xl">
                Real-time qualitative analysis from LLM agents — risk flags, demand multipliers, and event detection across all grid regions.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="cyan">
                <Brain className="w-3 h-3" />
                AGENTS ONLINE
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">

        {/* Global Narrative */}
        <Card className="glow-cyan">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
              <MessageSquare className="w-4.5 h-4.5 text-cyan-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <SectionLabel>Global Context — Fusion Agent Narrative</SectionLabel>
                <Badge variant="cyan">GPT-4 ANALYSIS</Badge>
              </div>
              {loading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-5/6" />
                </div>
              ) : (
                <p className="text-sm text-grid-text leading-relaxed">
                  {data?.impact_narrative}
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* Risk Summary Strip */}
        {!loading && data && (
          <div className="flex flex-wrap gap-3">
            {REGIONS.map(region => {
              const regionData = data.regions?.[region.id]
              if (!regionData) return null
              const risks = regionData.risk_flags
              const activeRisks = Object.entries(risks).filter(([, v]) => v)

              return (
                <div key={region.id}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg border"
                  style={{
                    background: activeRisks.length > 0 ? 'rgba(245,158,11,0.05)' : 'rgba(16,185,129,0.05)',
                    borderColor: activeRisks.length > 0 ? 'rgba(245,158,11,0.2)' : 'rgba(16,185,129,0.15)',
                  }}>
                  <span className="text-xs font-bold" style={{ color: region.color, fontFamily: 'Rajdhani, sans-serif', letterSpacing: '0.1em' }}>
                    {region.id}
                  </span>
                  {activeRisks.length === 0 ? (
                    <span className="text-[10px] text-green-400" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                      ✓ No Risks
                    </span>
                  ) : (
                    <span className="text-[10px] text-amber-400 flex items-center gap-1"
                      style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                      <AlertTriangle className="w-3 h-3" />
                      {activeRisks.length} risk{activeRisks.length > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* Region Cards Grid */}
        {loading ? (
          <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <Card key={i}>
                <Skeleton className="h-6 w-16 mb-3" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-20 w-full mb-3" />
                <Skeleton className="h-4 w-3/4" />
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-4">
            {REGIONS.map(region => (
              <RegionCard
                key={region.id}
                regionId={region.id}
                data={data?.regions?.[region.id]}
              />
            ))}
          </div>
        )}

      </div>
    </div>
  )
}
