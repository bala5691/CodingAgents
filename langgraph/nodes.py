import json
import subprocess
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from model_router import ModelRouter
from state import AgentState
from workspace_tools import build_workspace_tools
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
        HumanMessage(content=state["request"])])

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
    workspace_path = state["workspace_path"]
    iteration = (state.get("iteration", 0) + 1)

    # Build filesystem tools restricted to this project.
    tools, changed_files = (build_workspace_tools(workspace_path))
    tools_by_name = {tool.name: tool for tool in tools}

    # Get Qwen3-Coder
    model = router.get_client("implementation")
    model_with_tools = (model.bind_tools(tools))

    # Previous QA / Review feedback
    visual_qa = state.get( "visual_qa", "",)
    local_review = state.get("local_review", "")
    frontier_review = state.get("frontier_review", "")

    messages = [SystemMessage(content="""
        You are acting as the implementation agent.
        You are working directly against a real project workspace.

        IMPORTANT RULES:
        1. Inspect the project before making changes.
        2. Use list_files to understand the current structure.
        3. Use read_file before modifying an existing file.
        4. Use write_file to create or update source files.
        5. Never return the complete source code in the final response.
        6. Actually modify the project using the provided tools.
        7. Do not invent files that you have not inspected when modifying an existing application.
        8. Preserve existing working functionality unless the requirements explicitly require changing it.
        9. Incorporate previous QA and review feedback.
        10. Keep the implementation production-quality.
        11. Do not write outside the project workspace.
        12. When the implementation is complete, stop calling tools and return a concise summary of:
            - what was implemented
            - important architectural decisions
            - files changed
            - anything still requiring attention

        When creating a new application, ensure that all files needed to
        build and start the application are created.

        Examples include, where applicable:
        - package.json
        - source files
        - configuration
        - entry points
        - styles
        - application components

        Do not merely explain what should be written.
        You MUST use write_file to make the changes.
        """),
        HumanMessage(content=f"""
        ORIGINAL REQUEST
        ================
        {state["request"]}

        IMPLEMENTATION PLAN
        ===================
        {state["plan"]}

        DESIGN
        ======
        {state["design"]}

        PROJECT WORKSPACE
        =================
        {workspace_path}

        PREVIOUS VISUAL QA
        ==================
        {visual_qa or "No previous visual QA feedback."}

        PREVIOUS LOCAL REVIEW
        =====================
        {local_review or "No previous local review feedback."}

        PREVIOUS FRONTIER REVIEW
        ========================
        {frontier_review or "No previous frontier review feedback."}

        CURRENT ITERATION
        =================
        {iteration}

        Please inspect the workspace and implement the requested changes
        directly in the project.
        """)
    ]

    # Tool-calling loop
    # Prevent model getting stuck forever calling tools.
    MAX_TOOL_ROUNDS = 40
    final_summary = ""

    for round_number in range(MAX_TOOL_ROUNDS):
        response = (model_with_tools.invoke(messages))
        messages.append(response)
        tool_calls = getattr(response, "tool_calls", None)

        # No tool calls means coder considers work done.
        if not tool_calls:
            final_summary = (response.content if isinstance(response.content, str) else str(response.content))
            break

        # Execute requested tools
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})
            tool_call_id = tool_call["id"]
            tool = tools_by_name.get(tool_name)

            if tool is None:
                result = (f"ERROR: unknown tool {tool_name}")
            else:
                try:
                    result = tool.invoke( tool_args)
                except Exception as exc:
                    result = (f"ERROR executing {tool_name}: {type(exc).__name__}: {exc}")

            messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
    else:
        raise RuntimeError(f"Implementation agent exceeded {MAX_TOOL_ROUNDS} tool rounds.")

    # Validate that code was actually changed.
    changed = sorted(changed_files)

    if not changed:
        raise RuntimeError("Implementation agent completed without creating or modifying any files.")


    return {
        "implementation": final_summary,
        "changed_files": changed,
        "workspace_path": workspace_path,
        "iteration": iteration,
        "local_review": "",
        "frontier_review": "",
        "local_review_passed": False,
        "frontier_review_passed": False,
        "visual_qa_passed": False
    }
    
    
# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------
def validation_node(state: AgentState,) -> dict:
    workspace = state["workspace_path"]
    commands = [["npm", "install"], ["npm", "run", "build"]]
    logs = []

    for command in commands:
        process = subprocess.run(command, cwd=workspace, capture_output=True, text=True, timeout=300)
        logs.append(f"""
            COMMAND:
            {" ".join(command)}
            STDOUT:
            {process.stdout}
            STDERR:
            {process.stderr}
            """)

        if process.returncode != 0:
            return {"build_passed": False, "build_feedback": "\n".join(logs)}

    return {"build_passed": True, "build_feedback": "\n".join(logs)}


# ---------------------------------------------------------
# RENDER / EXECUTE
# ---------------------------------------------------------
def render_node(state: AgentState) -> dict:
    # screenshots = capture_application_screenshots(state["implementation"])
    screenshots = capture_application_screenshots(
        workspace_path=state["workspace_path"],
        routes={
            "home": "/",
            "dashboard": "/dashboard",
            # "tickets": "/tickets",
        })
    return { "screenshots": screenshots }


def capture_application_screenshots(workspace_path: str, routes: dict[str, str] | None = None) -> list[str]:
    workspace = Path(workspace_path).resolve()
    screenshot_dir = (workspace / ".qa" / "screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    routes = routes or {"home": "/"}
    app_url = "http://127.0.0.1:3000"

    # subprocess.run(["npm", "install"], cwd=workspace, check=True)
    # subprocess.run(["npm", "run", "build"], cwd=workspace, check=True)
    server = subprocess.Popen(["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "3000"], cwd=workspace)

    try:
        wait_for_server(app_url)
        screenshots = []
        viewports = {
            "desktop": {"width": 1440, "height": 900},
            "mobile": {"width": 390, "height": 844},
        }

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for device_name, viewport in viewports.items():
                context = browser.new_context(viewport=viewport)
                page = context.new_page()
                
                # Login to app before taking screen shot
                # page.goto(f"{app_url}/login")
                # page.fill('[name="email"]', "qa@example.com")
                # page.fill('[name="password"]', "test-password")
                # page.click('button[type="submit"]')
                # page.wait_for_url("**/dashboard")
                # page.screenshot(path="dashboard.png", full_page=True)

                for page_name, route in routes.items():
                    page.goto( f"{app_url}{route}", wait_until="networkidle")
                    screenshot_path = (screenshot_dir / f"{page_name}-{device_name}.png")
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    screenshots.append(str(screenshot_path))

                context.close()
            browser.close()
        return screenshots
    finally:
        server.terminate()
        server.wait(timeout=10)


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
        
        PREVIOUS BUILD / VALIDATION RESULT
        ==================================
        {state["build_feedback"]}

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