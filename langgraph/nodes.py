from langchain_core.messages import HumanMessage, SystemMessage

from model_router import ModelRouter
from state import AgentState
from utils import extract_json, image_to_data_uri, message_text


router = ModelRouter()

# ---------------------------------------------------------
# PLANNING
# ---------------------------------------------------------
def planning_node(state: AgentState) -> dict:
    response = router.invoke("planning", [
        SystemMessage(content="""
        You are the planning agent.

        Convert the user's request into a concrete software implementation plan.

        Identify:
        - functional requirements
        - non-functional requirements
        - components
        - dependencies
        - execution order
        - acceptance criteria
        - likely technical risks

        Do NOT write implementation code yet.
        """), 
        HumanMessage(content=state["request"])],
    )

    return { "plan": message_text(response), "iteration": state.get("iteration", 0) }


# ---------------------------------------------------------
# DESIGN
# ---------------------------------------------------------
def design_node(state: AgentState) -> dict:
    response = router.invoke("design", [
        SystemMessage(content="""
        You are the system/UI design agent.
        Using the approved planning document, produce the detailed design.

        Include where applicable:
        1. architecture
        2. modules/components
        3. API contracts
        4. data models
        5. UI component hierarchy
        6. state management
        7. error handling
        8. security considerations
        9. responsive design behavior
        10. implementation guidance for the coding agent

        Do not implement the complete application.
        """), 
        HumanMessage(content=f"""
        USER REQUEST:
        {state["request"]}

        IMPLEMENTATION PLAN:
        {state["plan"]}
        """)]
    )

    return { "design": message_text(response) }


# ---------------------------------------------------------
# IMPLEMENTATION
# ---------------------------------------------------------
def implementation_node(state: AgentState) -> dict:
    previous_qa = state.get("visual_qa", "")
    local_review = state.get("local_review", "")
    frontier_review = state.get("frontier_review", "")
    iteration = state.get("iteration", 0) + 1

    response = router.invoke("implementation", [
        SystemMessage(content="""
        You are the implementation agent.
        Produce production-quality code based on the supplied architecture.

        Requirements:
        - satisfy the original request
        - follow the design
        - keep modules maintainable
        - include error handling
        - avoid placeholders unless absolutely necessary
        - incorporate QA/reviewer feedback when provided
        - preserve working behavior while fixing requested problems

        Return the complete revised implementation.
        """), 
        HumanMessage(content=f"""
        ORIGINAL REQUEST
        ================
        {state["request"]}

        PLAN
        ====
        {state["plan"]}

        DESIGN
        ======
        {state["design"]}

        PREVIOUS VISUAL QA
        ==================
        {previous_qa or "No previous visual QA."}

        LOCAL REVIEW
        ============
        {local_review or "No previous local review."}

        FRONTIER REVIEW
        ===============
        {frontier_review or "No previous frontier review."}

        ITERATION
        =========
        {iteration}
        """)]
    )

    return {
        "implementation": message_text(response),
        "iteration": iteration,
        "local_review": "",
        "frontier_review": "",
        "local_review_passed": False,
        "frontier_review_passed": False,
    }


# ---------------------------------------------------------
# RENDER / EXECUTE
# ---------------------------------------------------------
def render_node(state: AgentState) -> dict:
    """
    Replace this function with your application sandbox.
    Typical workflow:

        implementation
             |
             v
        write files
             |
             v
        npm/pnpm install
             |
             v
        npm run build
             |
             v
        start app
             |
             v
        Playwright
             |
             v
        screenshot(s)

    The screenshot paths are then given to Qwen3-VL.
    """

    screenshots = capture_application_screenshots(state["implementation"])
    return { "screenshots": screenshots }


def capture_application_screenshots(implementation: str) -> list[str]:
    """
    Integrate your sandbox / coding environment here.
    Example return:
        [
            "/tmp/build/home-desktop.png",
            "/tmp/build/home-mobile.png",
            "/tmp/build/settings.png",
        ]
    """
    raise NotImplementedError("Connect this function to your build + Playwright sandbox.")


