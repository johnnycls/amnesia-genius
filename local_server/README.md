# amnesia-agent-local-server

Reusable local HTTP server for `amnesia-agent-kernel` clients such as the Ren'Py frontend.

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

## API

The versioned API is rooted at `/v1`:

- `GET /v1/health`
- `GET|PUT /v1/config` and `POST /v1/config/reset`
- `POST /v1/turn` — direct Server-Sent Events stream
- `GET|PUT|POST /v1/workspace/system-prompt`
- `GET|PUT|POST /v1/workspace/memory`
- `GET /v1/workspace/history`
- `GET /v1/workspace/history/{YYYY-MM-DD}`
- `POST /v1/workspace/history/reset`
- `POST /v1/shutdown`

`POST /v1/turn` accepts `{"text": "..."}` and streams typed JSON envelopes:

```text
data: {"type":"delta","data":{"text":"..."}}

data: {"type":"assistant","data":{"answer":"...","choices":[]}}

data: {"type":"done","data":{}}
```

Closing the SSE connection cancels the active kernel turn. The server owns one session and rejects
another turn while one is active. Configuration changes invalidate the current session and apply
to the next turn.

Configuration is stored separately from the kernel workspace at
`~/.amnesia-agent-local-server/config.json`.
