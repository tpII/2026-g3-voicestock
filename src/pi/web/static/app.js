const POLL_INTERVAL_MS = 1000;
const RETRY_INTERVAL_MS = 2000;

const connectionStatus = document.querySelector("#connection-status");
const connectionLabel = document.querySelector("#connection-label");
const loadingMessage = document.querySelector("#loading-message");
const systemMessage = document.querySelector("#system-message");
const emptyState = document.querySelector("#empty-state");
const idleHeadline = document.querySelector("#idle-headline");
const idleDetail = document.querySelector("#idle-detail");
const operatorMessage = document.querySelector("#operator-message");
const activityState = document.querySelector("#activity-state");
const activityHeadline = document.querySelector("#activity-headline");
const activityDetail = document.querySelector("#activity-detail");
const pendingCard = document.querySelector("#pending-card");
const operationNotice = document.querySelector("#operation-notice");
const confirmationMessage = document.querySelector("#confirmation-message");
const fieldProduct = document.querySelector("#field-product");
const fieldOperation = document.querySelector("#field-operation");
const fieldQuantity = document.querySelector("#field-quantity");
const fieldUnit = document.querySelector("#field-unit");
const recognizedSection = document.querySelector("#recognized-section");
const recognizedText = document.querySelector("#recognized-text");
const cancelButton = document.querySelector("#cancel-button");
const confirmButton = document.querySelector("#confirm-button");
const feedback = document.querySelector("#feedback");

const state = {
  operation: null,
  snapshot: null,
  resolving: false,
  failureOperationId: null,
  pollDelayMs: POLL_INTERVAL_MS,
};

let queue = Promise.resolve();
let pollTimer = 0;
let feedbackTimer = 0;
let renderedSignature = "";

function enqueue(task) {
  const run = queue.then(task, task);
  queue = run.then(
    () => undefined,
    () => undefined,
  );
  return run;
}

function setConnection(kind, label) {
  if (
    connectionStatus.dataset.state === kind &&
    connectionLabel.textContent === label
  ) {
    return;
  }
  connectionStatus.dataset.state = kind;
  connectionLabel.textContent = label;
}

function hidePanels() {
  loadingMessage.hidden = true;
  systemMessage.hidden = true;
  emptyState.hidden = true;
  activityState.hidden = true;
  pendingCard.hidden = true;
}

function showFeedback(message) {
  feedback.hidden = false;
  feedback.textContent = message;
  window.clearTimeout(feedbackTimer);
  feedbackTimer = window.setTimeout(() => {
    feedback.hidden = true;
    feedback.textContent = "";
  }, 2800);
}

function showFailure(operationId) {
  state.failureOperationId = operationId;
  operationNotice.hidden = false;
  operationNotice.textContent =
    "No se pudo confirmar la operación.\n\nLa operación sigue pendiente.\nPodés intentar nuevamente.";
}

function clearFailure() {
  state.failureOperationId = null;
  operationNotice.hidden = true;
  operationNotice.textContent = "";
}

function setBusy(action) {
  cancelButton.disabled = true;
  confirmButton.disabled = true;
  if (action === "confirm") {
    confirmButton.textContent = "Confirmando...";
    return;
  }
  cancelButton.textContent = "Cancelando...";
}

function setIdleButtons() {
  cancelButton.disabled = false;
  confirmButton.disabled = false;
  cancelButton.textContent = "Cancelar";
  confirmButton.textContent = "Confirmar";
}

function renderLoading() {
  renderedSignature = "";
  hidePanels();
  loadingMessage.hidden = false;
  setConnection("connecting", "Conectando");
}

function renderIdle(status) {
  hidePanels();
  clearFailure();
  emptyState.hidden = false;
  idleHeadline.textContent = status.headline || "";
  idleDetail.textContent = status.detail || "";
  idleDetail.hidden = !status.detail;
  if (status.operator_message) {
    operatorMessage.hidden = false;
    operatorMessage.textContent = status.operator_message;
  } else {
    operatorMessage.hidden = true;
    operatorMessage.textContent = "";
  }
  state.operation = null;
  state.snapshot = null;
  setConnection("ready", "Listo");
  state.pollDelayMs = POLL_INTERVAL_MS;
}

function renderActivity(status) {
  hidePanels();
  clearFailure();
  activityState.hidden = false;
  activityHeadline.textContent = status.headline || "";
  activityDetail.textContent = status.detail || "";
  activityDetail.hidden = !status.detail;
  state.operation = null;
  state.snapshot = null;
  setConnection("ready", "Listo");
  state.pollDelayMs = POLL_INTERVAL_MS;
}

function renderNotReady() {
  renderedSignature = "";
  hidePanels();
  clearFailure();
  systemMessage.hidden = false;
  systemMessage.textContent =
    "VoiceStock todavía no está disponible.\nReintentando conexión...";
  state.operation = null;
  state.snapshot = null;
  setConnection("unavailable", "No disponible");
  state.pollDelayMs = RETRY_INTERVAL_MS;
}

function renderDisconnected() {
  renderedSignature = "";
  hidePanels();
  clearFailure();
  systemMessage.hidden = false;
  systemMessage.textContent = "No se pudo conectar. Reintentando...";
  state.operation = null;
  state.snapshot = null;
  setConnection("unavailable", "No disponible");
  state.pollDelayMs = RETRY_INTERVAL_MS;
}

