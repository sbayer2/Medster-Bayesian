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

    # Build info section with mode indicator (always show mode)
    mode_line = f"{Colors.DIM}  Reasoning Mode: {Colors.CYAN}{mode.upper()}{Colors.DIM} - {mode_desc}{Colors.ENDC}"

    info = f"""
{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}
{Colors.DIM}  Powered by: Claude Sonnet 4.5 + Coherent FHIR + MCP Medical Server{Colors.ENDC}
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
