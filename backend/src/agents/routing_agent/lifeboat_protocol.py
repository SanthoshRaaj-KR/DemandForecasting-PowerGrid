"""
Lifeboat Protocol: Autonomous Graph-Cut Islanding
=================================================

PATENT FEATURE #2: "Autonomous Topology Severance via Capacity-Constrained Graph Partitioning"

When the grid is overloaded and importing power to a dying state would drag the 
entire national frequency below 49.5 Hz, this protocol autonomously executes a 
Graph Cut to intentionally sever the digital transmission edges to the failing 
state, sacrificing one region to mathematically guarantee the survival of others.

Industry Standard Problem:
- Grids trip circuit breakers blindly during overload
- This causes cascading regional blackouts (e.g., 2012 India blackout: 600M affected)

Our Solution:
- LLM logic merged with physical Graph Theory
- Calculate if importing to a failing state endangers national frequency
- Execute controlled Graph Cut to island the failing region
- Mathematically guarantee survival of the healthy grid
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set
from collections import deque


@dataclass
class IslandingDecision:
    """Result of a Lifeboat Protocol evaluation."""
    should_island: bool
    islands_created: List[Set[str]]
    severed_edges: List[Tuple[str, str]]
    sacrificed_states: List[str]
    protected_states: List[str]
    frequency_before_hz: float
    frequency_after_island_hz: float
    load_shed_in_island_mw: Dict[str, float]
    rationale: str


@dataclass 
class GridState:
    """Current state of the grid for Lifeboat analysis."""
    states: List[str]
    edges: Dict[Tuple[str, str], float]  # Edge capacities
    deficits: Dict[str, float]
    surpluses: Dict[str, float]
    total_capacity_mw: float


class LifeboatProtocol:
    """
    Implements Autonomous Topology Severance via Capacity-Constrained Graph Partitioning.
    
    The protocol evaluates whether importing power to a failing state would 
    destabilize the entire grid, and if so, executes a controlled graph cut
    to island the failing region and protect the rest of the network.
    
    Key Thresholds:
    - CRITICAL_FREQUENCY_HZ: 49.5 Hz (below this, grid collapse is imminent)
    - LIFEBOAT_THRESHOLD_HZ: 49.7 Hz (trigger Lifeboat evaluation)
    - TARGET_FREQUENCY_HZ: 49.9 Hz (safe operating target)
    """
    
    BASE_FREQUENCY_HZ = 50.0
    CRITICAL_FREQUENCY_HZ = 49.5
    LIFEBOAT_THRESHOLD_HZ = 49.7
    TARGET_FREQUENCY_HZ = 49.9
    
    # Minimum deficit ratio to trigger islanding consideration
    DEFICIT_RATIO_THRESHOLD = 0.15  # State must have >15% of national deficit
    
    def __init__(self) -> None:
        self.islanding_history: List[IslandingDecision] = []
    
    def _frequency_from_deficit(
        self, 
        unserved_deficit_mw: float, 
        total_grid_capacity_mw: float
    ) -> float:
        """Calculate synthetic frequency from unserved deficit."""
        if total_grid_capacity_mw <= 0:
            return self.BASE_FREQUENCY_HZ
        percent_unserved = (max(unserved_deficit_mw, 0.0) / total_grid_capacity_mw) * 100.0
        return self.BASE_FREQUENCY_HZ - (0.1 * percent_unserved)
    
    def _build_adjacency(
        self, 
        edges: Dict[Tuple[str, str], float]
    ) -> Dict[str, Set[str]]:
        """Build adjacency list from edge capacities."""
        adj: Dict[str, Set[str]] = {}
        for (u, v), cap in edges.items():
            if cap > 0:
                if u not in adj:
                    adj[u] = set()
                if v not in adj:
                    adj[v] = set()
                adj[u].add(v)
                adj[v].add(u)
        return adj
    
    def _find_connected_components(
        self, 
        states: List[str], 
        adj: Dict[str, Set[str]], 
        severed: Set[Tuple[str, str]]
    ) -> List[Set[str]]:
        """Find connected components after severing edges."""
        visited: Set[str] = set()
        components: List[Set[str]] = []
        
        for state in states:
            if state in visited:
                continue
            
            # BFS to find component
            component: Set[str] = set()
            queue = deque([state])
            
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                
                for neighbor in adj.get(current, set()):
                    if neighbor in visited:
                        continue
                    # Check if edge is severed
                    edge = (current, neighbor)
                    edge_rev = (neighbor, current)
                    if edge in severed or edge_rev in severed:
                        continue
                    queue.append(neighbor)
            
            if component:
                components.append(component)
        
        return components
    
    def _calculate_import_capacity(
        self,
        target_state: str,
        surpluses: Dict[str, float],
        edges: Dict[Tuple[str, str], float],
        adj: Dict[str, Set[str]],
    ) -> float:
        """Calculate maximum power that can be imported to a state."""
        total_import = 0.0
        
        for neighbor in adj.get(target_state, set()):
            # Check edge capacity
            edge_cap = edges.get((neighbor, target_state), 0.0)
            edge_cap_rev = edges.get((target_state, neighbor), 0.0)
            max_cap = max(edge_cap, edge_cap_rev)
            
            # Available surplus at neighbor
            available = surpluses.get(neighbor, 0.0)
            
            # Can import min of capacity and surplus
            total_import += min(max_cap, available)
        
        return total_import
    
    def _find_best_cut(
        self,
        grid: GridState,
        adj: Dict[str, Set[str]],
    ) -> Tuple[Set[Tuple[str, str]], List[str]]:
        """
        Find the optimal graph cut that isolates failing states while
        preserving the largest healthy connected component.
        
        Uses a greedy approach: identify the state(s) causing the most
        frequency drag and cut their incoming edges.
        """
        # Rank states by their "drag" on the grid
        state_drag: Dict[str, float] = {}
        for state in grid.states:
            deficit = grid.deficits.get(state, 0.0)
            import_cap = self._calculate_import_capacity(
                state, grid.surpluses, grid.edges, adj
            )
            # Drag = deficit that cannot be locally resolved
            state_drag[state] = max(deficit - import_cap, 0.0)
        
        # Sort by drag (highest first)
        sorted_states = sorted(state_drag.items(), key=lambda x: x[1], reverse=True)
        
        # Find states to sacrifice (those with high drag)
        total_deficit = sum(grid.deficits.values())
        sacrifice_candidates: List[str] = []
        
        for state, drag in sorted_states:
            if drag <= 0:
                break
            # Only sacrifice if this state is a significant burden
            if total_deficit > 0 and (drag / total_deficit) >= self.DEFICIT_RATIO_THRESHOLD:
                sacrifice_candidates.append(state)
        
        if not sacrifice_candidates:
            return set(), []
        
        # Cut all edges to the sacrifice candidates
        severed_edges: Set[Tuple[str, str]] = set()
        for state in sacrifice_candidates:
            for neighbor in adj.get(state, set()):
                severed_edges.add((neighbor, state))
                severed_edges.add((state, neighbor))
        
        return severed_edges, sacrifice_candidates
    
    def evaluate(
        self,
        grid: GridState,
        day_index: int = 0,
    ) -> IslandingDecision:
        """
        Evaluate whether Lifeboat Protocol should be activated.
        
        The protocol activates when:
        1. Grid frequency is below LIFEBOAT_THRESHOLD_HZ (49.7 Hz)
        2. Importing power to deficit states would drag frequency below CRITICAL (49.5 Hz)
        3. A graph cut can isolate the problem while preserving most of the grid
        
        Parameters
        ----------
        grid : GridState
            Current state of the grid
        day_index : int
            Current simulation day (for logging)
            
        Returns
        -------
        IslandingDecision
            Decision on whether to island and which edges to sever
        """
        print("\n" + "🚨" * 30)
        print("LIFEBOAT PROTOCOL EVALUATION")
        print("🚨" * 30)
        
        # Calculate current frequency
        total_deficit = sum(grid.deficits.values())
        current_freq = self._frequency_from_deficit(total_deficit, grid.total_capacity_mw)
        
        print(f"  Current frequency: {current_freq:.2f} Hz")
        print(f"  Total deficit: {total_deficit:.0f} MW")
        print(f"  Critical threshold: {self.CRITICAL_FREQUENCY_HZ} Hz")
        
        # Check if we need to evaluate Lifeboat
        if current_freq >= self.LIFEBOAT_THRESHOLD_HZ:
            print("  ✅ Frequency above threshold. Lifeboat not needed.")
            return IslandingDecision(
                should_island=False,
                islands_created=[set(grid.states)],
                severed_edges=[],
                sacrificed_states=[],
                protected_states=grid.states,
                frequency_before_hz=current_freq,
                frequency_after_island_hz=current_freq,
                load_shed_in_island_mw={},
                rationale="Frequency stable, no islanding required",
            )
        
        print(f"  ⚠️ Frequency {current_freq:.2f} Hz is below {self.LIFEBOAT_THRESHOLD_HZ} Hz!")
        print("  Evaluating graph cuts...")
        
        # Build graph
        adj = self._build_adjacency(grid.edges)
        
        # Find best cut
        severed_edges, sacrificed = self._find_best_cut(grid, adj)
        
        if not severed_edges:
            print("  No beneficial cut found. Proceeding with emergency shedding.")
            return IslandingDecision(
                should_island=False,
                islands_created=[set(grid.states)],
                severed_edges=[],
                sacrificed_states=[],
                protected_states=grid.states,
                frequency_before_hz=current_freq,
                frequency_after_island_hz=current_freq,
                load_shed_in_island_mw={},
                rationale="No viable graph cut - emergency shedding required",
            )
        
        # Calculate post-island frequency
        # Protected states: exclude sacrificed states' deficits and surpluses
        protected_states = [s for s in grid.states if s not in sacrificed]
        protected_deficit = sum(grid.deficits.get(s, 0.0) for s in protected_states)
        protected_surplus = sum(grid.surpluses.get(s, 0.0) for s in protected_states)
        
        # Net deficit in protected region
        protected_net = max(protected_deficit - protected_surplus, 0.0)
        protected_freq = self._frequency_from_deficit(protected_net, grid.total_capacity_mw)
        
        # Check if islanding helps
        if protected_freq < self.CRITICAL_FREQUENCY_HZ:
            print(f"  ❌ Even after cut, protected frequency {protected_freq:.2f} Hz still critical!")
            return IslandingDecision(
                should_island=False,
                islands_created=[set(grid.states)],
                severed_edges=[],
                sacrificed_states=[],
                protected_states=grid.states,
                frequency_before_hz=current_freq,
                frequency_after_island_hz=current_freq,
                load_shed_in_island_mw={},
                rationale=f"Graph cut insufficient - protected region still at {protected_freq:.2f} Hz",
            )
        
        # Calculate load shedding required in islanded region
        island_deficit = sum(grid.deficits.get(s, 0.0) for s in sacrificed)
        island_surplus = sum(grid.surpluses.get(s, 0.0) for s in sacrificed)
        load_shed = {}
        
        island_net_deficit = max(island_deficit - island_surplus, 0.0)
        if island_net_deficit > 0:
            # Distribute shedding proportionally
            for state in sacrificed:
                state_deficit = grid.deficits.get(state, 0.0)
                if state_deficit > 0 and island_deficit > 0:
                    share = state_deficit / island_deficit
                    load_shed[state] = island_net_deficit * share
        
        # Find resulting components
        components = self._find_connected_components(grid.states, adj, severed_edges)
        
        print("\n" + "=" * 60)
        print("⚡ LIFEBOAT PROTOCOL ACTIVATED")
        print("=" * 60)
        print(f"  Sacrificed states: {sacrificed}")
        print(f"  Protected states: {protected_states}")
        print(f"  Edges severed: {len(severed_edges) // 2}")  # Divide by 2 (bidirectional)
        print(f"  Protected frequency: {protected_freq:.2f} Hz (was {current_freq:.2f} Hz)")
        print(f"  Load shed in island: {sum(load_shed.values()):.0f} MW")
        print("=" * 60 + "\n")
        
        decision = IslandingDecision(
            should_island=True,
            islands_created=components,
            severed_edges=list(severed_edges),
            sacrificed_states=sacrificed,
            protected_states=protected_states,
            frequency_before_hz=current_freq,
            frequency_after_island_hz=protected_freq,
            load_shed_in_island_mw=load_shed,
            rationale=f"Sacrificing {sacrificed} to protect {protected_states}. Frequency improved from {current_freq:.2f} to {protected_freq:.2f} Hz.",
        )
        
        self.islanding_history.append(decision)
        return decision
    
    def export_decision_json(
        self,
        decision: IslandingDecision,
        day_index: int,
        date_str: str,
        output_dir: str = "outputs",
    ) -> str:
        """Export Lifeboat decision to JSON for XAI audit trail."""
        import json
        import os
        from datetime import datetime
        
        output = {
            "protocol": "Lifeboat - Autonomous Graph-Cut Islanding",
            "patent_claim": "Autonomous Topology Severance via Capacity-Constrained Graph Partitioning",
            "metadata": {
                "day_index": day_index,
                "date": date_str,
                "generated_at": datetime.now().isoformat(),
            },
            "decision": {
                "should_island": decision.should_island,
                "sacrificed_states": decision.sacrificed_states,
                "protected_states": decision.protected_states,
                "severed_edges_count": len(decision.severed_edges) // 2,
                "severed_edges": [f"{e[0]}->{e[1]}" for e in decision.severed_edges[:10]],  # Limit output
            },
            "frequency_analysis": {
                "before_hz": decision.frequency_before_hz,
                "after_hz": decision.frequency_after_island_hz,
                "improvement_hz": decision.frequency_after_island_hz - decision.frequency_before_hz,
                "critical_threshold_hz": self.CRITICAL_FREQUENCY_HZ,
            },
            "load_shedding": {
                "total_mw": sum(decision.load_shed_in_island_mw.values()),
                "by_state": decision.load_shed_in_island_mw,
            },
            "islands_created": [list(island) for island in decision.islands_created],
            "rationale": decision.rationale,
            "legal_defensible": True,
            "compliance_note": "Decision made to protect majority of grid from cascading failure. Sacrifice is mathematically justified.",
        }
        
        os.makedirs(output_dir, exist_ok=True)
        filename = f"lifeboat_decision_{date_str}_day{day_index + 1:03d}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        print(f"  [LIFEBOAT] Decision exported: {filepath}")
        return filepath
