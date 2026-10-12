"""
Simulation Runner for Phase 3.
Orchestrates dual execution on CPUSimulator and PIMSimulator,
followed by automated semantic verification via CorrectnessComparator.
"""
from typing import Dict, Any, Optional, List
from .cpu_simulator import CPUSimulator
from .pim_simulator import PIMSimulator
from .correctness_comparator import CorrectnessComparator


class SimulationRunner:
    """
    Coordinates CPU and PIM simulation passes and verifies correctness.
    """

    def __init__(self, max_steps: int = 50000):
        self.cpu_sim = CPUSimulator(max_steps=max_steps)
        self.pim_sim = PIMSimulator(max_steps=max_steps)
        self.comparator = CorrectnessComparator()

    def run(
        self,
        ir_instructions: List[Dict[str, Any]],
        mapped_instructions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes both CPU and PIM simulations and runs the correctness comparator.
        """
        # 1. Run CPU Simulator
        cpu_res = self.cpu_sim.run(ir_instructions)

        # 2. Run PIM Simulator
        pim_res = self.pim_sim.run(mapped_instructions)

        # 3. Compare Results
        comp_res = self.comparator.compare(cpu_res, pim_res)

        return {
            "cpu": cpu_res,
            "pim": pim_res,
            "comparison": comp_res
        }
