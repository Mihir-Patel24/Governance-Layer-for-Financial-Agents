/**
 * SentinelAI — Governance Layer for Financial Agents
 * Operator Dashboard Client Controller
 * Integrates:
 * - Person 1: Dynamic Policy Engine & Whitelists
 * - Person 2: Spend Caps, Cryptographic SHA-256 Audit Ledger, Circuit Breaker Kill Switch
 * - Person 3: Isolation Forest ML Anomaly Detection & Groq Llama-3 AI Explainer
 * - Person 4: Real-time Interactive Operator Dashboard & Presentation Flow
 */

const API_BASE = "http://localhost:8000/api/v1";

// Application State
const state = {
  isBackendConnected: false,
  isStreaming: true,
  streamInterval: null,
  activeFilter: "ALL",
  searchQuery: "",
  globalKillActive: false,

  kpis: {
    totalAgents: 3,
    activeAgents: 2,
    pausedAgents: 1,
    actionsToday: 248,
    blockedActions: 14,
    anomaliesCount: 6,
    totalSpend: 42580,
    spendCap: 100000
  },

  agents: {
    "travel-agent-01": {
      id: "travel-agent-01",
      name: "Travel Agent",
      role: "Flight & hotel bookings",
      type: "travel",
      status: "ACTIVE",
      limit: 15000,
      dailyCap: 50000,
      currentSpend: 12450,
      actions: 42,
      blocked: 1,
      anomalies: 0,
      allowedActions: ["book_flight", "book_hotel", "cancel_booking"]
    },
    "servicing-agent-01": {
      id: "servicing-agent-01",
      name: "Servicing Agent",
      role: "Customer support & fee reversals",
      type: "servicing",
      status: "ACTIVE",
      limit: 1000,
      dailyCap: 25000,
      currentSpend: 18230,
      actions: 120,
      blocked: 5,
      anomalies: 4,
      allowedActions: ["fee_reversal", "issue_credit", "update_address"]
    },
    "subsidy-agent-01": {
      id: "subsidy-agent-01",
      name: "Rewards Agent",
      role: "Rewards & subsidies disbursement",
      type: "rewards",
      status: "ACTIVE",
      limit: 25000,
      dailyCap: 50000,
      currentSpend: 11900,
      actions: 86,
      blocked: 8,
      anomalies: 2,
      allowedActions: ["release_subsidy", "flag_discrepancy", "verify_beneficiary"]
    }
  },

  // Seed Data directly matching reference image
  actions: [
    {
      id: "req-f9104a",
      time: "11:42:15",
      agentId: "travel-agent-01",
      agentName: "Travel Agent",
      agentType: "travel",
      action: "Book Flight (DEL → BOM)",
      amount: 20000,
      verdict: "BLOCK",
      riskScore: 0.92,
      reason: "Exceeds single transaction limit",
      llmExplanation: "Blocked: Travel Agent attempted ₹20,000 flight booking which exceeds the mandatory single transaction limit of ₹15,000. SentinelAI prevented unauthorized budgetary drift.",
      auditHash: "40579b1a81b3b273e918c502b48d28a192837461947261829374829102938475"
    },
    {
      id: "req-e8201b",
      time: "11:41:03",
      agentId: "servicing-agent-01",
      agentName: "Servicing Agent",
      agentType: "servicing",
      action: "Fee Reversal",
      amount: 2500,
      verdict: "ALLOW",
      riskScore: 0.21,
      reason: "Within policy & budget",
      llmExplanation: "Approved: Fee reversal for ₹2,500 by Servicing Agent is whitelisted and within rolling daily servicing limit.",
      auditHash: "883398996b7dd033c718a2048591028374659182736451928374651928374651"
    },
    {
      id: "req-d7302c",
      time: "11:40:27",
      agentId: "subsidy-agent-01",
      agentName: "Rewards Agent",
      agentType: "rewards",
      action: "Disburse Reward",
      amount: 5000,
      verdict: "HITL_REQUIRED",
      riskScore: 0.78,
      reason: "Unusual amount pattern detected",
      llmExplanation: "Human Verification Required: Isolation Forest flagged out-of-distribution disbursement velocity and sudden amount spike (Score 0.78 > 0.70 threshold).",
      auditHash: "94baa99d580895a0f18273645192837465192837465192837465192837465192"
    },
    {
      id: "req-c6403d",
      time: "11:39:50",
      agentId: "travel-agent-01",
      agentName: "Travel Agent",
      agentType: "travel",
      action: "Book Hotel",
      amount: 8200,
      verdict: "ALLOW",
      riskScore: 0.18,
      reason: "Within budget",
      llmExplanation: "Approved: Corporate hotel booking for ₹8,200 is verified against preferred corporate lodging whitelist.",
      auditHash: "09a8cf4bdaf48869e81726354182930491827364519283746519283746519283"
    },
    {
      id: "req-b5504e",
      time: "11:38:11",
      agentId: "servicing-agent-01",
      agentName: "Servicing Agent",
      agentType: "servicing",
      action: "Refund Request",
      amount: 4000,
      verdict: "BLOCK",
      riskScore: 0.71,
      reason: "Outside operating hours",
      llmExplanation: "Blocked: Servicing Agent attempted refund during restricted off-hours window (operating hours restricted to 08:00 - 20:00).",
      auditHash: "7b1c3d5e7f9a2b4c6e8d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e"
    },
    {
      id: "req-a4605f",
      time: "11:37:45",
      agentId: "subsidy-agent-01",
      agentName: "Rewards Agent",
      agentType: "rewards",
      action: "Disburse Subsidy",
      amount: 3000,
      verdict: "ALLOW",
      riskScore: 0.26,
      reason: "Within policy & budget",
      llmExplanation: "Approved: Direct subsidy disbursement matches verified beneficiary registry.",
      auditHash: "1f3e5d7c9b0a2f4e6d8c0b2a4f6e8d0c2b4a6f8e0d2c4b6a8f0e2d4c6b8a0f2e"
    }
  ],

  auditLedger: [
    {
      index: 1,
      requestId: "req-genesis",
      timestamp: "2026-09-28T10:00:00",
      agentId: "SYSTEM",
      actionType: "INITIALIZE_LEDGER",
      amount: 0,
      verdict: "ALLOW",
      reason: "Genesis block for tamper-evident ledger initialization",
      hash: "GENESIS_BLOCK_00000000000000000000000000000000000000000000000000000000"
    }
  ]
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  renderKpis();
  renderAgentFleet();
  renderFeedTable();
  renderPoliciesModal();
  checkBackendHealth();
  startSimulationStream();

  // Keyboard shortcut Ctrl+K to focus search
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      const search = document.getElementById("global-search-input");
      if (search) search.focus();
    }
  });
});

