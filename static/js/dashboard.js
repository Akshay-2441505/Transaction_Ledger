/**
 * Transaction Ledger API - Financial Dashboard Client
 * Interacts directly with the same-origin FastAPI backend endpoints.
 */

// Application State
const state = {
  activeAccountId: localStorage.getItem("active_account_id") || null,
  activeAccountName: localStorage.getItem("active_account_name") || "No Account Selected",
  recentAccounts: JSON.parse(localStorage.getItem("recent_accounts") || "[]"),
  currentFilter: null, // null | 'credit' | 'debit'
  currentPage: 1,
  limit: 10,
  totalPages: 0,
  totalRecords: 0,
  isSubmitting: false,
};

// DOM Elements
const elements = {
  // Navigation
  navItems: document.querySelectorAll(".nav-item"),
  viewSections: document.querySelectorAll(".view-section"),
  breadcrumbCurrent: document.getElementById("breadcrumbCurrent"),
  apiStatusDot: document.getElementById("apiStatusDot"),
  apiStatusText: document.getElementById("apiStatusText"),
  btnRefreshAll: document.getElementById("btnRefreshAll"),

  // Sidebar badge
  sidebarAccountName: document.getElementById("sidebarAccountName"),
  sidebarAccountId: document.getElementById("sidebarAccountId"),

  // Overview metrics
  metricBalance: document.getElementById("metricBalance"),
  metricTotalRecords: document.getElementById("metricTotalRecords"),
  metricCreditsTotal: document.getElementById("metricCreditsTotal"),
  metricDebitsTotal: document.getElementById("metricDebitsTotal"),
  recentActivityTableBody: document.getElementById("recentActivityTableBody"),
  recentActivityEmpty: document.getElementById("recentActivityEmpty"),
  chartContainer: document.getElementById("chartContainer"),

  // Account Management
  formCreateAccount: document.getElementById("formCreateAccount"),
  inputAccountHolderName: document.getElementById("inputAccountHolderName"),
  btnSubmitCreateAccount: document.getElementById("btnSubmitCreateAccount"),
  accountSelectDropdown: document.getElementById("accountSelectDropdown"),
  inputManualAccountId: document.getElementById("inputManualAccountId"),
  btnLoadManualAccount: document.getElementById("btnLoadManualAccount"),
  activeAccountDetailsCard: document.getElementById("activeAccountDetailsCard"),

  // Credit / Debit Form
  formTransaction: document.getElementById("formTransaction"),
  toggleCredit: document.getElementById("toggleCredit"),
  toggleDebit: document.getElementById("toggleDebit"),
  inputTxType: document.getElementById("inputTxType"),
  inputTxAmount: document.getElementById("inputTxAmount"),
  inputTxDescription: document.getElementById("inputTxDescription"),
  inputTxReference: document.getElementById("inputTxReference"),
  btnGenerateRef: document.getElementById("btnGenerateRef"),
  btnSubmitTransaction: document.getElementById("btnSubmitTransaction"),
  txFormAccountWarning: document.getElementById("txFormAccountWarning"),

  // Transaction History View
  historyTableBody: document.getElementById("historyTableBody"),
  historyEmptyState: document.getElementById("historyEmptyState"),
  filterAll: document.getElementById("filterAll"),
  filterCredit: document.getElementById("filterCredit"),
  filterDebit: document.getElementById("filterDebit"),
  btnPrevPage: document.getElementById("btnPrevPage"),
  btnNextPage: document.getElementById("btnNextPage"),
  pageIndicator: document.getElementById("pageIndicator"),
  paginationCountInfo: document.getElementById("paginationCountInfo"),

  // Toast Container
  toastContainer: document.getElementById("toastContainer"),
};

// Utilities
function formatINR(amount) {
  const num = parseFloat(amount);
  if (isNaN(num)) return "₹0.00";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

function formatDate(isoString) {
  if (!isoString) return "-";
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return isoString;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function showToast(title, message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  const content = document.createElement("div");
  content.className = "toast-content";

  const titleEl = document.createElement("div");
  titleEl.className = "toast-title";
  titleEl.textContent = title;

  const msgEl = document.createElement("div");
  msgEl.className = "toast-message";
  msgEl.textContent = message;

  content.appendChild(titleEl);
  content.appendChild(msgEl);

  const closeBtn = document.createElement("button");
  closeBtn.className = "toast-close";
  closeBtn.innerHTML = "&times;";
  closeBtn.onclick = () => toast.remove();

  toast.appendChild(content);
  toast.appendChild(closeBtn);

  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) {
      toast.remove();
    }
  }, 5000);
}