function renderRecognizedText(text) {
  const value = typeof text === "string" ? text.trim() : "";
  recognizedText.textContent = value;
  recognizedSection.hidden = value === "";
}

function sameSnapshot(operation) {
  const current = state.snapshot;
  if (!current) {
    return false;
  }
  return (
    current.operation_id === operation.operation_id &&
    current.confirmation_message === operation.confirmation_message &&
    current.product === operation.product &&
    current.operation === operation.operation &&
    current.quantity === operation.quantity &&
    current.unit === operation.unit &&
    current.recognized_text === operation.recognized_text
  );
}

function renderPending(operation) {
  const failureStillApplies = state.failureOperationId === operation.operation_id;
  if (
    sameSnapshot(operation) &&
    !pendingCard.hidden &&
    !confirmButton.disabled &&
    (state.failureOperationId === null || failureStillApplies)
  ) {
    state.operation = { operation_id: operation.operation_id };
    return;
  }
  if (!failureStillApplies) {
    clearFailure();
  }
  hidePanels();
  pendingCard.hidden = false;
  if (failureStillApplies) {
    operationNotice.hidden = false;
  }
  confirmationMessage.textContent = operation.confirmation_message ?? "";
  fieldProduct.textContent = operation.product ?? "";
  fieldOperation.textContent = operation.operation ?? "";
  fieldQuantity.textContent =
    operation.quantity === undefined || operation.quantity === null
      ? ""
      : String(operation.quantity);
  fieldUnit.textContent = operation.unit ?? "";
  renderRecognizedText(operation.recognized_text);
  state.operation = { operation_id: operation.operation_id };
  state.snapshot = operation;
  if (!state.resolving) {
    setIdleButtons();
  }
  setConnection("ready", "Listo");
  state.pollDelayMs = POLL_INTERVAL_MS;
}

async function readJson(response) {
  if (response.status === 204) {
    return null;
  }
  const text = await response.text();
  if (!text) {
    return null;
  }
  return JSON.parse(text);
}

function cycleSignature(status) {
  return JSON.stringify({
    phase: status.phase,
    headline: status.headline,
    detail: status.detail,
    operator_message: status.operator_message || "",
    pending: status.pending_operation || null,
    failure: state.failureOperationId,
  });
}

function renderStatus(status) {
  const pending = status.pending_operation;
  const pendingId = pending && pending.operation_id;
  if (state.failureOperationId !== null && state.failureOperationId !== pendingId) {
    clearFailure();
  }
  const signature = cycleSignature(status);
  if (signature === renderedSignature) {
    return;
  }
  renderedSignature = signature;
  if (
    status.phase === "wait_confirmation" &&
    status.pending_operation &&
    status.pending_operation.operation_id
  ) {
    renderPending(status.pending_operation);
    return;
  }
  if (status.phase === "recording" || status.phase === "processing") {
    renderActivity(status);
    return;
  }
  if (status.phase === "idle") {
    renderIdle(status);
    return;
  }
  renderDisconnected();
}

async function fetchCycleStatus() {
  if (state.resolving) {
    return;
  }
  try {
    const response = await fetch("/api/v1/system-status", {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (state.resolving) {
      return;
    }
    if (response.status === 200) {
      const body = await readJson(response);
      if (body && body.phase) {
        renderStatus(body);
        return;
      }
    }
    if (response.status === 503) {
      const body = await readJson(response);
      if (body && body.code === "application_not_ready") {
        renderNotReady();
        return;
      }
    }
    renderDisconnected();
  } catch {
    renderDisconnected();
  }
}

function applyResolution(status, body, action, operationId) {
  if (
    status === 200 &&
    body &&
    (body.status === "success" || body.status === "already_resolved")
  ) {
    clearFailure();
    showFeedback(action === "confirm" ? "Operación confirmada" : "Operación cancelada");
    return;
  }
  if (status === 409 && body && body.status === "stale_operation") {
    clearFailure();
    showFeedback("La operación cambió. Actualizando información...");
    return;
  }
  if (status === 409 && body && body.status === "conflict") {
    clearFailure();
    showFeedback("La operación ya fue resuelta.");
    return;
  }
  if (status === 503 && body && body.status === "execution_failed") {
    showFailure(operationId);
    return;
  }
  if (status === 503 && body && body.code === "application_not_ready") {
    renderNotReady();
  }
}

async function resolveOperation(action) {
  if (!state.operation || state.resolving) {
    return;
  }
  const operationId = state.operation.operation_id;
  state.resolving = true;
  setBusy(action);
  await enqueue(async () => {
    try {
      const response = await fetch(
        `/api/v1/pending-operation/${encodeURIComponent(operationId)}/${action}`,
        { method: "POST", cache: "no-store" },
      );
      const body = await readJson(response);
      applyResolution(response.status, body, action, operationId);
    } catch {
      renderDisconnected();
    } finally {
      state.resolving = false;
      await fetchCycleStatus();
    }
  });
}

function scheduleNextPoll() {
  window.clearTimeout(pollTimer);
  pollTimer = window.setTimeout(() => {
    enqueue(async () => {
      try {
        await fetchCycleStatus();
      } finally {
        scheduleNextPoll();
      }
    });
  }, state.pollDelayMs);
}

confirmButton.addEventListener("click", () => {
  resolveOperation("confirm");
});

cancelButton.addEventListener("click", () => {
  resolveOperation("cancel");
});

renderLoading();
enqueue(async () => {
  await fetchCycleStatus();
  scheduleNextPoll();
});
