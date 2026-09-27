import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.anomaly.dummy_detector import DummyAnomalyDetector
from agents.anomaly.models import AnomalyType, AnomalyResult


def print_separator(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_dummy_detector():
    print_separator("Person 3 Mid-Sem Anomaly Detector Unit Test")

    detector = DummyAnomalyDetector()
    results = detector.detect()

    # Test 1: Count
    assert len(results) == 6, f"Expected 6 dummy records, got {len(results)}"
    print("[PASS] Dataset loaded successfully (6 items).")

    # Test 2: Source check
    for item in results:
        assert item.source == "dummy", f"Expected source 'dummy', got {item.source}"
        assert item.anomaly_id is not None
        assert item.agent_id is not None
        assert item.action_type is not None
        assert 0.0 <= item.anomaly_score <= 1.0
    print("[PASS] Every record contains required fields with source='dummy'.")

    # Test 3: Normal cases (Case 1, 3, 5)
    normals = [r for r in results if not r.is_anomaly]
    assert len(normals) == 3, f"Expected 3 normal records, got {len(normals)}"
    for n in normals:
        assert n.anomaly_type == AnomalyType.NORMAL
    print("[PASS] Normal records return is_anomaly=False and anomaly_type=NORMAL.")

    # Test 4: Anomalous cases (Case 2, 4, 6)
    anomalies = [r for r in results if r.is_anomaly]
    assert len(anomalies) == 3, f"Expected 3 anomalous records, got {len(anomalies)}"
    print("[PASS] Anomalous records identified (3 total).")

    # Test 5: Specific scenario verification
    travel_spike = next(r for r in results if r.anomaly_type == AnomalyType.SPENDING_SPIKE)
    assert travel_spike.agent_id == "travel-agent-01"
    assert travel_spike.amount == 25000.0
    assert travel_spike.is_anomaly is True
    print(f"[PASS] Spending Spike verified: {travel_spike.agent_id} Rs.{travel_spike.amount} (score: {travel_spike.anomaly_score})")

    servicing_burst = next(r for r in results if r.anomaly_type == AnomalyType.RAPID_ACTION_BURST)
    assert servicing_burst.agent_id == "servicing-agent-01"
    assert servicing_burst.is_anomaly is True
    print(f"[PASS] Rapid Action Burst verified: {servicing_burst.agent_id} {servicing_burst.action_type} (score: {servicing_burst.anomaly_score})")

    rewards_unauth = next(r for r in results if r.anomaly_type == AnomalyType.UNAUTHORIZED_ACTION)
    assert rewards_unauth.agent_id == "rewards-agent-01"
    assert rewards_unauth.action_type == "cash_withdrawal"
    assert rewards_unauth.is_anomaly is True
    print(f"[PASS] Unauthorized Action verified: {rewards_unauth.agent_id} {rewards_unauth.action_type} (score: {rewards_unauth.anomaly_score})")

    # Test 6: Agent filtering
    servicing_feed = detector.get_dummy_feed(agent_id="servicing-agent-01")
    assert len(servicing_feed) == 2
    assert all(item.agent_id == "servicing-agent-01" for item in servicing_feed)
    print(f"[PASS] Agent ID filtering verified (servicing-agent-01 returned {len(servicing_feed)} records).")

    print_separator("All Mid-Sem Dummy Anomaly Detector Tests Passed Successfully!")


if __name__ == "__main__":
    test_dummy_detector()
