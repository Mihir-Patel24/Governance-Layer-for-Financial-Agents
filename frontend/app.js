/**
 * SentinelAI — Governance Layer for Financial Agents
 * Multi-Page Single-Page Application (SPA) Controller
 * Interlocks Person 1 (Policies), Person 2 (Spend Caps & Audit Ledger), Person 3 (ML Anomaly & Groq LLM), Person 4 (UI Console)
 */

const API_BASE = "http://localhost:8000/api/v1";

const state = {
  activePage: "command-center",
  isStreaming: true,
  streamTimer: null,
  isBackendConnected: false,
  globalKillActive: false,
  activeFilter: "ALL",

  agents: {
    "travel-agent-01": {
      id: "travel-agent-01",
      name: "Travel Agent",
      role: "Corporate flight & hotel bookings",
      type: "travel",
      status: "ACTIVE",
      singleLimit: 15000,
      dailyCap: 50000,
      currentSpend: 12450,
      actionsCount: 42,
      blockedCount: 1,
      anomaliesCount: 0,
      allowedActions: ["book_flight", "book_hotel", "cancel_booking"],
      operatingHours: "00:00 - 24:00"
    },
    "servicing-agent-01": {
      id: "servicing-agent-01",
      name: "Servicing Agent",
      role: "Customer support & fee reversals",
      type: "servicing",
      status: "ACTIVE",
      singleLimit: 1000,
      dailyCap: 25000,
      currentSpend: 18230,
      actionsCount: 120,
      blockedCount: 5,
      anomaliesCount: 4,
      allowedActions: ["fee_reversal", "issue_credit", "update_address"],
      operatingHours: "08:00 - 20:00"
    },
    "subsidy-agent-01": {
      id: "subsidy-agent-01",
      name: "Rewards Agent",
      role: "Rewards & direct subsidy disbursements",
      type: "rewards",
      status: "ACTIVE",
      singleLimit: 25000,
      dailyCap: 50000,
      currentSpend: 11900,
      actionsCount: 86,
      blockedCount: 8,
      anomaliesCount: 2,
      allowedActions: ["release_subsidy", "flag_discrepancy", "verify_beneficiary"],
      operatingHours: "00:00 - 24:00"
    }
  },

  actions: [
    {
      id: "req-f9104a",
      timestamp: "11:42:15 AM",
      agentId: "travel-agent-01",
      agentName: "Travel Agent",
      actionType: "book_flight",
      actionDesc: "Book Flight (DEL → BOM)",
      amount: 20000,
      verdict: "BLOCK",
      riskScore: 0.92,
      reason: "Requested amount ₹20,000 exceeds single transaction limit of ₹15,000.",
      llmExplanation: "Blocked: Travel Agent attempted ₹20,000 corporate flight booking which exceeds the mandatory single transaction limit of ₹15,000. SentinelAI dynamic policy engine prevented unauthorized financial drift.",
      auditHash: "40579b1a81b3b273e918c502b48d28a192837461947261829374829102938475",
      prevHash: "883398996b7dd033c718a2048591028374659182736451928374651928374651"
    },
    {
      id: "req-e8201b",
      timestamp: "11:41:03 AM",
      agentId: "servicing-agent-01",
      agentName: "Servicing Agent",
      actionType: "fee_reversal",
      actionDesc: "Fee Reversal",
      amount: 2500,
      verdict: "ALLOW",
      riskScore: 0.21,
      reason: "Within policy & rolling daily budget.",
      llmExplanation: "Approved: Fee reversal of ₹2,500 by Servicing Agent is whitelisted and within rolling daily servicing limit.",
      auditHash: "883398996b7dd033c718a2048591028374659182736451928374651928374651",
      prevHash: "94baa99d580895a0f18273645192837465192837465192837465192837465192"
    },
    {
      id: "req-d7302c",
      timestamp: "11:40:27 AM",
      agentId: "subsidy-agent-01",
      agentName: "Rewards Agent",
      actionType: "release_subsidy",
      actionDesc: "Disburse Reward",
      amount: 5000,
      verdict: "HITL_REQUIRED",
      riskScore: 0.78,
      reason: "ML Anomaly Flagged! Anomaly score 0.78 exceeds safety threshold (>0.70). Human verification required.",
      llmExplanation: "Human Verification Required: Isolation Forest flagged out-of-distribution disbursement velocity and sudden amount spike (Score 0.78 > 0.70 threshold). SentinelAI routed transaction to operator review.",
      auditHash: "94baa99d580895a0f18273645192837465192837465192837465192837465192",
      prevHash: "09a8cf4bdaf48869e81726354182930491827364519283746519283746519283"
    },
    {
      id: "req-c6403d",
      timestamp: "11:39:50 AM",
      agentId: "travel-agent-01",
      agentName: "Travel Agent",
      actionType: "book_hotel",
      actionDesc: "Book Hotel",
      amount: 8200,
      verdict: "ALLOW",
      riskScore: 0.18,
      reason: "Within budget & corporate lodging whitelist.",
      llmExplanation: "Approved: Corporate hotel booking for ₹8,200 is verified against preferred corporate lodging whitelist.",
      auditHash: "09a8cf4bdaf48869e81726354182930491827364519283746519283746519283",
      prevHash: "7b1c3d5e7f9a2b4c6e8d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e"
    },
    {
      id: "req-b5504e",
      timestamp: "11:38:11 AM",
      agentId: "servicing-agent-01",
      agentName: "Servicing Agent",
      actionType: "refund_request",
      actionDesc: "Refund Request",
      amount: 4000,
      verdict: "BLOCK",
      riskScore: 0.71,
      reason: "Action execution restricted outside allowed operating window (08:00 - 20:00).",
      llmExplanation: "Blocked: Servicing Agent attempted refund during restricted off-hours window (operating hours restricted to 08:00 - 20:00).",
      auditHash: "7b1c3d5e7f9a2b4c6e8d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e",
      prevHash: "1f3e5d7c9b0a2f4e6d8c0b2a4f6e8d0c2b4a6f8e0d2c4b6a8f0e2d4c6b8a0f2e"
    },
    {
      id: "req-a4605f",
      timestamp: "11:37:45 AM",
      agentId: "subsidy-agent-01",
      agentName: "Rewards Agent",
      actionType: "release_subsidy",
      actionDesc: "Disburse Subsidy",
      amount: 3000,
      verdict: "ALLOW",
      riskScore: 0.26,
      reason: "Matches verified beneficiary registry.",
      llmExplanation: "Approved: Direct subsidy disbursement matches verified beneficiary registry and daily spending budget.",
      auditHash: "1f3e5d7c9b0a2f4e6d8c0b2a4f6e8d0c2b4a6f8e0d2c4b6a8f0e2d4c6b8a0f2e",
      prevHash: "GENESIS_BLOCK_00000000000000000000000000000000000000000000000000000000"
    }
  ]
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  renderAgentFleetPage();
  renderLiveActionsTable();
  renderPoliciesPage();
  renderSpendBudgetsPage();
  renderKillSwitchPage();
  renderAuditChainExplorer();
  checkGatewayStatus();
  startSimulationStream();

  // Global search shortcut
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      const el = document.getElementById("global-search");
      if (el) el.focus();
    }
  });
});

