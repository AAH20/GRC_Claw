# Deep-Dive Analysis: block/agent-task-queue

> **For:** Ahmed Hassan — 330 agent slots, preventing concurrent execution of expensive operations
> **Source:** https://github.com/block/agent-task-queue (Apache 2.0, v0.4.1)
> **Date:** 2026-10-01

---

## 1. Architecture Overview

### 1.1 What It Is

`agent-task-queue` is a **local MCP (Model Context Protocol) server** that serializes expensive shell commands across multiple AI agents. It prevents the "thundering herd" problem where 330 agents independently trigger builds, tests, or container operations that thrash the machine.

**Core insight:** AI coding tools have built-in shell timeouts (30s–120s). A CLI-based queue fails because agents give up waiting. An MCP server keeps the connection alive indefinitely — the agent's tool call blocks until the task completes, with no timeout configuration needed.

### 1.2 Architecture Components

```
┌─────────────────────────────────────────────────────────┐
│                    AI Agents (×330)                      │
│  Hermes / Claude Code / Cursor / Copilot / Windsurf     │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP tool call (run_task)
                       ▼
┌─────────────────────────────────────────────────────────┐
│              agent-task-queue MCP Server                 │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  FIFO Queue │  │  Zombie      │  │  Hierarchical │  │
│  │  Manager    │  │  Protector   │  │  Capacity     │  │
│  │  (SQLite)   │  │  (PID check) │  │  Engine       │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Process    │  │  Output      │  │  Auto-Kill    │  │
│  │  Groups     │  │  Log Manager │  │  (120min)     │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │ subprocess execution
                       ▼
┌─────────────────────────────────────────────────────────┐
│              SQLite (WAL mode) — queue.db                │
│  /tmp/agent-task-queue/queue.db                          │
└─────────────────────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────────┐
    │ tq CLI   │ │ IntelliJ │ │ Desktop      │
    │ (human)  │ │ Plugin   │ │ Sidecar      │
    └──────────┘ └──────────┘ └──────────────┘
```

### 1.3 MCP Server

- **Protocol:** MCP over stdio (launched as a subprocess by the AI tool)
- **Implementation:** ~600 lines of Python
- **State:** SQLite with Write-Ahead Logging (WAL) for concurrent reads
- **Connection model:** Persistent — the MCP connection stays alive while tasks wait in queue
- **Tool exposed:** `run_task` — the single tool agents call

### 1.4 FIFO Queues

- **Default:** All `run_task` calls share one global queue (capacity 1)
- **Named queues:** `queue_name` parameter isolates workloads (e.g., `android` vs `web` run in parallel)
- **Strict FIFO:** Within each exact `queue_name`, tasks execute first-in-first-out
- **No queue timeouts:** Tasks can wait indefinitely — `timeout_seconds` only applies to execution time
- **Sibling queue caveat:** Sibling queues sharing a parent scope compete for parent capacity on a best-effort basis; FIFO is guaranteed within each exact queue, not across siblings

### 1.5 Zombie Protection

When an agent crashes while a task is running:

1. **Detection:** Next task checks if the parent process (agent) is still alive via PID check
2. **Orphan cleanup:** Kills any orphaned child process (the actual build/test)
3. **Lock clearing:** Removes the stale lock from SQLite
4. **Continuation:** Execution proceeds normally

**PID reuse detection:** v0.2.0+ detects when a PID has been reused by an unrelated process (e.g., Chrome) vs. an actual `task_queue` process. Each server/CLI instance gets a unique `SERVER_INSTANCE_ID` to detect orphaned tasks from crashed/restarted processes.

**Cancellation handling:** Properly cleans up queue entries when MCP clients disconnect (e.g., sub-agents cancelled).

### 1.6 Auto-Kill

Tasks running longer than 120 minutes are automatically terminated. This prevents a single hung build from blocking the entire queue indefinitely.

---

## 2. Key Features for Ahmed's Stack

### 2.1 Hierarchical Queue Capacities

The most relevant feature for 330 agent slots. Hierarchical queues let you:

- **Limit parallelism** across a group of related queues
- **Preserve FIFO** within each child queue
- **Fan out** from shared prep to exclusive leaf execution

**How it works:**

```
--queue-capacity=gradle=2              # Parent scope: max 2 concurrent
--queue-capacity=gradle/emu-5557=1     # Leaf: exclusive
--queue-capacity=gradle/emu-5559=1     # Leaf: exclusive
```

