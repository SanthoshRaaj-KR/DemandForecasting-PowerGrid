"""Top-level orchestrator and orchestration workflow for the Smart Grid backend."""

from datetime import date
import json
from pathlib import Path

from src.agents.intelligence_agent.orchestrator import SmartGridIntelligenceAgent

BACKEND_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BACKEND_DIR / "outputs"


def generate_baseline_schedule() -> dict:
    """
    STAGE 1: Generate 30-day baseline schedule before simulation.
    
    This runs the A Priori Planner (ForwardMarketPlanner) to create a 
    baseline schedule with LLM sleep/wake flags, enabling ~70% cost reduction.
    """
    from src.agents.intelligence_agent.forward_market_planner import ForwardMarketPlanner
    from src.agents.fusion_agent.inference import predict_all_regions, load_artefacts
    import json as json_lib
    from pathlib import Path as PathLib
    
    print("\n" + "=" * 70)
    print("STAGE 1: A PRIORI PLANNER - Generating 30-day baseline schedule")
    print("=" * 70)
    
    # Load grid config
    grid_config_path = BACKEND_DIR / "config" / "grid_config.json"
    grid_config = json_lib.loads(grid_config_path.read_text(encoding="utf-8"))
    
    base_generation = {
        node_id: node_data["generation_mw"]
        for node_id, node_data in grid_config["nodes"].items()
    }
    
    # Get 30-day LightGBM predictions (use 7-day model repeated)
    print("[main] Loading LightGBM predictions...")
    try:
        load_artefacts()
        predictions_30d = {}
        
        # For each state, run predictions
        for state_id in base_generation.keys():
            # Get 7-day predictions and extend to 30
            preds_7day = predict_all_regions().get(state_id, {})
            pred_values = preds_7day.get("predicted_mw", [])
            
            # Extend to 30 days by repeating pattern
            if pred_values:
                extended = pred_values * 5  # 7*5 = 35 days, trim to 30
                predictions_30d[state_id] = {"predicted_mw": extended[:30]}
            else:
                # Fallback: use base generation as demand estimate
                predictions_30d[state_id] = {"predicted_mw": [base_generation[state_id]] * 30}
        
    except Exception as e:
        print(f"[main] Warning: Could not load LightGBM predictions: {e}")
        print("[main] Using base generation as fallback")
        predictions_30d = {
            state_id: {"predicted_mw": [gen_mw] * 30}
            for state_id, gen_mw in base_generation.items()
        }
    
    # Run planner
    planner = ForwardMarketPlanner()
    baseline = planner.compute_baseline(
        predictions_30d=predictions_30d,
        base_generation=base_generation,
        simulation_days=30
    )
    
    # Export to JSON with LLM flags
    baseline_json = planner.export_baseline_schedule_json(baseline, llm_threshold_mw=50.0)
    
    # Save to file
    output_path = OUTPUTS_DIR / f"baseline_schedule_{date.today().isoformat()}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(baseline_json, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Print summary
    print(f"[main] Baseline schedule -> {output_path}")
    print(f"[main] Total days: {baseline_json['days']}")
    print(f"[main] LLM wake days: {baseline_json['llm_wake_days']}/{baseline_json['days']} ({100 - baseline_json['cost_reduction_pct']:.1f}%)")
    print(f"[main] LLM sleep days: {baseline_json['llm_sleep_days']}/{baseline_json['days']} ({baseline_json['cost_reduction_pct']:.1f}%)")
    print(f"[main] 💰 Projected cost reduction: {baseline_json['cost_reduction_pct']:.1f}%")
    print("=" * 70 + "\n")
    
    return baseline_json


