from langgraph.graph import END, START, StateGraph

from nodes import *
from routing import (route_after_review, route_after_visual_qa)
from state import AgentState


def build_graph():
    graph = StateGraph(AgentState)

    # --------------------------------------------------
    # Nodes
    # --------------------------------------------------
    graph.add_node("planning", planning_node)
    graph.add_node("design", design_node)
    graph.add_node("implementation", implementation_node)
    graph.add_node("validation", validation_node)
    graph.add_node("render", render_node)
    graph.add_node("visual_qa", visual_qa_node)
    graph.add_node("review_dispatch", review_dispatch_node)
    graph.add_node("review_local", local_review_node)
    graph.add_node("review_frontier", frontier_review_node)
    graph.add_node("review_gate", review_gate_node)
    graph.add_node("final", final_node)

    # --------------------------------------------------
    # Main pipeline
    # --------------------------------------------------
    graph.add_edge(START, "planning")
    graph.add_edge("planning", "design")
    graph.add_edge("design", "implementation")
    graph.add_edge("implementation", "validation")
    graph.add_conditional_edges("validation_qa", route_after_validation_qas,
        {
            "retry": "implementation",
            "review": "render",
            "final": "final",
        })
    # graph.add_edge("validation", "render")
    graph.add_edge("render", "visual_qa")

    # --------------------------------------------------
    # Visual QA decision
    # --------------------------------------------------
    graph.add_conditional_edges("visual_qa", route_after_visual_qa,
        {
            "retry": "implementation",
            "review": "review_dispatch",
            "final": "final",
        })

    # --------------------------------------------------
    # PARALLEL REVIEW
    # --------------------------------------------------
    graph.add_edge("review_dispatch", "review_local")
    graph.add_edge("review_dispatch", "review_frontier")

    # review_gate executes only after both finish.
    graph.add_edge(["review_local", "review_frontier"], "review_gate")

    # --------------------------------------------------
    # Review decision
    # --------------------------------------------------
    graph.add_conditional_edges("review_gate", route_after_review,
        {
            "retry": "implementation",
            "final": "final",
        })
    graph.add_edge("final", END)

    return graph.compile()


app = build_graph()