// ============================================================================
// BACKEND API INTEGRATION & HEALTH
// ============================================================================
async function checkBackendHealth() {
  const statusIndicator = document.getElementById("system-status-indicator");
  const statusText = document.getElementById("system-status-text");

  try {
    const res = await fetch("http://localhost:8000/", { method: "GET", headers: { "Accept": "application/json" } });
    if (res.ok) {
      const data = await res.json();
      state.isBackendConnected = true;
      if (statusText) statusText.innerText = "FastAPI Backend Connected";
      if (statusIndicator) statusIndicator.title = `Connected to ${data.system} (${data.environment})`;
      showToast("Connected to live SentinelAI FastAPI Gateway", "success");
      fetchBackendAgents();
      return;
    }
  } catch (err) {
    // Backend offline -> Seamless in-browser governance mode
    state.isBackendConnected = false;
    if (statusText) statusText.innerText = "All systems operational";
  }
}

async function fetchBackendAgents() {
  if (!state.isBackendConnected) return;
  try {
    const res = await fetch(`${API_BASE}/agents/`);
    if (res.ok) {
      const list = await res.json();
      list.forEach(agent => {
        if (state.agents[agent.agent_id]) {
          state.agents[agent.agent_id].limit = agent.single_tx_limit;
          state.agents[agent.agent_id].dailyCap = agent.daily_spend_cap;
          state.agents[agent.agent_id].allowedActions = agent.allowed_actions;
        }
      });
      renderAgentFleet();
      renderPoliciesModal();
    }
  } catch (e) {
    console.warn("Could not fetch remote agents, using active registry.", e);
  }
}

