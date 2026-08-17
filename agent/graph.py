import os
from dotenv import load_dotenv
load_dotenv()

# LangSmith tracing — reads from .env automatically
os.environ["LANGCHAIN_TRACING_V2"]  = os.getenv("LANGSMITH_TRACING", "false")
os.environ["LANGCHAIN_API_KEY"]      = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"]      = os.getenv("LANGSMITH_PROJECT", "housing-allocation-system")
os.environ["LANGCHAIN_ENDPOINT"]     = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
from langgraph.graph import StateGraph, END
from agent.state import HousingAgentState
from agent.nodes import (
    load_request_node,
    validate_request_node,
    search_rooms_node,
    score_compatibility_node,
    assign_room_node,
    handle_unresolved_node,
    handle_on_hold_node,
    send_notification_node
)

# ─────────────────────────────────────────────
# CONDITIONAL EDGE FUNCTIONS
# These decide which node to go to next
# ─────────────────────────────────────────────

def decide_after_validation(state: HousingAgentState) -> str:
    if state["status"] == "on_hold":
        return "on_hold"
    elif state["status"] == "rejected":
        return "notify"
    else:
        return "search_rooms"


def decide_after_assignment(state: HousingAgentState) -> str:
    if state["status"] == "allocated":
        return "notify"
    elif state["status"] == "retry" and state["attempts"] < 3:
        return "search_rooms"
    else:
        return "unresolved"


def decide_after_unresolved(state: HousingAgentState) -> str:
    return "notify"


def decide_after_on_hold(state: HousingAgentState) -> str:
    return "notify"


# ─────────────────────────────────────────────
# BUILD THE GRAPH
# ─────────────────────────────────────────────

def build_housing_agent():
    graph = StateGraph(HousingAgentState)

    # Add all nodes
    graph.add_node("load_request",       load_request_node)
    graph.add_node("validate_request",   validate_request_node)
    graph.add_node("search_rooms",       search_rooms_node)
    graph.add_node("score_compatibility", score_compatibility_node)
    graph.add_node("assign_room",        assign_room_node)
    graph.add_node("handle_unresolved",  handle_unresolved_node)
    graph.add_node("handle_on_hold",     handle_on_hold_node)
    graph.add_node("send_notification",  send_notification_node)

    # Entry point
    graph.set_entry_point("load_request")

    # Simple edges — always go to next node
    graph.add_edge("load_request",        "validate_request")
    graph.add_edge("search_rooms",        "score_compatibility")
    graph.add_edge("score_compatibility", "assign_room")

    # Conditional edges — decide based on state
    graph.add_conditional_edges(
        "validate_request",
        decide_after_validation,
        {
            "search_rooms": "search_rooms",
            "on_hold":      "handle_on_hold",
            "notify":       "send_notification"
        }
    )

    graph.add_conditional_edges(
        "assign_room",
        decide_after_assignment,
        {
            "notify":       "send_notification",
            "search_rooms": "search_rooms",
            "unresolved":   "handle_unresolved"
        }
    )

    graph.add_conditional_edges(
        "handle_unresolved",
        decide_after_unresolved,
        {
            "notify": "send_notification"
        }
    )

    graph.add_conditional_edges(
        "handle_on_hold",
        decide_after_on_hold,
        {
            "notify": "send_notification"
        }
    )

    # End
    graph.add_edge("send_notification", END)

    return graph.compile()


# Single instance of the compiled agent
housing_agent = build_housing_agent()