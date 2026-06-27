# Testing Strategy for Yakoon

## Why there are no tests yet and how we proceed

---

## 1. Architecture Principle: Determinism → Testability as a Side Effect

Small, testable units have been central from the start. But the **reason** isn't "I want good tests." The reason is **determinism**.

```python
# Not: "I want to be able to test"
# But: "I want the system to remain traceable"
# Testability is the side effect, not the goal.
```

Every architectural decision serves determinism:

- **Nodes** are simple dataclasses → no hidden state
- **Handlers** are async generators with explicit ports → no implicit dependencies
- **Container** is a key-value store with parent chain → no global singletons
- **Projections** are immutable → no side effects when rendering
- **Compiler stages** are pure functions → same input → same output
- **Controls/Effects** are immutable values → no action on creation

```python
# Everything a handler needs comes explicitly via space.ports.get()
# → No global imports, no hidden dependencies

# Everything a handler produces is an Outcome
# → No side effects, no hidden state changes

# Everything that is a Block is a frozen dataclass
# → No mutable objects, no identity problems
```

**Testability is a welcome side effect.** The real reason: the system must remain traceable. And this is exactly why AI can be used safely later — an AI needs a deterministic system to predict the consequences of its own code.

> **Determinism is the goal. Testability and AI safety are the consequences.**

## 2. Why There Are Currently No Tests

The architecture went through many iterations:
- Node system (multiple versions)
- Ports/Container (provide↓/publish↑ directions)
- Flow execution (generator-based)
- Projection compiler (4 stages)
- Capability security (PermissionChecker)

In each iteration, fundamental interfaces changed. Tests written during iteration only test last week's version — and become dead weight on the next refactor.

The decision was: **Iterate until the architecture solidifies, then test.**

---

## 3. Testability Is Not Lost

The key promise: **Target: 100% testability** — and that's not hard because everything uses loose coupling via ports.

### Ports as Natural Test Doubles

Every port is a test-double point:

```python
# Production: real Projector
platform.ports.provide(OnProjectionResolve, projector.project)

# Test: mock Projector
async def fake_project(*, resource, state):
    return Projection(
        id="test.prj",
        header=ProjectionHeader(role="info", title="Test"),
        blocks=[ParagraphBlock(text=[InlineText("Hello World")])],
    )

platform.ports.provide(OnProjectionResolve, fake_project)
```

Because all dependencies are obtained via `ports.get()`, **every port can be replaced with a double in tests** — no monkey-patching, no mocking framework, no magic.

### Testing Generator Flows Without a Scheduler

The core — generator flows — is testable without a scheduler:

```python
async def test_welcome_handler():
    space = MockNodeSpace()
    gen = welcome.run(space)

    outcome = await gen.__anext__()
    assert isinstance(outcome, Outcome)
    assert len(outcome.effects) == 1
    assert isinstance(outcome.effects[0], EmitView)
    assert outcome.control is None  # no stop → continues

    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()
```

### Testing Projections Without a Render Engine

Projections are immutable dataclasses — directly created and compared:

```python
def test_projection_has_correct_structure():
    projection = Projection(
        id="prj.test",
        header=ProjectionHeader(role="success", title="OK"),
        blocks=[
            KvBlock(items=[
                KvItemBlock(key="Status", value=[InlineText("Active")]),
            ]),
        ],
    )

    assert projection.header.role == "success"
    assert len(projection.blocks) == 1
    assert isinstance(projection.blocks[0], KvBlock)
```

### Testing Compiler Stages in Isolation

The compiler is split into 4 isolated stages — each is a pure function:

```python
tokens = tokenize_text("<p>Hello <strong>World</strong></p>")
ast = build_ast(tokens)
normalize_ast(ast)
projection = Mapper().map_projection(ast)
```

---

## 4. Test Pyramid

```
      /\
     /  \
    / E2E \             ← 3-5 tests (system: Dispatch → Flow → Client)
   /--------\
  /Integration\         ← 20-30 tests (Compiler, Scheduler, Postgres backend)
 /----------------\
/   Unit Tests    \    ← 200-400 tests (Handler, Ports, Nodes, Flows, Model)
/------------------\
```

### Unit Tests (Base)

| Component | Tests | Description |
|-----------|-------|-------------|
| Node (add, mount, find) | ~20 | Hierarchy operations |
| NodePorts (provide, publish, get, fork) | ~15 | Container chains |
| Container (bind, get, fork, mount) | ~10 | Base container |
| FlowCursor (next, send, push, pop) | ~15 | Generator stack |
| Outcome, Control, Effect | ~10 | Primitives |
| Projection models (blocks, inlines) | ~30 | Dataclass tests |
| Compiler (Tokenize, AST, Normalize) | ~20 | Pure functions |
| Mapper (Block mapper, Inline mapper) | ~30 | Tag→Model |
| Serializer/Deserializer | ~10 | Wire protocol |
| PermissionChecker | ~10 | RBAC logic |
| Naming allocation | ~5 | Naming |
| **Total Unit** | **~175** | |

### Integration Tests

| Component | Tests | Description |
|-----------|-------|-------------|
| Projector (Jinja2 → Projection) | ~10 | Full pipeline test |
| Scheduler (Queue, Dispatch, Sleep) | ~10 | Scheduling logic |
| Engine (step_flow, dispatch) | ~10 | Flow lifecycle |
| Postgres backend | ~10 | DB operations |
| Identity space (user, group, grant) | ~15 | Cross-space |
| **Total Integration** | **~55** | |

### E2E Tests

| Scenario | Description |
|---------|-------------|
| Command input → Projection output | Full Dispatch→Flow→Projection chain |
| `receive` → input → response | Interactive flow across steps |
| Background job (bg/fg/list/stop) | Job lifecycle |
| Permission check (allowed/denied) | Auth + Node resolution |
| **Total E2E** | ~5 |

### Summary

```
Unit:         ~175 tests
Integration:  ~55 tests
E2E:           ~5 tests
─────────────────────
Total:        ~235 tests
```

---

## 5. Mocking Strategy

### What is NOT mocked

- **Projection models** — pure dataclasses, no mock needed
- **Control/Effect/Outcome** — immutable value objects
- **Container/NodePorts** — test helpers themselves (no IO)

### What is mocked

```python
space.ports.provide(OnProject, FakeProjector())
space.ports.provide(OnSourceRead, FakeDataSource())
space.ports.provide(OnSessionSave, FakeSessionSaver())

class FakeSession:
    def __init__(self):
        self._flows = {}
        self._foreground = None
        self.lang = "en"
```

### What is NOT mocked (integration)

- **Compiler** — full pipeline test with real `.sam` templates
- **Projector** — Jinja2 + Compiler as integration
- **Scheduler** — real queue + event loop

---

## 6. Test Runner Setup

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["y5n", "y5nspace", "y5nstore", "y5ntrans", "y5napp"]
omit = ["*/tests/*", "*/__old__/*"]
```

```bash
# requirements-dev.txt
pytest>=8.0
pytest-asyncio>=0.24
pytest-cov>=5.0
syrupy>=4.0        # Snapshot testing for Projections
```

---

## 7. Summary

| Metric | Today | Target |
|--------|-------|--------|
| Tests | 0 | ~235 |
| Code Coverage | 0% | >80% |
| Test Runner | None | pytest + asyncio |
| CI | None | GitHub Actions |
| Snapshot Tests | None | syrupy for Projections |

**The architecture is testable.** Ports are natural mock points. Generator flows are testable without a scheduler. The compiler is decomposed into pure functions. Projections are immutable dataclasses.

Only the files are missing.


