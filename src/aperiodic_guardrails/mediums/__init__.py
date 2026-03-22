"""AST medium registry for the zero-knowledge executor."""
from aperiodic_guardrails.mediums.web_scraper import build_web_scraper_ast
from aperiodic_guardrails.mediums.graph_solver import build_graph_solver_ast
from aperiodic_guardrails.mediums.tot_solver import build_tot_solver_ast

REGISTRY = {
    "web_scraper": build_web_scraper_ast,
    "graph_solver": build_graph_solver_ast,
    "tot_solver": build_tot_solver_ast,
}

def get_medium(name: str):
    if name not in REGISTRY:
        raise ValueError(f"Unknown medium '{name}'. Available: {list(REGISTRY.keys())}")
    return REGISTRY[name]
