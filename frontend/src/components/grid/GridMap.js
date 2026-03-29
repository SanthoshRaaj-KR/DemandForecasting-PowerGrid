'use client'
import { useState, useEffect } from 'react'
import { REGIONS, EDGES, GRID_STATUS } from '@/lib/data'

// Convert percentage coords to SVG coords
function pct(val, max) { return (val / 100) * max }

export function GridMap({ animated = false, highlight = null, className = '' }) {
  const [flowOffset, setFlowOffset] = useState(0)
  const [pulseNodes, setPulseNodes] = useState([])

  const W = 500, H = 420

  useEffect(() => {
    if (!animated) return
    const id = setInterval(() => setFlowOffset(o => (o + 2) % 30), 60)
    return () => clearInterval(id)
  }, [animated])

  useEffect(() => {
    if (highlight) setPulseNodes([highlight])
  }, [highlight])

  const getNodePos = (id) => {
    const r = REGIONS.find(r => r.id === id)
    return { x: pct(r.x, W), y: pct(r.y, H) }
  }

  const getCongestionColor = (congestion) => {
    if (congestion > 80) return '#ef4444'
    if (congestion > 60) return '#f59e0b'
    return '#00d4ff'
  }

  const getSoCColor = (soc) => {
    if (soc > 0.6) return '#10b981'
    if (soc > 0.3) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div className={`relative ${className}`}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full h-full"
        style={{ filter: 'drop-shadow(0 0 30px rgba(0,212,255,0.06))' }}
      >
        <defs>
          {/* Glow filters */}
          <filter id="glow-cyan">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="glow-red">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="node-glow">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>

          {/* Gradient for India silhouette */}
          <radialGradient id="bg-grad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(0,212,255,0.03)" />
            <stop offset="100%" stopColor="rgba(0,212,255,0)" />
          </radialGradient>
        </defs>

        {/* Background grid dots */}
        <pattern id="dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
          <circle cx="1" cy="1" r="0.5" fill="rgba(0,212,255,0.06)" />
        </pattern>
        <rect width={W} height={H} fill="url(#dots)" />

        {/* India rough outline hint */}
        <ellipse cx={W * 0.52} cy={H * 0.5} rx={W * 0.32} ry={H * 0.44}
          fill="url(#bg-grad)" opacity="0.5" />

        {/* Transmission Edges */}
        {EDGES.map((edge, i) => {
          const from = getNodePos(edge.from)
          const to = getNodePos(edge.to)
          const color = getCongestionColor(edge.congestion)
          const isCongested = edge.congestion > 80
          const midX = (from.x + to.x) / 2 + (i % 2 === 0 ? 15 : -15)
          const midY = (from.y + to.y) / 2 + (i % 2 === 0 ? -15 : 15)
          const d = `M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`

          return (
            <g key={`${edge.from}-${edge.to}`}>
              {/* Shadow path */}
              <path
                d={d}
                fill="none"
                stroke={color}
                strokeWidth={isCongested ? 6 : 3}
                opacity={0.08}
                filter={isCongested ? 'url(#glow-red)' : undefined}
              />
              {/* Main path */}
              <path
                d={d}
                fill="none"
                stroke={color}
                strokeWidth={isCongested ? 2.5 : 1.5}
                opacity={isCongested ? 0.9 : 0.6}
                strokeDasharray={isCongested ? 'none' : undefined}
              />
              {/* Animated flow dash */}
              {animated && (
                <path
                  d={d}
                  fill="none"
                  stroke={color}
                  strokeWidth={2}
                  opacity={0.9}
                  strokeDasharray="6 8"
                  strokeDashoffset={-flowOffset}
                  style={{ filter: `drop-shadow(0 0 3px ${color})` }}
                />
              )}
              {/* Congestion label */}
              <text
                x={midX}
                y={midY - 4}
                fill={color}
                fontSize="9"
                textAnchor="middle"
                fontFamily="IBM Plex Mono"
                opacity={0.8}
              >
                {edge.congestion}%
              </text>
              {isCongested && (
                <text
                  x={midX}
                  y={midY + 8}
                  fill="#ef4444"
                  fontSize="8"
                  textAnchor="middle"
                  fontFamily="IBM Plex Mono"
                  opacity={0.9}
                >
                  ⚠ CONG
                </text>
              )}
            </g>
          )
        })}

        {/* Region Nodes */}
        {REGIONS.map(region => {
          const pos = getNodePos(region.id)
          const status = GRID_STATUS[region.id]
          const soc = status?.battery_soc || 0.5
          const deficit = status?.deficit || 0
          const socColor = getSoCColor(soc)
          const isDeficit = deficit < 0
          const isPulse = pulseNodes.includes(region.id)

          return (
            <g key={region.id} filter="url(#node-glow)">
              {/* Pulse ring for active nodes */}
              {(animated || isPulse) && (
                <circle
                  cx={pos.x} cy={pos.y} r="28"
                  fill="none"
                  stroke={region.color}
                  strokeWidth="1"
                  opacity="0.2"
                >
                  <animate
                    attributeName="r"
                    values="22;38;22"
                    dur="2.5s"
                    repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    values="0.3;0;0.3"
                    dur="2.5s"
                    repeatCount="indefinite"
                  />
                </circle>
              )}

              {/* Node background */}
              <circle
                cx={pos.x} cy={pos.y} r="22"
                fill="rgba(7,10,15,0.9)"
                stroke={region.color}
                strokeWidth="1.5"
                opacity="0.9"
              />

              {/* SoC arc */}
              <circle
                cx={pos.x} cy={pos.y} r="22"
                fill="none"
                stroke={socColor}
                strokeWidth="3"
                strokeDasharray={`${soc * 138.2} 138.2`}
                strokeDashoffset="-34.5"
                strokeLinecap="round"
                transform={`rotate(-90 ${pos.x} ${pos.y})`}
                opacity="0.7"
              />

              {/* Region ID */}
              <text
                x={pos.x} y={pos.y - 4}
                fill={region.color}
                fontSize="10"
                fontWeight="700"
                textAnchor="middle"
                fontFamily="Rajdhani, sans-serif"
                letterSpacing="1"
              >
                {region.id}
              </text>

              {/* Deficit/Surplus */}
              <text
                x={pos.x} y={pos.y + 8}
                fill={isDeficit ? '#ef4444' : '#10b981'}
                fontSize="8"
                textAnchor="middle"
                fontFamily="IBM Plex Mono"
              >
                {isDeficit ? '▼' : '▲'}{Math.abs(deficit)}
              </text>

              {/* SoC label */}
              <text
                x={pos.x} y={pos.y + 18}
                fill={socColor}
                fontSize="7"
                textAnchor="middle"
                fontFamily="IBM Plex Mono"
                opacity="0.8"
              >
                {Math.round(soc * 100)}%
              </text>

              {/* Region name below node */}
              <text
                x={pos.x} y={pos.y + 36}
                fill="rgba(148,163,184,0.7)"
                fontSize="8"
                textAnchor="middle"
                fontFamily="DM Sans, sans-serif"
              >
                {region.name}
              </text>
            </g>
          )
        })}

        {/* Legend */}
        <g transform={`translate(10, ${H - 80})`}>
          <rect width="130" height="72" rx="6" fill="rgba(7,10,15,0.8)" stroke="rgba(30,45,61,0.8)" strokeWidth="1" />
          <text x="10" y="16" fill="rgba(148,163,184,0.6)" fontSize="8" fontFamily="IBM Plex Mono">TRANSMISSION</text>
          {[
            { color: '#00d4ff', label: 'Normal (<60%)' },
            { color: '#f59e0b', label: 'Warning (60-80%)' },
            { color: '#ef4444', label: 'Critical (>80%)' },
          ].map((item, i) => (
            <g key={i} transform={`translate(10, ${26 + i * 14})`}>
              <line x1="0" y1="4" x2="16" y2="4" stroke={item.color} strokeWidth="2" />
              <text x="22" y="8" fill="rgba(148,163,184,0.7)" fontSize="8" fontFamily="IBM Plex Mono">{item.label}</text>
            </g>
          ))}
        </g>

        {/* Battery SoC legend */}
        <g transform={`translate(${W - 130}, ${H - 60})`}>
          <rect width="120" height="52" rx="6" fill="rgba(7,10,15,0.8)" stroke="rgba(30,45,61,0.8)" strokeWidth="1" />
          <text x="10" y="14" fill="rgba(148,163,184,0.6)" fontSize="8" fontFamily="IBM Plex Mono">BATTERY SoC</text>
          {[
            { color: '#10b981', label: '>60%' },
            { color: '#f59e0b', label: '30-60%' },
            { color: '#ef4444', label: '<30%' },
          ].map((item, i) => (
            <g key={i} transform={`translate(10, ${20 + i * 10})`}>
              <circle cx="4" cy="4" r="3" fill={item.color} />
              <text x="12" y="8" fill="rgba(148,163,184,0.7)" fontSize="8" fontFamily="IBM Plex Mono">{item.label}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  )
}