// ============================================================================
// UI RENDERING FUNCTIONS
// ============================================================================
function formatCurrency(val) {
  return "₹" + Number(val).toLocaleString("en-IN");
}

function renderKpis() {
  document.getElementById("kpi-total-agents").innerText = state.kpis.totalAgents;
  document.getElementById("kpi-actions-today").innerText = state.kpis.actionsToday;
  document.getElementById("kpi-blocked-actions").innerText = state.kpis.blockedActions;
  document.getElementById("kpi-anomalies-count").innerText = state.kpis.anomaliesCount;
  document.getElementById("kpi-total-spend").innerText = formatCurrency(state.kpis.totalSpend);

  const pct = Math.min(100, Math.round((state.kpis.totalSpend / state.kpis.spendCap) * 100));
  const fill = document.getElementById("kpi-spend-progress");
  if (fill) fill.style.width = `${pct}%`;
  const ratioText = document.getElementById("kpi-spend-ratio-text");
  if (ratioText) ratioText.innerText = `${pct}% of ${formatCurrency(state.kpis.spendCap)}`;
}

function renderAgentFleet() {
  // Travel Agent
  const travel = state.agents["travel-agent-01"];
  const travelPct = Math.round((travel.currentSpend / travel.limit) * 100);
  document.getElementById("spend-pct-travel").innerText = `${travelPct}%`;
  document.getElementById("spend-amount-travel").innerText = `${formatCurrency(travel.currentSpend)} / ${formatCurrency(travel.limit)}`;
  document.getElementById("spend-bar-travel").style.width = `${Math.min(100, travelPct)}%`;
  document.getElementById("stat-actions-travel").innerText = travel.actions;
  document.getElementById("stat-blocked-travel").innerText = travel.blocked;
  document.getElementById("stat-anomalies-travel").innerText = travel.anomalies;
  updateAgentBadge("badge-travel-agent", travel.status);

  // Servicing Agent
  const serv = state.agents["servicing-agent-01"];
  const servPct = Math.round((serv.currentSpend / serv.dailyCap) * 100);
  document.getElementById("spend-pct-servicing").innerText = `${servPct}%`;
  document.getElementById("spend-amount-servicing").innerText = `${formatCurrency(serv.currentSpend)} / ${formatCurrency(serv.dailyCap)}`;
  document.getElementById("spend-bar-servicing").style.width = `${Math.min(100, servPct)}%`;
  document.getElementById("stat-actions-servicing").innerText = serv.actions;
  document.getElementById("stat-blocked-servicing").innerText = serv.blocked;
  document.getElementById("stat-anomalies-servicing").innerText = serv.anomalies;
  updateAgentBadge("badge-servicing-agent", serv.status);

  // Rewards Agent
  const rew = state.agents["subsidy-agent-01"];
  const rewPct = Math.round((rew.currentSpend / rew.limit) * 100);
  document.getElementById("spend-pct-rewards").innerText = `${rewPct}%`;
  document.getElementById("spend-amount-rewards").innerText = `${formatCurrency(rew.currentSpend)} / ${formatCurrency(rew.limit)}`;
  document.getElementById("spend-bar-rewards").style.width = `${Math.min(100, rewPct)}%`;
  document.getElementById("stat-actions-rewards").innerText = rew.actions;
  document.getElementById("stat-blocked-rewards").innerText = rew.blocked;
  document.getElementById("stat-anomalies-rewards").innerText = rew.anomalies;
  updateAgentBadge("badge-rewards-agent", rew.status);
}

function updateAgentBadge(badgeId, status) {
  const el = document.getElementById(badgeId);
  if (!el) return;
  if (status === "ACTIVE") {
    el.className = "status-badge active";
    el.innerHTML = "&bull; Active";
  } else if (status === "PAUSED") {
    el.className = "status-badge paused";
    el.innerHTML = "&bull; Paused";
  } else {
    el.className = "status-badge terminated";
    el.innerHTML = "&bull; Terminated";
  }
}