- Configured capacities apply to a scope **and all descendants**
- Capacities are **process-local** — not persisted in `queue.db`
- If multiple servers share the same data directory, they must start with matching `--queue-capacity` flags
- Without configuration, each exact `queue_name` is a FIFO queue with capacity 1

**For 330 agents:** You can create a hierarchy like:

```
--queue-capacity=build=10              # Max 10 concurrent builds
--queue-capacity=build/android=4       # Max 4 Android builds
--queue-capacity=build/web=4           # Max 4 web builds
--queue-capacity=build/ios=2           # Max 2 iOS builds
--queue-capacity=test=20               # Max 20 concurrent tests
--queue-capacity=test/unit=15          # Max 15 unit tests
--queue-capacity=test/integration=5    # Max 5 integration tests
```

### 2.2 Desktop Sidecar

A **Compose Multiplatform desktop app** (`desktop-sidecar/`) for real-time queue visibility:

- Reads the same local SQLite database as `tq` and the IntelliJ plugin
- Shows: running tasks, waiting tasks, exact queues grouped by root scope
- Run with: `cd desktop-sidecar && ./gradlew run`
- Point at custom data dir: `./gradlew run --args="--data-dir /path/to/agent-task-queue"`
- Defaults to `$TASK_QUEUE_DATA_DIR` or `/tmp/agent-task-queue`
- Shows live occupancy from `queue.db`; configured `--queue-capacity` limits are process-local and not stored in SQLite, so the UI shows live tasks and queue topology rather than persisted capacity settings

### 2.3 IntelliJ Plugin

Full JetBrains IDE plugin for agent-task-queue visibility:

- **Status bar widget:** Shows current queue state (4 display modes: hidden, minimal, default, verbose)
- **Tool window:** Table of all tasks with ID, status, queue name, command, relative time
- **Output tabs:** Per-task closeable tabs with live streaming console output
- **Notifications:** Balloon notifications for queue events (task starts, finishes, fails)
- **Architecture:** Reads SQLite directly (read-only via JDBC with WAL mode) — works even when no MCP server is running
- **Polling:** 1s interval when tasks exist (active), 3s when empty (idle)

### 2.4 CLI Tool (`tq`)

```bash
# Run commands through the same queue that agents use
tq ./gradlew assembleDebug
tq -q android ./gradlew test
tq -t 600 npm test
tq -C /path/to/project make

# Inspect queue
tq list
tq list --json
tq logs --json
tq clear
tq clear --json
```

Prevents resource contention between humans and AI agents — when you run a build via `tq`, any agent-initiated builds will wait in the same queue.

### 2.5 Environment Variables

Pass build-specific config via `env_vars="KEY=val,KEY2=val2"` — e.g., `ANDROID_SERIAL=emulator-5560`.

### 2.6 Output Management

- Output goes to log files instead of returning inline (saves context window tokens)
- `--max-output-files=50` — number of task output files to retain
- `--max-log-size=5` — max metrics log size in MB before rotation
- `--tail-lines=50` — lines of output to include on failure
- v0.4.0+: `.raw.log` companion files for clean output with no filtering

---

## 3. Integration Guide — agent-task-queue with Hermes Agent

### 3.1 How Hermes Configures MCP Servers

Hermes reads MCP config from `~/.hermes/config.yaml` under `mcp_servers`. Each server entry specifies how to start it (stdio) or connect to it (HTTP).

**Key config keys:**

| Key | Type | Meaning |
|-----|------|---------|
| `command` | string | Executable for a stdio MCP server |
| `args` | list | Arguments for the stdio server |
| `env` | mapping | Environment variables passed to the subprocess |
| `timeout` | number | Tool call timeout in seconds (default: 300) |
| `connect_timeout` | number | Initial connection timeout (default: 60) |
| `enabled` | bool | Skip the server entirely when false |
| `tools` | mapping | Per-server tool filtering (`include`/`exclude`) |
| `supports_parallel_tool_calls` | bool | Allow tools from this server to run concurrently |

**MCP tools appear in the agent's tool list with the naming pattern:** `mcp__<servername>__<toolname>`

For agent-task-queue, the tool would be: `mcp__agent-task-queue__run_task`

### 3.2 Step-by-Step Integration

#### Step 1: Install agent-task-queue

```bash
# Option A: uvx (ephemeral, always latest)
uvx agent-task-queue@latest

# Option B: uv tool (persistent install)
uv tool install agent-task-queue
```

#### Step 2: Add to Hermes config.yaml

