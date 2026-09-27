from enum import Enum
from typing import List, Dict, Any


class ScenarioType(str, Enum):
    NORMAL = "NORMAL"
    SPENDING_SPIKE = "SPENDING_SPIKE"
    BURST = "BURST"
    POLICY_LIMIT_ATTEMPT = "POLICY_LIMIT_ATTEMPT"


class ScenarioGenerator:
    """
    Deterministic scenario generator for synthetic action streams across
    Travel, Servicing, and Rewards agents.
    """

    @staticmethod
    def get_travel_scenario(scenario_type: ScenarioType) -> List[Dict[str, Any]]:
        if scenario_type == ScenarioType.NORMAL:
            return [
                {
                    "action_type": "book_flight",
                    "amount": 8000.0,
                    "recipient": {"id": "indigo-air", "category": "airline"},
                    "description": "Domestic flight booking to Mumbai",
                    "context": {"location": "IN-MH", "cabin": "economy"}
                },
                {
                    "action_type": "book_hotel",
                    "amount": 5000.0,
                    "recipient": {"id": "taj-hotels", "category": "hotel"},
                    "description": "2-night stay at Taj Mumbai",
                    "context": {"location": "IN-MH"}
                },
                {
                    "action_type": "cancel_booking",
                    "amount": 0.0,
                    "recipient": {"id": "indigo-air", "category": "airline"},
                    "description": "Cancellation of previous flight booking",
                    "context": {"reason": "schedule_change"}
                }
            ]

        elif scenario_type == ScenarioType.SPENDING_SPIKE:
            return [
                {
                    "action_type": "book_flight",
                    "amount": 6000.0,
                    "recipient": {"id": "air-india", "category": "airline"},
                    "description": "Standard domestic travel flight"
                },
                {
                    "action_type": "book_flight",
                    "amount": 25000.0,  # Sudden spike exceeding ₹15,000 limit
                    "recipient": {"id": "emirates", "category": "airline"},
                    "description": "Luxury first-class international travel booking",
                    "context": {"flag": "high_value_spike"}
                }
            ]

        elif scenario_type == ScenarioType.BURST:
            return [
                {
                    "action_type": "book_flight",
                    "amount": 4000.0,
                    "description": f"Rapid flight reservation request #{i+1}",
                    "recipient": {"id": f"carrier-{i+1}", "category": "airline"}
                }
                for i in range(5)
            ]

        elif scenario_type == ScenarioType.POLICY_LIMIT_ATTEMPT:
            return [
                {
                    "action_type": "book_flight",
                    "amount": 99000.0,  # Far exceeds single_tx_limit
                    "description": "Extreme spending transaction attempt"
                },
                {
                    "action_type": "unauthorized_crypto_purchase",
                    "amount": 1000.0,  # Disallowed action type
                    "description": "Unauthorized crypto action attempt"
                }
            ]

        return []

    @staticmethod
    def get_servicing_scenario(scenario_type: ScenarioType) -> List[Dict[str, Any]]:
        if scenario_type == ScenarioType.NORMAL:
            return [
                {
                    "action_type": "fee_reversal",
                    "amount": 500.0,
                    "description": "Monthly maintenance fee reversal for customer",
                    "context": {"customer_tier": "gold"}
                },
                {
                    "action_type": "issue_credit",
                    "amount": 300.0,
                    "description": "Customer service inconvenience credit",
                    "context": {"ticket_id": "TICK-9082"}
                },
                {
                    "action_type": "update_address",
                    "amount": 0.0,
                    "description": "Update primary customer mailing address",
                    "context": {"city": "Bangalore", "pincode": "560001"}
                }
            ]

        elif scenario_type == ScenarioType.BURST:
            return [
                {
                    "action_type": "fee_reversal",
                    "amount": 500.0,
                    "description": f"Rapid sequential fee reversal #{i+1}",
                    "context": {"burst_sequence": i+1}
                }
                for i in range(5)
            ]

        elif scenario_type == ScenarioType.SPENDING_SPIKE:
            return [
                {
                    "action_type": "fee_reversal",
                    "amount": 200.0,
                    "description": "Minor fee reversal"
                },
                {
                    "action_type": "issue_credit",
                    "amount": 8000.0,  # Exceeds servicing limit of ₹1,000
                    "description": "Unusual massive credit issuance"
                }
            ]

        elif scenario_type == ScenarioType.POLICY_LIMIT_ATTEMPT:
            return [
                {
                    "action_type": "wire_transfer",
                    "amount": 500.0,  # Unauthorized action for servicing agent
                    "description": "Attempted unauthorized wire transfer via servicing portal"
                }
            ]

        return []

    @staticmethod
    def get_rewards_scenario(scenario_type: ScenarioType) -> List[Dict[str, Any]]:
        if scenario_type == ScenarioType.NORMAL:
            return [
                {
                    "action_type": "redeem_points",
                    "amount": 0.0,
                    "description": "Redeem 5,000 reward points for Amazon voucher",
                    "context": {"points_redeemed": 5000, "catalog_item": "AMZN-VOUCHER-500"}
                },
                {
                    "action_type": "transfer_points",
                    "amount": 0.0,
                    "description": "Transfer 2,000 points to partner frequent flyer account",
                    "context": {"points_transferred": 2000, "partner": "AirIndia-FlyingReturn"}
                },
                {
                    "action_type": "apply_reward",
                    "amount": 0.0,
                    "description": "Apply 10% cash discount reward code on transaction",
                    "context": {"reward_code": "PROMO10"}
                }
            ]

        elif scenario_type == ScenarioType.BURST:
            return [
                {
                    "action_type": "redeem_points",
                    "amount": 0.0,
                    "description": f"Rapid reward points redemption #{i+1}",
                    "context": {"sequence": i+1, "points": 1000}
                }
                for i in range(4)
            ]

        elif scenario_type == ScenarioType.SPENDING_SPIKE:
            return [
                {
                    "action_type": "apply_reward",
                    "amount": 12000.0,  # Exceeds registered rewards limit of ₹5,000
                    "description": "Apply large cashback reward exceeding single limit"
                }
            ]

        elif scenario_type == ScenarioType.POLICY_LIMIT_ATTEMPT:
            return [
                {
                    "action_type": "cash_withdrawal",
                    "amount": 2000.0,  # Unauthorized action for rewards agent
                    "description": "Attempted cash withdrawal using rewards agent profile"
                }
            ]

        return []