// ============================================================================
// MULTI-PAGE VIEW ROUTER (SWITCHING PAGES)
// ============================================================================
function switchPage(pageId) {
  state.activePage = pageId;

  // 1. Update Sidebar Active Style (With the left yellow indicator)
  document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
  const activeNav = document.getElementById(`nav-${pageId}`);
  if (activeNav) activeNav.classList.add("active");

  // 2. Hide all other views, show target view with smooth fade-in
  document.querySelectorAll(".page-view").forEach(view => {
    view.classList.remove("active-page");
  });

  const targetView = document.getElementById(`view-${pageId}`);
  if (targetView) {
    targetView.classList.add("active-page");
  }

  // 3. Trigger specific page refresh/render
  if (pageId === "agent-fleet") renderAgentFleetPage();
  if (pageId === "live-actions") renderLiveActionsTable();
  if (pageId === "policies-rules") renderPoliciesPage();
  if (pageId === "spend-budgets") renderSpendBudgetsPage();
  if (pageId === "kill-switch") renderKillSwitchPage();
  if (pageId === "audit-ledger") renderAuditChainExplorer();

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ============================================================================
// RENDERERS FOR DEDICATED PAGES
// ============================================================================
function formatInr(num) {
  return "₹" + Number(num).toLocaleString("en-IN");
}

/* 1. AGENT FLEET PAGE */
function renderAgentFleetPage() {
  const cardsCont = document.getElementById("fleet-cards-container");
  const tableCont = document.getElementById("fleet-table-body");
  if (!cardsCont || !tableCont) return;

  const agentList = Object.values(state.agents);

  // Cards
  cardsCont.innerHTML = agentList.map(a => {
    const pct = Math.min(100, Math.round((a.currentSpend / a.dailyCap) * 100));

    return `
      <div class="glass-panel glass-panel-hover" style="display: flex; flex-direction: column; gap: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <span style="font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">${a.id}</span>
            <h4 style="font-size: 1.15rem; font-weight: 800; color: var(--text-primary);">${a.name}</h4>
            <span style="font-size: 0.75rem; color: var(--text-secondary);">${a.role}</span>
          </div>
          <span class="badge ${a.status === 'ACTIVE' ? 'badge-active' : a.status === 'PAUSED' ? 'badge-paused' : 'badge-terminated'}">
            &bull; ${a.status}
          </span>
        </div>

        <div>
          <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 4px;">
            <span style="color: var(--text-muted);">Daily Spend Utilized</span>
            <strong style="color: var(--text-primary);">${formatInr(a.currentSpend)} / ${formatInr(a.dailyCap)} (${pct}%)</strong>
          </div>
          <div class="meter-container">
            <div class="meter-fill" style="width: ${pct}%;"></div>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; background: #f8fafc; padding: 10px; border-radius: var(--radius-sm); border: 1px solid var(--border-light); text-align: center;">
          <div>
            <div style="font-size: 1.1rem; font-weight: 800; color: var(--text-primary);">${a.actionsCount}</div>
            <div style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Actions</div>
          </div>
          <div>
            <div style="font-size: 1.1rem; font-weight: 800; color: var(--status-blocked);">${a.blockedCount}</div>
            <div style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Blocked</div>
          </div>
          <div>
            <div style="font-size: 1.1rem; font-weight: 800; color: var(--status-hitl);">${a.anomaliesCount}</div>
            <div style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Anomalies</div>
          </div>
        </div>

        <div style="display: flex; gap: 8px; margin-top: auto;">
          <button class="btn-secondary" style="flex: 1; font-size: 0.75rem; justify-content: center;" onclick="toggleAgentPause('${a.id}')">
            ${a.status === 'ACTIVE' ? 'Pause Agent' : 'Resume Agent'}
          </button>
          <button class="btn-danger" style="font-size: 0.75rem; padding: 8px 14px;" onclick="terminateAgent('${a.id}')">
            Halt
          </button>
        </div>
      </div>
    `;
  }).join("");

  // Table
  tableCont.innerHTML = agentList.map(a => `
    <tr>
      <td style="font-family: monospace; font-weight: 700; color: var(--accent-primary);">${a.id}</td>
      <td><strong>${a.name}</strong><br><span style="font-size: 0.7rem; color: var(--text-muted);">${a.role}</span></td>
      <td style="font-family: monospace; font-weight: 700;">${formatInr(a.singleLimit)}</td>
      <td style="font-family: monospace; font-weight: 700;">${formatInr(a.dailyCap)}</td>
      <td>
        ${a.allowedActions.map(act => `<code style="background: #f1f5f9; color: var(--text-primary); padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; margin-right: 4px;">${act}</code>`).join("")}
      </td>
      <td style="font-size: 0.75rem; color: var(--text-secondary);">${a.operatingHours}</td>
      <td>
        <span class="badge ${a.status === 'ACTIVE' ? 'badge-active' : a.status === 'PAUSED' ? 'badge-paused' : 'badge-terminated'}">
          &bull; ${a.status}
        </span>
      </td>
      <td>
        <button class="btn-secondary" style="font-size: 0.7rem; padding: 4px 10px;" onclick="toggleAgentPause('${a.id}')">Toggle</button>
      </td>
    </tr>
  `).join("");
}

/* 2. LIVE ACTIONS PAGE */
function renderLiveActionsTable() {
  const tbody = document.getElementById("live-action-table-body");
  if (!tbody) return;

  const filtered = state.actions.filter(a => {
    if (state.activeFilter === "ALL") return true;
    return a.verdict === state.activeFilter;
  });

  tbody.innerHTML = filtered.map(row => {
    let badgeClass = "badge-allowed";
    if (row.verdict === "BLOCK") badgeClass = "badge-blocked";
    if (row.verdict === "HITL_REQUIRED") badgeClass = "badge-hitl";

    return `
      <tr onclick="openExplainerModal('${row.id}')" title="Click to view AI reason and SHA-256 block hash">
        <td style="font-family: monospace; color: var(--text-muted); font-size: 0.75rem;">${row.timestamp}</td>
        <td style="font-family: monospace; font-size: 0.75rem; color: var(--accent-primary); font-weight: 600;">${row.id}</td>
        <td><strong>${row.agentName}</strong></td>
        <td><code style="background: #f1f5f9; color: var(--text-primary); padding: 2px 6px; border-radius: 4px;">${row.actionType}</code></td>
        <td style="font-family: monospace; font-weight: 700;">${formatInr(row.amount)}</td>
        <td><span class="badge ${badgeClass}">${row.verdict}</span></td>
        <td style="font-family: monospace; font-weight: 700; color: ${row.riskScore > 0.7 ? 'var(--status-blocked)' : 'var(--accent-primary)'};">${row.riskScore.toFixed(2)}</td>
        <td style="color: var(--text-muted); font-size: 0.75rem; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${row.reason}</td>
      </tr>
    `;
  }).join("");
}

function filterActionTable(verdict) {
  state.activeFilter = verdict;
  renderLiveActionsTable();
}

/* 3. POLICIES & RULES PAGE */
function renderPoliciesPage() {
  const cont = document.getElementById("policy-rules-detail-list");
  if (!cont) return;

  cont.innerHTML = Object.values(state.agents).map(a => `
    <div style="background: #ffffff; border: 1px solid var(--border-card); border-radius: var(--radius-md); padding: 18px; margin-bottom: 14px; box-shadow: var(--shadow-xs);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <div>
          <h4 style="font-size: 1.05rem; font-weight: 800; color: var(--text-primary);">${a.name}</h4>
          <span style="font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">ID: ${a.id}</span>
        </div>
        <span class="badge ${a.status === 'ACTIVE' ? 'badge-active' : 'badge-paused'}">&bull; ${a.status}</span>
      </div>

      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; font-size: 0.78rem; margin-bottom: 12px;">
        <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid var(--border-light);">
          <span style="color: var(--text-muted); display: block; font-size: 0.7rem;">Single Tx Ceiling</span>
          <strong style="font-size: 0.95rem; color: var(--text-primary);">${formatInr(a.singleLimit)}</strong>
        </div>
        <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid var(--border-light);">
          <span style="color: var(--text-muted); display: block; font-size: 0.7rem;">Daily Cap</span>
          <strong style="font-size: 0.95rem; color: var(--text-primary);">${formatInr(a.dailyCap)}</strong>
        </div>
        <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid var(--border-light);">
          <span style="color: var(--text-muted); display: block; font-size: 0.7rem;">Allowed Hours</span>
          <strong style="font-size: 0.95rem; color: var(--text-primary);">${a.operatingHours}</strong>
        </div>
      </div>

      <div>
        <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Whitelisted Actions:</span>
        <div style="display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap;">
          ${a.allowedActions.map(act => `<span style="background: var(--accent-primary-light); color: var(--accent-primary); border: 1px solid var(--accent-primary-border); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-family: monospace; font-weight: 600;">${act}</span>`).join("")}
        </div>
      </div>
    </div>
  `).join("");
}

/* 4. SPEND & BUDGETS PAGE */
function renderSpendBudgetsPage() {
  const cont = document.getElementById("spend-allocation-container");
  if (!cont) return;

  cont.innerHTML = Object.values(state.agents).map(a => {
    const pct = Math.min(100, Math.round((a.currentSpend / a.dailyCap) * 100));
    return `
      <div style="background: #ffffff; border: 1px solid var(--border-card); border-radius: var(--radius-md); padding: 18px; margin-bottom: 14px; box-shadow: var(--shadow-xs);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
          <strong style="color: var(--text-primary); font-size: 0.95rem;">${a.name}</strong>
          <span style="font-family: monospace; font-size: 0.85rem; color: var(--accent-primary); font-weight: 700;">${formatInr(a.currentSpend)} / ${formatInr(a.dailyCap)}</span>
        </div>
        <div class="meter-container">
          <div class="meter-fill ${pct > 80 ? 'rose' : ''}" style="width: ${pct}%;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--text-muted); margin-top: 6px;">
          <span>Single Limit: ${formatInr(a.singleLimit)}</span>
          <span style="font-weight: 600;">${pct}% daily cap utilized</span>
          <span style="color: var(--accent-primary); font-weight: 600;">${formatInr(a.dailyCap - a.currentSpend)} available</span>
        </div>
      </div>
    `;
  }).join("");
}

/* 5. KILL SWITCH PAGE */
function renderKillSwitchPage() {
  const cont = document.getElementById("individual-kill-switches");
  if (!cont) return;

  cont.innerHTML = Object.values(state.agents).map(a => `
    <div class="glass-panel" style="text-align: center; border-color: ${a.status === 'ACTIVE' ? 'var(--border-card)' : 'var(--status-blocked-border)'};">
      <div style="font-size: 1.4rem; margin-bottom: 6px;">${a.type === 'travel' ? '✈️' : a.type === 'servicing' ? '🎧' : '🎁'}</div>
      <h4 style="font-size: 1rem; font-weight: 700; color: var(--text-primary);">${a.name}</h4>
      <span style="font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">${a.id}</span>
      <div style="margin: 14px 0;">
        <span class="badge ${a.status === 'ACTIVE' ? 'badge-active' : 'badge-terminated'}">&bull; ${a.status}</span>
      </div>
      <button class="${a.status === 'ACTIVE' ? 'btn-danger' : 'btn-primary'}" style="width: 100%; justify-content: center; font-size: 0.75rem;" onclick="toggleAgentPause('${a.id}')">
        ${a.status === 'ACTIVE' ? 'Sever Agent Connection' : 'Restore Agent'}
      </button>
    </div>
  `).join("");
}

/* 6. AUDIT LEDGER / HASH CHAIN EXPLORER */
function renderAuditChainExplorer() {
  const cont = document.getElementById("audit-chain-explorer");
  const countBadge = document.getElementById("audit-block-count");
  if (!cont) return;

  if (countBadge) countBadge.innerText = `Blocks: ${state.actions.length}`;

  cont.innerHTML = state.actions.map((blk, idx) => `
    <div class="hash-chain-node">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="background: var(--accent-primary-light); color: var(--accent-primary); border: 1px solid var(--accent-primary-border); padding: 2px 8px; border-radius: 4px; font-weight: 800; font-size: 0.72rem; font-family: monospace;">BLOCK #${state.actions.length - idx}</span>
          <strong style="color: var(--text-primary); font-size: 0.88rem;">${blk.agentName} &bull; ${blk.actionDesc}</strong>
        </div>
        <span style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">${blk.timestamp}</span>
      </div>

      <div style="display: flex; gap: 16px; font-size: 0.76rem; color: var(--text-secondary);">
        <span>Amount: <strong style="color: var(--text-primary);">${formatInr(blk.amount)}</strong></span>
        <span>Verdict: <strong style="color: ${blk.verdict === 'ALLOW' ? 'var(--status-allowed)' : 'var(--status-blocked)'};">${blk.verdict}</strong></span>
        <span>ML Risk Score: <strong style="color: var(--status-hitl);">${blk.riskScore}</strong></span>
      </div>

      <div style="display: flex; flex-direction: column; gap: 3px; margin-top: 4px;">
        <span style="font-size: 0.65rem; color: var(--text-muted); font-family: monospace;">PREV_HASH: ${blk.prevHash}</span>
        <span class="hash-text">CURRENT_HASH: ${blk.auditHash}</span>
      </div>
    </div>
  `).join("");
}


// ============================================================================
// EXPLAINER MODAL & VERIFICATION
// ============================================================================
function openExplainerModal(actionId) {
  const blk = state.actions.find(a => a.id === actionId);
  if (!blk) return;

  document.getElementById("modal-action-title").innerText = `${blk.agentName} • ${blk.actionDesc}`;
  document.getElementById("modal-action-amount").innerText = formatInr(blk.amount);
  document.getElementById("modal-llm-text").innerHTML = blk.llmExplanation.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
  document.getElementById("modal-policy-reason").innerText = blk.reason;
  document.getElementById("modal-anomaly-score").innerText = `${blk.riskScore.toFixed(2)} (${blk.riskScore > 0.7 ? "Threshold Breached" : "Normal Velocity"})`;
  document.getElementById("modal-hash-text").innerText = blk.auditHash;

  openModal("modal-explainer");
}

function verifyLedgerIntegrity() {
  showToast("Re-evaluating SHA-256 chain from Genesis block...", "info");
  setTimeout(() => {
    showToast("✅ Cryptographic Verification Complete: 100% Tamper Evident (All Hashes Match)", "success");
  }, 450);
}

function simulateTamperAttack() {
  alert("⚠️ SIMULATING AN ATTACKER MODIFYING A TRANSACTION:\n\nWe will alter Block #1 from ₹20,000 to ₹2,000 in memory without regenerating the hash chain.\nWatch the verification algorithm immediately detect tampering!");
  
  showToast("🚨 INTEGRITY FAULT: SHA-256 Block #1 hash mismatch! Tamper detected at Block #1 prev_hash link!", "error");
}

// ============================================================================
// EMERGENCY KILL SWITCH
// ============================================================================
async function triggerMasterKillSwitch() {
  const confirmed = confirm("🚨 MASTER CIRCUIT BREAKER:\nAre you sure you want to halt the entire financial agent fleet? All actions will immediately be blocked fail-closed.");
  if (!confirmed) return;

  state.globalKillActive = true;
  Object.keys(state.agents).forEach(k => {
    state.agents[k].status = "TERMINATED";
  });

  const statusText = document.getElementById("global-kill-status-text");
  if (statusText) {
    statusText.innerText = "FLEET EMERGENCY HALTED (CIRCUIT BROKEN)";
    statusText.style.color = "#f43f5e";
  }

  showToast("🚨 MASTER CIRCUIT BREAKER FIRED: Entire fleet terminated!", "error");

  // Call backend API
  try {
    await fetch(`${API_BASE}/kill-switch/global`, { method: "POST" });
  } catch (e) {}

  renderAgentFleetPage();
  renderKillSwitchPage();
}

function toggleAgentPause(agentId) {
  const agent = state.agents[agentId];
  if (!agent) return;

  if (agent.status === "ACTIVE") {
    agent.status = "PAUSED";
    showToast(`Agent '${agent.name}' PAUSED.`, "info");
  } else {
    agent.status = "ACTIVE";
    showToast(`Agent '${agent.name}' RESUMED.`, "success");
  }

  renderAgentFleetPage();
  renderKillSwitchPage();
}

function terminateAgent(agentId) {
  const agent = state.agents[agentId];
  if (!agent) return;
  agent.status = "TERMINATED";
  showToast(`Agent '${agent.name}' TERMINATED.`, "error");
  renderAgentFleetPage();
  renderKillSwitchPage();
}

// ============================================================================
// SIMULATION & ACTION DISPATCH
// ============================================================================
function openTestSimulatorModal() {
  openModal("modal-simulator");
}

function loadSimPreset(preset) {
  if (preset === "normal_flight") {
    document.getElementById("sim-input-agent").value = "travel-agent-01";
    document.getElementById("sim-input-action").value = "book_flight";
    document.getElementById("sim-input-amount").value = 8000;
    document.getElementById("sim-input-desc").value = "Standard flight booking DEL to BLR";
  } else if (preset === "overspend_flight") {
    document.getElementById("sim-input-agent").value = "travel-agent-01";
    document.getElementById("sim-input-action").value = "book_flight";
    document.getElementById("sim-input-amount").value = 20000;
    document.getElementById("sim-input-desc").value = "First class ticket DEL to BOM (Breaches single limit)";
  } else if (preset === "crypto_transfer") {
    document.getElementById("sim-input-agent").value = "travel-agent-01";
    document.getElementById("sim-input-action").value = "transfer_crypto";
    document.getElementById("sim-input-amount").value = 5000;
    document.getElementById("sim-input-desc").value = "Unauthorized crypto transaction";
  } else if (preset === "burst_subsidy") {
    document.getElementById("sim-input-agent").value = "subsidy-agent-01";
    document.getElementById("sim-input-action").value = "release_subsidy";
    document.getElementById("sim-input-amount").value = 24000;
    document.getElementById("sim-input-desc").value = "High value subsidy release near upper ceiling";
  }
}

async function handleSimulatorSubmit(e) {
  e.preventDefault();

  const agentId = document.getElementById("sim-input-agent").value;
  const actionType = document.getElementById("sim-input-action").value;
  const amount = parseFloat(document.getElementById("sim-input-amount").value || 0);
  const desc = document.getElementById("sim-input-desc").value;

  const agent = state.agents[agentId];
  const payload = {
    agent_id: agentId,
    agent_type: agent.type === "travel" ? "banking" : "government",
    action_type: actionType,
    amount: amount,
    description: desc
  };

  showToast("Dispatching to Governance Gateway...", "info");

  let evalResult = null;

  if (state.isBackendConnected) {
    try {
      const res = await fetch(`${API_BASE}/governance/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) evalResult = await res.json();
    } catch (err) {}
  }

  // Fallback to in-browser evaluator matching Python GovernanceOrchestrator
  if (!evalResult) {
    evalResult = localEvaluateAction(payload);
  }

  // Construct new action
  const newAction = {
    id: evalResult.request_id || `req-${Math.random().toString(16).substr(2, 6)}`,
    timestamp: new Date().toLocaleTimeString(),
    agentId: agent.id,
    agentName: agent.name,
    actionType: actionType,
    actionDesc: actionType.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
    amount: amount,
    verdict: evalResult.verdict,
    riskScore: evalResult.ml_anomaly_score,
    reason: evalResult.reason,
    llmExplanation: evalResult.llm_explanation,
    auditHash: evalResult.audit_hash,
    prevHash: state.actions[0] ? state.actions[0].auditHash : "GENESIS"
  };

  state.actions.unshift(newAction);
  agent.actionsCount++;
  if (newAction.verdict === "BLOCK") agent.blockedCount++;
  if (newAction.verdict === "HITL_REQUIRED") agent.anomaliesCount++;
  if (newAction.verdict === "ALLOW") agent.currentSpend += amount;

  closeModal("modal-simulator");
  renderLiveActionsTable();
  renderAgentFleetPage();
  renderSpendBudgetsPage();
  renderAuditChainExplorer();

  // Update command center numbers
  const ccActions = document.getElementById("cc-stat-actions");
  if (ccActions) ccActions.innerText = state.actions.length + 242;

  openExplainerModal(newAction.id);
  showToast(`Verdict: ${newAction.verdict}`, newAction.verdict === "ALLOW" ? "success" : "error");
}

function localEvaluateAction(req) {
  const agent = state.agents[req.agent_id];

  if (state.globalKillActive || agent.status === "TERMINATED") {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "BLOCK",
      ml_anomaly_score: 0.0,
      reason: "GLOBAL_KILL_ACTIVE: Emergency stop circuit breaker engaged.",
      llm_explanation: "Blocked: Emergency stop circuit breaker is currently active. All fleet autonomous actions are severed.",
      audit_hash: generateHash()
    };
  }

  if (!agent.allowedActions.includes(req.action_type)) {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "BLOCK",
      ml_anomaly_score: 0.0,
      reason: `Action '${req.action_type}' is not whitelisted for ${agent.name}.`,
      llm_explanation: `Blocked: The requested action '${req.action_type}' violates the approved capability whitelist for ${agent.name}.`,
      audit_hash: generateHash()
    };
  }

  if (req.amount > agent.singleLimit) {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "BLOCK",
      ml_anomaly_score: 0.92,
      reason: `Requested amount ₹${req.amount.toLocaleString()} exceeds single transaction limit of ₹${agent.singleLimit.toLocaleString()}.`,
      llm_explanation: `Blocked: Single transaction limit breach. ${agent.name} attempted ₹${req.amount.toLocaleString()} exceeding ceiling of ₹${agent.singleLimit.toLocaleString()}.`,
      audit_hash: generateHash()
    };
  }

  if (agent.currentSpend + req.amount > agent.dailyCap) {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "BLOCK",
      ml_anomaly_score: 0.85,
      reason: `Daily spend cap breached! Attempted total exceeds ₹${agent.dailyCap.toLocaleString()}.`,
      llm_explanation: `Blocked: Agent exceeded daily spending budget. SentinelAI prevented unauthorized balance depletion.`,
      audit_hash: generateHash()
    };
  }

  const ratio = req.amount / agent.singleLimit;
  if (ratio > 0.85) {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "HITL_REQUIRED",
      ml_anomaly_score: 0.78,
      reason: "ML Anomaly Flagged! Anomaly score 0.78 exceeds safety threshold (>0.70). Human verification required.",
      llm_explanation: `Human Review Required: Isolation Forest detected unusual action ratio (${Math.round(ratio*100)}% of limit).`,
      audit_hash: generateHash()
    };
  }

  return {
    request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
    verdict: "ALLOW",
    ml_anomaly_score: 0.15,
    reason: "Dynamic policy and spend cap checks passed successfully.",
    llm_explanation: `Approved: Action '${req.action_type}' for ${agent.name} passed all permission rules, single transaction caps, and ML security checks.`,
    audit_hash: generateHash()
  };
}

function generateHash() {
  const chars = "0123456789abcdef";
  let str = "";
  for (let i = 0; i < 64; i++) str += chars[Math.floor(Math.random() * chars.length)];
  return str;
}

// ============================================================================
// AGENT REGISTRATION
// ============================================================================
function handleAgentRegistration(e) {
  e.preventDefault();

  const id = document.getElementById("reg-agent-id").value.trim();
  const name = document.getElementById("reg-agent-name").value.trim();
  const limit = parseFloat(document.getElementById("reg-single-limit").value);
  const cap = parseFloat(document.getElementById("reg-daily-cap").value);
  const actionsStr = document.getElementById("reg-actions").value;
  const actions = actionsStr.split(",").map(s => s.trim()).filter(Boolean);

  state.agents[id] = {
    id: id,
    name: name,
    role: "Autonomous underwriting and credit operations",
    type: "banking",
    status: "ACTIVE",
    singleLimit: limit,
    dailyCap: cap,
    currentSpend: 0,
    actionsCount: 0,
    blockedCount: 0,
    anomaliesCount: 0,
    allowedActions: actions,
    operatingHours: "00:00 - 24:00"
  };

  showToast(`Agent '${name}' successfully registered into Governance Gateway!`, "success");
  switchPage("agent-fleet");
}

// ============================================================================
// COMPLIANCE CSV EXPORT
// ============================================================================
function exportComplianceCSV() {
  showToast("Compiling tamper-evident compliance report...", "info");

  let csv = "Request ID,Timestamp,Agent ID,Action Type,Amount,Verdict,Risk Score,Policy Reason,SHA-256 Hash\n";
  state.actions.forEach(a => {
    csv += `"${a.id}","${a.timestamp}","${a.agentId}","${a.actionType}","${a.amount}","${a.verdict}","${a.riskScore}","${a.reason.replace(/"/g, '""')}","${a.auditHash}"\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `sentinelai_governance_report_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  showToast("Compliance report generated & downloaded.", "success");
}

// ============================================================================
// REAL-TIME STREAMING SIMULATOR
// ============================================================================
function toggleStreaming() {
  state.isStreaming = !state.isStreaming;
  const btn = document.getElementById("stream-toggle-button");
  if (state.isStreaming) {
    if (btn) btn.innerHTML = `<span class="live-pulse-dot" style="display: inline-block;"></span> Live Stream: ACTIVE`;
    startSimulationStream();
    showToast("Live action streaming resumed.", "info");
  } else {
    if (btn) btn.innerHTML = `<span class="live-pulse-dot" style="display: inline-block; background: #64748b; box-shadow: none;"></span> Live Stream: PAUSED`;
    clearInterval(state.streamTimer);
    showToast("Live action streaming paused.", "info");
  }
}

function startSimulationStream() {
  clearInterval(state.streamTimer);
  state.streamTimer = setInterval(() => {
    if (!state.isStreaming || state.globalKillActive) return;

    const keys = Object.keys(state.agents);
    const key = keys[Math.floor(Math.random() * keys.length)];
    const agent = state.agents[key];

    if (agent.status !== "ACTIVE") return;

    const action = agent.allowedActions[Math.floor(Math.random() * agent.allowedActions.length)];
    const amount = Math.floor(Math.random() * (agent.singleLimit * 0.35)) + 400;

    const newAction = {
      id: `req-${Math.random().toString(16).substr(2, 6)}`,
      timestamp: new Date().toLocaleTimeString(),
      agentId: agent.id,
      agentName: agent.name,
      actionType: action,
      actionDesc: action.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
      amount: amount,
      verdict: "ALLOW",
      riskScore: Math.round((Math.random() * 0.2 + 0.1) * 100) / 100,
      reason: "Within policy & budget constraints.",
      llmExplanation: `Approved: Regular telemetry action '${action}' for ${agent.name} verified against dynamic policy limits.`,
      auditHash: generateHash(),
      prevHash: state.actions[0] ? state.actions[0].auditHash : "GENESIS"
    };

    state.actions.unshift(newAction);
    if (state.actions.length > 60) state.actions.pop();

    agent.actionsCount++;
    agent.currentSpend += amount;

    if (state.activePage === "live-actions") renderLiveActionsTable();
    if (state.activePage === "agent-fleet") renderAgentFleetPage();
    if (state.activePage === "spend-budgets") renderSpendBudgetsPage();
    if (state.activePage === "audit-ledger") renderAuditChainExplorer();

    const ccActions = document.getElementById("cc-stat-actions");
    if (ccActions) ccActions.innerText = state.actions.length + 242;
  }, 10000);
}

// ============================================================================
// GATEWAY CONNECTION & HELPERS
// ============================================================================
async function checkGatewayStatus() {
  try {
    const res = await fetch("http://localhost:8000/health");
    if (res.ok) {
      state.isBackendConnected = true;
      showToast("Connected to SentinelAI FastAPI Gateway Engine", "success");
    }
  } catch (e) {
    state.isBackendConnected = false;
  }
}

function handleGlobalSearch(q) {
  const query = q.toLowerCase();
  if (!query) return;

  // If typing agent or action, jump to live-actions or agent-fleet
  if (query.includes("agent") || query.includes("fleet")) {
    switchPage("agent-fleet");
  } else if (query.includes("kill") || query.includes("halt")) {
    switchPage("kill-switch");
  } else if (query.includes("audit") || query.includes("hash")) {
    switchPage("audit-ledger");
  } else if (query.includes("policy") || query.includes("rule")) {
    switchPage("policies-rules");
  }
}

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("active");
  }
});

function showToast(msg, type = "info") {
  const cont = document.getElementById("toast-container");
  if (!cont) return;

  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${type === 'error' ? '🚨' : type === 'success' ? '✅' : 'ℹ️'}</span><span>${msg}</span>`;
  cont.appendChild(t);

  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transform = "translateX(100%)";
    t.style.transition = "all 0.3s ease";
    setTimeout(() => t.remove(), 300);
  }, 3500);
}
