'use client'

import { useState } from 'react'
import { STAGES } from '@/lib/stageConfig'
import { StageCardList } from '@/components/ui/StageCard'
import { Badge, Card } from '@/components/ui/Primitives'

export default function StagesPage() {
  const [expandedId, setExpandedId] = useState(null)
  const [statuses] = useState({
    1: 'complete',
    2: 'complete',
    3: 'running',
    4: 'idle',
  })

  const handleToggle = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 pt-20">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Orchestration Pipeline</h1>
          <p className="text-gray-400">
            The Smart Grid runs through 4 stages every day. Click any stage to see details.
          </p>
        </div>

        <Card className="mb-6">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h2 className="text-lg font-semibold">Today&apos;s Status</h2>
              <p className="text-sm text-gray-400">Simulation Date: 2026-04-07</p>
            </div>
            <div className="flex gap-2">
              <Badge variant="green">2 Complete</Badge>
              <Badge variant="amber">1 Running</Badge>
              <Badge variant="default">1 Pending</Badge>
            </div>
          </div>
        </Card>

        <StageCardList
          stages={STAGES}
          statuses={statuses}
          expandedId={expandedId}
          onToggle={handleToggle}
        />

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Tip: On sleep days, Stage 3 (Waterfall) is skipped to save costs.</p>
        </div>
      </div>
    </div>
  )
}
