# ADR 11: Transport is untyped. SDK is typed.

**Status:** Proposed — design decisions made, implementation pending

> **The wire transports. The SDK models.**
>
> Transport carries data. The SDK owns the typed model. The wire layer owns
> no domain types — it moves dicts, JSON, and events. Every typed model lives
> in the SDK, generated from the YDS specification. Developers work against
> `sdk.models`, never against the wire.

`DocumentEvent` is not a document model — it is a **transport model**. It
exists because documents travel over a transport, not because the transport
understands documents. The wire knows nothing about `InlineStrong`, `Paragraph`,
or `Header`.

## Context

The document pipeline currently carries two parallel representations:

- the compiler produces plain dicts (the wire format),
- the API hand-maintains `Inline*` dataclasses and `DocumentHeader`, plus a
  hand-written decoder (`INLINE_TYPES`, `_reconstruct_inlines`) that
  reconstructs those classes on the client side.

The YDS specification is canonical, and a generator already emits the document
model into `sdk/models.py` (`Document`, `Header`, `Paragraph`, `InlineText`,
...). The hand-maintained API model is a second source of truth — with drift
(e.g. the compiler allows only two of the four specified `error_kind` values).

Who owns the typing? The answer mirrors the earlier resource decision (who
owns the interpretation): **not the transport — the client.** The developer
works against `sdk.models`.

## The layers

```
          YDS
           │
      Generator
           │
           ▼
      SDK Models          ← the only typed model
           ▲
           │
    from_dict() / to_dict()
           │
           ▼
Wire (dict / JSON)        ← untyped data
           ▲
           │
       Transport          ← messages, not documents
```

- **Transport** owns dicts, JSON, bytes, events — no domain types.
- **SDK** owns the models — all generated from YDS.
- **Compiler** produces the wire format, not the SDK model.
- **Runtime** coordinates.

## The SDK is complete: `from_dict()` / `to_dict()`

The generated models already provide `to_dict()` (model → wire). To make the
SDK symmetric and to remove the hand-written decoder, the generator also emits
`from_dict()`:

```python
doc = Document.from_dict(data)   # wire → typed model
data = doc.to_dict()             # typed model → wire
```

The decoder disappears entirely — deserialization becomes `JSON → dict`,
then `SDK.from_dict`.

## Consequences

- `DocumentEvent` carries data only: `header: dict`, `patch: {ops}` — the API
  knows no document types.
- `DocumentHeader`, the `Inline*` dataclasses, `model.py`, and the typed
  decoder are removed from the API.
- The shell, console, and commands use `sdk.models`; wire → model happens via
  `from_dict()` in the SDK.
- The rule is general: it applies not just to documents but to every typed
  payload — events, responses, requests, configuration. Typed models always
  live in the SDK; the wire always carries data.

## Rejected alternatives

- **Typed wire** — the API owns `DocumentHeader`/`Inline*` and the decoder.
  Duplicates the SDK model and creates drift (the current state).
- **API importing the SDK** — wrong dependency direction; the SDK is the
  client of the wire.

## Relationship to Ownership First

Every ADR reduces to the same principle: **each layer owns exactly one
responsibility.** The node declares, the host interprets, the runtime
coordinates — and the wire transports, the SDK models. Giving a lower layer
(the wire) knowledge that belongs to an upper layer (the SDK) is the same
mistake as giving the runtime knowledge that belongs to the host.
