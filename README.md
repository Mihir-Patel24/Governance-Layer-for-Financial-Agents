# Governance-Layer-for-Financial-Agents

## Person 2 (The Enforcer)

### 1. What Person 2 Owns
Person 2 is responsible for the **Enforcer subsystem**, which makes sure that policy decisions stick and are provable. This includes:
- **Spend Cap Service**: Real-time budget tracking per agent, resets, and rollover logic.
- **Kill Switch Service**: Per-agent halt and fleet-wide halt, with instant propagation.
- **Audit Log**: Hash-chained, append-only table to provide tamper-evident logging of all governance decisions.
- **Audit Query/Export API**: Providing transparency and data for the dashboard and compliance reports.

### 2. Architecture
The Enforcer operates as a critical step in the governance pipeline:
`Agent -> Person 1 Gateway -> Policy Decision -> Person 2 Enforcement -> Final Decision -> Audit -> Dashboard`

Person 2's components interact tightly with PostgreSQL for persistent state and Redis for fast-path kill-switch caching.

### 3. Component Responsibilities
- **EnforcerService (`app/services/enforcer_service.py`)**: The central pipeline orchestrating the precedence rules (validate -> fleet halt -> agent halt -> policy -> duplicate check -> spend cap -> audit).
- **SpendCapService (`app/services/spend_cap_service.py`)**: Tracks budgets. Uses row-level locking (`SELECT FOR UPDATE`) to prevent concurrent double-spending.
- **KillSwitchService (`app/services/kill_switch_service.py`)**: Manages halt states. Updates PostgreSQL first for persistence, then Redis for sub-millisecond propagation.
- **AuditService (`app/services/audit_service.py`)**: Constructs hash chains and verifies them.

### 4. Database Structure
Implemented in SQLAlchemy & Alembic:
- `agents`: Master registry.
- `spend_state`: Agent budgets and current spend (enforces uniqueness per period).
- `kill_switch_state`: Per-agent halt status.
- `fleet_kill_switch_state`: Singleton table for fleet halt status.
- `audit_log`: Append-only, indexed, hash-chained log.
- `idempotency_keys`: Stores action decisions to prevent duplicate execution.

### 5. Spend Flow
1. Agent requests an action with an amount.
2. `EnforcerService` checks idempotency.
3. Acquires a pessimistic row-lock on the agent's budget.
4. Checks if period expired (auto-resets if needed).
5. Validates `current_spent + requested_amount <= limit`.
6. Updates `current_spent` if allowed, otherwise denies without modifying budget.
7. Commits transaction and releases lock.

### 6. Kill-Switch Flow
- **Fleet Halt**: Overrides all individual agents. If fleet is halted, all agents are effectively halted.
- **Agent Halt**: Halts a specific agent.
- **Propagation**: Status is instantly cached in Redis. The next enforcement check reads from Redis (or falls back to DB if Redis is down).

### 7. Audit-Chain Algorithm
Every significant event is logged to `audit_log`.
- `canonical_data` = Deterministic JSON of the event fields, including `previous_hash`.
- `current_hash` = SHA-256 of `canonical_data`.
- The first entry uses "GENESIS" as `previous_hash`.

### 8. Hash Verification
The verification endpoint (`GET /api/v1/audit/verify`) iterates through the log in sequence:
1. Checks that `e[i].previous_hash == e[i-1].current_hash`.
2. Recomputes `current_hash` from the canonical JSON payload and compares it to the stored hash.
Any mismatch flags the exact sequence number where tampering occurred.

### 9. API Endpoints
- **Spend**: `/api/v1/spend/*` (check, reserve, configure, reset)
- **Kill Switch**: `/api/v1/kill-switch/*` (agent halt/resume, fleet halt/resume, status)
- **Audit**: `/api/v1/audit/*` (logs, verify, export)
- **Integration**: `/api/v1/enforce` (central entry point for Person 1)
- **Agents**: `/api/v1/agents` (registration)

### 10. Environment Setup
1. Copy `.env.example` to `.env`.
2. Ensure PostgreSQL is running on `localhost:5432` with user `govuser`/`govpass` and database `govdb`.
3. Ensure Redis is running on `localhost:6379`.
4. Install dependencies: `pip install -r requirements.txt` (or via your environment manager).

### 11. Database Migration
```bash
# Run migrations from the backend directory
alembic upgrade head
```

### 12. Redis Setup
The system expects Redis on `localhost:6379/0`. If Redis is unavailable, the Kill Switch gracefully degrades to read directly from PostgreSQL.

### 13. Running Tests
```bash
# Run the test suite
python -m pytest tests/ -v
```
Tests use an in-memory SQLite database for speed and isolation.

### 14. Demo Instructions
```bash
# 1. Start the API server in one terminal
uvicorn app.main:app --reload

# 2. In another terminal, seed the database
python scripts/seed.py

# 3. Run the interactive demo script
python scripts/demo.py
```

### 15. Person 1 Integration
Person 1 (Policy Gateway) should POST to `/api/v1/enforce` passing `opa_allowed=true/false` after their OPA check. The Enforcer handles the rest of the precedence rules and auditing.

### 16. Person 4 Integration
Person 4 (Dashboard) can poll or query `/api/v1/kill-switch/status` for live fleet and agent statuses, and `/api/v1/audit/logs` for the live event feed.
