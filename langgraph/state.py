from typing import TypedDict


class AgentState(TypedDict, total=False):
    # Input
    request: str

    # Generated artifacts
    plan: str
    design: str
    workspace_path: str
    changed_files: list[str]
    # implementation: str

    # Visual execution
    screenshots: list[str]

    # QA
    visual_qa: str
    visual_qa_passed: bool

    # Parallel reviews
    local_review: str
    local_review_passed: bool

    frontier_review: str
    frontier_review_passed: bool

    # Loop control
    iteration: int
    max_iterations: int

    # Final result
    status: str
    final_output: str