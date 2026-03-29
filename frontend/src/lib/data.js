// ─── Region Definitions ──────────────────────────────────────────────
export const REGIONS = [
  { id: 'BHR', name: 'Bihar', fullName: 'Bihar (NR)', color: '#00d4ff', x: 62, y: 35 },
  { id: 'UP',  name: 'NR UP', fullName: 'Uttar Pradesh (NR)', color: '#0066ff', x: 42, y: 28 },
  { id: 'WB',  name: 'West Bengal', fullName: 'West Bengal (ER)', color: '#8b5cf6', x: 72, y: 48 },
  { id: 'KAR', name: 'Karnataka', fullName: 'Karnataka (SR)', color: '#10b981', x: 42, y: 72 },
]

export const EDGES = [
  { from: 'BHR', to: 'UP',  congestion: 45, capacity: 2200 },
  { from: 'BHR', to: 'WB',  congestion: 82, capacity: 1800 },
  { from: 'UP',  to: 'KAR', congestion: 31, capacity: 3000 },
  { from: 'WB',  to: 'KAR', congestion: 67, capacity: 1500 },
  { from: 'UP',  to: 'WB',  congestion: 55, capacity: 2000 },
]

// ─── 7-Day Forecast Data ─────────────────────────────────────────────
const today = new Date()
const days = Array.from({ length: 7 }, (_, i) => {
  const d = new Date(today)
  d.setDate(d.getDate() + i)
  return d.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' })
})

export const FORECAST_DATA = days.map((day, i) => ({
  day,
  BHR: 4200 + Math.sin(i * 0.8) * 300 + Math.random() * 200,
  UP:  8100 + Math.cos(i * 0.6) * 400 + Math.random() * 300,
  WB:  5800 + Math.sin(i * 1.1) * 250 + Math.random() * 180,
  KAR: 6900 + Math.cos(i * 0.9) * 350 + Math.random() * 220,
  tempBHR: 38 + Math.sin(i * 0.5) * 4,
  tempUP:  36 + Math.cos(i * 0.7) * 3,
  solarKAR: 5.2 + Math.sin(i * 1.2) * 0.8,
}))

// ─── Grid Status ─────────────────────────────────────────────────────
export const GRID_STATUS = {
  BHR: { demand: 4312, supply: 4180, battery_soc: 0.62, deficit: -132 },
  UP:  { demand: 8340, supply: 8520, battery_soc: 0.78, deficit: 180 },
  WB:  { demand: 5920, supply: 5700, battery_soc: 0.41, deficit: -220 },
  KAR: { demand: 6890, supply: 7100, battery_soc: 0.85, deficit: 210 },
}

// ─── Intelligence Data ────────────────────────────────────────────────
export const INTELLIGENCE_DATA = {
  impact_narrative: `Northern region faces acute thermal stress with temperatures breaching 40°C across Bihar and UP corridors. LightGBM models indicate 18% demand uplift probability in next 72 hours. The Kumbh Mela pre-positioning has triggered synthetic hoarding patterns in UP nodes. Karnataka solar surplus (5.8 GW available) presents optimal arbitrage window — Routing Agent recommends direct HVDC dispatch via Western corridor to offset Bihar deficit. Carbon tax optimization at current ₹850/tonne suggests blended dispatch favoring renewable-heavy Karnataka profile. State agents are converging on a SYNDICATE trade structure to pool risk.`,
  regions: {
    BHR: {
      multipliers: { edm: 1.18, gcm: 0.94 },
      risk_flags: { demand_spike_risk: true, pre_event_hoard: false, supply_crunch: false },
      detected_events: [
        { type: 'HEATWAVE', label: 'Severe Heatwave Alert', severity: 'HIGH', timestamp: '06:00 IST' },
        { type: 'INDUSTRIAL', label: 'Bhilai Steel ramp-up', severity: 'MED', timestamp: '08:30 IST' },
      ],
      weather: { temp: 41, humidity: 68, condition: 'Scorching', forecast: ['☀️','☀️','🌤️','⛅','☀️'] },
    },
    UP: {
      multipliers: { edm: 1.22, gcm: 1.05 },
      risk_flags: { demand_spike_risk: true, pre_event_hoard: true, supply_crunch: false },
      detected_events: [
        { type: 'EVENT', label: 'Kumbh Mela Pre-Positioning', severity: 'HIGH', timestamp: '04:00 IST' },
        { type: 'FESTIVAL', label: 'Diwali Demand Surge (72h)', severity: 'HIGH', timestamp: '00:00 IST' },
        { type: 'MARKET', label: 'Agri pump loads peaking', severity: 'LOW', timestamp: '10:00 IST' },
      ],
      weather: { temp: 38, humidity: 54, condition: 'Hot & Hazy', forecast: ['🌤️','☀️','☀️','⛅','🌧️'] },
    },
    WB: {
      multipliers: { edm: 0.97, gcm: 0.88 },
      risk_flags: { demand_spike_risk: false, pre_event_hoard: false, supply_crunch: true },
      detected_events: [
        { type: 'SUPPLY', label: 'Farakka Unit #3 Offline', severity: 'HIGH', timestamp: '02:15 IST' },
        { type: 'RAIN', label: 'Pre-monsoon load drop', severity: 'LOW', timestamp: '09:00 IST' },
      ],
      weather: { temp: 33, humidity: 82, condition: 'Pre-Monsoon', forecast: ['⛅','🌧️','🌧️','⛅','🌤️'] },
    },
    KAR: {
      multipliers: { edm: 0.91, gcm: 1.31 },
      risk_flags: { demand_spike_risk: false, pre_event_hoard: false, supply_crunch: false },
      detected_events: [
        { type: 'SOLAR', label: 'Pavagada peak generation', severity: 'INFO', timestamp: '11:00 IST' },
        { type: 'EXPORT', label: 'Surplus export opportunity', severity: 'INFO', timestamp: '11:30 IST' },
      ],
      weather: { temp: 29, humidity: 61, condition: 'Partly Cloudy', forecast: ['⛅','⛅','🌤️','☀️','⛅'] },
    },
  }
}