Edit `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  agent-task-queue:
    command: "uvx"
    args:
      - "agent-task-queue@latest"
      - "--data-dir=/tmp/agent-task-queue"
      - "--max-output-files=100"
      - "--lock-timeout=60"
      - "--queue-capacity=build=10"
      - "--queue-capacity=build/android=4"
      - "--queue-capacity=build/web=4"
      - "--queue-capacity=test=20"
      - "--queue-capacity=test/unit=15"
      - "--queue-capacity=test/integration=5"
    enabled: true
    timeout: 300
    connect_timeout: 60
    tools:
      include:
        - run_task
```

#### Step 3: Reload MCP in Hermes

```
/reload-mcp
```

Or restart Hermes entirely.

#### Step 4: Verify

Ask Hermes: "Tell me which MCP-backed tools are available right now." You should see `mcp__agent-task-queue__run_task`.

#### Step 5: Use it

The agent will now call `run_task` for expensive operations:

```
run_task(
  command="./gradlew assembleDebug",
  working_directory="/path/to/android-project",
  queue_name="build/android",
  env_vars="ANDROID_SERIAL=emulator-5560"
)
```

### 3.3 Important: Agent May Need Configuration to Prefer MCP

Some agents automatically prefer MCP tools (Amp, Copilot, Windsurf). Others may need configuration to prefer `run_task` over built-in shell commands. For Hermes, you may need to add instructions to your `AGENTS.md` or project rules:

```markdown
## Build Commands
Always use the agent-task-queue MCP tool (run_task) for expensive operations:
- Builds (gradle, bazel, make, cmake, mvn, cargo, go build, npm/yarn/pnpm build)
- Container operations (docker build, docker-compose, podman, kubectl, helm)
- Test suites (pytest, jest, mocha, rspec)

Never run these directly via shell — they must go through the queue.
```

### 3.4 Multi-Agent Coordination with Hermes

For Ahmed's 330 agent slots, the pattern would be:

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  agent-task-queue:
    command: "uvx"
    args:
      - "agent-task-queue@latest"
      - "--data-dir=/tmp/agent-task-queue"
      - "--queue-capacity=build=10"
      - "--queue-capacity=test=20"
      - "--queue-capacity=container=5"
    enabled: true
    timeout: 300
    tools:
      include:
        - run_task
```

All 330 Hermes agent instances share the same MCP server configuration. The MCP server (one instance) manages the queue; all agents block on their tool calls until their task completes.

---

## 4. Configuration Examples

### 4.1 Basic MCP Server Setup

```json
{
  "mcpServers": {
    "agent-task-queue": {
      "command": "uvx",
      "args": ["agent-task-queue@latest"]
    }
  }
}
```

### 4.2 Full Configuration with Hierarchical Queues

```json
{
  "mcpServers": {
    "agent-task-queue": {
      "command": "uvx",
      "args": [
        "agent-task-queue@latest",
        "--data-dir=/tmp/agent-task-queue",
        "--max-output-files=100",
        "--lock-timeout=60",
        "--queue-capacity=gradle=2",
        "--queue-capacity=gradle/emu-5557=1",
        "--queue-capacity=gradle/emu-5559=1"
      ]
    }
  }
}
```

### 4.3 Hermes config.yaml (Full)

```yaml
mcp_servers:
  agent-task-queue:
    command: "uvx"
    args:
      - "agent-task-queue@latest"
      - "--data-dir=/tmp/agent-task-queue"
      - "--max-output-files=100"
      - "--lock-timeout=60"
      - "--queue-capacity=build=10"
      - "--queue-capacity=build/android=4"
      - "--queue-capacity=build/web=4"
      - "--queue-capacity=build/ios=2"
      - "--queue-capacity=test=20"
      - "--queue-capacity=test/unit=15"
      - "--queue-capacity=test/integration=5"
      - "--queue-capacity=container=5"
    enabled: true
    timeout: 300
    connect_timeout: 60
    tools:
      include:
        - run_task
```

### 4.4 Queue Definitions for 330 Agents

```yaml
# Tier 1: Global build queue (max 10 concurrent)
--queue-capacity=build=10

# Tier 2: Per-platform build queues
--queue-capacity=build/android=4
--queue-capacity=build/web=4
--queue-capacity=build/ios=2

# Tier 3: Per-emulator test queues (exclusive)
--queue-capacity=test/android/emu-5557=1
--queue-capacity=test/android/emu-5559=1
--queue-capacity=test/android/emu-5561=1

