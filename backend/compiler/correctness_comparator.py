"""
Correctness Comparator for CPU vs PIM Simulation.
Verifies semantic equivalence between host CPU execution and mixed PIM/CPU execution:
- Final return values
- Scalar variable states
- Array buffer contents
- Standard I/O output streams
Produces an authoritative PASS, FAIL, or ERROR verdict with granular discrepancy analysis.
"""
from typing import Dict, Any, List, Optional


class CorrectnessComparator:
    """
    Compares the execution outputs of CPUSimulator and PIMSimulator.
    Validates that PIM offloading preserved the program semantics.
    """

    def compare(
        self,
        cpu_result: Dict[str, Any],
        pim_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Performs comprehensive semantic validation between CPU and PIM simulation results.
        Returns a structured verdict with discrepancy explanations.
        """
        cpu_status = cpu_result.get("status", "UNKNOWN")
        pim_status = pim_result.get("status", "UNKNOWN")

        discrepancies: List[str] = []

        # 1. Error / Failure handling
        if cpu_status == "ERROR" or pim_status == "ERROR":
            if cpu_status == "ERROR" and pim_status == "ERROR":
                # Both faulted (e.g. division by zero or index out of bounds)
                return {
                    "verdict": "PASS",
                    "is_match": True,
                    "status": "PASS",
                    "reason": "Both CPU and PIM environments detected the runtime fault consistently.",
                    "discrepancies": [],
                    "summary": {
                        "return_value_match": True,
                        "variables_match": True,
                        "arrays_match": True,
                        "output_match": True,
                        "cpu_status": cpu_status,
                        "pim_status": pim_status,
                        "cpu_error": cpu_result.get("error"),
                        "pim_error": pim_result.get("error")
                    },
                    "cpu_steps": cpu_result.get("total_steps", 0),
                    "pim_steps": pim_result.get("total_steps", 0)
                }
            else:
                faulting = "CPU" if cpu_status == "ERROR" else "PIM"
                err_msg = cpu_result.get("error") if cpu_status == "ERROR" else pim_result.get("error")
                discrepancies.append(f"{faulting} execution encountered runtime error: {err_msg}")
                return {
                    "verdict": "ERROR",
                    "is_match": False,
                    "status": "ERROR",
                    "reason": f"Execution divergence: {faulting} halted with error while the other completed.",
                    "discrepancies": discrepancies,
                    "summary": {
                        "return_value_match": False,
                        "variables_match": False,
                        "arrays_match": False,
                        "output_match": False,
                        "cpu_status": cpu_status,
                        "pim_status": pim_status,
                        "cpu_error": cpu_result.get("error"),
                        "pim_error": pim_result.get("error")
                    },
                    "cpu_steps": cpu_result.get("total_steps", 0),
                    "pim_steps": pim_result.get("total_steps", 0)
                }

        # 2. Return Value Comparison
        cpu_ret = cpu_result.get("return_value")
        pim_ret = pim_result.get("return_value")
        return_value_match = (cpu_ret == pim_ret)
        if not return_value_match:
            discrepancies.append(f"Return value mismatch: CPU returned {cpu_ret}, PIM returned {pim_ret}")

        # 3. Scalar Variables Comparison
        cpu_vars = cpu_result.get("final_variables", {})
        pim_vars = pim_result.get("final_variables", {})
        all_var_keys = sorted(set(cpu_vars.keys()) | set(pim_vars.keys()))
        var_diffs: Dict[str, Dict[str, Any]] = {}
        for key in all_var_keys:
            v_cpu = cpu_vars.get(key)
            v_pim = pim_vars.get(key)
            if v_cpu != v_pim:
                var_diffs[key] = {"cpu": v_cpu, "pim": v_pim}
                discrepancies.append(f"Variable '{key}' mismatch: CPU={v_cpu}, PIM={v_pim}")

        variables_match = (len(var_diffs) == 0)

        # 4. Arrays Comparison
        cpu_arrs = cpu_result.get("final_arrays", {})
        pim_arrs = pim_result.get("final_arrays", {})
        all_arr_keys = sorted(set(cpu_arrs.keys()) | set(pim_arrs.keys()))
        arr_diffs: Dict[str, Dict[str, Any]] = {}
        for key in all_arr_keys:
            a_cpu = cpu_arrs.get(key, [])
            a_pim = pim_arrs.get(key, [])
            if a_cpu != a_pim:
                arr_diffs[key] = {"cpu": a_cpu, "pim": a_pim}
                discrepancies.append(f"Array '{key}' content mismatch: CPU={a_cpu}, PIM={a_pim}")

        arrays_match = (len(arr_diffs) == 0)

        # 5. Output Stream Comparison
        cpu_out = cpu_result.get("output", [])
        pim_out = pim_result.get("output", [])
        output_match = (cpu_out == pim_out)
        if not output_match:
            discrepancies.append(f"Standard output mismatch: CPU emitted {cpu_out}, PIM emitted {pim_out}")

        # 6. Overall Verdict
        is_match = return_value_match and variables_match and arrays_match and output_match
        verdict = "PASS" if is_match else "FAIL"

        return {
            "verdict": verdict,
            "is_match": is_match,
            "status": verdict,
            "reason": "All execution results, memory states, and output streams match identically." if is_match else f"{len(discrepancies)} semantic discrepancies detected.",
            "discrepancies": discrepancies,
            "summary": {
                "return_value_match": return_value_match,
                "variables_match": variables_match,
                "arrays_match": arrays_match,
                "output_match": output_match,
                "cpu_status": cpu_status,
                "pim_status": pim_status,
                "variable_differences": var_diffs,
                "array_differences": arr_diffs,
                "cpu_steps": cpu_result.get("total_steps", 0),
                "pim_steps": pim_result.get("total_steps", 0),
                "pim_in_situ_steps": pim_result.get("pim_steps", 0),
                "pim_cpu_fallback_steps": pim_result.get("cpu_steps", 0)
            }
        }
