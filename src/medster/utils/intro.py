import os
from medster.utils.ui import Colors
from medster.prompts import ACTIVE_PROMPTS


def print_intro():
    """Print the Medster ASCII art and introduction with mode indicator."""

    ascii_art = f"""
{Colors.CYAN}{Colors.BOLD}
 ███╗   ███╗███████╗██████╗ ███████╗████████╗███████╗██████╗
 ████╗ ████║██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
 ██╔████╔██║█████╗  ██║  ██║███████╗   ██║   █████╗  ██████╔╝
 ██║╚██╔╝██║██╔══╝  ██║  ██║╚════██║   ██║   ██╔══╝  ██╔══██╗
 ██║ ╚═╝ ██║███████╗██████╔╝███████║   ██║   ███████╗██║  ██║
 ╚═╝     ╚═╝╚══════╝╚═════╝ ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
{Colors.ENDC}
"""

    # Determine subtitle based on mode
    mode = ACTIVE_PROMPTS["mode"]
    mode_desc = ACTIVE_PROMPTS.get("description", "")

    if mode == "bayesian":
        subtitle = f"{Colors.DIM}Autonomous Clinical Case Analysis Agent {Colors.CYAN}[BAYESIAN MODE]{Colors.ENDC}"
    else:
        subtitle = f"{Colors.DIM}Autonomous Clinical Case Analysis Agent{Colors.ENDC}"

    # Detect LLM provider and model
    provider = os.getenv("LLM_PROVIDER", "claude").lower()
    if provider == "openai":
        llm_model = os.getenv("LLM_MODEL", "gpt-5.1")
        # Only show reasoning effort for GPT-5.x models (not GPT-4.x)
        if llm_model in ["gpt-5.1", "gpt-5"]:
            reasoning_effort = os.getenv("REASONING_EFFORT", "none")
            llm_info = f"{llm_model.upper()} (reasoning: {reasoning_effort})"
        else:
            llm_info = llm_model.upper()
    else:
        llm_model = os.getenv("LLM_MODEL", "claude-sonnet-4.5")
        llm_info = "Claude Sonnet 4.5"

    # Build info section with mode indicator (always show mode)
    mode_line = f"{Colors.DIM}  Reasoning Mode: {Colors.CYAN}{mode.upper()}{Colors.DIM} - {mode_desc}{Colors.ENDC}"
    llm_line = f"{Colors.DIM}  Powered by: {Colors.GREEN}{llm_info}{Colors.DIM} + Coherent FHIR + MCP Medical Server{Colors.ENDC}"

    info = f"""
{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}
{llm_line}
{Colors.DIM}  Primary Use Case: Clinical Case Analysis{Colors.ENDC}
{mode_line}
{Colors.DIM}  Type 'exit' or 'quit' to end session{Colors.ENDC}
{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}

{Colors.YELLOW}⚠  DISCLAIMER: For research and educational purposes only.{Colors.ENDC}
{Colors.YELLOW}   Not for clinical decision-making without physician review.{Colors.ENDC}
"""

    print(ascii_art)
    print(subtitle)
    print(info)
