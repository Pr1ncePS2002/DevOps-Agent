from __future__ import annotations


def advise_plan(*, action: str, environments: list[str], post_steps: list[str]) -> list[str]:
    """MVP stub.

    Later: use embeddings + vector search to validate against SOP/playbooks.
    """

    warnings: list[str] = []
    if "production" in environments:
        warnings.append("Production environment selected: ensure change window and approvals.")
    if action == "unknown":
        warnings.append("Could not confidently classify action. Review plan carefully.")
    if "run_tests" not in post_steps:
        warnings.append("No tests requested. Consider adding run_tests.")

    return warnings
