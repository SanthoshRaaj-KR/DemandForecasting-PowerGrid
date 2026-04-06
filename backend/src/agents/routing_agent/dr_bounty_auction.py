"""
DR Bounty Micro-Auctions: Game-Theoretic Demand Response
========================================================

FEATURE #4: Game-Theoretic DR Bounties (Micro-Auctions)

Industry Standard Problem:
- Demand-Response (DR) usually pays a flat, static fee to factories
- No price discovery, no competition, inefficient allocation

Our Enhancement:
- Localized Reverse-Auction when deficit hits
- ProsumerAgents (EVs, Factories, Smart Homes) bid against each other
- Each prosumer calculates their own "pain threshold"
- System clears the cheapest bids first
- Creates micro-economy that rewards efficiency

This implements a truthful mechanism design where prosumers have
incentive to bid their true cost (second-price-like clearing).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random


class ProsumerType(Enum):
    """Types of prosumers that can participate in DR auctions."""
    EV_FLEET = "ev_fleet"
    FACTORY = "factory"
    SMART_HOME = "smart_home"
    COLD_STORAGE = "cold_storage"
    COMMERCIAL_HVAC = "commercial_hvac"
    DATA_CENTER = "data_center"


@dataclass
class Prosumer:
    """A prosumer that can participate in DR auctions."""
    id: str
    type: ProsumerType
    state: str
    max_capacity_mw: float
    min_bid_price_inr: float  # Minimum price they'll accept to curtail
    flexibility_hours: int  # How long they can curtail
    priority_score: float = 1.0  # Higher = more essential (hospitals=10, homes=1)


@dataclass
class DRBid:
    """A bid in the DR micro-auction."""
    prosumer_id: str
    prosumer_type: ProsumerType
    state: str
    offered_mw: float
    bid_price_inr_per_mw: float
    duration_hours: int
    timestamp: float = 0.0


@dataclass
class AuctionClearingResult:
    """Result of clearing a DR micro-auction."""
    state: str
    deficit_mw_requested: float
    deficit_mw_fulfilled: float
    clearing_price_inr: float
    total_cost_inr: float
    accepted_bids: List[DRBid]
    rejected_bids: List[DRBid]
    savings_vs_flat_rate_inr: float
    prosumer_breakdown: Dict[str, float]  # By type


@dataclass
class AuctionRound:
    """A complete auction round with all states."""
    round_id: str
    timestamp: str
    state_results: Dict[str, AuctionClearingResult]
    total_deficit_resolved_mw: float
    total_cost_inr: float
    average_clearing_price_inr: float


class DRBountyAuction:
    """
    Implements Game-Theoretic DR Bounties via Reverse Micro-Auctions.
    
    Auction Mechanism:
    1. State broadcasts deficit amount
    2. Prosumers submit sealed bids (price to curtail)
    3. Bids sorted by price (lowest first)
    4. Accept bids until deficit is met
    5. All winners paid at CLEARING PRICE (highest accepted bid)
       This is like a second-price auction - incentivizes truthful bidding
    
    Economic Properties:
    - Truthful: Prosumers bid their true cost (no gaming)
    - Efficient: Lowest-cost curtailment selected first
    - Fair: All winners receive same price (no discrimination)
    """
    
    # Benchmark flat rate for comparison (industry standard)
    FLAT_RATE_INR_PER_MW = 8.0
    
    # Price caps to prevent gouging
    MIN_BID_PRICE = 1.0  # INR/MW
    MAX_BID_PRICE = 20.0  # INR/MW (cap to prevent price spikes)
    
    def __init__(self) -> None:
        self.prosumer_registry: Dict[str, Prosumer] = {}
        self.auction_history: List[AuctionRound] = []
        self._initialize_default_prosumers()
    
    def _initialize_default_prosumers(self) -> None:
        """Initialize default prosumer population for each state."""
        states = ["UP", "Bihar", "WB", "Karnataka"]
        
        prosumer_templates = [
            (ProsumerType.EV_FLEET, 5.0, 15.0, 3.0, 4, 2.0),
            (ProsumerType.FACTORY, 20.0, 50.0, 5.0, 2, 5.0),
            (ProsumerType.SMART_HOME, 0.5, 2.0, 2.0, 6, 1.0),
            (ProsumerType.COLD_STORAGE, 8.0, 20.0, 4.0, 3, 3.0),
            (ProsumerType.COMMERCIAL_HVAC, 10.0, 30.0, 4.5, 2, 4.0),
            (ProsumerType.DATA_CENTER, 15.0, 40.0, 7.0, 1, 8.0),
        ]
        
        for state in states:
            for i, (p_type, min_cap, max_cap, min_price, flex, priority) in enumerate(prosumer_templates):
                # Create multiple prosumers of each type
                for j in range(3):  # 3 of each type per state
                    prosumer_id = f"{state}_{p_type.value}_{j}"
                    capacity = random.uniform(min_cap, max_cap)
                    price = random.uniform(min_price, min_price + 3.0)
                    
                    self.prosumer_registry[prosumer_id] = Prosumer(
                        id=prosumer_id,
                        type=p_type,
                        state=state,
                        max_capacity_mw=capacity,
                        min_bid_price_inr=price,
                        flexibility_hours=flex,
                        priority_score=priority,
                    )
    
    def register_prosumer(self, prosumer: Prosumer) -> None:
        """Register a prosumer for auction participation."""
        self.prosumer_registry[prosumer.id] = prosumer
    
    def _generate_bids_for_state(
        self, 
        state: str, 
        deficit_mw: float,
        urgency_multiplier: float = 1.0,
    ) -> List[DRBid]:
        """
        Generate bids from prosumers in a state.
        
        In a real system, prosumers would submit their own bids.
        Here we simulate their bidding behavior based on:
        - Their minimum acceptable price
        - Market conditions (urgency multiplier)
        - Random variation (information asymmetry)
        """
        bids = []
        
        for prosumer in self.prosumer_registry.values():
            if prosumer.state != state:
                continue
            
            # Prosumer decides whether to participate
            # Higher urgency = more likely to participate
            participation_prob = 0.6 + (0.3 * urgency_multiplier)
            if random.random() > participation_prob:
                continue
            
            # Calculate bid price (based on true cost + small markup)
            # Truthful mechanism means they bid close to true cost
            true_cost = prosumer.min_bid_price_inr
            information_noise = random.uniform(-0.5, 1.0)
            bid_price = max(
                self.MIN_BID_PRICE,
                min(self.MAX_BID_PRICE, true_cost + information_noise)
            )
            
            # Offer capacity (may offer partial)
            offer_ratio = random.uniform(0.5, 1.0)
            offered_mw = prosumer.max_capacity_mw * offer_ratio
            
            bids.append(DRBid(
                prosumer_id=prosumer.id,
                prosumer_type=prosumer.type,
                state=state,
                offered_mw=offered_mw,
                bid_price_inr_per_mw=bid_price,
                duration_hours=prosumer.flexibility_hours,
            ))
        
        return bids
    
    def clear_auction(
        self,
        state: str,
        deficit_mw: float,
        bids: Optional[List[DRBid]] = None,
        urgency_multiplier: float = 1.0,
    ) -> AuctionClearingResult:
        """
        Clear a DR micro-auction for a single state.
        
        Clearing Algorithm:
        1. Sort bids by price (ascending)
        2. Accept bids until deficit is fulfilled
        3. Clearing price = highest accepted bid price
        4. All winners paid at clearing price (uniform pricing)
        
        Parameters
        ----------
        state : str
            State requesting DR
        deficit_mw : float
            Amount of deficit to fulfill
        bids : Optional[List[DRBid]]
            Pre-submitted bids (if None, generate from registry)
        urgency_multiplier : float
            Market urgency (1.0 = normal, 2.0 = emergency)
            
        Returns
        -------
        AuctionClearingResult
            Auction clearing result with accepted/rejected bids
        """
        if bids is None:
            bids = self._generate_bids_for_state(state, deficit_mw, urgency_multiplier)
        
        if not bids:
            return AuctionClearingResult(
                state=state,
                deficit_mw_requested=deficit_mw,
                deficit_mw_fulfilled=0.0,
                clearing_price_inr=0.0,
                total_cost_inr=0.0,
                accepted_bids=[],
                rejected_bids=[],
                savings_vs_flat_rate_inr=0.0,
                prosumer_breakdown={},
            )
        
        # Sort bids by price (lowest first)
        sorted_bids = sorted(bids, key=lambda b: b.bid_price_inr_per_mw)
        
        accepted: List[DRBid] = []
        rejected: List[DRBid] = []
        fulfilled_mw = 0.0
        clearing_price = 0.0
        
        for bid in sorted_bids:
            remaining_deficit = deficit_mw - fulfilled_mw
            
            if remaining_deficit <= 0:
                rejected.append(bid)
                continue
            
            # Accept bid (may be partially accepted)
            accepted_mw = min(bid.offered_mw, remaining_deficit)
            fulfilled_mw += accepted_mw
            clearing_price = bid.bid_price_inr_per_mw  # Highest accepted bid
            
            # Create accepted bid (with actual accepted MW)
            accepted_bid = DRBid(
                prosumer_id=bid.prosumer_id,
                prosumer_type=bid.prosumer_type,
                state=bid.state,
                offered_mw=accepted_mw,
                bid_price_inr_per_mw=bid.bid_price_inr_per_mw,
                duration_hours=bid.duration_hours,
            )
            accepted.append(accepted_bid)
        
        # Calculate total cost (uniform pricing at clearing price)
        total_cost = fulfilled_mw * clearing_price
        
        # Compare to flat rate
        flat_rate_cost = fulfilled_mw * self.FLAT_RATE_INR_PER_MW
        savings = flat_rate_cost - total_cost
        
        # Breakdown by prosumer type
        type_breakdown: Dict[str, float] = {}
        for bid in accepted:
            type_name = bid.prosumer_type.value
            type_breakdown[type_name] = type_breakdown.get(type_name, 0.0) + bid.offered_mw
        
        return AuctionClearingResult(
            state=state,
            deficit_mw_requested=deficit_mw,
            deficit_mw_fulfilled=fulfilled_mw,
            clearing_price_inr=clearing_price,
            total_cost_inr=total_cost,
            accepted_bids=accepted,
            rejected_bids=rejected,
            savings_vs_flat_rate_inr=savings,
            prosumer_breakdown=type_breakdown,
        )
    
    def run_auction_round(
        self,
        deficits_by_state: Dict[str, float],
        round_id: str = "",
        timestamp: str = "",
    ) -> AuctionRound:
        """
        Run a complete auction round for all deficit states.
        
        Parameters
        ----------
        deficits_by_state : Dict[str, float]
            Deficit MW by state (only states with deficit > 0 will auction)
        round_id : str
            Identifier for this auction round
        timestamp : str
            Timestamp for the round
            
        Returns
        -------
        AuctionRound
            Complete results for all state auctions
        """
        print("\n" + "💰" * 30)
        print("DR BOUNTY MICRO-AUCTION")
        print("💰" * 30)
        
        state_results: Dict[str, AuctionClearingResult] = {}
        total_resolved = 0.0
        total_cost = 0.0
        
        for state, deficit in deficits_by_state.items():
            if deficit <= 0:
                continue
            
            print(f"\n  [{state}] Deficit: {deficit:.0f} MW - Starting auction...")
            
            # Calculate urgency (higher deficit = more urgent)
            max_state_deficit = 200.0  # Baseline
            urgency = min(2.0, 1.0 + (deficit / max_state_deficit))
            
            result = self.clear_auction(state, deficit, urgency_multiplier=urgency)
            state_results[state] = result
            
            total_resolved += result.deficit_mw_fulfilled
            total_cost += result.total_cost_inr
            
            print(f"    Fulfilled: {result.deficit_mw_fulfilled:.0f} MW / {deficit:.0f} MW")
            print(f"    Clearing price: ₹{result.clearing_price_inr:.2f}/MW")
            print(f"    Total cost: ₹{result.total_cost_inr:,.0f}")
            print(f"    Savings vs flat rate: ₹{result.savings_vs_flat_rate_inr:,.0f}")
            print(f"    Accepted bids: {len(result.accepted_bids)}")
        
        avg_price = (total_cost / total_resolved) if total_resolved > 0 else 0.0
        
        round_result = AuctionRound(
            round_id=round_id or f"round_{timestamp}",
            timestamp=timestamp,
            state_results=state_results,
            total_deficit_resolved_mw=total_resolved,
            total_cost_inr=total_cost,
            average_clearing_price_inr=avg_price,
        )
        
        self.auction_history.append(round_result)
        
        print("\n" + "-" * 60)
        print("AUCTION ROUND SUMMARY")
        print("-" * 60)
        print(f"  Total resolved: {total_resolved:.0f} MW")
        print(f"  Total cost: ₹{total_cost:,.0f}")
        print(f"  Average clearing price: ₹{avg_price:.2f}/MW")
        print(f"  States auctioned: {list(state_results.keys())}")
        print("💰" * 30 + "\n")
        
        return round_result
    
    def export_auction_results(
        self,
        round_result: AuctionRound,
        output_dir: str = "outputs",
    ) -> str:
        """Export auction results to JSON for transparency and audit."""
        import json
        import os
        from datetime import datetime
        
        output = {
            "protocol": "DR Bounty Micro-Auctions",
            "mechanism": "Reverse Second-Price Auction (Uniform Clearing)",
            "metadata": {
                "round_id": round_result.round_id,
                "timestamp": round_result.timestamp,
                "generated_at": datetime.now().isoformat(),
            },
            "summary": {
                "total_deficit_resolved_mw": round_result.total_deficit_resolved_mw,
                "total_cost_inr": round_result.total_cost_inr,
                "average_clearing_price_inr": round_result.average_clearing_price_inr,
                "flat_rate_benchmark_inr": self.FLAT_RATE_INR_PER_MW,
            },
            "state_results": {},
            "economic_properties": {
                "mechanism_type": "Truthful (incentive-compatible)",
                "pricing_rule": "Uniform price at highest accepted bid",
                "efficiency": "Lowest-cost prosumers selected first",
            },
        }
        
        for state, result in round_result.state_results.items():
            output["state_results"][state] = {
                "deficit_requested_mw": result.deficit_mw_requested,
                "deficit_fulfilled_mw": result.deficit_mw_fulfilled,
                "fulfillment_rate_pct": (result.deficit_mw_fulfilled / result.deficit_mw_requested * 100) if result.deficit_mw_requested > 0 else 0,
                "clearing_price_inr": result.clearing_price_inr,
                "total_cost_inr": result.total_cost_inr,
                "savings_vs_flat_rate_inr": result.savings_vs_flat_rate_inr,
                "accepted_bids_count": len(result.accepted_bids),
                "rejected_bids_count": len(result.rejected_bids),
                "prosumer_breakdown": result.prosumer_breakdown,
            }
        
        os.makedirs(output_dir, exist_ok=True)
        filename = f"dr_auction_{round_result.timestamp or 'latest'}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        print(f"  [DR AUCTION] Results exported: {filepath}")
        return filepath
