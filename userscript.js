// ==UserScript==
// @name         Live Stream Signals — Dell.com
// @namespace    https://github.com/DanielALievano/RecommenderForDell
// @version      0.2
// @description  Persistent behavioral signal tracker + recommendation strip for dell.com
// @author       LiveStreamSignals
// @match        https://www.dell.com/*
// @match        https://dell.com/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function () {
  "use strict";

  // Prevent double-injection on SPA navigations
  if (window.__lssActive) return;
  window.__lssActive = true;

  var API_BASE = "http://localhost:8000";
  var PANEL_MAX_LINES = 40;

  // -----------------------------------------------------------------------
  // Session identity — persists across full page navigations in same tab
  // -----------------------------------------------------------------------
  function uuidv4() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0, v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  var SESSION_ID = (function () {
    try {
      var k = "lss_sid";
      var id = sessionStorage.getItem(k);
      if (!id) { id = "s_ecid_" + uuidv4(); sessionStorage.setItem(k, id); }
      return id;
    } catch (e) { return "s_ecid_" + uuidv4(); }
  })();

  var VISIT_NUMBER = (function () {
    try {
      var k = "lss_visit";
      var n = parseInt(localStorage.getItem(k) || "0", 10) + 1;
      localStorage.setItem(k, String(n));
      return n;
    } catch (e) { return 1; }
  })();

  // Accumulated products seen across pages (persists in sessionStorage)
  var _seenProducts = (function () {
    try {
      return JSON.parse(sessionStorage.getItem("lss_products") || "[]");
    } catch (e) { return []; }
  })();

  function _saveSeenProducts() {
    try { sessionStorage.setItem("lss_products", JSON.stringify(_seenProducts.slice(-20))); } catch (e) {}
  }

  function _addProduct(name) {
    if (!name || name.length < 3) return;
    var clean = name.trim().replace(/\s+/g, " ").slice(0, 100);
    if (!_seenProducts.includes(clean)) {
      _seenProducts.push(clean);
      _saveSeenProducts();
    }
  }

  // -----------------------------------------------------------------------
  // Panel
  // -----------------------------------------------------------------------
  var _logEl = null, _statusEl = null;
  var _sentCount = 0, _eventCount = 0;

  function _initPanel() {
    var host = document.createElement("div");
    host.id = "lss-debug-host";
    host.style.cssText = "position:fixed;bottom:16px;right:16px;z-index:2147483647;font-size:0;";
    document.body.appendChild(host);

    var shadow = host.attachShadow({ mode: "open" });
    var style = document.createElement("style");
    style.textContent = [
      ".panel{width:440px;max-height:440px;background:#1a1a2e;color:#e0e0e0;font-family:Consolas,'Courier New',monospace;font-size:11px;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,.5);display:flex;flex-direction:column;overflow:hidden;border:1px solid #0076CE}",
      ".hdr{background:#0076CE;color:#fff;padding:6px 12px;display:flex;align-items:center;justify-content:space-between;font-size:12px;font-weight:bold;cursor:move;user-select:none}",
      ".dot{width:8px;height:8px;border-radius:50%;background:#4ade80;animation:pulse 1.5s infinite}",
      "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}",
      ".stat-bar{background:#12122a;padding:4px 12px;font-size:10px;color:#9ca3af;border-bottom:1px solid #2d2d5e;display:flex;gap:14px;flex-wrap:wrap}",
      ".stat{color:#60a5fa;font-weight:bold}",
      ".products-bar{background:#0d1117;padding:4px 12px;font-size:10px;color:#9ca3af;border-bottom:1px solid #2d2d5e;min-height:20px}",
      ".ptag{display:inline-block;background:#1e3a5f;color:#93c5fd;border-radius:3px;padding:1px 6px;margin:1px 2px;font-size:10px}",
      ".log{flex:1;overflow-y:auto;padding:4px 0}",
      ".line{padding:2px 12px;line-height:1.5;border-left:3px solid transparent}",
      ".line:hover{background:rgba(255,255,255,.03)}",
      ".t1{border-left-color:#f59e0b;color:#fde68a}",
      ".t2{border-left-color:#60a5fa;color:#bfdbfe}",
      ".t3{border-left-color:#6b7280;color:#9ca3af}",
      ".sys{border-left-color:#4ade80;color:#86efac;font-style:italic}",
      ".err{border-left-color:#f87171;color:#fca5a5}",
      ".ts{color:#6b7280;margin-right:5px}",
      ".ctrl{padding:6px 12px;display:flex;gap:8px;border-top:1px solid #2d2d5e}",
      "button{background:#0076CE;color:#fff;border:none;border-radius:4px;padding:3px 10px;font-size:10px;cursor:pointer;font-family:inherit}",
      "button:hover{background:#005fa3}",
      ".sec{background:#2d2d5e}",
      ".sec:hover{background:#3d3d7e}"
    ].join("");

    var panel = document.createElement("div"); panel.className = "panel";

    var hdr = document.createElement("div"); hdr.className = "hdr";
    hdr.innerHTML = '<div style="display:flex;align-items:center;gap:8px"><div class="dot"></div><span>Live Stream Signals</span></div>' +
      '<span style="font-size:10px;opacity:.7">' + SESSION_ID.slice(0, 18) + "...</span>";

    var statBar = document.createElement("div"); statBar.className = "stat-bar";
    statBar.innerHTML = 'Events:<span class="stat" id="ec">0</span> Sent:<span class="stat" id="sc">0</span> Backend:<span class="stat" id="bs">checking</span>';

    var prodBar = document.createElement("div"); prodBar.className = "products-bar";
    prodBar.id = "prod-bar";
    prodBar.innerHTML = '<span style="color:#6b7280">Products seen: </span>';

    var log = document.createElement("div"); log.className = "log";

    var ctrl = document.createElement("div"); ctrl.className = "ctrl";
    ctrl.innerHTML = '<button id="fb">Flush now</button><button id="cb" class="sec">Clear</button><button id="xb" class="sec">Hide</button>';

    panel.appendChild(hdr);
    panel.appendChild(statBar);
    panel.appendChild(prodBar);
    panel.appendChild(log);
    panel.appendChild(ctrl);
    shadow.appendChild(style);
    shadow.appendChild(panel);

    _logEl = log;
    _statusEl = shadow;

    ctrl.querySelector("#fb").addEventListener("click", function () { _flush("manual"); });
    ctrl.querySelector("#cb").addEventListener("click", function () { log.innerHTML = ""; });
    ctrl.querySelector("#xb").addEventListener("click", function () { host.style.display = "none"; });

    // Draggable
    var drag = false, ox = 0, oy = 0;
    hdr.addEventListener("mousedown", function (e) { drag = true; ox = e.clientX - host.offsetLeft; oy = e.clientY - host.offsetTop; });
    document.addEventListener("mousemove", function (e) {
      if (!drag) return;
      host.style.left = (e.clientX - ox) + "px"; host.style.bottom = "auto";
      host.style.top = (e.clientY - oy) + "px"; host.style.right = "auto";
    });
    document.addEventListener("mouseup", function () { drag = false; });

    _refreshProductBar(shadow);
  }

  function _refreshProductBar(shadow) {
    try {
      var bar = (shadow || _statusEl).querySelector("#prod-bar");
      if (!bar) return;
      if (_seenProducts.length === 0) {
        bar.innerHTML = '<span style="color:#6b7280">Products seen: none yet — browse some laptop pages</span>';
      } else {
        bar.innerHTML = '<span style="color:#6b7280">Products seen: </span>' +
          _seenProducts.map(function (p) { return '<span class="ptag">' + _esc(p) + '</span>'; }).join("");
      }
    } catch (e) {}
  }

  function _log(tier, line) {
    if (!_logEl) return;
    try {
      var cls = tier === "sys" ? "sys" : tier === "err" ? "err" : "t" + tier;
      var now = new Date().toTimeString().slice(0, 8);
      var div = document.createElement("div");
      div.className = "line " + cls;
      div.innerHTML = '<span class="ts">' + now + "</span>" + _esc(line);
      _logEl.appendChild(div);
      while (_logEl.children.length > PANEL_MAX_LINES) _logEl.removeChild(_logEl.firstChild);
      _logEl.scrollTop = _logEl.scrollHeight;
    } catch (e) {}
  }

  function _esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

  function _updateStatus() {
    if (!_statusEl) return;
    var ec = _statusEl.querySelector("#ec"), sc = _statusEl.querySelector("#sc");
    if (ec) ec.textContent = _eventCount;
    if (sc) sc.textContent = _sentCount;
  }

  function _setBackend(s, ok) {
    if (!_statusEl) return;
    var el = _statusEl.querySelector("#bs");
    if (el) { el.textContent = s; el.style.color = ok ? "#4ade80" : "#f87171"; }
  }

  // -----------------------------------------------------------------------
  // Product scanner — runs on every page load
  // -----------------------------------------------------------------------
  var _PRODUCT_SELECTORS = [
    "h1", "h2",
    "[class*='product-title']", "[class*='product-name']",
    "[data-testid*='product']", "[class*='item-title']",
    ".ps-title", ".model-name", "[class*='laptop-name']",
  ].join(",");

  var _PRODUCT_PATTERN = /\b(xps|inspiron|latitude|precision|vostro|alienware|g\d|dell)\b/i;

  function _scanPageProducts() {
    try {
      var h1 = document.querySelector("h1");
      if (h1 && _PRODUCT_PATTERN.test(h1.textContent)) {
        _addProduct(h1.textContent.trim().replace(/\s+/g, " ").slice(0, 80));
      }

      document.querySelectorAll(_PRODUCT_SELECTORS).forEach(function (el) {
        var text = (el.textContent || "").trim().replace(/\s+/g, " ");
        if (text.length > 5 && text.length < 120 && _PRODUCT_PATTERN.test(text)) {
          _addProduct(text.slice(0, 80));
        }
      });

      // Also check URL path for product hints
      var urlMatch = location.pathname.match(/\/(xps|inspiron|latitude|precision|vostro|alienware)[^/]*/i);
      if (urlMatch) _addProduct(urlMatch[0].replace(/\//g, "").replace(/-/g, " ").trim());

      _refreshProductBar(_statusEl);
    } catch (e) {}
  }

  // -----------------------------------------------------------------------
  // Buffer & flush
  // -----------------------------------------------------------------------
  var _buffer = [];
  var _pageStart = Date.now();
  var _activeSeconds = 0;
  var _tabActive = !document.hidden;

  function _elapsed() { return Math.round((Date.now() - _pageStart) / 1000); }
  function _clean(s) { return String(s || "").replace(/[\r\n\t]+/g, " ").trim().slice(0, 200); }

  var _CTX = [
    [/nav(igation)?|navbar|site-nav/i, "navigation"],
    [/paginat|page-nav/i, "pagination"],
    [/breadcrumb/i, "breadcrumb"],
    [/menu|dropdown/i, "menu"],
    [/header|masthead/i, "header"],
    [/footer/i, "footer"],
    [/promo|banner|hero|sale/i, "promo_banner"],
    [/product[-_]?card|item[-_]?card|tile/i, "product_card"],
    [/spec[-_]?section|tech[-_]?spec/i, "spec_section"],
    [/spec[-_]?item|spec[-_]?row/i, "spec_item"],
  ];

  function _ctx(el) {
    var cur = el;
    for (var d = 0; d < 10 && cur && cur !== document.body; d++) {
      var cls = (cur.className || "") + " " + (cur.getAttribute("data-testid") || "") + " " + (cur.id || "");
      for (var i = 0; i < _CTX.length; i++) if (_CTX[i][0].test(cls)) return _CTX[i][1];
      cur = cur.parentElement;
    }
    return "content";
  }

  function _record(tier, conf, type, content, ctx, dwell) {
    try {
      _eventCount++;
      var parts = ["[" + _elapsed() + "s]", "[T" + tier + " " + conf.toFixed(2) + "]",
        type.toUpperCase().replace(/_/g, " ")];
      if (dwell) parts.push(dwell.toFixed(0) + "s on");
      if (content) parts.push('"' + _clean(content) + '"');
      if (ctx && ctx !== "content") parts.push("(" + ctx + ")");
      var line = parts.join(" ");
      _buffer.push(line);
      _log(tier, line);
      _updateStatus();
      if (_buffer.length >= 20) _flush("buffer_full");
    } catch (e) {}
  }

  async function _flush(trigger) {
    try {
      if (_buffer.length === 0) return;
      var narrative = _buffer.join("\n");
      _buffer = [];

      // Include seen products as context lines at the top of each narrative
      var productContext = "";
      if (_seenProducts.length > 0) {
        productContext = "[0s] [T1 0.90] PRODUCTS BROWSED \"" + _seenProducts.join(" | ") + "\" (session_context)\n";
      }

      var payload = {
        session_id: SESSION_ID,
        visit_number: VISIT_NUMBER,
        page_url: location.href,
        page_title: document.title,
        referrer: document.referrer || "",
        active_seconds: _activeSeconds,
        total_events: _eventCount,
        trigger: trigger || "timer",
        narrative: productContext + narrative,
      };

      _log("sys", "Flushing " + narrative.split("\n").length + " events  trigger=" + trigger);
      if (_seenProducts.length > 0) _log("sys", "Products: " + _seenProducts.join(", "));

      try {
        var r = await fetch(API_BASE + "/api/clickstream/ingest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          keepalive: true,
        });
        if (r.ok) {
          var d = await r.json();
          _sentCount++; _updateStatus();
          _log("sys", "ACK acted=" + d.acted + " delta=" + d.delta + " signals=" + d.signal_count);
          if (d.acted) _log("sys", "Intent shift detected — LLM running in background");
        } else {
          _log("err", "Server " + r.status);
        }
      } catch (e) {
        _log("err", "POST failed — is backend running? " + e.message);
      }
    } catch (e) {}
  }

  window._lssFlush = function (t) { _flush(t || "manual"); };
  window._lssProducts = function () { return _seenProducts.slice(); };
  window._lssSession = function () { return SESSION_ID; };

  setInterval(function () { _flush("timer"); }, 15000);
  setInterval(function () { if (_tabActive) _activeSeconds++; }, 1000);

  document.addEventListener("visibilitychange", function () {
    _tabActive = !document.hidden;
    _record(3, 0.40, _tabActive ? "tab_visible" : "tab_hidden", "", "", 0);
  });

  // -----------------------------------------------------------------------
  // Event listeners
  // -----------------------------------------------------------------------

  // Scroll
  var _maxScroll = 0;
  window.addEventListener("scroll", function () {
    try {
      var pct = Math.round(((window.scrollY + window.innerHeight) / document.body.scrollHeight) * 100);
      if (pct > _maxScroll + 15) { _maxScroll = pct; _record(3, 0.30, "scroll_depth", pct + "%", "", 0); }
    } catch (e) {}
  }, { passive: true });

  // Clicks
  var _lct = 0, _lcTarget = null, _lcc = 0;
  document.addEventListener("click", function (e) {
    try {
      var t = e.target, now = Date.now();
      var c = _ctx(t);
      var label = _clean(t.innerText || t.getAttribute("aria-label") || t.getAttribute("title") || "").slice(0, 80);

      // If clicking a product-looking label, record it
      if (label && _PRODUCT_PATTERN.test(label)) _addProduct(label);

      if (t === _lcTarget && now - _lct < 500) {
        _lcc++;
        if (_lcc >= 3) {
          _record(1, 0.85, "rage_click", label, c, 0);
          setTimeout(function () { _flush("rage_click"); }, 50);
          _lcc = 0;
        }
      } else { _lcc = 1; }
      _lcTarget = t; _lct = now;

      var isInt = t.tagName === "A" || t.tagName === "BUTTON" || t.tagName === "INPUT" ||
        t.tagName === "SELECT" || t.getAttribute("role") === "button";
      if (isInt) _record(2, 0.65, "click", label, c, 0);
    } catch (e) {}
  }, true);

  // Text select & copy
  document.addEventListener("selectionchange", function () {
    try {
      var sel = window.getSelection();
      if (sel && sel.toString().trim().length > 5) {
        var text = _clean(sel.toString());
        var c = sel.anchorNode && sel.anchorNode.parentElement ? _ctx(sel.anchorNode.parentElement) : "content";
        _record(1, 0.80, "text_select", text, c, 0);
      }
    } catch (e) {}
  });

  document.addEventListener("copy", function () {
    try {
      var sel = window.getSelection();
      if (sel) {
        var t = _clean(sel.toString());
        if (t.length > 2) {
          _record(1, 0.88, "text_copy", t, "", 0);
          setTimeout(function () { _flush("text_copy"); }, 50);
        }
      }
    } catch (e) {}
  });

  // Search / input
  var _inputDebounce = {};
  document.addEventListener("input", function (e) {
    try {
      var t = e.target;
      var name = _clean(t.name || t.placeholder || t.getAttribute("aria-label") || "");
      var val = _clean(t.value || "");
      var c = _ctx(t);
      var key = name || "field";
      if (_inputDebounce[key]) clearTimeout(_inputDebounce[key]);
      _inputDebounce[key] = setTimeout(function () {
        var isSrc = t.type === "search" || /search/i.test(name) || t.getAttribute("role") === "searchbox";
        if (isSrc && val.length > 2) {
          _record(1, 0.90, "search_query", val, c, 0);
          setTimeout(function () { _flush("search_query"); }, 50);
        } else if (val.length > 0) {
          _record(2, 0.60, "input_change", name + " -> " + val, c, 0);
        }
      }, 600);
    } catch (e) {}
  }, true);

  // Multi-pass hover
  var _hc = {}, _ht = {};
  document.addEventListener("mouseover", function (e) {
    try {
      var t = e.target;
      var label = _clean(t.getAttribute("aria-label") || t.innerText || "").slice(0, 60);
      if (!label || label.length < 3) return;
      if (_PRODUCT_PATTERN.test(label)) _addProduct(label);
      _hc[label] = (_hc[label] || 0) + 1;
      if (_hc[label] >= 2) {
        if (_ht[label]) clearTimeout(_ht[label]);
        _ht[label] = setTimeout(function () { _record(2, 0.75, "multi_pass", label, _ctx(t), 0); }, 1000);
      }
    } catch (e) {}
  }, { passive: true });

  // Viewport dwell via IntersectionObserver
  var _dwellTimers = new WeakMap();
  try {
    var _io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        try {
          var el = entry.target;
          if (entry.intersectionRatio >= 0.6 && _tabActive) {
            if (!_dwellTimers.has(el)) {
              var start = Date.now();
              var timer = setTimeout(function () {
                var secs = (Date.now() - start) / 1000;
                var label = _clean(el.getAttribute("aria-label") || el.innerText || "").slice(0, 80);
                var c = _ctx(el);
                if (label.length > 2) {
                  if (_PRODUCT_PATTERN.test(label)) _addProduct(label);
                  _record(2, 0.70, "viewport_dwell", label, c, secs);
                  _refreshProductBar(_statusEl);
                }
              }, 2000);
              _dwellTimers.set(el, { timer: timer, start: start });
            }
          } else {
            var ex = _dwellTimers.get(el);
            if (ex) { clearTimeout(ex.timer); _dwellTimers.delete(el); }
          }
        } catch (e) {}
      });
    }, { threshold: 0.6 });

    setTimeout(function () {
      try {
        document.querySelectorAll("h1,h2,[class*='product-card'],[class*='item-card'],[class*='promo'],[class*='banner']")
          .forEach(function (el) { _io.observe(el); });
      } catch (e) {}
    }, 800);
  } catch (e) {}

  // Idle
  var _idleTimer = null;
  function _resetIdle() {
    if (_idleTimer) clearTimeout(_idleTimer);
    _idleTimer = setTimeout(function () {
      _record(2, 0.75, "idle_start", "", "", 0);
      setTimeout(function () { _flush("idle_start"); }, 100);
    }, 4000);
  }
  ["mousemove", "keydown", "scroll", "click"].forEach(function (ev) {
    document.addEventListener(ev, _resetIdle, { passive: true });
  });
  _resetIdle();

  // URL / filter change
  var _lastParams = location.search;
  (function () {
    try {
      var op = history.pushState, or = history.replaceState;
      history.pushState = function () { op.apply(history, arguments); _checkUrl(); };
      history.replaceState = function () { or.apply(history, arguments); _checkUrl(); };
      window.addEventListener("popstate", _checkUrl);
    } catch (e) {}
  })();
  function _checkUrl() {
    try {
      if (location.search !== _lastParams) {
        var oldP = new URLSearchParams(_lastParams), newP = new URLSearchParams(location.search);
        newP.forEach(function (v, k) { if (oldP.get(k) !== v) _record(1, 0.85, "filter_applied", v, "(" + k + ")", 0); });
        _lastParams = location.search;
        _flush("filter_change");
      }
    } catch (e) {}
  }

  // Pagehide
  window.addEventListener("pagehide", function () {
    try {
      _record(2, 0.50, "page_exit", "", "", 0);
      if (_buffer.length === 0) return;
      var narrative = _buffer.join("\n"); _buffer = [];
      var productContext = _seenProducts.length > 0
        ? "[0s] [T1 0.90] PRODUCTS BROWSED \"" + _seenProducts.join(" | ") + "\" (session_context)\n" : "";
      navigator.sendBeacon(API_BASE + "/api/clickstream/ingest", new Blob([JSON.stringify({
        session_id: SESSION_ID, visit_number: VISIT_NUMBER, page_url: location.href,
        page_title: document.title, referrer: document.referrer || "",
        active_seconds: _activeSeconds, total_events: _eventCount,
        trigger: "pagehide", narrative: productContext + narrative,
      })], { type: "application/json" }));
    } catch (e) {}
  });

  // -----------------------------------------------------------------------
  // SSE nudge strip
  // -----------------------------------------------------------------------
  try {
    var es = new EventSource(API_BASE + "/api/session/stream/" + SESSION_ID);
    es.addEventListener("nudge", function (e) {
      try {
        var data = JSON.parse(e.data);
        _log("sys", "NUDGE: " + data.action_type + " — " + data.message);
        _renderNudge(data);
      } catch (ex) {}
    });
    es.onerror = function () {};
  } catch (e) {}

  function _renderNudge(data) {
    try {
      var old = document.getElementById("lss-nudge-host");
      if (old) old.remove();
      var host = document.createElement("div");
      host.id = "lss-nudge-host";
      host.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:2147483646;pointer-events:none;";
      document.body.insertBefore(host, document.body.firstChild);
      var shadow = host.attachShadow({ mode: "closed" });
      var style = document.createElement("style");
      style.textContent = ".strip{background:#0076CE;color:#fff;font-family:-apple-system,sans-serif;font-size:14px;padding:10px 16px;display:flex;align-items:center;gap:12px;pointer-events:all;box-shadow:0 2px 8px rgba(0,0,0,.25)}.msg{flex:1}.chip{background:rgba(255,255,255,.15);border-radius:4px;padding:2px 8px;font-size:12px;white-space:nowrap;cursor:pointer;text-decoration:none;color:#fff;margin-right:4px}.chip:hover{background:rgba(255,255,255,.3)}.x{background:none;border:none;color:rgba(255,255,255,.8);font-size:18px;cursor:pointer;padding:0 4px}";
      var strip = document.createElement("div"); strip.className = "strip";
      var msg = document.createElement("span"); msg.className = "msg"; msg.textContent = data.message || "Based on your browsing, here are some picks for you.";
      strip.appendChild(msg);
      if (data.products && data.products.length > 0) {
        data.products.slice(0, 3).forEach(function (p) {
          var a = document.createElement("a"); a.className = "chip";
          a.textContent = p.name || p.id || "View";
          a.href = p.url || "#"; a.target = "_blank"; a.rel = "noopener";
          strip.appendChild(a);
        });
      }
      var btn = document.createElement("button"); btn.className = "x"; btn.textContent = "\xD7";
      btn.addEventListener("click", function () { host.remove(); });
      strip.appendChild(btn);
      shadow.appendChild(style); shadow.appendChild(strip);
    } catch (e) {}
  }

  // -----------------------------------------------------------------------
  // Ping & init
  // -----------------------------------------------------------------------
  async function _ping() {
    try {
      var r = await fetch(API_BASE + "/health", { signal: AbortSignal.timeout(2000) });
      _setBackend(r.ok ? "online" : "error " + r.status, r.ok);
      if (r.ok) _log("sys", "Backend online");
    } catch (e) {
      _setBackend("offline", false);
      _log("err", "Backend offline — start uvicorn first");
    }
  }

  _initPanel();
  _ping();
  _scanPageProducts();

  _log("sys", "Session: " + SESSION_ID + " (persists across pages)");
  _log("sys", "Page: " + document.title.slice(0, 60));
  _log("sys", "Products so far: " + (_seenProducts.length || "none yet"));

  console.log("[LiveStreamSignals] Active. Session:", SESSION_ID);
  console.log("  _lssFlush()     — manual flush");
  console.log("  _lssProducts()  — list seen products");
  console.log("  _lssSession()   — session id");
})();
