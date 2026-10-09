import { useState, useCallback } from "react";

// ---------------------------------------------------------------------------
// Cookie helpers
// ---------------------------------------------------------------------------

function getCookie(name) {
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)")
  );
  return match ? decodeURIComponent(match[1]) : null;
}

function setCookie(name, value, days) {
  let cookie = `${name}=${encodeURIComponent(value)};path=/;SameSite=Lax`;
  if (days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    cookie += `;expires=${expires}`;
  }
  document.cookie = cookie;
}

function uuid() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useCookieStore() {
  // Session ID — session cookie (no expiry = tab lifetime on same domain)
  const [sessionId] = useState(() => {
    let id = getCookie("lss_sid");
    if (!id) {
      id = "s_ecid_" + uuid();
      setCookie("lss_sid", id); // no days → session cookie
    }
    return id;
  });

  // Visit number — persistent 1-year cookie
  const [visitNumber] = useState(() => {
    const n = parseInt(getCookie("lss_visit") || "0", 10) + 1;
    setCookie("lss_visit", String(n), 365);
    return n;
  });

  // Seen products — persistent 30-day cookie, survives navigation
  const [seenProducts, setSeenProducts] = useState(() => {
    try {
      return JSON.parse(getCookie("lss_products") || "[]");
    } catch {
      return [];
    }
  });

  const addProduct = useCallback((name) => {
    if (!name || name.length < 3) return;
    const clean = name.trim().replace(/\s+/g, " ").slice(0, 100);
    setSeenProducts((prev) => {
      if (prev.includes(clean)) return prev;
      const next = [...prev, clean].slice(-20);
      setCookie("lss_products", JSON.stringify(next), 30);
      return next;
    });
  }, []);

  // Dismissed nudge types — 1-day cookie so the same action_type isn't
  // shown again within the same browsing day
  const [dismissedNudges, setDismissedNudges] = useState(() => {
    try {
      return JSON.parse(getCookie("lss_dismissed") || "[]");
    } catch {
      return [];
    }
  });

  const dismissNudge = useCallback((actionType) => {
    setDismissedNudges((prev) => {
      const next = [...new Set([...prev, actionType])];
      setCookie("lss_dismissed", JSON.stringify(next), 1);
      return next;
    });
  }, []);

  const isNudgeDismissed = useCallback(
    (actionType) => dismissedNudges.includes(actionType),
    [dismissedNudges]
  );

  const clearDismissed = useCallback(() => {
    setDismissedNudges([]);
    setCookie("lss_dismissed", "[]", 1);
  }, []);

  return {
    sessionId,
    visitNumber,
    seenProducts,
    addProduct,
    dismissedNudges,
    dismissNudge,
    isNudgeDismissed,
    clearDismissed,
  };
}