// Navigation Tab Switcher
function switchTab(targetViewId) {
  elements.viewSections.forEach((section) => {
    section.classList.toggle("active", section.id === targetViewId);
  });

  elements.navItems.forEach((nav) => {
    const isTarget = nav.dataset.view === targetViewId;
    nav.classList.toggle("active", isTarget);
    if (isTarget) {
      const label = nav.querySelector("span") ? nav.querySelector("span").textContent : "Overview";
      elements.breadcrumbCurrent.textContent = label;
    }
  });

  // If switched to transactions or overview, refresh active account data
  if (state.activeAccountId) {
    fetchAccountData();
  }
}

// Account Switcher and Storage
function setActiveAccount(id, name) {
  state.activeAccountId = id;
  state.activeAccountName = name || `Account (${id.substring(0, 8)}...)`;

  localStorage.setItem("active_account_id", state.activeAccountId);
  localStorage.setItem("active_account_name", state.activeAccountName);

  // Update recent accounts list (max 10)
  const existingIdx = state.recentAccounts.findIndex((acc) => acc.id === id);
  if (existingIdx !== -1) {
    state.recentAccounts[existingIdx].name = state.activeAccountName;
  } else {
    state.recentAccounts.unshift({ id, name: state.activeAccountName });
    if (state.recentAccounts.length > 10) {
      state.recentAccounts.pop();
    }
  }
  localStorage.setItem("recent_accounts", JSON.stringify(state.recentAccounts));

  renderAccountBadges();
  fetchAccountData();
}

function renderAccountBadges() {
  if (state.activeAccountId) {
    elements.sidebarAccountName.textContent = state.activeAccountName;
    elements.sidebarAccountId.textContent = state.activeAccountId;
    elements.sidebarAccountId.title = state.activeAccountId;
    if (elements.txFormAccountWarning) {
      elements.txFormAccountWarning.style.display = "none";
    }
  } else {
    elements.sidebarAccountName.textContent = "No Account Selected";
    elements.sidebarAccountId.textContent = "Create or select an account";
    if (elements.txFormAccountWarning) {
      elements.txFormAccountWarning.style.display = "block";
    }
  }

  // Populate Dropdown
  elements.accountSelectDropdown.innerHTML = '<option value="">-- Choose from recent accounts --</option>';
  state.recentAccounts.forEach((acc) => {
    const opt = document.createElement("option");
    opt.value = acc.id;
    opt.textContent = `${acc.name} (${acc.id.substring(0, 8)}...)`;
    if (acc.id === state.activeAccountId) {
      opt.selected = true;
    }
    elements.accountSelectDropdown.appendChild(opt);
  });
}

// Backend API Service
async function checkHealth() {
  try {
    const res = await fetch("/health");
    if (res.ok) {
      elements.apiStatusDot.style.backgroundColor = "var(--accent-green)";
      elements.apiStatusText.textContent = "API Online";
    } else {
      elements.apiStatusDot.style.backgroundColor = "var(--accent-red)";
      elements.apiStatusText.textContent = "API Error";
    }
  } catch (err) {
    elements.apiStatusDot.style.backgroundColor = "var(--accent-red)";
    elements.apiStatusText.textContent = "Disconnected";
  }
}

async function fetchAccountData() {
  if (!state.activeAccountId) return;

  // 1. Fetch balance
  try {
    const balRes = await fetch(`/accounts/${state.activeAccountId}/balance`);
    if (balRes.ok) {
      const balData = await balRes.json();
      elements.metricBalance.textContent = formatINR(balData.balance);
    } else if (balRes.status === 404) {
      showToast("Account Not Found", "The currently selected account was not found on the server.", "error");
      elements.metricBalance.textContent = "₹0.00";
    }
  } catch (err) {
    console.error("Failed to fetch balance:", err);
  }

  // 2. Fetch transactions for history & overview
  await fetchTransactionHistory();
}

async function fetchTransactionHistory() {
  if (!state.activeAccountId) {
    renderHistoryTable([], { total_records: 0, total_pages: 0, page: 1 });
    return;
  }

  let url = `/accounts/${state.activeAccountId}/transactions?page=${state.currentPage}&limit=${state.limit}`;
  if (state.currentFilter) {
    url += `&type=${state.currentFilter}`;
  }

  try {
    const res = await fetch(url);
    if (!res.ok) {
      if (res.status === 404) {
        renderHistoryTable([], { total_records: 0, total_pages: 0, page: 1 });
      }
      return;
    }

    const data = await res.json();
    state.totalRecords = data.pagination.total_records;
    state.totalPages = data.pagination.total_pages;

    renderHistoryTable(data.items, data.pagination);
    renderOverviewActivity(data.items);
  } catch (err) {
    console.error("Failed to fetch transaction history:", err);
  }
}

