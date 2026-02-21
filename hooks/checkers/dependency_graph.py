"""Dependency graph builder for incremental test intelligence.

Parses Python import statements to build a reverse dependency graph,
then uses it to identify which test files are affected when a source
file changes. This enables smarter test running — only execute tests
whose inputs have actually changed.

Uses a TTL-based file cache to avoid re-scanning and re-parsing the
entire project on every edit.
"""

from __future__ import annotations

import ast
import hashlib
import json
import tempfile
import time
from pathlib import Path

from _util import is_test_file

_CACHE_TTL_SECONDS = 30
_SKIP_DIRS = {".venv", "venv", "node_modules", "__pycache__", ".git", "dist", "build"}


def parse_python_imports(file_path: Path) -> set[str]:
    """Extract top-level module names imported by a Python file.

    Uses AST parsing for accuracy (ignores comments and strings).
    Returns a set of module name strings. For relative imports,
    returns the dotted form (e.g., ".utils", "..config").
    """
    if not file_path.exists():
        return set()

    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, OSError):
        return set()

    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                prefix = "." * (node.level or 0)
                imports.add(f"{prefix}{node.module}")
            elif node.level:
                # "from .. import X" with no module
                imports.add("." * node.level)

    return imports


def _module_to_stem(module_name: str) -> str | None:
    """Convert a module name to its likely file stem.

    "os.path" -> "path"
    "utils" -> "utils"
    ".utils" -> "utils"
    "pkg.core" -> "core"
    """
    # Strip leading dots (relative imports)
    cleaned = module_name.lstrip(".")
    if not cleaned:
        return None
    # Take the last component
    parts = cleaned.split(".")
    return parts[-1] if parts else None


def _collect_py_files(project_root: Path) -> list[Path]:
    """Collect all Python files, skipping noise directories."""
    py_files: list[Path] = []
    for py_file in project_root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in py_file.parts):
            continue
        py_files.append(py_file)
    return py_files


def _cache_path(project_root: Path) -> Path:
    """Get cache file path for a project root."""
    root_hash = hashlib.md5(str(project_root.resolve()).encode()).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f"sf-dep-graph-{root_hash}.json"


def _load_cache(project_root: Path) -> tuple[dict[str, set[str]], dict[str, list[Path]]] | None:
    """Load cached graph and test index if still fresh (within TTL).

    Returns (graph, test_index) or None if cache is stale/missing.
    """
    cache_file = _cache_path(project_root)
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text())
        if time.time() - data.get("ts", 0) > _CACHE_TTL_SECONDS:
            return None

        graph = {k: set(v) for k, v in data["graph"].items()}
        test_index = {k: [Path(p) for p in v] for k, v in data["test_index"].items()}
        return graph, test_index
    except (json.JSONDecodeError, OSError, KeyError, TypeError):
        return None


def _save_cache(
    project_root: Path,
    graph: dict[str, set[str]],
    test_index: dict[str, list[Path]],
) -> None:
    """Save graph and test index to temp-file cache."""
    try:
        data = {
            "ts": time.time(),
            "graph": {k: sorted(v) for k, v in graph.items()},
            "test_index": {k: [str(p) for p in v] for k, v in test_index.items()},
        }
        _cache_path(project_root).write_text(json.dumps(data))
    except OSError:
        pass


def _build_graph_from_files(py_files: list[Path]) -> dict[str, set[str]]:
    """Build a reverse import graph from a pre-collected list of Python files."""
    graph: dict[str, set[str]] = {}
    for py_file in py_files:
        file_stem = py_file.stem
        imports = parse_python_imports(py_file)
        for imp in imports:
            dep_stem = _module_to_stem(imp)
            if dep_stem is None:
                continue
            if dep_stem not in graph:
                graph[dep_stem] = set()
            graph[dep_stem].add(file_stem)
    return graph


def build_import_graph(project_root: Path) -> dict[str, set[str]]:
    """Build a reverse dependency graph for Python files.

    Returns a dict mapping module stems to sets of module stems
    that depend on (import from) them.

    Example: {"utils": {"app", "service"}} means app.py and
    service.py both import from utils.py.
    """
    return _build_graph_from_files(_collect_py_files(project_root))


def _build_test_index(py_files: list[Path]) -> dict[str, list[Path]]:
    """Build a stem-to-test-files index from a pre-collected file list."""
    index: dict[str, list[Path]] = {}
    for py_file in py_files:
        if is_test_file(py_file):
            stem = py_file.stem
            if stem not in index:
                index[stem] = []
            index[stem].append(py_file)
    return index


def _get_graph_and_index(
    project_root: Path,
) -> tuple[dict[str, set[str]], dict[str, list[Path]]]:
    """Get import graph and test index, using cache when possible.

    On cache hit (within TTL), returns immediately without scanning
    the filesystem or parsing any ASTs.
    """
    cached = _load_cache(project_root)
    if cached is not None:
        return cached

    py_files = _collect_py_files(project_root)
    graph = _build_graph_from_files(py_files)
    test_index = _build_test_index(py_files)

    _save_cache(project_root, graph, test_index)
    return graph, test_index


def find_affected_tests(
    changed_file: Path,
    *,
    project_root: Path | None = None,
    max_depth: int = 10,
) -> list[Path]:
    """Find test files affected by a change to the given source file.

    Traverses the reverse dependency graph from the changed file
    outward, collecting any test files encountered.

    If the changed file is itself a test file, it returns that file.
    """
    if not changed_file.exists():
        return []

    root = project_root or changed_file.parent

    # If the changed file is a test, return it directly
    if is_test_file(changed_file):
        return [changed_file]

    graph, test_index = _get_graph_and_index(root)
    changed_stem = changed_file.stem

    # BFS traversal through reverse dependencies
    visited: set[str] = set()
    queue: list[str] = [changed_stem]
    test_files: list[Path] = []
    depth = 0

    while queue and depth < max_depth:
        next_queue: list[str] = []
        for stem in queue:
            if stem in visited:
                continue
            visited.add(stem)

            dependents = graph.get(stem, set())
            for dep in dependents:
                if dep not in visited:
                    next_queue.append(dep)
                    # Look up test files from the pre-built index
                    test_files.extend(test_index.get(dep, []))

        queue = next_queue
        depth += 1

    # Also check for conventional test file for the changed module
    test_files.extend(test_index.get(f"test_{changed_stem}", []))

    # Deduplicate
    seen: set[str] = set()
    unique: list[Path] = []
    for t in test_files:
        key = str(t)
        if key not in seen:
            seen.add(key)
            unique.append(t)

    return unique