# ---------------------------------------------------------
# VISUAL QA
# ---------------------------------------------------------
def visual_qa_node(state: AgentState) -> dict:
    screenshots = state.get("screenshots", [])
    image_content = []

    for screenshot in screenshots:
        image_content.append({ "type": "image_url", "image_url": { "url": image_to_data_uri(screenshot) }})

    response = router.invoke("visual_qa", [
            SystemMessage(content="""
            You are the visual QA engineer.

            Evaluate the rendered application against:

            - original user request
            - design
            - layout correctness
            - clipping/overflow
            - spacing/alignment
            - typography
            - responsive behavior
            - missing UI elements
            - broken elements
            - inconsistent styling
            - visual regressions

            Return ONLY JSON:
            {
            "passed": true,
            "score": 0-100,
            "issues": [
                {
                "severity": "critical|major|minor",
                "description": "...",
                "recommended_fix": "..."
                }
            ],
            "summary": "..."
            }

            Set passed=false if a critical or major issue needs another
            implementation iteration.
            """
            ),
            HumanMessage(content=[{"type": "text", "text": f"""
            ORIGINAL REQUEST:
            {state["request"]}

            DESIGN:
            {state["design"]}
            """}, 
            *image_content ])
        ]
    )

    raw = message_text(response)
    result = extract_json(raw)

    return { "visual_qa": raw, "visual_qa_passed": bool(result.get("passed", False)) }


# ---------------------------------------------------------
# LOCAL REVIEW
# GPT-OSS -> DeepSeek fallback
# ---------------------------------------------------------

def local_review_node(state: AgentState) -> dict:
    response = router.invoke("review_local", [
        SystemMessage(content="""
        You are a senior software reviewer.
        Review the implementation for:
        - correctness
        - architecture
        - maintainability
        - security
        - error handling
        - concurrency issues
        - edge cases
        - requirement coverage
        - unnecessary complexity
        - probable runtime defects

        Return ONLY JSON:
        {
            "passed": true,
            "score": 0-100,
            "blocking_issues": [],
            "non_blocking_issues": [],
            "recommended_changes": [],
            "summary": "..."
        }
        """), 
        HumanMessage(content=f"""
        REQUEST
        =======
        {state["request"]}

        PLAN
        ====
        {state["plan"]}

        DESIGN
        ======
        {state["design"]}

        IMPLEMENTATION
        ==============
        {state["implementation"]}

        VISUAL QA
        =========
        {state["visual_qa"]}
        """)]
    )

    raw = message_text(response)
    result = extract_json(raw)

    return { "local_review": raw, "local_review_passed": bool(result.get("passed", False))}


# ---------------------------------------------------------
# FRONTIER REVIEW
# ---------------------------------------------------------

def frontier_review_node(state: AgentState) -> dict:
    response = router.invoke("review_frontier", [
        SystemMessage(content="""
        Act as the final independent engineering reviewer.

        You have not participated in planning or implementation.

        Look aggressively for mistakes the other agents may have missed.

        Check:

        - requirements
        - logical correctness
        - integration problems
        - architecture
        - security
        - maintainability
        - implementation completeness
        - visual QA findings

        Return ONLY JSON:

        {
        "passed": true,
        "confidence": 0-100,
        "blocking_issues": [],
        "recommended_changes": [],
        "summary": "..."
        }
        """),
        HumanMessage(content=f"""
        ORIGINAL REQUEST:
        {state["request"]}

        DESIGN:
        {state["design"]}

        IMPLEMENTATION:
        {state["implementation"]}

        VISUAL QA:
        {state["visual_qa"]}
        """)]
    )

    raw = message_text(response)
    result = extract_json(raw)
    return { "frontier_review": raw, "frontier_review_passed": bool(result.get("passed", False)) }


# ---------------------------------------------------------
# NO-OP DISPATCH NODE
# ---------------------------------------------------------

def review_dispatch_node(state: AgentState) -> dict:
    """
    Enables fan-out to the two review paths.
    """
    return {}


# ---------------------------------------------------------
# REVIEW GATE
# ---------------------------------------------------------

def review_gate_node(state: AgentState) -> dict:
    passed = (state.get("local_review_passed", False) and state.get("frontier_review_passed", False))
    return { "status": "approved" if passed else "rework" }


# ---------------------------------------------------------
# FINAL
# ---------------------------------------------------------

def final_node(state: AgentState) -> dict:
    approved = (state.get("visual_qa_passed", False) and state.get("local_review_passed", False) and state.get("frontier_review_passed", False))

    if approved:
        status = "completed"
    else:
        status = "completed_with_review_warnings"

    return { "status": status, "final_output": state["implementation"] }