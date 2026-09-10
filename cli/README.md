# amnesia-agent-cli

Minimal terminal CLI and configuration store for `amnesia-agent-kernel`.

## Install

```text
pip install ./kernel
pip install ./cli
amnesia-agent
```

## Configuration

`ConfigStore` owns the user-editable file at:

```text
~/.amnesia-agent-cli/config.json
```

It is separate from the kernel workspace. The store seeds missing configuration and validates the JSON values,
and returns a `LoadedConfig` containing `ProviderConfig` and `ExecutionPolicy`.
The kernel performs LiteLLM preflight during `KernelSession` initialization:

```python
from amnesia_agent_cli.config import ConfigStore

store = ConfigStore()
store.setup()
loaded = store.load()
```

Invalid configuration errors include the config path so the CLI can open the file
with the platform’s default editor. `ConfigStore.reset()` restores the packaged
blank/default configuration.

## CLI behavior

The CLI creates one `ConfigStore`. Before every user turn it reloads the
configuration and constructs a fresh kernel `KernelSession` from that snapshot.
Session initialization performs provider preflight; typed initialization or turn
failures are logged and terminate the process. The session creates the default
kernel workspace internally. The CLI renders kernel events as terminal output.

```text
amnesia-agent
amnesia-agent --version
```

Reset operations are exposed through the Python APIs, not as destructive CLI
commands.
