from state import AgentState


def route_after_visual_qa(state: AgentState) -> str:
    if state.get("visual_qa_passed"):
        return "review"

    if state.get("iteration", 0) >= state.get( "max_iterations", 3):
        return "final"

    return "retry"


def route_after_review(state: AgentState) -> str:
    both_approved = (state.get("local_review_passed", False) and state.get("frontier_review_passed", False))

    if both_approved:
        return "final"

    if state.get("iteration", 0) >= state.get("max_iterations", 3):
        return "final"

    return "retry"