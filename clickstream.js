/**
 * Live Stream Signals — clickstream tracker for dell.com
 * Injectable as a DevTools snippet or <script> tag.
 * Never modifies the page (except the nudge strip) and swallows all errors silently.
 */
(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // Config
  // -----------------------------------------------------------------------
  const API_BASE = "http://localhost:8000";
  const FLUSH_BUFFER_SIZE = 20;
  const FLUSH_INTERVAL_MS = 15000;
  const T1_FLUSH_DELAY_MS = 50;
  const IDLE_FLUSH_DELAY_MS = 100;
  const VIEWPORT_DWELL_THRESHOLD_S = 2;
  const VIEWPORT_VISIBILITY_RATIO = 0.6;

  // -----------------------------------------------------------------------
  // Session identity
  // -----------------------------------------------------------------------
  function uuidv4() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0,
        v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  var SESSION_ID = (() => {
    try {
      var k = "lss_sid";
      var id = sessionStorage.getItem(k);
      if (!id) {
        id = "s_ecid_" + uuidv4();
        sessionStorage.setItem(k, id);
      }
      return id;
    } catch (e) {
      return "s_ecid_" + uuidv4();
    }
  })();

  var VISIT_NUMBER = (() => {
    try {
      var k = "lss_visit";
      var n = parseInt(localStorage.getItem(k) || "0", 10) + 1;
      localStorage.setItem(k, String(n));
      return n;
    } catch (e) {
      return 1;
    }
  })();

  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------
  var _buffer = [];
  var _pageStart = Date.now();
  var _activeSeconds = 0;
  var _totalEvents = 0;
  var _tabActive = !document.hidden;
  var _activeTimer = null;
  var _flushTimer = null;
  var _pushedActionTypes = new Set();

  // Per-page state
  var _currentUrl = location.href;
  var _currentTitle = document.title;

  // -----------------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------------
  function clean(str) {
    if (!str) return "";
    return String(str).replace(/[\r\n\t]+/g, " ").trim().slice(0, 200);
  }

  function elapsed() {
    return Math.round((Date.now() - _pageStart) / 1000);
  }

  // -----------------------------------------------------------------------
  // Context classification
  // -----------------------------------------------------------------------
  var _CTX_PATTERNS = [
    [/nav(igation)?|navbar|site-nav/i, "navigation"],
    [/paginat|page-nav|pagination/i, "pagination"],
    [/breadcrumb/i, "breadcrumb"],
    [/menu|dropdown|flyout/i, "menu"],
    [/header|masthead|site-header/i, "header"],
    [/footer|site-footer/i, "footer"],
    [/promo|banner|hero|sale|offer/i, "promo_banner"],
    [/product[-_]?card|item[-_]?card|tile[-_]?card/i, "product_card"],
    [/spec[-_]?section|specs[-_]?container|tech[-_]?specs/i, "spec_section"],
    [/spec[-_]?item|spec[-_]?row/i, "spec_item"],
  ];

  function nearestContainer(el) {
    var cur = el;
    for (var depth = 0; depth < 10 && cur && cur !== document.body; depth++) {
      var cls = (cur.className || "") + " " + (cur.getAttribute("data-testid") || "") + " " + (cur.id || "");
      for (var i = 0; i < _CTX_PATTERNS.length; i++) {
        if (_CTX_PATTERNS[i][0].test(cls)) return _CTX_PATTERNS[i][1];
      }
      cur = cur.parentElement;
    }
    return "content";
  }

  // -----------------------------------------------------------------------
  // Narrative line builder
  // -----------------------------------------------------------------------
  function _toNarrative(tier, conf, eventType, content, ctx, dwellSecs) {
    var parts = [];
    parts.push("[" + elapsed() + "s]");
    parts.push("[T" + tier + " " + conf.toFixed(2) + "]");
    parts.push(eventType.toUpperCase().replace(/_/g, " "));
    if (dwellSecs) {
      parts.push(dwellSecs.toFixed(0) + "s on");
    }
    if (content) {
      parts.push('"' + clean(content) + '"');
    }
    if (ctx && ctx !== "content") {
      parts.push("(" + ctx + ")");
    }
    return parts.join(" ");
  }

  // -----------------------------------------------------------------------
  // Buffer
  // -----------------------------------------------------------------------
  function _record(tier, conf, eventType, content, ctx, dwellSecs) {
    try {
      _totalEvents++;
      var line = _toNarrative(tier, conf, eventType, content, ctx, dwellSecs);
      _buffer.push(line);
      if (_buffer.length >= FLUSH_BUFFER_SIZE) {
        _flush("buffer_full");
      }
    } catch (e) {}
  }

  // -----------------------------------------------------------------------
  // Flush
  // -----------------------------------------------------------------------
  function _flush(trigger) {
    try {
      if (_buffer.length === 0) return;
      var narrative = _buffer.join("\n");
      _buffer = [];

      var payload = {
        session_id: SESSION_ID,
        visit_number: VISIT_NUMBER,
        page_url: location.href,
        page_title: document.title,
        referrer: document.referrer || "",
        active_seconds: _activeSeconds,
        total_events: _totalEvents,
        trigger: trigger || "timer",
        narrative: narrative,
      };

      var body = JSON.stringify(payload);
      var url = API_BASE + "/api/clickstream/ingest";

      try {
        fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: body,
          keepalive: true,
        }).catch(function () {});
      } catch (e) {}
    } catch (e) {}
  }

  // Expose for manual testing
  window._flush = _flush;

  // -----------------------------------------------------------------------
  // Active time tracking
  // -----------------------------------------------------------------------
  function _startActiveTimer() {
    if (_activeTimer) return;
    _activeTimer = setInterval(function () {
      if (_tabActive) _activeSeconds++;
    }, 1000);
  }

  _startActiveTimer();

  document.addEventListener("visibilitychange", function () {
    try {
      _tabActive = !document.hidden;
      if (document.hidden) {
        _record(3, 0.40, "tab_hidden", "", "", 0);
      } else {
        _record(3, 0.40, "tab_visible", "", "", 0);
      }
    } catch (e) {}
  });

  // Periodic flush
  _flushTimer = setInterval(function () {
    _flush("timer");
  }, FLUSH_INTERVAL_MS);

  // -----------------------------------------------------------------------
  // Scroll tracking
  // -----------------------------------------------------------------------
  var _maxScroll = 0;
  var _scrollMode = "vertical";

  window.addEventListener(
    "scroll",
    function () {
      try {
        var pct = Math.round(
          ((window.scrollY + window.innerHeight) / document.body.scrollHeight) * 100
        );
        if (pct > _maxScroll + 10) {
          _maxScroll = pct;
          _record(3, 0.30, "scroll_depth", pct + "%", "", 0);
        }
      } catch (e) {}
    },
    { passive: true }
  );

  // -----------------------------------------------------------------------
  // Click tracking
  // -----------------------------------------------------------------------
  var _lastClickTime = 0;
  var _lastClickTarget = null;
  var _clickCount = 0;
  var _deadClickTimer = null;

  document.addEventListener(
    "click",
    function (e) {
      try {
        var t = e.target;
        var now = Date.now();
        var ctx = nearestContainer(t);
        var label = clean(t.innerText || t.getAttribute("aria-label") || t.getAttribute("title") || t.getAttribute("value") || "");

        // Rage click detection (3+ clicks within 500ms on same target)
        if (t === _lastClickTarget && now - _lastClickTime < 500) {
          _clickCount++;
          if (_clickCount >= 3) {
            _record(1, 0.85, "rage_click", label, ctx, 0);
            setTimeout(function () {
              _flush("rage_click");
            }, T1_FLUSH_DELAY_MS);
            _clickCount = 0;
          }
        } else {
          _clickCount = 1;
        }
        _lastClickTarget = t;
        _lastClickTime = now;

        // Dead click: click on non-interactive element
        var isInteractive =
          t.tagName === "A" ||
          t.tagName === "BUTTON" ||
          t.tagName === "INPUT" ||
          t.tagName === "SELECT" ||
          t.role === "button" ||
          t.getAttribute("onclick");
        if (!isInteractive) {
          if (_deadClickTimer) clearTimeout(_deadClickTimer);
          _deadClickTimer = setTimeout(function () {
            _record(1, 0.80, "dead_click", label, ctx, 0);
            setTimeout(function () {
              _flush("dead_click");
            }, T1_FLUSH_DELAY_MS);
          }, 300);
        } else {
          if (_deadClickTimer) clearTimeout(_deadClickTimer);
          _record(2, 0.65, "click", label, ctx, 0);
        }
      } catch (e) {}
    },
    true
  );

  // -----------------------------------------------------------------------
  // Text selection / copy
  // -----------------------------------------------------------------------
  document.addEventListener("selectionchange", function () {
    try {
      var sel = window.getSelection();
      if (sel && sel.toString().trim().length > 5) {
        var content = clean(sel.toString());
        var ctx = sel.anchorNode && sel.anchorNode.parentElement
          ? nearestContainer(sel.anchorNode.parentElement)
          : "content";
        _record(1, 0.80, "text_select", content, ctx, 0);
      }
    } catch (e) {}
  });

  document.addEventListener("copy", function () {
    try {
      var sel = window.getSelection();
      if (sel) {
        var content = clean(sel.toString());
        if (content.length > 2) {
          _record(1, 0.88, "text_copy", content, "", 0);
          setTimeout(function () {
            _flush("text_copy");
          }, T1_FLUSH_DELAY_MS);
        }
      }
    } catch (e) {}
  });

  // -----------------------------------------------------------------------
  // Input / search tracking
  // -----------------------------------------------------------------------
  var _inputDebounce = {};

  document.addEventListener(
    "input",
    function (e) {
      try {
        var t = e.target;
        var name = clean(t.name || t.placeholder || t.getAttribute("aria-label") || "");
        var val = clean(t.value || "");
        var ctx = nearestContainer(t);
        var key = name || "field";

        if (_inputDebounce[key]) clearTimeout(_inputDebounce[key]);
        _inputDebounce[key] = setTimeout(function () {
          // Search detection
          var isSearch =
            t.type === "search" ||
            /search/i.test(name) ||
            t.getAttribute("role") === "searchbox";
          if (isSearch && val.length > 2) {
            _record(1, 0.90, "search_query", val, ctx, 0);
            setTimeout(function () {
              _flush("search_query");
            }, T1_FLUSH_DELAY_MS);
          } else if (val.length > 0) {
            _record(2, 0.60, "input_change", name + " -> " + val, ctx, 0);
          }
        }, 600);
      } catch (e) {}
    },
    true
  );

  // -----------------------------------------------------------------------
  // Cursor thrash detection
  // -----------------------------------------------------------------------
  var _mousePositions = [];
  var _thrashTimer = null;

  document.addEventListener(
    "mousemove",
    function (e) {
      try {
        _mousePositions.push({ x: e.clientX, y: e.clientY, t: Date.now() });
        if (_mousePositions.length > 20) _mousePositions.shift();

        if (_thrashTimer) return;
        _thrashTimer = setTimeout(function () {
          _thrashTimer = null;
          if (_mousePositions.length < 10) return;
          var reversals = 0;
          for (var i = 2; i < _mousePositions.length; i++) {
            var dx1 = _mousePositions[i - 1].x - _mousePositions[i - 2].x;
            var dx2 = _mousePositions[i].x - _mousePositions[i - 1].x;
            if (dx1 !== 0 && dx2 !== 0 && dx1 * dx2 < 0) reversals++;
          }
          if (reversals >= 5) {
            _record(2, 0.70, "cursor_thrash", "", "", 0);
          }
        }, 500);
      } catch (e) {}
    },
    { passive: true }
  );

  // -----------------------------------------------------------------------
  // Multi-pass (repeated element hover)
  // -----------------------------------------------------------------------
  var _hoverCounts = {};
  var _hoverTimer = {};

  document.addEventListener(
    "mouseover",
    function (e) {
      try {
        var t = e.target;
        var label = clean(
          t.getAttribute("aria-label") || t.innerText || ""
        ).slice(0, 60);
        if (!label || label.length < 3) return;
        if (!_hoverCounts[label]) _hoverCounts[label] = 0;
        _hoverCounts[label]++;

        if (_hoverCounts[label] >= 2) {
          if (_hoverTimer[label]) clearTimeout(_hoverTimer[label]);
          _hoverTimer[label] = setTimeout(function () {
            var ctx = nearestContainer(t);
            _record(2, 0.75, "multi_pass", label, ctx, 0);
          }, 1000);
        }
      } catch (e) {}
    },
    { passive: true }
  );

  // -----------------------------------------------------------------------
  // Idle detection
  // -----------------------------------------------------------------------
  var _idleTimer = null;
  var _IDLE_THRESHOLD_MS = 4000;

  function _resetIdleTimer() {
    if (_idleTimer) clearTimeout(_idleTimer);
    _idleTimer = setTimeout(function () {
      _record(2, 0.75, "idle_start", "", "", 0);
      setTimeout(function () {
        _flush("idle_start");
      }, IDLE_FLUSH_DELAY_MS);
    }, _IDLE_THRESHOLD_MS);
  }

  ["mousemove", "keydown", "scroll", "click"].forEach(function (ev) {
    document.addEventListener(ev, _resetIdleTimer, { passive: true });
  });
  _resetIdleTimer();

  // -----------------------------------------------------------------------
  // Dwell tracking (IntersectionObserver)
  // -----------------------------------------------------------------------
  var _dwellTimers = new WeakMap();
  var _dwellObserver = null;

  try {
    _dwellObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          try {
            var el = entry.target;
            if (entry.intersectionRatio >= VIEWPORT_VISIBILITY_RATIO && _tabActive) {
              if (!_dwellTimers.has(el)) {
                var startTime = Date.now();
                var timer = setTimeout(function () {
                  var seconds = (Date.now() - startTime) / 1000;
                  var label = clean(el.getAttribute("aria-label") || el.innerText || el.getAttribute("title") || "");
                  var ctx = nearestContainer(el);
                  if (label.length > 2) {
                    _record(2, 0.70, "viewport_dwell", label, ctx, seconds);
                  }
                }, VIEWPORT_DWELL_THRESHOLD_S * 1000);
                _dwellTimers.set(el, { timer: timer, start: startTime });
              }
            } else {
              var existing = _dwellTimers.get(el);
              if (existing) {
                clearTimeout(existing.timer);
                _dwellTimers.delete(el);
              }
            }
          } catch (e) {}
        });
      },
      { threshold: VIEWPORT_VISIBILITY_RATIO }
    );

    // Observe product cards and promo elements
    setTimeout(function () {
      try {
        var selectors = [
          '[class*="product-card"]',
          '[class*="item-card"]',
          '[class*="promo"]',
          '[class*="banner"]',
          "h1",
          "h2",
        ].join(",");
        document.querySelectorAll(selectors).forEach(function (el) {
          _dwellObserver.observe(el);
        });
      } catch (e) {}
    }, 500);
  } catch (e) {}

  // -----------------------------------------------------------------------
  // MutationObserver for product grid updates
  // -----------------------------------------------------------------------
  try {
    var _mutationObserver = new MutationObserver(function (mutations) {
      try {
        var gridChanged = mutations.some(function (m) {
          return (
            m.addedNodes.length > 0 &&
            (m.target.className || "").match(/grid|list|results|products/i)
          );
        });
        if (gridChanged) {
          var count = document.querySelectorAll('[class*="product-card"], [class*="item-card"]').length;
          _record(2, 0.55, "results_updated", count + " items", "", 0);
        }
      } catch (e) {}
    });
    _mutationObserver.observe(document.body, { childList: true, subtree: true });
  } catch (e) {}

  // -----------------------------------------------------------------------
  // SPA navigation (history wrapping)
  // -----------------------------------------------------------------------
  function _onPageChange(newUrl) {
    try {
      if (newUrl === _currentUrl) return;
      _record(2, 0.60, "page_change", newUrl, "", 0);
      _flush("page_change");
      // Reset per-page state
      _currentUrl = newUrl;
      _currentTitle = document.title;
      _pageStart = Date.now();
      _maxScroll = 0;
      _hoverCounts = {};
    } catch (e) {}
  }

  (function () {
    try {
      var orig = history.pushState;
      history.pushState = function () {
        orig.apply(history, arguments);
        _onPageChange(location.href);
      };
      var origReplace = history.replaceState;
      history.replaceState = function () {
        origReplace.apply(history, arguments);
        // Detect filter changes via URL param diffs
        var params = new URLSearchParams(location.search);
        // (param comparison could be extended)
        _onPageChange(location.href);
      };
      window.addEventListener("popstate", function () {
        _onPageChange(location.href);
      });
    } catch (e) {}
  })();

  // -----------------------------------------------------------------------
  // Touch tracking
  // -----------------------------------------------------------------------
  var _touchStart = null;
  var _touchHoldTimer = null;
  var _touchMoves = 0;

  document.addEventListener(
    "touchstart",
    function (e) {
      try {
        _touchStart = { t: Date.now(), x: e.touches[0].clientX, y: e.touches[0].clientY };
        _touchMoves = 0;
        var el = e.target;
        var label = clean(el.getAttribute("aria-label") || el.innerText || "");
        var ctx = nearestContainer(el);
        if (_touchHoldTimer) clearTimeout(_touchHoldTimer);
        _touchHoldTimer = setTimeout(function () {
          var seconds = (Date.now() - _touchStart.t) / 1000;
          _record(2, 0.65, "touch_hold", label, ctx, seconds);
        }, 800);
      } catch (e) {}
    },
    { passive: true }
  );

  document.addEventListener(
    "touchmove",
    function () {
      try {
        _touchMoves++;
        if (_touchHoldTimer) clearTimeout(_touchHoldTimer);
        if (_touchMoves > 5) {
          // Touch thrash
          _record(2, 0.60, "cursor_thrash", "", "", 0);
          _touchMoves = 0;
        }
      } catch (e) {}
    },
    { passive: true }
  );

  document.addEventListener("touchend", function () {
    try {
      if (_touchHoldTimer) clearTimeout(_touchHoldTimer);
    } catch (e) {}
  });

  // -----------------------------------------------------------------------
  // Pagehide (sendBeacon)
  // -----------------------------------------------------------------------
  window.addEventListener("pagehide", function () {
    try {
      _record(2, 0.50, "page_exit", "", "", 0);
      if (_buffer.length === 0) return;
      var narrative = _buffer.join("\n");
      _buffer = [];
      var payload = JSON.stringify({
        session_id: SESSION_ID,
        visit_number: VISIT_NUMBER,
        page_url: location.href,
        page_title: document.title,
        referrer: document.referrer || "",
        active_seconds: _activeSeconds,
        total_events: _totalEvents,
        trigger: "pagehide",
        narrative: narrative,
      });
      navigator.sendBeacon(API_BASE + "/api/clickstream/ingest", new Blob([payload], { type: "application/json" }));
    } catch (e) {}
  });

  // -----------------------------------------------------------------------
  // Actuator: SSE nudge strip (shadow DOM)
  // -----------------------------------------------------------------------
  (function () {
    try {
      var es = new EventSource(API_BASE + "/api/session/stream/" + SESSION_ID);

      es.addEventListener("nudge", function (e) {
        try {
          var data = JSON.parse(e.data);
          if (_pushedActionTypes.has(data.action_type)) return;
          _pushedActionTypes.add(data.action_type);
          _renderNudge(data);
        } catch (ex) {}
      });

      es.onerror = function () {};
    } catch (e) {}
  })();

  function _renderNudge(data) {
    try {
      // Container
      var host = document.createElement("div");
      host.id = "lss-nudge-host";
      host.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:2147483647;pointer-events:none;";
      document.body.insertBefore(host, document.body.firstChild);

      var shadow = host.attachShadow({ mode: "closed" });

      var style = document.createElement("style");
      style.textContent = `
        .strip {
          background: #0076CE;
          color: #fff;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          font-size: 14px;
          padding: 10px 16px;
          display: flex;
          align-items: center;
          gap: 12px;
          pointer-events: all;
          box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        }
        .msg { flex: 1; }
        .products { display: flex; gap: 8px; }
        .product-chip {
          background: rgba(255,255,255,0.15);
          border-radius: 4px;
          padding: 2px 8px;
          font-size: 12px;
          white-space: nowrap;
          cursor: pointer;
          text-decoration: none;
          color: #fff;
        }
        .product-chip:hover { background: rgba(255,255,255,0.30); }
        .dismiss {
          background: none;
          border: none;
          color: rgba(255,255,255,0.8);
          font-size: 18px;
          cursor: pointer;
          padding: 0 4px;
          line-height: 1;
        }
        .dismiss:hover { color: #fff; }
      `;

      var strip = document.createElement("div");
      strip.className = "strip";

      var msg = document.createElement("span");
      msg.className = "msg";
      msg.textContent = data.message || "We noticed something that might help.";
      strip.appendChild(msg);

      if (data.products && data.products.length > 0) {
        var productsDiv = document.createElement("div");
        productsDiv.className = "products";
        data.products.slice(0, 2).forEach(function (p) {
          var chip = document.createElement("a");
          chip.className = "product-chip";
          chip.textContent = p.name || p.id || "View";
          chip.href = p.url || "#";
          chip.target = "_blank";
          chip.rel = "noopener";
          productsDiv.appendChild(chip);
        });
        strip.appendChild(productsDiv);
      }

      var btn = document.createElement("button");
      btn.className = "dismiss";
      btn.setAttribute("aria-label", "Dismiss suggestion");
      btn.textContent = "\u00D7";
      btn.addEventListener("click", function () {
        try {
          host.remove();
        } catch (e) {}
      });
      strip.appendChild(btn);

      shadow.appendChild(style);
      shadow.appendChild(strip);
    } catch (e) {}
  }

  console.log("[LiveStreamSignals] Tracker active. Session:", SESSION_ID);
})();
