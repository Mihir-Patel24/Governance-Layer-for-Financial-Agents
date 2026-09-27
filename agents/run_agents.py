"""
Entrypoint wrapper for running the Governance Layer Agent Simulation.
Delegates to run_simulation.py for unified execution and data export.
"""

from agents.run_simulation import run_full_simulation

if __name__ == "__main__":
    run_full_simulation()
