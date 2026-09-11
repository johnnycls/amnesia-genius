# amnesia-agent-local-server

Reusable local HTTP server for `amnesia-agent-kernel` clients such as the Ren'Py and Electron frontends.

**Python >=3.10**

## Development

```text
pip install ./kernel
pip install ./local_server
amnesia-agent-local-server
```

The server binds to `127.0.0.1:8765` by default. Override the bind address or port with:

```text
amnesia-agent-local-server --host 127.0.0.1 --port 8765
```

This server intentionally exposes the kernel's unrestricted local bash tool. Keep it bound to
loopback and run it only on a trusted machine.

## Configuration

The server stores configuration at:

```text
~/.amnesia-agent-local-server/config.json
```

This is separate from the kernel workspace at `~/.amnesia-agent/`. The config schema is
identical to the CLI's (see [cli/README.md](../cli/README.md) for key descriptions).
The API key is never exposed in responses; `/v1/config` returns `api_key_set: boolean`
instead.

## API

All endpoints are versioned under `/v1`.

### Health

```text
GET /v1/health
→ {"status": "ok", "active_turn": false, "api_version": "v1", "instance_id": "..."}
```

### Configuration

```text
GET  /v1/config           → config object (api_key masked)
PUT  /v1/config           → partial update (any subset of keys)
POST /v1/config/reset     → restore defaults
```

### Turns (SSE)

```text
POST /v1/turn   {"text": "..."}
```

Returns a Server-Sent Events stream with typed envelopes:

```text
data: {"type":"delta","data":{"text":"..."}}
data: {"type":"assistant","data":{"message":{...}}}
data: {"type":"tool_call","data":{"message":{...}}}
data: {"type":"tool_result","data":{"message":{...}}}
data: {"type":"done","data":{}}
```

- Returns **409** if a turn is already active (one turn at a time).
- Closing the SSE connection cancels the active turn.
- The response uses structured output (`answer_with_choices` JSON schema) when
  the provider supports it, yielding `answer` and `choices` fields.

### Workspace

```text
GET  /v1/workspace/system-prompt        → current system prompt
PUT  /v1/workspace/system-prompt        → replace system prompt
POST /v1/workspace/system-prompt/reset  → reset to default

GET  /v1/workspace/memory               → current memory
PUT  /v1/workspace/memory               → replace memory
POST /v1/workspace/memory/reset         → reset to default

GET  /v1/workspace/history              → list of dates (newest first)
GET  /v1/workspace/history/{YYYY-MM-DD} → one day's history
POST /v1/workspace/history/reset        → clear all history
```

### Shutdown

```text
POST /v1/shutdown
```

Graceful shutdown: finishes any in-progress work, then stops the server.

## Session management

The server owns one `KernelSession`. Configuration changes invalidate the current
session and apply to the next turn. The `instance_id` (random UUID, set at startup)
is returned in `/v1/health` so frontends can detect port conflicts with stale servers.

## Troubleshooting

**409 on `/v1/turn`** — A turn is already active. Only one turn runs at a time.
Wait for the current turn to finish or close the SSE connection to cancel it.

**Server won't start** — Ensure `amnesia-agent-local-server` is on your PATH.
Check that port 8765 is not in use by another process.

**Config changes not taking effect** — Configuration changes invalidate the
current session. The new config applies on the next turn, not immediately.