def generate_intelligence() -> dict:
    """
    STAGE 2: Generate daily intelligence (anomaly detection and Delta calculation).
    
    Creates Delta JSON file ONLY if anomalies detected (LLMs wake up).
    If no anomalies, LLMs stay asleep and use baseline schedule.
    """
    from src.agents.intelligence_agent.orchestrator import IntelligenceOrchestrator
    
    print("\n" + "=" * 70)
    print("STAGE 2: INTELLIGENCE EXTRACTION - Daily anomaly detection")
    print("=" * 70)
    
    agent = SmartGridIntelligenceAgent()
    intelligence = agent.run_all_regions()
    SmartGridIntelligenceAgent.print_summary_table(intelligence)
    
    # Check if any state has anomalies (should wake orchestrator)
    any_wake = any(
        data.get("deviation_result", {}).get("should_wake_orchestrator", False)
        for data in intelligence.values()
    )
    
    if any_wake:
        # Export Delta JSON (only on anomaly days)
        delta = agent.export_delta_json(day_index=0, output_dir=OUTPUTS_DIR)
        print(f"[main] 🚨 ANOMALY DETECTED - Delta MW: {delta.get('anomaly_delta_mw', 0):+.0f}")
        print(f"[main] ⚡ LLM Agents: AWAKE - Running waterfall resolution")
    else:
        print(f"[main] ✅ No anomalies - LLM Agents: DORMANT")
        print(f"[main] 💤 Using baseline schedule (no Delta JSON created)")

    output_path = OUTPUTS_DIR / f"grid_intelligence_{date.today().isoformat()}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(intelligence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[main] Intelligence JSON -> {output_path}")
    print("=" * 70 + "\n")
    
    return intelligence


def run_simulation_step():
    from run_simulation import run_simulation

    print("[main] Starting simulation pipeline (run_simulation.py)")
    run_simulation()
    print("[main] Simulation completed")


def execute_waterfall_demo(day_index: int = 0, date_str: str = "") -> dict:
    """
    Execute the 4-step waterfall with XAI Phase Trace export.
    
    This demonstrates the CORE WORKFLOW:
    1. Temporal (Battery) → 2. Economic (DR) → 3. Spatial (BFS) → 4. Fallback
    
    Returns a dict with waterfall result and XAI trace path.
    """
    from datetime import datetime, timedelta
    from src.agents.routing_agent.unified_routing_orchestrator import UnifiedRoutingOrchestrator
    
    print("\n" + "=" * 70)
    print("STAGE 3: WATERFALL ORCHESTRATOR EXECUTION")
    print("=" * 70)
    
    # Initialize orchestrator
    orchestrator = UnifiedRoutingOrchestrator()
    
    # Date setup
    if not date_str:
        base_date = datetime(2025, 1, 1)
        sim_date = base_date + timedelta(days=day_index)
        date_str = sim_date.strftime("%Y-%m-%d")
    
    # Sample deficit scenario (simulating a heatwave in UP)
    deficit_states_mw = {
        "UP": 180.0,      # Uttar Pradesh has 180 MW deficit
        "Bihar": 45.0,    # Bihar has 45 MW deficit
    }
    
    surplus_states_mw = {
        "WB": 120.0,      # West Bengal has surplus
        "Karnataka": 80.0, # Karnataka has surplus
    }
    
    # Battery state-of-charge (50 MW each)
    battery_soc = {
        "UP": 50.0,
        "Bihar": 30.0,
        "WB": 40.0,
        "Karnataka": 60.0,
    }
    
    battery_capacity = {
        "UP": 100.0,
        "Bihar": 100.0,
        "WB": 100.0,
        "Karnataka": 100.0,
    }
    
    # Transmission edge capacities (based on grid topology)
    daily_edge_capacities_mw = {
        ("WB", "Bihar"): 100.0,
        ("Bihar", "UP"): 80.0,
        ("Bihar", "WB"): 100.0,
        ("UP", "Bihar"): 80.0,
        ("Karnataka", "WB"): 70.0,
        ("WB", "Karnataka"): 70.0,
    }
    
    total_grid_capacity_mw = 2000.0  # National grid capacity
    
    # Execute waterfall
    waterfall_result = orchestrator.execute_waterfall(
        deficit_states_mw=deficit_states_mw,
        surplus_states_mw=surplus_states_mw,
        battery_soc=battery_soc,
        battery_capacity=battery_capacity,
        daily_edge_capacities_mw=daily_edge_capacities_mw,
        total_grid_capacity_mw=total_grid_capacity_mw,
        dr_clearing_price=6.0,
        day_index=day_index,
        date_str=date_str,
    )
    
    # Export XAI Phase Trace
    xai_trace_path = orchestrator.export_xai_phase_trace(
        waterfall_result=waterfall_result,
        day_index=day_index,
        date_str=date_str,
        output_dir="outputs",
    )
    
    return {
        "steps_executed": len(waterfall_result.steps_executed),
        "total_resolved_mw": waterfall_result.total_resolved_mw,
        "load_shedding_mw": sum(waterfall_result.load_shedding_mw.values()),
        "memory_warning": waterfall_result.memory_warning,
        "xai_trace_path": xai_trace_path,
        "waterfall_complete": waterfall_result.waterfall_complete,
    }