// ─── Simulation Stream Logs ───────────────────────────────────────────
export const SIM_LOGS = [
  { agent: 'SYSTEM',   text: 'Initializing India Grid Digital Twin v2.4.1...', delay: 0 },
  { agent: 'SYSTEM',   text: 'LightGBM forecast loaded. 7-day horizon active.', delay: 400 },
  { agent: 'SYSTEM',   text: 'Spawning State Agents for BHR, UP, WB, KAR...', delay: 900 },
  { agent: 'BHR_AGENT',text: 'Bihar reporting. Deficit: -132 MW. Thermal stress index: 0.82. Requesting emergency procurement.', delay: 1600 },
  { agent: 'UP_AGENT', text: 'UP online. Surplus: +180 MW. Pre-event hoarding pattern detected. Offering conditional 120 MW at ₹6.2/kWh.', delay: 2400 },
  { agent: 'WB_AGENT', text: 'West Bengal critical. Farakka Unit #3 offline. Net deficit: -220 MW. Accepting any trade > ₹5.8/kWh.', delay: 3200 },
  { agent: 'KAR_AGENT',text: 'Karnataka solar surplus: 210 MW available NOW. Pavagada output at peak. Proposing bulk export at ₹4.9/kWh.', delay: 4100 },
  { agent: 'ROUTING',  text: 'Analyzing transmission corridors... BHR-WB line congestion at 82%. CRITICAL threshold.', delay: 5000 },
  { agent: 'ROUTING',  text: 'Recommending alternate path: KAR → UP → BHR via Western HVDC. Congestion: 31%.', delay: 5800 },
  { agent: 'BHR_AGENT',text: 'Bihar rejects UP offer — price too high. Counter-offering ₹5.5/kWh for 100 MW.', delay: 6600 },
  { agent: 'UP_AGENT', text: 'UP counters: ₹5.9/kWh, 100 MW, 48-hour contract. Take it or leave it.', delay: 7400 },
  { agent: 'FUSION',   text: 'Deadlock detected. Initiating SYNDICATE formation protocol. Carbon tax optimization: ₹850/tonne.', delay: 8200 },
  { agent: 'FUSION',   text: 'Optimal solution: KAR→BHR (150 MW at ₹5.1/kWh) + UP→WB (100 MW at ₹5.7/kWh). Carbon savings: ₹2.1L.', delay: 9100 },
  { agent: 'BHR_AGENT',text: 'Bihar ACCEPTS KAR trade. Routing via UP corridor. ETA: 4 minutes.', delay: 9800 },
  { agent: 'WB_AGENT', text: 'West Bengal ACCEPTS UP offer. Deficit resolved. Grid stability restored.', delay: 10500 },
  { agent: 'SYSTEM',   text: 'All trades cleared. Carbon tax applied. Writing dispatch orders...', delay: 11200 },
  { agent: 'SYSTEM',   text: '✓ SIMULATION COMPLETE. 2 trades executed. Total value: ₹47.3 Lakhs.', delay: 12000 },
]

// ─── Dispatch Results ─────────────────────────────────────────────────
export const DISPATCH_RESULTS = [
  {
    id: 'TXN-2024-0891',
    type: 'SYNDICATE',
    seller: 'KAR',
    buyer: 'BHR',
    quantity_mw: 150,
    price_kwh: 5.1,
    total_value: 27540,
    path: ['KAR', 'UP', 'BHR'],
    carbon_tax: 12750,
    carbon_savings: 142000,
    status: 'CLEARED',
    timestamp: new Date().toISOString(),
  },
  {
    id: 'TXN-2024-0892',
    type: 'NEGOTIATED',
    seller: 'UP',
    buyer: 'WB',
    quantity_mw: 100,
    price_kwh: 5.7,
    total_value: 19260,
    path: ['UP', 'WB'],
    carbon_tax: 8500,
    carbon_savings: 68000,
    status: 'CLEARED',
    timestamp: new Date().toISOString(),
  },
]
