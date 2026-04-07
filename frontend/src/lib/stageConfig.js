/**
 * Stage configuration for the 4-stage orchestration pipeline.
 */

export const STAGES = [
  {
    id: 1,
    name: 'A Priori Baseline',
    shortName: 'Baseline',
    icon: 'B',
    color: 'blue',
    description: 'Generate 30-day demand forecast and baseline schedule',
    plainLanguage:
      'Predict expected demand for each state over 30 days using historical patterns, weather forecasts, and known events.',
    whenActive: 'Runs once at simulation start to create the master plan.',
    outputs: ['30-day forecast', 'LLM sleep/wake schedule', 'Baseline costs'],
  },
  {
    id: 2,
    name: 'Intelligence and Delta',
    shortName: 'Intelligence',
    icon: 'I',
    color: 'purple',
    description: 'Detect anomalies and decide whether to wake LLM agents',
    plainLanguage:
      'Compare live conditions against the baseline and calculate Delta. Small Delta stays on baseline; large Delta wakes the full system.',
    whenActive: 'Runs every simulated day to make the WAKE/SLEEP decision.',
    outputs: ['Anomaly Delta (MW)', 'Wake/Sleep decision', 'Event impacts'],
    decisionLogic:
      'If Delta > 50 MW -> WAKE (run full orchestration)\nIf Delta <= 50 MW -> SLEEP (use baseline)',
  },
  {
    id: 3,
    name: 'Waterfall Resolution',
    shortName: 'Waterfall',
    icon: 'W',
    color: 'cyan',
    description: 'Resolve deficits using a 4-step sequence',
    plainLanguage:
      'On anomaly days, resolve shortages in strict order: battery, demand response auctions, cross-state routing, and finally controlled fallback.',
    whenActive: 'Runs only on WAKE days when anomaly is detected.',
    outputs: ['Battery discharge', 'DR activations', 'Trade dispatches', 'Load shedding'],
    waterfallSteps: [
      { step: 1, name: 'Battery (Temporal)', desc: 'Drain stored energy first' },
      { step: 2, name: 'DR Auction (Economic)', desc: 'Incentivize load reduction' },
      { step: 3, name: 'Transmission (Spatial)', desc: 'Route power from surplus states' },
      { step: 4, name: 'Lifeboat (Fallback)', desc: 'Emergency islanding if required' },
    ],
  },
  {
    id: 4,
    name: 'Memory and XAI',
    shortName: 'Memory',
    icon: 'M',
    color: 'green',
    description: 'Learn from failures and export explainable audit trail',
    plainLanguage:
      'Capture what went wrong today, carry warnings forward, and produce a regulator-friendly explanation of decisions.',
    whenActive: 'Runs at end of every day to close the learning loop.',
    outputs: ['Memory warnings (3-day buffer)', 'XAI audit ledger', 'Parameter autopsy hints'],
  },
]

export const STAGE_COLORS = {
  blue: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
    badge: 'bg-blue-500/20 text-blue-300',
  },
  purple: {
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/30',
    text: 'text-purple-400',
    badge: 'bg-purple-500/20 text-purple-300',
  },
  cyan: {
    bg: 'bg-cyan-500/10',
    border: 'border-cyan-500/30',
    text: 'text-cyan-400',
    badge: 'bg-cyan-500/20 text-cyan-300',
  },
  green: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    text: 'text-green-400',
    badge: 'bg-green-500/20 text-green-300',
  },
}

export const getStageById = (id) => STAGES.find((s) => s.id === id)
export const getStageColors = (colorName) => STAGE_COLORS[colorName] || STAGE_COLORS.blue
