'use client'
import { AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-react'

// ── Card ─────────────────────────────────────────────────────────────
export function Card({ children, className = '', glow = false, ...props }) {
  return (
    <div
      className={`glass rounded-xl p-5 relative overflow-hidden ${glow ? 'glow-cyan' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

// ── Section Label ────────────────────────────────────────────────────
export function SectionLabel({ children }) {
  return (
    <div className="text-[10px] uppercase tracking-[0.25em] text-grid-textDim mb-1"
      style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
      {children}
    </div>
  )
}

// ── Stat Block ───────────────────────────────────────────────────────
export function StatBlock({ label, value, unit, sub, color = 'text-white' }) {
  return (
    <div>
      <SectionLabel>{label}</SectionLabel>
      <div className={`text-2xl font-bold leading-none ${color}`}
        style={{ fontFamily: 'Rajdhani, sans-serif' }}>
        {value}
        {unit && <span className="text-sm font-normal text-grid-textDim ml-1">{unit}</span>}
      </div>
      {sub && <div className="text-xs text-grid-textDim mt-0.5">{sub}</div>}
    </div>
  )
}

// ── Badge ────────────────────────────────────────────────────────────
export function Badge({ children, variant = 'default' }) {
  const variants = {
    default:  'bg-white/5 text-grid-textDim border-white/10',
    cyan:     'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    amber:    'bg-amber-500/10 text-amber-400 border-amber-500/20',
    red:      'bg-red-500/10 text-red-400 border-red-500/20 risk-active',
    green:    'bg-green-500/10 text-green-400 border-green-500/20',
    purple:   'bg-purple-500/10 text-purple-400 border-purple-500/20',
    info:     'bg-blue-500/10 text-blue-400 border-blue-500/20',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-medium tracking-wider ${variants[variant]}`}
      style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
      {children}
    </span>
  )
}

// ── Risk Flag ────────────────────────────────────────────────────────
export function RiskFlag({ label, active, icon: Icon }) {
  if (!active) return (
    <div className="flex items-center gap-1.5 text-xs text-grid-muted opacity-30">
      <CheckCircle className="w-3 h-3" />
      <span>{label}</span>
    </div>
  )
  return (
    <div className="flex items-center gap-1.5 text-xs text-red-400 risk-active">
      <AlertTriangle className="w-3 h-3" />
      <span className="font-medium">{label}</span>
    </div>
  )
}

// ── Divider ──────────────────────────────────────────────────────────
export function Divider({ className = '' }) {
  return <div className={`border-t border-grid-border/50 ${className}`} />
}

// ── Loading Skeleton ─────────────────────────────────────────────────
export function Skeleton({ className = '' }) {
  return (
    <div className={`animate-pulse bg-grid-border/50 rounded ${className}`} />
  )
}

// ── Progress Bar ─────────────────────────────────────────────────────
export function ProgressBar({ value, max = 100, color = '#00d4ff', height = 4 }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div className="w-full rounded-full overflow-hidden" style={{ height, background: 'rgba(30,45,61,0.5)' }}>
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${pct}%`, background: color, boxShadow: `0 0 8px ${color}66` }}
      />
    </div>
  )
}

// ── Gauge ────────────────────────────────────────────────────────────
export function Gauge({ value, label, min = 0, max = 2, color = '#00d4ff' }) {
  const pct = (value - min) / (max - min)
  const angle = -135 + pct * 270
  const isWarning = value > 1.1 || value < 0.85

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-20 h-12 overflow-hidden">
        <svg viewBox="0 0 80 48" className="w-full h-full">
          {/* Track arc */}
          <path
            d="M 8 44 A 32 32 0 0 1 72 44"
            fill="none"
            stroke="rgba(30,45,61,0.8)"
            strokeWidth="5"
            strokeLinecap="round"
          />
          {/* Value arc */}
          <path
            d="M 8 44 A 32 32 0 0 1 72 44"
            fill="none"
            stroke={isWarning ? '#f59e0b' : color}
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={`${pct * 100.5} 100.5`}
            style={{ filter: `drop-shadow(0 0 4px ${isWarning ? '#f59e0b' : color})` }}
          />
          {/* Needle */}
          <line
            x1="40" y1="44"
            x2={40 + 26 * Math.cos((angle - 90) * Math.PI / 180)}
            y2={44 + 26 * Math.sin((angle - 90) * Math.PI / 180)}
            stroke={isWarning ? '#f59e0b' : color}
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <circle cx="40" cy="44" r="3" fill={isWarning ? '#f59e0b' : color} />
        </svg>
      </div>
      <div className="text-center">
        <div className={`text-sm font-bold ${isWarning ? 'text-amber-400' : 'text-white'}`}
          style={{ fontFamily: 'Rajdhani, sans-serif' }}>
          {value.toFixed(2)}x
        </div>
        <div className="text-[9px] text-grid-textDim uppercase tracking-wider"
          style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
          {label}
        </div>
      </div>
    </div>
  )
}