function renderHistoryTable(items, pagination) {
  elements.historyTableBody.innerHTML = "";

  if (!items || items.length === 0) {
    elements.historyEmptyState.style.display = "flex";
  } else {
    elements.historyEmptyState.style.display = "none";

    items.forEach((item) => {
      const row = document.createElement("tr");

      // Type cell
      const typeTd = document.createElement("td");
      const badge = document.createElement("span");
      badge.className = `tx-badge ${item.type}`;
      badge.textContent = item.type;
      typeTd.appendChild(badge);
      row.appendChild(typeTd);

      // Amount cell
      const amountTd = document.createElement("td");
      amountTd.className = `tx-amount tx-${item.type}`;
      amountTd.textContent = `${item.type === "credit" ? "+" : "-"}${formatINR(item.amount)}`;
      row.appendChild(amountTd);

      // Reference cell
      const refTd = document.createElement("td");
      const refSpan = document.createElement("span");
      refSpan.className = "tx-ref-badge";
      refSpan.textContent = item.reference_id;
      refTd.appendChild(refSpan);
      row.appendChild(refTd);

      // Description cell
      const descTd = document.createElement("td");
      descTd.textContent = item.description;
      row.appendChild(descTd);

      // Timestamp cell
      const timeTd = document.createElement("td");
      timeTd.className = "tx-timestamp";
      timeTd.textContent = formatDate(item.created_at);
      row.appendChild(timeTd);

      elements.historyTableBody.appendChild(row);
    });
  }

  // Update pagination controls
  elements.metricTotalRecords.textContent = pagination.total_records;
  elements.paginationCountInfo.textContent = `Showing ${items.length} of ${pagination.total_records} transactions`;
  elements.pageIndicator.textContent = `Page ${pagination.page} of ${Math.max(1, pagination.total_pages)}`;
  elements.btnPrevPage.disabled = pagination.page <= 1;
  elements.btnNextPage.disabled = pagination.page >= pagination.total_pages;
}

function renderOverviewActivity(items) {
  elements.recentActivityTableBody.innerHTML = "";

  if (!items || items.length === 0) {
    elements.recentActivityEmpty.style.display = "flex";
    elements.metricCreditsTotal.textContent = "₹0.00";
    elements.metricDebitsTotal.textContent = "₹0.00";
    renderActivityChart(0, 0);
    return;
  }

  elements.recentActivityEmpty.style.display = "none";

  // Calculate actual aggregates from current history
  let totalCredits = 0;
  let totalDebits = 0;

  items.slice(0, 5).forEach((item) => {
    const row = document.createElement("tr");

    const typeTd = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = `tx-badge ${item.type}`;
    badge.textContent = item.type;
    typeTd.appendChild(badge);
    row.appendChild(typeTd);

    const amountTd = document.createElement("td");
    amountTd.className = `tx-amount tx-${item.type}`;
    amountTd.textContent = `${item.type === "credit" ? "+" : "-"}${formatINR(item.amount)}`;
    row.appendChild(amountTd);

    const descTd = document.createElement("td");
    descTd.textContent = item.description;
    row.appendChild(descTd);

    const timeTd = document.createElement("td");
    timeTd.className = "tx-timestamp";
    timeTd.textContent = formatDate(item.created_at);
    row.appendChild(timeTd);

    elements.recentActivityTableBody.appendChild(row);
  });

  items.forEach((item) => {
    const val = parseFloat(item.amount);
    if (item.type === "credit") totalCredits += val;
    if (item.type === "debit") totalDebits += val;
  });

  elements.metricCreditsTotal.textContent = formatINR(totalCredits);
  elements.metricDebitsTotal.textContent = formatINR(totalDebits);

  renderActivityChart(totalCredits, totalDebits);
}