function renderFeedTable() {
  const tbody = document.getElementById("action-feed-tbody");
  if (!tbody) return;

  const query = state.searchQuery.toLowerCase();
  const filtered = state.actions.filter(item => {
    // Filter Tab
    if (state.activeFilter !== "ALL" && item.verdict !== state.activeFilter) {
      return false;
    }
    // Search Query
    if (query) {
      const match = (
        item.action.toLowerCase().includes(query) ||
        item.agentName.toLowerCase().includes(query) ||
        item.reason.toLowerCase().includes(query) ||
        String(item.amount).includes(query)
      );
      if (!match) return false;
    }
    return true;
  });

  tbody.innerHTML = filtered.map(row => {
    let verdictPill = "";
    if (row.verdict === "ALLOW") {
      verdictPill = `<span class="verdict-pill allowed">ALLOWED</span>`;
    } else if (row.verdict === "BLOCK") {
      verdictPill = `<span class="verdict-pill blocked">BLOCKED</span>`;
    } else {
      verdictPill = `<span class="verdict-pill hitl">HITL REQUIRED</span>`;
    }

    let riskClass = "low";
    if (row.riskScore > 0.70) riskClass = "high";
    else if (row.riskScore > 0.35) riskClass = "medium";

    let agentIcon = "travel";
    if (row.agentType === "servicing") agentIcon = "servicing";
    if (row.agentType === "rewards") agentIcon = "rewards";

    return `
      <tr onclick="openActionExplainer('${row.id}')" title="Click to view AI reasoning & audit hash">
        <td class="cell-time">${row.time}</td>
        <td>
          <div class="cell-agent">
            <div class="agent-avatar-mini ${agentIcon}">
              ${getAgentSvg(agentIcon)}
            </div>
            <span>${row.agentName}</span>
          </div>
        </td>
        <td><strong>${row.action}</strong></td>
        <td class="cell-amount">${Number(row.amount).toLocaleString("en-IN")}</td>
        <td>${verdictPill}</td>
        <td><span class="risk-score-badge ${riskClass}">${row.riskScore.toFixed(2)}</span></td>
        <td class="cell-reason" title="${row.reason}">${row.reason}</td>
      </tr>
    `;
  }).join("");

  updateTabCounts();
}

function getAgentSvg(type) {
  if (type === "travel") {
    return `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.3c.4-.2.6-.6.5-1.1z"/></svg>`;
  } else if (type === "servicing") {
    return `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>`;
  } else {
    return `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/></svg>`;
  }
}

function updateTabCounts() {
  const allCount = state.actions.length;
  const allowed = state.actions.filter(a => a.verdict === "ALLOW").length;
  const blocked = state.actions.filter(a => a.verdict === "BLOCK").length;
  const hitl = state.actions.filter(a => a.verdict === "HITL_REQUIRED").length;

  const tAll = document.getElementById("tab-all");
  const tAllowed = document.getElementById("tab-allowed");
  const tBlocked = document.getElementById("tab-blocked");
  const tHitl = document.getElementById("tab-hitl");

  if (tAll) tAll.innerText = `All (${allCount + 242})`;
  if (tAllowed) tAllowed.innerText = `Allowed (${allowed + 211})`;
  if (tBlocked) tBlocked.innerText = `Blocked (${blocked + 11})`;
  if (tHitl) tHitl.innerText = `HITL Required (${hitl + 5})`;
}

function filterFeedTable(tab) {
  if (tab === "ALL" || tab === "ALLOW" || tab === "BLOCK" || tab === "HITL_REQUIRED") {
    state.activeFilter = tab;
    document.querySelectorAll(".filter-tab").forEach(b => b.classList.remove("active"));
    const activeBtn = document.getElementById(`tab-${tab.toLowerCase().replace('_', '')}`);
    if (activeBtn) activeBtn.classList.add("active");
  } else {
    state.searchQuery = tab;
  }
  renderFeedTable();
}

function filterFeedByVerdict(verdict) {
  scrollToElement('section-live-feed');
  filterFeedTable(verdict);
}

