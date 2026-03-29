# 🇮🇳 India Grid Digital Twin — Frontend

A premium Next.js 14 dashboard for the India Smart Grid Simulation system.

## Stack

- **Next.js 14** (App Router, JavaScript)
- **Tailwind CSS** — dark glassmorphic design system
- **Recharts** — 7-day LightGBM forecast area charts
- **Framer Motion** — ready to add transitions
- **Lucide React** — icons
- **IBM Plex Mono + Rajdhani + DM Sans** — custom font trio

## Pages

| Route | Page | Description |
|---|---|---|
| `/` | Dashboard | Hero + live grid status + 7-day forecast chart + feature cards |
| `/intelligence` | Intelligence Agents | LLM narrative + 4 region cards with gauges, risk flags, events, weather |
| `/simulation` | War Room | Terminal stream + agent chat bubbles + animated grid map + dispatch table |

## Setup

```bash
# 1. Install dependencies
npm install

# 2. Set your backend URL (optional — falls back to mock data)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 3. Run dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## API Integration

The frontend auto-connects to your FastAPI backend. If the backend is unreachable, it **silently falls back to rich mock data** so you can develop/demo standalone.

| Hook | Endpoint | Fallback |
|---|---|---|
| `useIntelligence()` | `GET /api/intelligence` | `INTELLIGENCE_DATA` mock |
| `useGridStatus()` | `GET /api/grid-status` | `GRID_STATUS` mock |
| `useSimulation()` | `POST /api/run-simulation` | `SIM_LOGS` sequential mock with delays |
| Dispatch results | `GET /api/simulation-result` | `DISPATCH_RESULTS` mock |

All mock data is in `src/lib/data.js` — edit it to match your actual backend shape.

## Simulation Flow

1. Go to `/simulation` → **War Room**
2. Click **"Run Sim"** in the terminal header
3. Watch agents negotiate in real-time (streamed logs)
4. Switch to **Agents** tab to see conversation bubbles
5. Switch to **Grid View** to see animated power flows
6. Switch to **Dispatch** tab to see cleared trade orders

## Backend Response Shape Expected

### `/api/intelligence`
```json
{
  "impact_narrative": "string",
  "regions": {
    "BHR": {
      "multipliers": { "edm": 1.18, "gcm": 0.94 },
      "risk_flags": { "demand_spike_risk": true, "pre_event_hoard": false, "supply_crunch": false },
      "detected_events": [{ "type": "HEATWAVE", "label": "...", "severity": "HIGH", "timestamp": "06:00 IST" }],
      "weather": { "temp": 41, "humidity": 68, "condition": "Scorching", "forecast": ["☀️","☀️","🌤️","⛅","☀️"] }
    }
  }
}
```

### `/api/grid-status`
```json
{
  "BHR": { "demand": 4312, "supply": 4180, "battery_soc": 0.62, "deficit": -132 }
}
```

### `POST /api/run-simulation` (SSE stream)
```
data: [BHR_AGENT]: Bihar reporting...
data: [ROUTING]: Analyzing corridors...
```
Parse lines with `[AGENT_NAME]:` prefix to route to agent chat bubbles.

### `/api/simulation-result`
```json
[{
  "id": "TXN-2024-0891",
  "type": "SYNDICATE",
  "seller": "KAR", "buyer": "BHR",
  "quantity_mw": 150, "price_kwh": 5.1,
  "total_value": 27540,
  "path": ["KAR", "UP", "BHR"],
  "carbon_tax": 12750, "carbon_savings": 142000,
  "status": "CLEARED"
}]
```

## Customization

- **Colors**: Edit `src/app/globals.css` CSS variables and `tailwind.config.js`
- **Regions**: Add/remove regions in `src/lib/data.js` → `REGIONS` array
- **Mock data**: All in `src/lib/data.js`
- **Grid topology**: Edit `EDGES` in `src/lib/data.js` for node positions and congestion thresholds

## File Structure

```
src/
├── app/
│   ├── layout.js          # Root layout + NavBar
│   ├── page.js            # Home / Dashboard
│   ├── intelligence/
│   │   └── page.js        # Intelligence Agents page
│   └── simulation/
│       └── page.js        # War Room / Simulation page
├── components/
│   ├── ui/
│   │   ├── NavBar.js      # Top navigation
│   │   └── Primitives.js  # Card, Badge, Gauge, ProgressBar, etc.
│   ├── charts/
│   │   └── ForecastChart.js   # 7-day Recharts area chart
│   ├── grid/
│   │   ├── GridMap.js         # SVG node-edge grid topology
│   │   ├── SimTerminal.js     # Glassmorphic terminal
│   │   └── DispatchTable.js   # Trade settlement cards
│   └── agents/
│       ├── RegionCard.js      # Per-region intelligence card
│       └── AgentChat.js       # Conversation bubbles
├── hooks/
│   └── useApi.js          # API hooks with mock fallback
└── lib/
    └── data.js            # All mock data + constants
```
