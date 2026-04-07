'use client'

/**
 * XAI Dashboard - 3-Panel Human-Readable Grid Status
 * ===================================================
 * Displays NOW / PREDICTED / RISK WATCH panels with
 * executive-friendly summaries and optional technical details.
 * 
 * @typedef {Object} PanelData
 * @property {string} title - Panel title ("NOW", "PREDICTED", "RISK WATCH")
 * @property {string} icon - Emoji icon for the panel
 * @property {string} headline - Main message (1-2 sentences)
 * @property {string[]} bullet_points - Supporting details
 * @property {'info'|'warning'|'critical'} severity - Severity level for color coding
 * @property {string} timestamp - When this was computed
 * 
 * @typedef {Object} XAIData
 * @property {string} plain_summary - 2-3 sentence executive summary
 * @property {string} technical_details - Full technical breakdown
 * @property {{ now: PanelData, predicted: PanelData, risk_watch: PanelData }} panel_data
 * @property {string} computed_at - ISO timestamp
 */

import { useState } from 'react'

const severityColors = {
  info: {
    bg: 'bg-blue-900/20',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
    headlineBg: 'bg-blue-500/10',
  },
  warning: {
    bg: 'bg-yellow-900/20',
    border: 'border-yellow-500/30',
    text: 'text-yellow-400',
    headlineBg: 'bg-yellow-500/10',
  },
  critical: {
    bg: 'bg-red-900/20',
    border: 'border-red-500/30',
    text: 'text-red-400',
    headlineBg: 'bg-red-500/10',
  },
}

function Panel({ panel }) {
  const colors = severityColors[panel.severity] || severityColors.info
  
  return (
    <div className={`${colors.bg} ${colors.border} border rounded-lg p-4 h-full`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{panel.icon}</span>
        <h3 className={`font-bold ${colors.text}`}>{panel.title}</h3>
        <span className="ml-auto text-xs text-grid-textDim font-mono">{panel.timestamp}</span>
      </div>
      
      <div className={`${colors.headlineBg} rounded p-2 mb-3`}>
        <p className={`font-semibold text-sm ${colors.text}`}>
          {panel.headline}
        </p>
      </div>
      
      {panel.bullet_points && panel.bullet_points.length > 0 && (
        <ul className="space-y-1.5">
          {panel.bullet_points.map((point, idx) => (
            <li key={idx} className="text-xs text-grid-textDim flex items-start gap-2">
              <span className="text-grid-textDim/50">•</span>
              <span>{point}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

/**
 * XAI Dashboard Component
 * @param {{ data: XAIData | null, loading?: boolean }} props
 */
export function XAIDashboard({ data, loading }) {
  const [showDetails, setShowDetails] = useState(false)
  
  if (loading) {
    return (
      <div className="glass rounded-xl p-6 animate-pulse">
        <div className="h-8 bg-grid-border/30 rounded w-1/3 mb-4"></div>
        <div className="h-16 bg-grid-border/20 rounded mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-48 bg-grid-border/20 rounded"></div>
          <div className="h-48 bg-grid-border/20 rounded"></div>
          <div className="h-48 bg-grid-border/20 rounded"></div>
        </div>
      </div>
    )
  }
  
  if (!data) {
    return (
      <div className="glass rounded-xl p-6">
        <p className="text-grid-textDim text-center">No XAI data available</p>
      </div>
    )
  }
  
  return (
    <div className="glass rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
            Grid Intelligence Dashboard
          </h2>
          <p className="text-xs text-grid-textDim">Executive summary with 3-panel view</p>
        </div>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-xs px-3 py-1.5 rounded border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10 transition-colors font-medium"
          style={{ fontFamily: 'IBM Plex Mono, monospace' }}
        >
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>
      </div>
      
      {/* Plain Summary */}
      <div className="bg-grid-bg/50 border border-grid-border/30 rounded-lg p-4 mb-4">
        <p className="text-white text-sm leading-relaxed">{data.plain_summary}</p>
      </div>
      
      {/* 3-Panel Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <Panel panel={data.panel_data.now} />
        <Panel panel={data.panel_data.predicted} />
        <Panel panel={data.panel_data.risk_watch} />
      </div>
      
      {/* Technical Details (collapsible) */}
      {showDetails && (
        <div className="bg-grid-bg border border-grid-border/30 rounded-lg p-4 mt-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-grid-textDim font-medium">TECHNICAL DETAILS</span>
            <div className="flex-1 h-px bg-grid-border/30" />
          </div>
          <pre className="text-green-400 text-xs font-mono whitespace-pre-wrap overflow-x-auto leading-relaxed">
            {data.technical_details}
          </pre>
        </div>
      )}
      
      {/* Timestamp */}
      <div className="text-right text-[10px] text-grid-textDim mt-3 font-mono">
        Last updated: {new Date(data.computed_at).toLocaleString('en-IN')}
      </div>
    </div>
  )
}

export default XAIDashboard