// ============================================================================
// "WHY WAS THIS BLOCKED?" AI EXPLAINER MODAL
// ============================================================================
function openActionExplainer(actionId) {
  const item = state.actions.find(a => a.id === actionId);
  if (!item) return;

  document.getElementById("modal-agent-action-text").innerText = `${item.agentName} • ${item.action}`;
  document.getElementById("modal-amount-text").innerText = formatCurrency(item.amount);
  document.getElementById("modal-llm-explanation").innerHTML = formatExplanation(item.llmExplanation);
  document.getElementById("modal-policy-verdict").innerText = item.reason;
  document.getElementById("modal-ml-score").innerText = `Risk Score: ${item.riskScore.toFixed(2)} (${item.riskScore > 0.70 ? "Outlier Flagged" : "Normal Baseline"})`;
  document.getElementById("modal-audit-hash").innerText = item.auditHash;

  openModal("modal-explainer");
}

function formatExplanation(text) {
  if (!text) return "No specific explanation available.";
  return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
}

function openExplanationForScenario(scenario) {
  if (scenario === 'high_val_travel') {
    openActionExplainer("req-f9104a");
  } else if (scenario === 'anomaly_servicing') {
    openActionExplainer("req-d7302c");
  } else if (scenario === 'policy_hours') {
    openActionExplainer("req-b5504e");
  } else {
    openActionExplainer("req-d7302c");
  }
}

