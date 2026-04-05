"""
workflow.py — NewsGenie Agent Workflow
Compiles the agent and provides a run_agent() helper used by both
the Streamlit UI and the Jupyter notebook.
"""

from agents import create_news_agent

# ── Singleton agent (shared across Streamlit reruns via module cache) ──────────
_agent = None


def get_agent():
    """Return the shared agent instance (lazy init)."""
    global _agent
    if _agent is None:
        _agent = create_news_agent()
    return _agent


def run_agent(user_message: str, thread_id: str = "default") -> dict:
    """
    Run the NewsGenie agent for a given user message.

    Args:
        user_message: The user's query
        thread_id:    Conversation thread ID for multi-turn memory

    Returns:
        dict with keys:
            - response:    Final text response from the agent
            - tools_used:  List of tool names the agent called
            - tool_inputs: List of tool input dicts
    """
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {"messages": [{"role": "user", "content": user_message}]}
    result = agent.invoke(inputs, config=config)

    # Extract the final AI message
    messages = result.get("messages", [])
    response_text = ""
    tools_used = []
    tool_inputs = []

    for msg in messages:
        # AIMessage with tool_calls → record tool usage
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tools_used.append(tc["name"])
                tool_inputs.append(tc.get("args", {}))
        # Final AI response (no tool calls)
        elif hasattr(msg, "content") and msg.content and hasattr(msg, "type") and msg.type == "ai":
            response_text = msg.content

    # Fallback: last message content
    if not response_text and messages:
        last = messages[-1]
        response_text = last.content if hasattr(last, "content") else str(last)

    return {
        "response": response_text,
        "tools_used": tools_used,
        "tool_inputs": tool_inputs,
    }


def reset_agent():
    """Reset the agent (clears memory)."""
    global _agent
    _agent = None


if __name__ == "__main__":
    print("NewsGenie Agentic System — Interactive Mode")
    print("=" * 50)
    print("Type 'quit' to exit, 'reset' to clear memory\n")

    thread = "cli-session"
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "reset":
            reset_agent()
            print("Agent memory cleared.\n")
            continue

        result = run_agent(user_input, thread_id=thread)
        if result["tools_used"]:
            print(f"[Tools used: {', '.join(result['tools_used'])}]")
        print(f"\nNewsGenie: {result['response']}\n")