def validate_routes():
    print("[main] Validating API route handlers (in-process calls)")
    try:
        import server
        grid = server.grid_status()
        intel = server.intelligence()
        dispatch = server.dispatch_log()
        sim = server.simulation_result()

        print(f"[main] /api/grid-status: {len(grid.get('nodes', []))} nodes, {len(grid.get('edges', []))} edges")
        print(f"[main] /api/intelligence: {len(intel)} nodes")
        print(f"[main] /api/dispatch-log: {len(dispatch)} records")
        print(f"[main] /api/simulation-result: {sim.get('date', 'n/a')} ({len(sim.get('dispatches', []))} dispatch picks)")
        return {
            "grid_status": grid,
            "intelligence": intel,
            "dispatch_log": dispatch,
            "simulation_result": sim,
        }
    except Exception as exc:
        print(f"[main] Could not call route functions in-process: {exc}")
        print("[main] Ensure the FastAPI server is running for API endpoint checks.")
        return {}


def main() -> None:
    """
    4-STAGE WORKFLOW:
    1. A Priori Planner: Generate 30-day baseline schedule
    2. Intelligence: Daily anomaly detection  
    3. Routing: Waterfall orchestration (Battery→DR→BFS→Fallback)
    4. XAI/Memory: Phase Trace export and memory learning
    """
    print("\n" + "🔌" * 35)
    print(" " * 15 + "SMART GRID SIMULATION")
    print(" " * 12 + "Multi-Agent Workflow (Stages 1-4)")
    print("🔌" * 35 + "\n")
    
    # STAGE 1: A Priori Planning
    baseline = generate_baseline_schedule()
    
    # STAGE 2: Intelligence (anomaly detection)
    print("\nSTAGE 2: Intelligence extraction...")
    intelligence = generate_intelligence()
    
    # STAGE 3: Waterfall Orchestration (demo with sample scenario)
    waterfall = execute_waterfall_demo(day_index=0, date_str="2025-01-01")
    
    # STAGE 4: Run full simulation (includes XAI/Memory)
    print("\nSTAGE 4: Running full simulation...")
    run_simulation_step()
    route_check = validate_routes()

    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETE ✓")
    print("=" * 70)
    print(f"STAGE 1 - Baseline: {baseline['days']} days, {baseline['cost_reduction_pct']:.1f}% LLM cost reduction")
    print(f"STAGE 2 - Intelligence: {len(intelligence)} state analyses")
    print(f"STAGE 3 - Waterfall: {waterfall['total_resolved_mw']:.0f} MW resolved, {waterfall['load_shedding_mw']:.0f} MW shed")
    print(f"STAGE 4 - XAI Trace: {waterfall['xai_trace_path']}")
    print(f"Route validation: {list(route_check.keys())}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