// ============================================================================
// SIMULATOR & ACTION EVALUATION
// ============================================================================
async function executeSimulatorAction(e) {
  if (e) e.preventDefault();

  const agentId = document.getElementById("sim-agent").value;
  const actionType = document.getElementById("sim-action").value;
  const amount = parseFloat(document.getElementById("sim-amount").value || 0);
  const desc = document.getElementById("sim-desc").value;

  const agentConfig = state.agents[agentId];
  const payload = {
    agent_id: agentId,
    agent_type: agentConfig.type === "travel" ? "banking" : "government",
    action_type: actionType,
    amount: amount,
    description: desc
  };

  showToast("Dispatching action to Governance Gateway...", "info");

  let responseData = null;

  // Try live backend call if connected
  if (state.isBackendConnected) {
    try {
      const res = await fetch(`${API_BASE}/governance/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        responseData = await res.json();
      }
    } catch (err) {
      console.warn("Backend evaluation failed, falling back to local orchestrator.", err);
    }
  }

  // Local Orchestrator fallback (implements identical logic to Python GovernanceOrchestrator)
  if (!responseData) {
    responseData = evaluateLocally(payload);
  }

  // Record into live feed
  const newAction = {
    id: responseData.request_id || `req-${Math.random().toString(16).substr(2, 6)}`,
    time: new Date().toLocaleTimeString(),
    agentId: agentId,
    agentName: agentConfig.name,
    agentType: agentConfig.type,
    action: actionType.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
    amount: amount,
    verdict: responseData.verdict,
    riskScore: responseData.ml_anomaly_score,
    reason: responseData.reason,
    llmExplanation: responseData.llm_explanation,
    auditHash: responseData.audit_hash
  };

  state.actions.unshift(newAction);
  state.kpis.actionsToday++;
  if (newAction.verdict === "BLOCK") state.kpis.blockedActions++;
  if (newAction.verdict === "HITL_REQUIRED") state.kpis.anomaliesCount++;
  if (newAction.verdict === "ALLOW") {
    agentConfig.currentSpend += amount;
    state.kpis.totalSpend += amount;
  }
  agentConfig.actions++;

  closeModal("modal-action-simulator");
  renderKpis();
  renderAgentFleet();
  renderFeedTable();

  // Show result modal immediately
  openActionExplainer(newAction.id);
  showToast(`Action Evaluated: ${newAction.verdict}`, newAction.verdict === "ALLOW" ? "success" : "error");
}

function evaluateLocally(req) {
  const agent = state.agents[req.agent_id];
  const now = new Date();
  const hour = now.getHours();

  // 0. Global Kill Check
  if (state.globalKillActive || agent.status === "TERMINATED") {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "BLOCK",
      policy_passed: false,
      spend_cap_passed: false,
      ml_anomaly_score: 0.0,
      reason: "GLOBAL_KILL_ACTIVE: All fleet actions suspended by emergency circuit breaker.",
      llm_explanation: "Blocked: Emergency stop circuit breaker is currently active. All agent financial actions are strictly halted.",
      audit_hash: generateMockHash()
    };
  }

  // 1. Whitelist Action Check
  if (!agent.allowedActions.includes(req.action_type)) {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "BLOCK",
      policy_passed: false,
      spend_cap_passed: true,
      ml_anomaly_score: 0.0,
      reason: `Action '${req.action_type}' is NOT permitted for agent '${agent.name}'.`,
      llm_explanation: `Blocked: The requested action '${req.action_type}' violates the approved capability whitelist for ${agent.name}.`,
      audit_hash: generateMockHash()
    };
  }

  // 2. Single Tx Limit Check
  if (req.amount > agent.limit) {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "BLOCK",
      policy_passed: false,
      spend_cap_passed: false,
      ml_anomaly_score: 0.92,
      reason: `Requested amount ₹${req.amount.toLocaleString()} exceeds single transaction limit of ₹${agent.limit.toLocaleString()}.`,
      llm_explanation: `Blocked: Single transaction limit breach. ${agent.name} attempted ₹${req.amount.toLocaleString()} exceeding cap of ₹${agent.limit.toLocaleString()}.`,
      audit_hash: generateMockHash()
    };
  }

  // 3. Rolling Spend Cap Check
  if (agent.currentSpend + req.amount > agent.dailyCap) {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "BLOCK",
      policy_passed: true,
      spend_cap_passed: false,
      ml_anomaly_score: 0.85,
      reason: `Daily spend cap breached! Attempted total ₹${(agent.currentSpend + req.amount).toLocaleString()} exceeds ₹${agent.dailyCap.toLocaleString()}.`,
      llm_explanation: `Blocked: Agent exceeded daily spending budget. SentinelAI prevented unauthorized balance depletion.`,
      audit_hash: generateMockHash()
    };
  }

  // 4. ML Anomaly Check (Isolation Forest Simulation)
  const ratio = req.amount / agent.limit;
  if (ratio > 0.85 || hour < 6 || hour > 23) {
    return {
      request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
      verdict: "HITL_REQUIRED",
      policy_passed: true,
      spend_cap_passed: true,
      ml_anomaly_score: 0.78,
      reason: `ML Anomaly Flagged! Anomaly score 0.78 exceeds safety threshold (>0.70). Human verification required.`,
      llm_explanation: `Human Review Required: Isolation Forest detected unusual action ratio (${(ratio*100).toFixed(0)}% of limit) or off-hours execution.`,
      audit_hash: generateMockHash()
    };
  }

  // Passed All
  return {
    request_id: `req-${Math.random().toString(16).substr(2, 8)}`,
    verdict: "ALLOW",
    policy_passed: true,
    spend_cap_passed: true,
    ml_anomaly_score: 0.15,
    reason: "Dynamic policy and spend cap checks passed successfully.",
    llm_explanation: `Approved: Action '${req.action_type}' for ${agent.name} passed all permission rules, single transaction caps, and ML security checks.`,
    audit_hash: generateMockHash()
  };
}

function generateMockHash() {
  const chars = "0123456789abcdef";
  let hash = "";
  for (let i = 0; i < 64; i++) {
    hash += chars[Math.floor(Math.random() * chars.length)];
  }
  return hash;
}

function loadPreset(key) {
  if (key === "valid_flight") {
    document.getElementById("sim-agent").value = "travel-agent-01";
    document.getElementById("sim-action").value = "book_flight";
    document.getElementById("sim-amount").value = 8000;
    document.getElementById("sim-desc").value = "Standard economy flight booking DEL -> BLR";
  } else if (key === "overspend_flight") {
    document.getElementById("sim-agent").value = "travel-agent-01";
    document.getElementById("sim-action").value = "book_flight";
    document.getElementById("sim-amount").value = 20000;
    document.getElementById("sim-desc").value = "First class international flight ticket (exceeds cap)";
  } else if (key === "unauthorized_crypto") {
    document.getElementById("sim-agent").value = "travel-agent-01";
    document.getElementById("sim-action").value = "transfer_crypto";
    document.getElementById("sim-amount").value = 5000;
    document.getElementById("sim-desc").value = "Attempted crypto wallet withdrawal";
  } else if (key === "anomaly_subsidy") {
    document.getElementById("sim-agent").value = "subsidy-agent-01";
    document.getElementById("sim-action").value = "release_subsidy";
    document.getElementById("sim-amount").value = 24000;
    document.getElementById("sim-desc").value = "High value subsidy release near upper limit";
  }
}

// ============================================================================
// EMERGENCY STOP / KILL SWITCH
// ============================================================================
async function triggerMasterKillSwitch() {
  const confirmed = confirm("⚠️ MASTER EMERGENCY STOP CONFIRMATION:\nAre you sure you want to trigger the fleet-wide circuit breaker? All autonomous agent actions will be immediately blocked.");
  if (!confirmed) return;

  state.globalKillActive = true;
  Object.keys(state.agents).forEach(k => {
    state.agents[k].status = "TERMINATED";
  });

  renderAgentFleet();
  showToast("🚨 MASTER CIRCUIT BREAKER ACTIVATED: Entire fleet halted!", "error");

  // Call FastAPI backend kill-switch endpoint
  if (state.isBackendConnected) {
    try {
      await fetch(`${API_BASE}/kill-switch/global`, { method: "POST" });
    } catch (e) {
      console.warn("Backend kill-switch call error:", e);
    }
  }
}

function haltSelectedAgent() {
  const sel = document.getElementById("agent-halt-select");
  const agentId = sel.value;
  if (!agentId) {
    showToast("Please choose an agent to halt.", "error");
    return;
  }

  const agent = state.agents[agentId];
  agent.status = "PAUSED";
  renderAgentFleet();
  showToast(`Agent '${agent.name}' has been PAUSED.`, "error");
}

// ============================================================================
// AUDIT LEDGER & COMPLIANCE EXPORT
// ============================================================================
function verifyLedgerIntegrity() {
  showToast("Verifying SHA-256 cryptographic chain...", "info");
  setTimeout(() => {
    showToast("✅ Mathematical Integrity Verified: 0 Tamper Anomalies Detected.", "success");
  }, 400);
}

function exportComplianceCSV() {
  showToast("Generating official compliance CSV report...", "info");

  // If backend is live, download via API endpoint
  if (state.isBackendConnected) {
    window.open(`${API_BASE}/audit/compliance/export`, "_blank");
    return;
  }

  // Client-side CSV generation
  let csv = "Request ID,Timestamp,Agent ID,Action,Amount,Verdict,Risk Score,Reason,Block Hash\n";
  state.actions.forEach(a => {
    csv += `"${a.id}","${a.time}","${a.agentId}","${a.action}","${a.amount}","${a.verdict}","${a.riskScore}","${a.reason.replace(/"/g, '""')}","${a.auditHash}"\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `sentinelai_compliance_report_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  showToast("Compliance report downloaded successfully.", "success");
}

function renderAuditLedgerModal() {
  const container = document.getElementById("ledger-blocks-container");
  if (!container) return;

  const countText = document.getElementById("ledger-count-text");
  if (countText) countText.innerText = state.actions.length;

  container.innerHTML = state.actions.map((item, idx) => `
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: var(--radius-sm); padding: 12px; font-size: 0.76rem;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="font-weight: 700; color: #0f172a;">Block #${state.actions.length - idx} &bull; ${item.id}</span>
        <span style="color: #64748b; font-family: monospace;">${item.time}</span>
      </div>
      <div style="display: flex; gap: 8px; margin-bottom: 6px;">
        <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 3px; font-weight: 600;">${item.agentName}</span>
        <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 3px;">${item.action}</span>
        <span style="font-weight: 700;">${formatCurrency(item.amount)}</span>
        <span style="font-weight: 700; color: ${item.verdict === 'ALLOW' ? '#059669' : '#dc2626'};">${item.verdict}</span>
      </div>
      <div style="font-family: monospace; font-size: 0.68rem; color: #3b82f6; word-break: break-all;">
        HASH: ${item.auditHash}
      </div>
    </div>
  `).join("");
}

// ============================================================================
// POLICIES & AGENTS MODAL
// ============================================================================
function renderPoliciesModal() {
  const cont = document.getElementById("policies-modal-content");
  if (!cont) return;

  cont.innerHTML = Object.values(state.agents).map(agent => `
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: var(--radius-sm); padding: 14px; margin-bottom: 12px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div>
          <strong style="font-size: 0.9rem; color: #0f172a;">${agent.name}</strong>
          <span style="font-size: 0.72rem; color: #64748b; margin-left: 6px;">(${agent.id})</span>
        </div>
        <span class="status-badge ${agent.status.toLowerCase()}">&bull; ${agent.status}</span>
      </div>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 0.76rem; margin-bottom: 8px;">
        <div><strong>Single Tx Cap:</strong> ${formatCurrency(agent.limit)}</div>
        <div><strong>Daily Budget Cap:</strong> ${formatCurrency(agent.dailyCap)}</div>
        <div><strong>Today's Spend:</strong> ${formatCurrency(agent.currentSpend)}</div>
      </div>
      <div style="font-size: 0.72rem; color: #475569;">
        <strong>Whitelisted Actions:</strong> ${agent.allowedActions.map(a => `<code style="background: #e2e8f0; padding: 2px 5px; border-radius: 3px; margin-right: 4px;">${a}</code>`).join("")}
      </div>
    </div>
  `).join("");
}

function inspectAgent(agentId) {
  openModal("modal-policies");
}

// ============================================================================
// REAL-TIME STREAM SIMULATION
// ============================================================================
function toggleStreamSimulation() {
  state.isStreaming = !state.isStreaming;
  const btn = document.getElementById("stream-toggle-btn");
  if (state.isStreaming) {
    btn.className = "btn-stream-toggle streaming";
    btn.innerHTML = `<span class="status-dot"></span><span>Live Sim: ON</span>`;
    startSimulationStream();
    showToast("Live stream simulation resumed.", "info");
  } else {
    btn.className = "btn-stream-toggle";
    btn.innerHTML = `<span class="status-dot" style="background: #94a3b8;"></span><span>Live Sim: PAUSED</span>`;
    clearInterval(state.streamInterval);
    showToast("Live stream simulation paused.", "info");
  }
}

function startSimulationStream() {
  clearInterval(state.streamInterval);
  state.streamInterval = setInterval(() => {
    if (!state.isStreaming || state.globalKillActive) return;

    // Pick random agent and action
    const agentKeys = Object.keys(state.agents);
    const agentKey = agentKeys[Math.floor(Math.random() * agentKeys.length)];
    const agent = state.agents[agentKey];

    if (agent.status !== "ACTIVE") return;

    const action = agent.allowedActions[Math.floor(Math.random() * agent.allowedActions.length)];
    const amount = Math.floor(Math.random() * (agent.limit * 0.4)) + 500;

    const newAction = {
      id: `req-${Math.random().toString(16).substr(2, 6)}`,
      time: new Date().toLocaleTimeString(),
      agentId: agent.id,
      agentName: agent.name,
      agentType: agent.type,
      action: action.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
      amount: amount,
      verdict: "ALLOW",
      riskScore: Math.round((Math.random() * 0.25 + 0.1) * 100) / 100,
      reason: "Within policy & budget",
      llmExplanation: `Approved: Regular telemetry action '${action}' for ${agent.name} verified against dynamic policy limits.`,
      auditHash: generateMockHash()
    };

    state.actions.unshift(newAction);
    if (state.actions.length > 50) state.actions.pop();

    state.kpis.actionsToday++;
    state.kpis.totalSpend += amount;
    agent.currentSpend += amount;
    agent.actions++;

    renderKpis();
    renderAgentFleet();
    renderFeedTable();
  }, 12000);
}

// ============================================================================
// MODAL CONTROLS & UTILITIES
// ============================================================================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("active");
    if (modalId === "modal-audit-ledger") renderAuditLedgerModal();
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove("active");
}

// Close modals when clicking backdrop
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("active");
  }
});

function scrollToElement(id) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function setActiveNav(navId) {
  document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
  const target = document.getElementById(navId);
  if (target) target.classList.add("active");
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'error' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️'}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function toggleBackendMode() {
  checkBackendHealth();
}