# Tier 4: Container operations (max 5 concurrent)
--queue-capacity=container=5
--queue-capacity=container/docker=3
--queue-capacity=container/k8s=2
```

### 4.5 Android Multi-Emulator Pattern

```bash
# Server startup
uvx agent-task-queue@latest \
  --queue-capacity=gradle=2 \
  --queue-capacity=gradle/emu-5557=1 \
  --queue-capacity=gradle/emu-5559=1 \
  --queue-capacity=gradle/emu-5561=1

# Step 1: Queue shared Gradle prep/build
run_task(
  command="./gradlew assembleDebug assembleDebugAndroidTest",
  working_directory="/project",
  queue_name="gradle/build"
)

# Step 2: Fan out one task per emulator (reuses prebuilt outputs)
run_task(
  command="./gradlew connectedDebugAndroidTest -x assembleDebug -x assembleDebugAndroidTest",
  working_directory="/project",
  queue_name="gradle/emu-5557",
  env_vars="ANDROID_SERIAL=127.0.0.1:5557"
)
run_task(
  command="./gradlew connectedDebugAndroidTest -x assembleDebug -x assembleDebugAndroidTest",
  working_directory="/project",
  queue_name="gradle/emu-5559",
  env_vars="ANDROID_SERIAL=127.0.0.1:5559"
)
```

### 4.6 CLI Usage

```bash
# Install CLI
uv tool install agent-task-queue

# Run through queue
tq ./gradlew assembleDebug
tq -q android ./gradlew test
tq -t 600 npm test
tq -C /path/to/project make

