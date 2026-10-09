import React, { useState } from "react";
import { useCookieStore } from "./hooks/useCookieStore.js";

const DELL_BLUE = "#0076CE";

const FAMILY_COLORS = {
  xps:        { bg: "#0076CE", accent: "#005fa3" },
  inspiron:   { bg: "#00843D", accent: "#006830" },
  alienware:  { bg: "#1a1a1a", accent: "#00aacc" },
  "g-series": { bg: "#E85D00", accent: "#c44e00" },
  latitude:   { bg: "#344D6D", accent: "#253755" },
  precision:  { bg: "#5E2D91", accent: "#4a1f73" },
  vostro:     { bg: "#6B6B6B", accent: "#555555" },
  ultrasharp: { bg: "#0076CE", accent: "#005fa3" },
};

function familyColors(family) {
  const key = (family || "").toLowerCase().replace(/\s+/g, "-");
  return FAMILY_COLORS[key] || { bg: DELL_BLUE, accent: "#005fa3" };
}

// ─── "Curated for you" pill (unchanged) ──────────────────────────────────────
function CuratedPill({ onClick }) {
  // State-driven entrance: avoids CSS @keyframes which React 18 hoists out of
  // shadow DOM into <head>, breaking the animation scope.
  const [entered, setEntered] = useState(false);
  const [hovered, setHovered] = useState(false);

  React.useEffect(() => {
    // Double rAF so the browser paints the initial hidden state first
    const id = requestAnimationFrame(() =>
      requestAnimationFrame(() => setEntered(true))
    );
    return () => cancelAnimationFrame(id);
  }, []);

  const translateY = !entered ? "80px" : hovered ? "-4px" : "0px";

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: "absolute",
        bottom: "28px",
        left: "50%",
        transform: `translateX(-50%) translateY(${translateY})`,
        opacity: entered ? 1 : 0,
        zIndex: 2147483645,
        pointerEvents: "all",
        display: "flex",
        alignItems: "center",
        gap: "12px",
        background: "linear-gradient(135deg, #0d1b2e 0%, #0076CE 100%)",
        color: "#fff",
        padding: "13px 22px",
        borderRadius: "100px",
        boxShadow: hovered
          ? "0 16px 48px rgba(0,118,206,0.70)"
          : "0 8px 32px rgba(0,118,206,0.45)",
        cursor: "pointer",
        userSelect: "none",
        minWidth: "340px",
        border: "1px solid rgba(255,255,255,0.15)",
        transition: "opacity 0.85s cubic-bezier(0.22,1,0.36,1), transform 0.85s cubic-bezier(0.22,1,0.36,1), box-shadow 0.22s ease",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
        <span style={{ fontSize: "20px", lineHeight: 1, flexShrink: 0 }}>✦</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: "14px", letterSpacing: "0.01em" }}>
            Curated for you
          </div>
          <div style={{ fontSize: "11px", opacity: 0.78, marginTop: "2px", whiteSpace: "nowrap" }}>
            Personalized picks, ready when you are.
          </div>
        </div>
        <span
          style={{
            flexShrink: 0,
            background: "rgba(255,255,255,0.18)",
            width: "28px",
            height: "28px",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "18px",
            fontWeight: 300,
          }}
        >
          ›
        </span>
      </div>
  );
}