function renderActivityChart(credits, debits) {
  elements.chartContainer.innerHTML = "";

  const total = credits + debits;
  if (total === 0) {
    const emptyNotice = document.createElement("div");
    emptyNotice.className = "empty-state";
    emptyNotice.textContent = "No transaction volume recorded yet for activity visualization.";
    elements.chartContainer.appendChild(emptyNotice);
    return;
  }

  const creditPct = Math.round((credits / total) * 100);
  const debitPct = 100 - creditPct;

  const barChart = document.createElement("div");
  barChart.className = "bar-chart-honest";

  // Credit Bar
  const creditCol = document.createElement("div");
  creditCol.className = "chart-bar-col";
  const creditFill = document.createElement("div");
  creditFill.className = "chart-bar-fill";
  creditFill.style.backgroundColor = "var(--accent-green)";
  creditFill.style.height = `${Math.max(8, creditPct)}%`;
  const creditLabel = document.createElement("div");
  creditLabel.className = "chart-bar-label";
  creditLabel.textContent = `Credit (${creditPct}%)`;
  creditCol.appendChild(creditFill);
  creditCol.appendChild(creditLabel);

  // Debit Bar
  const debitCol = document.createElement("div");
  debitCol.className = "chart-bar-col";
  const debitFill = document.createElement("div");
  debitFill.className = "chart-bar-fill";
  debitFill.style.backgroundColor = "var(--accent-red)";
  debitFill.style.height = `${Math.max(8, debitPct)}%`;
  const debitLabel = document.createElement("div");
  debitLabel.className = "chart-bar-label";
  debitLabel.textContent = `Debit (${debitPct}%)`;
  debitCol.appendChild(debitFill);
  debitCol.appendChild(debitLabel);

  barChart.appendChild(creditCol);
  barChart.appendChild(debitCol);

  // Legend
  const legend = document.createElement("div");
  legend.className = "chart-legend";
  legend.innerHTML = `
    <div class="legend-item"><span class="legend-color" style="background:var(--accent-green);"></span> Inflow: ${formatINR(credits)}</div>
    <div class="legend-item"><span class="legend-color" style="background:var(--accent-red);"></span> Outflow: ${formatINR(debits)}</div>
  `;

  elements.chartContainer.appendChild(barChart);
  elements.chartContainer.appendChild(legend);
}

// Action Handlers
elements.formCreateAccount.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = elements.inputAccountHolderName.value.trim();
  if (!name) {
    showToast("Validation Error", "Please provide a valid account holder name.", "error");
    return;
  }

  elements.btnSubmitCreateAccount.disabled = true;
  elements.btnSubmitCreateAccount.innerHTML = '<span class="spinner"></span> Creating...';

  try {
    const res = await fetch("/accounts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    const data = await res.json();

    if (res.status === 201) {
      showToast("Account Created", `Created account for ${data.name}. Balance: ₹${data.balance}`, "success");
      elements.inputAccountHolderName.value = "";
      setActiveAccount(data.id, data.name);
      switchTab("viewOverview");
    } else {
      const errMsg = data.error?.message || "Failed to create account.";
      showToast("Error Creating Account", errMsg, "error");
    }
  } catch (err) {
    showToast("Network Error", "Unable to reach the ledger server.", "error");
  } finally {
    elements.btnSubmitCreateAccount.disabled = false;
    elements.btnSubmitCreateAccount.textContent = "Create Account";
  }
});

elements.accountSelectDropdown.addEventListener("change", (e) => {
  const selectedId = e.target.value;
  if (!selectedId) return;
  const found = state.recentAccounts.find((a) => a.id === selectedId);
  if (found) {
    setActiveAccount(found.id, found.name);
    showToast("Account Switched", `Active account: ${found.name}`, "info");
  }
});

elements.btnLoadManualAccount.addEventListener("click", async () => {
  const inputId = elements.inputManualAccountId.value.trim();
  if (!inputId) {
    showToast("Input Required", "Please enter an account UUID.", "error");
    return;
  }

  try {
    const res = await fetch(`/accounts/${inputId}/balance`);
    if (res.ok) {
      const data = await res.json();
      setActiveAccount(data.account_id, `Account (${data.account_id.substring(0, 8)}...)`);
      elements.inputManualAccountId.value = "";
      showToast("Account Loaded", `Loaded balance: ${formatINR(data.balance)}`, "success");
      switchTab("viewOverview");
    } else {
      showToast("Account Not Found", "No account matches the provided UUID.", "error");
    }
  } catch (err) {
    showToast("Network Error", "Could not verify account.", "error");
  }
});

// Transaction Type Toggles
elements.toggleCredit.addEventListener("click", () => {
  elements.toggleCredit.classList.add("active", "credit");
  elements.toggleDebit.classList.remove("active", "debit");
  elements.inputTxType.value = "credit";
  elements.btnSubmitTransaction.textContent = "Submit Credit Transaction";
});

elements.toggleDebit.addEventListener("click", () => {
  elements.toggleDebit.classList.add("active", "debit");
  elements.toggleCredit.classList.remove("active", "credit");
  elements.inputTxType.value = "debit";
  elements.btnSubmitTransaction.textContent = "Submit Debit Transaction";
});

// Auto Reference Generator Helper
elements.btnGenerateRef.addEventListener("click", () => {
  const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
  const timestamp = Date.now().toString(36).toUpperCase();
  elements.inputTxReference.value = `TX-${timestamp}-${randomSuffix}`;
});

