from typing import TypedDict


class AgentState(TypedDict, total=False):
    # Input
    request: str
    name: str

    # Generated artifacts
    plan: str
    design: str
    
    # Real project location
    workspace_path: str
    
    # Files modified by Qwen3-Coder
    changed_files: list[str]
    
    # Coder's summary, NOT the entire codebase
    implementation: str
    
    build_passed: bool
    build_feedback: str

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