// ─── Individual product card ──────────────────────────────────────────────────
function ProductCard({ product }) {
  const { name, price_usd, badge, reason, highlights = [], specs, url, family } = product;
  const colors = familyColors(family);

  return (
    <div
      style={{
        minWidth: "210px",
        maxWidth: "240px",
        flex: "0 0 auto",
        display: "flex",
        flexDirection: "column",
        borderRadius: "6px",
        border: "1px solid #dde3ea",
        overflow: "hidden",
        background: "#fff",
        boxShadow: "0 2px 8px rgba(0,0,0,0.07)",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      {/* Gradient banner */}
      <div
        style={{
          background: `linear-gradient(135deg, ${colors.bg} 0%, ${colors.accent} 100%)`,
          padding: "12px 14px 14px",
          color: "#fff",
        }}
      >
        {badge && (
          <div
            style={{
              fontSize: "9px",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "1px",
              opacity: 0.82,
              marginBottom: "5px",
            }}
          >
            {badge}
          </div>
        )}
        <div style={{ fontSize: "14px", fontWeight: 700, lineHeight: 1.25 }}>
          {name || product.id}
        </div>
        {price_usd && (
          <div style={{ fontSize: "12px", fontWeight: 600, opacity: 0.88, marginTop: "5px" }}>
            From ${Number(price_usd).toLocaleString()}
          </div>
        )}
      </div>

      {/* Card body */}
      <div
        style={{
          padding: "10px 12px",
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: "8px",
        }}
      >
        {reason && (
          <div
            style={{
              fontSize: "11px",
              color: "#1e40af",
              background: "#eff6ff",
              border: "1px solid #bfdbfe",
              borderRadius: "4px",
              padding: "6px 8px",
              lineHeight: 1.45,
              fontStyle: "italic",
            }}
          >
            💡 {reason}
          </div>
        )}

        {specs && (
          <div style={{ fontSize: "10px", color: "#6b7280", lineHeight: 1.4 }}>
            {specs}
          </div>
        )}

        {highlights.length > 0 && (
          <>
            <div
              style={{
                fontSize: "9px",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.6px",
                color: "#374151",
                marginTop: "2px",
              }}
            >
              Key Features
            </div>
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "3px" }}>
              {highlights.slice(0, 3).map((h, i) => (
                <li
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "5px",
                    fontSize: "11px",
                    color: "#374151",
                  }}
                >
                  <span style={{ color: "#10b981", fontWeight: 700, flexShrink: 0, marginTop: "1px" }}>✓</span>
                  {h}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      {/* CTA */}
      <a
        href={url || "#"}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          display: "block",
          background: DELL_BLUE,
          color: "#fff",
          textDecoration: "none",
          textAlign: "center",
          padding: "9px",
          fontSize: "12px",
          fontWeight: 600,
          letterSpacing: "0.02em",
        }}
      >
        View Product →
      </a>
    </div>
  );
}

// ─── Bottom tray ──────────────────────────────────────────────────────────────
function RecommendationsTray({ data, onCollapse, onClose }) {
  const products = data?.products ?? [];
  const message = data?.message ?? "We found some picks for you — worth a look.";

  return (
    <div
      style={{
        width: "100%",
        background: "#fff",
        boxShadow: "0 -4px 24px rgba(0,0,0,0.18)",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      {/* Blue header bar */}
      <div
        style={{
          background: DELL_BLUE,
          color: "#fff",
          padding: "10px 16px",
          display: "flex",
          alignItems: "center",
          gap: "12px",
        }}
      >
        <span style={{ flex: 1, fontSize: "13px", fontWeight: 600 }}>{message}</span>
        <button
          onClick={onCollapse}
          title="Collapse"
          style={{
            background: "none",
            border: "none",
            color: "rgba(255,255,255,0.85)",
            fontSize: "13px",
            cursor: "pointer",
            padding: "0 4px",
            lineHeight: 1,
            flexShrink: 0,
          }}
        >
          ▼
        </button>
        <button
          onClick={onClose}
          title="Dismiss"
          style={{
            background: "none",
            border: "none",
            color: "rgba(255,255,255,0.85)",
            fontSize: "20px",
            cursor: "pointer",
            padding: "0 4px",
            lineHeight: 1,
            flexShrink: 0,
          }}
        >
          ×
        </button>
      </div>

      {/* Horizontal card row */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          padding: "14px 16px",
          overflowX: "auto",
          background: "#f8f9fb",
          scrollbarWidth: "thin",
        }}
      >
        {products.length > 0 ? (
          products.map((p, i) => <ProductCard key={p.id || i} product={p} />)
        ) : (
          <div style={{ padding: "24px 0", color: "#aaa", fontSize: "13px", width: "100%", textAlign: "center" }}>
            Browsing more products will help us personalize your picks.
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Root component ───────────────────────────────────────────────────────────
const SLIDE_MS = 1000;

export default function NudgePanel({ data, onDismiss, onRegisterClear }) {
  const { dismissNudge, isNudgeDismissed, clearDismissed } = useCookieStore();

  React.useEffect(() => {
    onRegisterClear?.(clearDismissed);
  }, [clearDismissed, onRegisterClear]);
  const [trayOpen, setTrayOpen] = useState(false);
  const [trayMounted, setTrayMounted] = useState(false);

  if (!data) return null;
  if (data.action_type && isNudgeDismissed(data.action_type)) return null;

  function handlePillClick() {
    setTrayMounted(true);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => setTrayOpen(true));
    });
  }

  // ▼ — just hides the tray, pill comes back, nudge is NOT dismissed
  function handleCollapse() {
    setTrayOpen(false);
    setTimeout(() => setTrayMounted(false), SLIDE_MS);
  }

  // × — permanently dismisses; pill goes away too
  function handleDismiss() {
    setTrayOpen(false);
    setTimeout(() => {
      setTrayMounted(false);
      if (data.action_type) dismissNudge(data.action_type);
      onDismiss?.();
    }, SLIDE_MS);
  }

  return (
    <>
      {/* Pill — shown only when tray is fully gone (not just closed) */}
      {!trayMounted && <CuratedPill onClick={handlePillClick} />}

      {/* Bottom tray — slides up from off-screen */}
      {trayMounted && (
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            zIndex: 2147483646,
            pointerEvents: trayOpen ? "all" : "none",
            transform: trayOpen ? "translateY(0)" : "translateY(100%)",
            transition: `transform ${SLIDE_MS}ms cubic-bezier(0.22, 1, 0.36, 1)`,
            willChange: "transform",
          }}
        >
          <RecommendationsTray
            data={data}
            onCollapse={handleCollapse}
            onClose={handleDismiss}
          />
        </div>
      )}
    </>
  );
}
