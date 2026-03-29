'use client'
import { useEffect, useState } from 'react'
import { REGIONS } from '@/lib/data'

const AGENT_DEFS = {
  BHR_AGENT: { name: 'Bihar Agent',    id: 'BHR', color: '#00d4ff', side: 'left',   avatar: '🏙' },
  UP_AGENT:  { name: 'UP Agent',       id: 'UP',  color: '#0066ff', side: 'right',  avatar: '🌾' },
  WB_AGENT:  { name: 'W.Bengal Agent', id: 'WB',  color: '#8b5cf6', side: 'left',   avatar: '⚓' },
  KAR_AGENT: { name: 'Karnataka Agent',id: 'KAR', color: '#10b981', side: 'right',  avatar: '☀️' },
  ROUTING:   { name: 'Routing Agent',  id: 'RT',  color: '#f59e0b', side: 'center', avatar: '🔀' },
  FUSION:    { name: 'Fusion Agent',   id: 'FUS', color: '#ef4444', side: 'center', avatar: '🧠' },
}

export function AgentChat({ logs }) {
  const agentLogs = logs.filter(l => AGENT_DEFS[l.agent])
  const visibleLogs = agentLogs.slice(-8) // show last 8 agent messages

  if (agentLogs.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-grid-textDim text-sm">
        <span>Agent conversations will appear here during simulation</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3 p-2 max-h-80 overflow-y-auto">
      {visibleLogs.map((log, i) => {
        const def = AGENT_DEFS[log.agent]
        if (!def) return null
        const isRight = def.side === 'right'
        const isCenter = def.side === 'center'

        if (isCenter) {
          return (
            <div key={i} className="flex justify-center">
              <div
                className="max-w-sm px-3 py-2 rounded-lg text-xs text-center"
                style={{
                  background: `${def.color}10`,
                  border: `1px solid ${def.color}25`,
                  color: def.color,
                  fontFamily: 'IBM Plex Mono, monospace',
                  animation: 'count-up 0.3s ease-out',
                }}
              >
                <div className="font-bold mb-0.5 flex items-center justify-center gap-1">
                  <span>{def.avatar}</span>
                  <span>{def.name}</span>
                </div>
                <div className="text-grid-text opacity-90">{log.text}</div>
              </div>
            </div>
          )
        }

        return (
          <div
            key={i}
            className={`flex items-start gap-2 ${isRight ? 'flex-row-reverse' : ''}`}
            style={{ animation: 'count-up 0.3s ease-out' }}
          >
            {/* Avatar */}
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-sm shrink-0 mt-0.5"
              style={{ background: `${def.color}18`, border: `1.5px solid ${def.color}40` }}
            >
              {def.avatar}
            </div>

            {/* Bubble */}
            <div className={`max-w-xs ${isRight ? 'items-end' : 'items-start'} flex flex-col gap-0.5`}>
              <div
                className="text-[9px] opacity-60"
                style={{ color: def.color, fontFamily: 'IBM Plex Mono, monospace' }}
              >
                {def.name}
              </div>
              <div
                className="px-3 py-2 rounded-xl text-xs leading-relaxed"
                style={{
                  background: `${def.color}12`,
                  border: `1px solid ${def.color}25`,
                  color: '#e2e8f0',
                  borderTopLeftRadius: !isRight ? '4px' : undefined,
                  borderTopRightRadius: isRight ? '4px' : undefined,
                  boxShadow: `0 0 12px ${def.color}15`,
                }}
              >
                {log.text}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
