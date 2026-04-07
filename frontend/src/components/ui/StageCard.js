'use client'

import { AlertCircle, CheckCircle2, ChevronDown, ChevronUp, Clock } from 'lucide-react'
import { getStageColors } from '@/lib/stageConfig'

export function StageCard({ stage, status = 'idle', isExpanded = false, onToggle }) {
  const colors = getStageColors(stage.color)

  const statusConfig = {
    idle: { icon: Clock, color: 'text-gray-400', label: 'Pending' },
    running: { icon: Clock, color: 'text-yellow-400 animate-pulse', label: 'Running' },
    complete: { icon: CheckCircle2, color: 'text-green-400', label: 'Complete' },
    error: { icon: AlertCircle, color: 'text-red-400', label: 'Error' },
    skipped: { icon: Clock, color: 'text-gray-500', label: 'Skipped' },
  }

  const { icon: StatusIcon, color: statusColor, label: statusLabel } =
    statusConfig[status] || statusConfig.idle

  return (
    <div className={`${colors.bg} ${colors.border} border rounded-xl overflow-hidden transition-all duration-300`}>
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl font-bold text-white/80">{stage.icon}</span>
          <div className="text-left">
            <h3 className={`font-semibold ${colors.text}`}>
              Stage {stage.id}: {stage.name}
            </h3>
            <p className="text-sm text-gray-400">{stage.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`flex items-center gap-1 text-sm ${statusColor}`}>
            <StatusIcon className="w-4 h-4" />
            {statusLabel}
          </span>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-4">
          <div className="bg-black/20 rounded-lg p-3">
            <h4 className="text-sm font-medium text-gray-300 mb-1">In Plain Language:</h4>
            <p className="text-sm text-gray-400">{stage.plainLanguage}</p>
          </div>

          <div className="flex items-start gap-2">
            <Clock className="w-4 h-4 text-gray-500 mt-0.5" />
            <div>
              <span className="text-xs text-gray-500 uppercase">When Active</span>
              <p className="text-sm text-gray-400">{stage.whenActive}</p>
            </div>
          </div>

          <div>
            <span className="text-xs text-gray-500 uppercase">Outputs</span>
            <div className="flex flex-wrap gap-2 mt-1">
              {stage.outputs.map((output, idx) => (
                <span key={idx} className={`text-xs px-2 py-1 rounded ${colors.badge}`}>
                  {output}
                </span>
              ))}
            </div>
          </div>

          {stage.waterfallSteps && (
            <div className="space-y-2">
              <span className="text-xs text-gray-500 uppercase">Waterfall Sequence</span>
              {stage.waterfallSteps.map((step) => (
                <div key={step.step} className="flex items-center gap-3 bg-black/20 rounded p-2">
                  <span
                    className={`w-6 h-6 rounded-full ${colors.badge} flex items-center justify-center text-xs font-bold`}
                  >
                    {step.step}
                  </span>
                  <div>
                    <span className="text-sm font-medium text-gray-300">{step.name}</span>
                    <span className="text-sm text-gray-500 ml-2">{step.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {stage.decisionLogic && (
            <div className="bg-black/20 rounded-lg p-3 font-mono text-xs">
              <span className="text-gray-500 uppercase text-[10px]">Decision Logic</span>
              <pre className="text-gray-400 mt-1 whitespace-pre-wrap">{stage.decisionLogic}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function StageCardList({ stages, statuses = {}, expandedId, onToggle }) {
  return (
    <div className="space-y-3">
      {stages.map((stage) => (
        <StageCard
          key={stage.id}
          stage={stage}
          status={statuses[stage.id] || 'idle'}
          isExpanded={expandedId === stage.id}
          onToggle={() => onToggle(stage.id)}
        />
      ))}
    </div>
  )
}
