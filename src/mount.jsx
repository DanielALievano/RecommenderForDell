/**
 * mount.jsx — entry point for the Vite IIFE build.
 *
 * Exposes window.__lssNudge = { show(data), hide() }
 *
 * The userscript calls window.__lssNudge.show(data) when an SSE nudge arrives.
 * React renders inside a shadow DOM host so dell.com styles can't bleed in.
 */
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import NudgePanel from "./NudgePanel.jsx";

// ---------------------------------------------------------------------------
// Shadow DOM container
// ---------------------------------------------------------------------------
function createHost() {
  const existing = document.getElementById("lss-nudge-host");
  if (existing) existing.remove();

  const host = document.createElement("div");
  host.id = "lss-nudge-host";
  host.style.cssText = "position:fixed;inset:0;z-index:2147483644;pointer-events:none;";
  document.body.insertBefore(host, document.body.firstChild);

  const shadow = host.attachShadow({ mode: "open" });
  const container = document.createElement("div");
  // Fill the host and act as the explicit containing block for absolute children
  container.style.cssText = "position:relative;width:100%;height:100%;pointer-events:none;";
  shadow.appendChild(container);
  return { host, container };
}

// ---------------------------------------------------------------------------
// Root app — keeps React mounted so cookie state survives across show/hide
// ---------------------------------------------------------------------------
let _root = null;
let _setData = null;
let _clearDismissed = null;
let _pendingData = null; // holds data if show() is called before the component mounts

function App() {
  // Initialise with any data that arrived before we were mounted
  const [data, setData] = useState(_pendingData);
  _setData = setData;
  _pendingData = null;
  return (
    <NudgePanel
      data={data}
      onDismiss={() => setData(null)}
      onRegisterClear={(fn) => { _clearDismissed = fn; }}
    />
  );
}

function ensureRoot() {
  if (_root) return;
  const { host, container } = createHost();
  _root = createRoot(container);
  // flushSync forces React to render synchronously so _setData is
  // guaranteed to be assigned before ensureRoot() returns
  flushSync(() => {
    _root.render(<App />);
  });
}

// Mount eagerly once the DOM is ready so _setData is available before the
// first button click (avoids the async render race on first call).
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", ensureRoot);
} else {
  ensureRoot();
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------
window.__lssNudge = {
  show(data) {
    if (_setData) {
      _setData(data);
    } else {
      _pendingData = data;
      ensureRoot();
    }
  },
  hide() {
    _setData?.(null);
  },
  clearDismissed() {
    _clearDismissed?.();
  },
};
