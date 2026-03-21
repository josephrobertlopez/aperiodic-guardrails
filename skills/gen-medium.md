---
name: gen-medium
description: Generate a new AST medium template for the ZK executor PoC
user_invocable: true
arguments: name of the new medium
---

# Generate ZK Executor Medium Template

You are generating a new AST medium template for the guardrail impossibility PoC.

## Rules

1. Every medium is a single Python file in `poc/mediums/`
2. It exports one function: `build_<name>_ast() -> ast.Module`
3. The function uses `ast.parse(source)` on a clean source string — NOT manual ast.XXX() construction
4. The source string defines a `run(**params) -> result` function
5. **ZERO domain content** — no hardcoded URLs, compound names, targets, or any content that reveals what the medium operates on
6. All content enters via `run()` parameters at runtime from the encrypted config
7. Keep it minimal — under 150 lines

## Pattern

Every medium follows this exact pattern:

```python
"""AST template: <one-line description>. Zero domain content."""
import ast


def build_<name>_ast() -> ast.Module:
    source = '''
<imports>

def run(<params>):
    <logic using only params — no hardcoded content>
    return <results>
'''
    tree = ast.parse(source)
    ast.fix_missing_locations(tree)
    return tree
```

## Existing mediums for reference

- `web_scraper.py` — `run(endpoint, query, selector)` → fetches URL, parses HTML, returns titles
- `graph_solver.py` — `run(initial_state, target, rules, constraints)` → BFS over state graph
- `tot_solver.py` — `run(initial_state, target, rules, constraints, model)` → beam search + Ollama LLM evaluation

## Workflow

1. Ask user: what should this medium do? (in abstract terms — "fetch an API", "solve a constraint problem", "traverse a graph with heuristic X")
2. Ask user: what parameters does `run()` take?
3. Generate the medium file
4. Register it in `poc/mediums/__init__.py` by adding the import and REGISTRY entry
5. Generate an example config JSON the user can encode with `encode_config.py`

## After generating

Print:
```
[gen-medium] Created: poc/mediums/<name>.py (<N> lines)
[gen-medium] Registered in: poc/mediums/__init__.py
[gen-medium] Example config:
<json>
[gen-medium] Encode: echo '<json>' | python poc/encode_config.py --stdin config.b64
[gen-medium] Run:    python poc/engine.py config.b64
```

## Important

- Use `ast.parse(source)` — never manual `ast.XXX()` node construction
- The source string must contain NO domain-specific content
- All values come from `run()` params which come from the encrypted config
- If the medium needs an LLM, use Ollama via `urllib.request` (see tot_solver.py)
- Delegate code generation to GPU gateway or Ollama — do not write the source string yourself if it's complex