// Submit Transaction
elements.formTransaction.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!state.activeAccountId) {
    showToast("Account Required", "Please select or create an account first.", "error");
    switchTab("viewAccounts");
    return;
  }

  const type = elements.inputTxType.value;
  const amountStr = elements.inputTxAmount.value.trim();
  const description = elements.inputTxDescription.value.trim();
  const reference_id = elements.inputTxReference.value.trim();

  if (!amountStr || isNaN(parseFloat(amountStr)) || parseFloat(amountStr) <= 0) {
    showToast("Validation Error", "Amount must be a positive number greater than 0.", "error");
    return;
  }

  if (!description) {
    showToast("Validation Error", "Description is required.", "error");
    return;
  }

  if (!reference_id) {
    showToast("Validation Error", "Reference ID is required.", "error");
    return;
  }

  elements.btnSubmitTransaction.disabled = true;
  elements.btnSubmitTransaction.innerHTML = '<span class="spinner"></span> Processing Transaction...';

  try {
    const res = await fetch(`/accounts/${state.activeAccountId}/transactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type,
        amount: amountStr,
        description,
        reference_id,
      }),
    });

    const data = await res.json();

    if (res.status === 201) {
      showToast(
        "Transaction Approved",
        `Successfully applied ${type}. New balance: ${formatINR(data.account_balance)}`,
        "success"
      );
      elements.inputTxAmount.value = "";
      elements.inputTxDescription.value = "";
      elements.inputTxReference.value = "";

      // Refresh balance & history
      await fetchAccountData();
    } else if (res.status === 409) {
      const code = data.error?.code;
      if (code === "INSUFFICIENT_BALANCE") {
        showToast("Insufficient Balance (409)", "The account does not have sufficient funds for this debit. Balance was not changed.", "error");
      } else if (code === "DUPLICATE_REFERENCE") {
        showToast("Duplicate Reference (409)", `Reference ID "${reference_id}" was already processed for this account.`, "error");
      } else {
        showToast("Conflict (409)", data.error?.message || "Transaction conflict.", "error");
      }
    } else if (res.status === 422) {
      const firstError = data.error?.details?.errors?.[0]?.message || "Validation failed on submitted fields.";
      showToast("Validation Error (422)", firstError, "error");
    } else {
      showToast("Error", data.error?.message || "Transaction failed.", "error");
    }
  } catch (err) {
    showToast("Network Error", "Could not complete transaction request.", "error");
  } finally {
    elements.btnSubmitTransaction.disabled = false;
    elements.btnSubmitTransaction.textContent = type === "credit" ? "Submit Credit Transaction" : "Submit Debit Transaction";
  }
});

// Filter Bar
elements.filterAll.addEventListener("click", () => {
  state.currentFilter = null;
  state.currentPage = 1;
  updateFilterPills(elements.filterAll);
  fetchTransactionHistory();
});

elements.filterCredit.addEventListener("click", () => {
  state.currentFilter = "credit";
  state.currentPage = 1;
  updateFilterPills(elements.filterCredit);
  fetchTransactionHistory();
});

elements.filterDebit.addEventListener("click", () => {
  state.currentFilter = "debit";
  state.currentPage = 1;
  updateFilterPills(elements.filterDebit);
  fetchTransactionHistory();
});

function updateFilterPills(activeBtn) {
  [elements.filterAll, elements.filterCredit, elements.filterDebit].forEach((b) => b.classList.remove("active"));
  activeBtn.classList.add("active");
}

// Pagination Controls
elements.btnPrevPage.addEventListener("click", () => {
  if (state.currentPage > 1) {
    state.currentPage--;
    fetchTransactionHistory();
  }
});

elements.btnNextPage.addEventListener("click", () => {
  if (state.currentPage < state.totalPages) {
    state.currentPage++;
    fetchTransactionHistory();
  }
});

elements.btnRefreshAll.addEventListener("click", () => {
  checkHealth();
  if (state.activeAccountId) {
    fetchAccountData();
    showToast("Refreshed", "Account balance and history reloaded.", "info");
  }
});

// Setup Tab Navigation
elements.navItems.forEach((item) => {
  item.addEventListener("click", () => {
    const viewId = item.dataset.view;
    if (viewId) {
      switchTab(viewId);
    }
  });
});

// Initial Bootstrap
window.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  renderAccountBadges();
  if (state.activeAccountId) {
    fetchAccountData();
  } else {
    // Prompt user to select/create
    elements.metricBalance.textContent = "₹0.00";
    elements.metricTotalRecords.textContent = "0";
  }
});