# Inspect
tq list
tq list --json
tq logs --json
tq clear
```

---

## 5. Comparison with Other Queueing Solutions

| Feature | agent-task-queue | BullMQ | Sidekiq | Celery | Temporal | TadMSTR/task-queue-mcp |
|---------|-----------------|---------|---------|--------|----------|----------------------|
| **Purpose** | Local AI agent coordination | Distributed job queue | Rails background jobs | Python distributed tasks | Durable execution | Agent orchestration |
| **Backend** | SQLite (WAL) | Redis | Redis | Redis/RabbitMQ | SQLite/Postgres | YAML files + MCP |
| **Protocol** | MCP (stdio) | Library | Library | Library | SDK/gRPC | MCP (HTTP) |
| **Zombie protection** | ✅ PID check + orphan kill | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Hierarchical queues** | ✅ `--queue-capacity` | ❌ | ❌ | ❌ | ✅ (task queues) | ❌ |
| **No queue timeouts** | ✅ (MCP keeps alive) | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Auto-kill** | ✅ (120min default) | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Desktop sidecar** | ✅ Compose Multiplatform | ❌ | ❌ | ❌ | ✅ (web UI) | ❌ |
| **IDE integration** | ✅ IntelliJ plugin | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Human + agent sharing** | ✅ (`tq` CLI) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Setup complexity** | Minimal (uvx) | High (Redis) | High (Redis) | High (broker) | Very high | Medium (Docker) |
| **Best for** | Local multi-agent dev | Production job queues | Rails apps | Python microservices | Enterprise workflows | Claude Code orchestration |

### When to Choose What

- **agent-task-queue:** Local development with multiple AI agents running expensive operations. Minimal setup, MCP-native, zombie-proof.
- **BullMQ:** Production job queues with Redis already in stack. No AI agent coordination needed.
- **Sidekiq:** Ruby/Rails background jobs. Not for AI agent coordination.
- **Celery:** Python distributed tasks. Heavy infrastructure.
- **Temporal:** Durable execution with saga patterns. Overkill for local build queuing.
- **TadMSTR/task-queue-mcp:** Claude Code-specific agent orchestration with YAML file-based tasks. More feature-rich for task lifecycle but more complex setup.

---

## 6. Pitfalls and Best Practices

### 6.1 Pitfalls

1. **Agents bypassing the queue:** Some agents may "be smart" and run commands directly via shell instead of using `run_task`. **Mitigation:** Add explicit instructions in `AGENTS.md` / project rules.

2. **Queue capacity misconfiguration:** If multiple servers share the same data directory but have different `--queue-capacity` flags, behavior is undefined. **Mitigation:** Always start all servers with matching capacity flags.

3. **Sibling queue FIFO not guaranteed:** FIFO ordering is guaranteed within each exact `queue_name`, not across sibling queues. **Mitigation:** Don't rely on cross-sibling ordering.

4. **Process-local capacities:** `--queue-capacity` overrides are not persisted in `queue.db`. **Mitigation:** Document your capacity config; the desktop sidecar shows live topology, not persisted settings.

5. **Database lock errors:** "Database is locked" errors can occur with zombie processes. **Mitigation:** `ps aux | grep task_queue` then `rm -rf /tmp/agent-task-queue/` and restart.

6. **Single point of failure:** One MCP server manages all queues. If it crashes, all agents block. **Mitigation:** The server is ~600 lines of Python, very stable. Zombie protection handles most crash scenarios.

7. **No authentication:** The MCP server has no auth. **Mitigation:** It's local-only (stdio), so only local processes can connect. Don't expose over network.

8. **Context window burn:** If agents call `run_task` for cheap operations, they waste tokens on queue overhead. **Mitigation:** Only use for expensive operations (builds, tests, containers).

9. **Timeout confusion:** `timeout_seconds` only applies to execution time, not queue wait time. **Mitigation:** Set generous timeouts for long builds; queue wait is unlimited.

10. **PID reuse false positives:** v0.2.0+ has PID reuse detection, but edge cases exist. **Mitigation:** Keep updated to latest version.

### 6.2 Best Practices

1. **Use hierarchical queues for resource management:** Map your queue hierarchy to your machine's resources (CPU cores, memory, disk I/O).

2. **Separate queues by workload type:** Don't mix builds and tests in the same queue — they have different resource profiles.

3. **Set appropriate timeouts:** `timeout_seconds` should be slightly longer than your longest expected build. Default 1200s (20min) is reasonable.

4. **Monitor with the desktop sidecar:** Run the Compose Multiplatform sidecar for real-time visibility into queue state.

5. **Use `tq` CLI for human operations:** When you run builds manually, use `tq` to avoid contention with agent-initiated builds.

6. **Configure `--lock-timeout` appropriately:** Default 120 minutes. Lower it if you want stale locks cleared faster.

7. **Retain enough output files:** `--max-output-files=100` gives you history for debugging. Don't set too low.

8. **Keep the MCP server updated:** `uvx agent-task-queue@latest` always pulls latest. For production, pin a version.

9. **Document your queue topology:** Since capacities are process-local, document your `--queue-capacity` flags in your project README.

10. **Test zombie protection:** Kill an agent mid-build and verify the next task detects the dead process and continues.

### 6.3 Recommended Setup for Ahmed's 330 Agent Slots

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  agent-task-queue:
    command: "uvx"
    args:
      - "agent-task-queue@latest"
      - "--data-dir=/tmp/agent-task-queue"
      - "--max-output-files=200"
      - "--lock-timeout=60"
      - "--tail-lines=100"
      # Build queues — limit concurrent builds to avoid thrashing
      - "--queue-capacity=build=10"
      - "--queue-capacity=build/android=4"
      - "--queue-capacity=build/web=4"
      - "--queue-capacity=build/ios=2"
      # Test queues — higher parallelism for tests
      - "--queue-capacity=test=20"
      - "--queue-capacity=test/unit=15"
      - "--queue-capacity=test/integration=5"
      # Container operations — moderate parallelism
      - "--queue-capacity=container=5"
      - "--queue-capacity=container/docker=3"
      - "--queue-capacity=container/k8s=2"
    enabled: true
    timeout: 300
    connect_timeout: 60
    tools:
      include:
        - run_task
```

```markdown
# AGENTS.md (project rules)
## Build and Test Commands
ALWAYS use the agent-task-queue MCP tool (run_task) for:
- Builds: gradle, bazel, make, cmake, mvn, cargo, go build, npm/yarn/pnpm build
- Containers: docker build, docker-compose, podman, kubectl, helm
- Tests: pytest, jest, mocha, rspec

NEVER run these directly via shell — they must go through the queue.

Queue naming convention:
- build/<platform> — for builds (build/android, build/web, build/ios)
- test/<suite> — for tests (test/unit, test/integration)
- container/<tool> — for container ops (container/docker, container/k8s)
```

---

## Summary

`agent-task-queue` is the right tool for Ahmed's use case: 330 agent slots on a single machine, needing to prevent concurrent execution of expensive operations. It's:

- **Minimal setup:** `uvx agent-task-queue@latest` — one command
- **MCP-native:** No shell timeout issues, agents just wait
- **Zombie-proof:** PID detection, orphan killing, stale lock clearing
- **Hierarchical:** `--queue-capacity` for resource-limited parallelism
- **Observable:** Desktop sidecar, IntelliJ plugin, `tq` CLI
- **Human-agent shared:** `tq` CLI puts humans in the same queue as agents

The main work is configuring the queue hierarchy to match your machine's resources and adding project rules so agents always use `run_task` instead of raw shell commands.
