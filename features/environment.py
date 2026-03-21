"""Behave environment configuration."""
import subprocess
import shutil


def before_all(context):
    """Check if Ollama is available before running any scenarios."""
    context.ollama_available = shutil.which("ollama") is not None
    if context.ollama_available:
        try:
            result = subprocess.run(
                ["ollama", "list"], capture_output=True, timeout=5
            )
            context.ollama_available = result.returncode == 0
        except Exception:
            context.ollama_available = False


def before_scenario(context, scenario):
    """Skip scenarios that require unavailable resources."""
    if "requires-ollama" in scenario.tags and not context.ollama_available:
        scenario.skip("Ollama not available")
    if "slow" in scenario.tags and not context.config.userdata.get("slow", False):
        scenario.skip("Slow test — run with -D slow=true")
