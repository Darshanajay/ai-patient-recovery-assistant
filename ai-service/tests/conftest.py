"""Small dependency shims let unit tests run without a local Ollama server.
The production requirements install real LangGraph and Ollama packages."""
import sys
import types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import langgraph.graph  # noqa: F401
except ImportError:
    langgraph = types.ModuleType("langgraph")
    graph_module = types.ModuleType("langgraph.graph")
    END = "__END__"

    class _CompiledGraph:
        def __init__(self, nodes, entry, edges):
            self.nodes, self.entry, self.edges = nodes, entry, edges
        def invoke(self, initial):
            state = dict(initial)
            current = self.entry
            visited = 0
            while current != END:
                state.update(self.nodes[current](state) or {})
                current = next((b for a, b in self.edges if a == current), END)
                visited += 1
                if visited > len(self.nodes) + 2:
                    raise RuntimeError("Test graph cycle detected")
            return state

    class StateGraph:
        def __init__(self, _state_type):
            self.nodes, self.edges, self.entry = {}, [], None
        def add_node(self, name, fn): self.nodes[name] = fn
        def set_entry_point(self, name): self.entry = name
        def add_edge(self, a, b): self.edges.append((a, b))
        def compile(self): return _CompiledGraph(self.nodes, self.entry, self.edges)

    graph_module.StateGraph = StateGraph
    graph_module.END = END
    langgraph.graph = graph_module
    sys.modules["langgraph"] = langgraph
    sys.modules["langgraph.graph"] = graph_module

try:
    import ollama  # noqa: F401
except ImportError:
    ollama = types.ModuleType("ollama")
    def _unavailable(*args, **kwargs):
        raise RuntimeError("Ollama is not running in unit tests")
    ollama.chat = _unavailable
    sys.modules["ollama"] = ollama
