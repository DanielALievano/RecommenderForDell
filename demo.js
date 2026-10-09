/**
 * Live Stream Signals — DEMO / DEBUG MODE
 * ----------------------------------------
 * Inject this on dell.com via DevTools Snippets.
 *
 * What it does:
 *   - Captures all browser events (clicks, dwells, search, scroll, etc.)
 *   - Shows a floating live panel so you can see events in real time
 *   - Attempts to POST to the backend (works if you allow mixed content — see below)
 *   - Works as a visual demo even if the backend is offline
 *
 * TO ALLOW MIXED CONTENT ON DELL.COM (one-time):
 *   Chrome address bar → click the lock icon → Site settings → Insecure content → Allow
 *   Then refresh dell.com and re-run this snippet.
 *
 * BACKEND:
 *   uvicorn app.main:app --reload --port 8000
 */
(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // Config
  // -----------------------------------------------------------------------
  var API_BASE = "http://localhost:8000";
  var PANEL_MAX_LINES = 30;

  // -----------------------------------------------------------------------
  // Session identity
  // -----------------------------------------------------------------------
  function uuidv4() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0, v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  // Read/write cookies — mirrors what the React useCookieStore hook uses
  function _getCookie(name) {
    var m = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : null;
  }
  function _setCookie(name, value, days) {
    var c = name + "=" + encodeURIComponent(value) + ";path=/;SameSite=Lax";
    if (days) c += ";expires=" + new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = c;
  }

  // Session ID — same cookie as React hook (lss_sid), persists across page loads
  var SESSION_ID = (function () {
    var id = _getCookie("lss_sid");
    if (!id) { id = "s_ecid_" + uuidv4(); _setCookie("lss_sid", id); }
    return id;
  })();

  // Visit number — same cookie as React hook (lss_visit)
  var VISIT_NUMBER = (function () {
    var n = parseInt(_getCookie("lss_visit") || "0", 10) + 1;
    _setCookie("lss_visit", String(n), 365);
    return n;
  })();

  // Seen products — read from the React-managed lss_products cookie on startup,
  // then keep in sync so both layers share the same context
  var _seenProducts = (function () {
    try { return JSON.parse(_getCookie("lss_products") || "[]"); } catch (e) { return []; }
  })();

  function _addProduct(name) {
    if (!name || name.length < 3) return;
    var clean = name.trim().replace(/\s+/g, " ").slice(0, 100);
    if (!_seenProducts.includes(clean)) {
      _seenProducts.push(clean);
      _seenProducts = _seenProducts.slice(-20);
      _setCookie("lss_products", JSON.stringify(_seenProducts), 30);
    }
  }

  // -----------------------------------------------------------------------
  // Debug panel (shadow DOM so it doesn't break dell.com styles)
  // -----------------------------------------------------------------------
  var _panelLines = [];
  var _panelEl = null;
  var _logEl = null;
  var _statusEl = null;
  var _sentCount = 0;
  var _eventCount = 0;

  function _initPanel() {
    var host = document.createElement("div");
    host.id = "lss-debug-host";
    host.style.cssText = "position:fixed;bottom:16px;right:16px;z-index:2147483647;";
    document.body.appendChild(host);

    var shadow = host.attachShadow({ mode: "open" });

    var style = document.createElement("style");
    style.textContent = `
      .panel {
        width: 420px;
        max-height: 420px;
        background: #1a1a2e;
        color: #e0e0e0;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 11px;
        border-radius: 8px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border: 1px solid #0076CE;
      }
      .header {
        background: #0076CE;
        color: #fff;
        padding: 6px 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12px;
        font-weight: bold;
        cursor: move;
        user-select: none;
      }
      .header-left { display: flex; align-items: center; gap: 8px; }
      .dot { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; animation: pulse 1.5s infinite; }
      @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
      .status {
        background: #12122a;
        padding: 4px 12px;
        font-size: 10px;
        color: #9ca3af;
        border-bottom: 1px solid #2d2d5e;
        display: flex;
        gap: 16px;
      }
      .stat { color: #60a5fa; font-weight: bold; }
      .log {
        flex: 1;
        overflow-y: auto;
        padding: 6px 0;
      }
      .line {
        padding: 2px 12px;
        line-height: 1.5;
        border-left: 3px solid transparent;
        transition: background 0.1s;
      }
      .line:hover { background: rgba(255,255,255,0.04); }
      .t1 { border-left-color: #f59e0b; color: #fde68a; }
      .t2 { border-left-color: #60a5fa; color: #bfdbfe; }
      .t3 { border-left-color: #6b7280; color: #9ca3af; }
      .sys { border-left-color: #4ade80; color: #86efac; font-style: italic; }
      .err { border-left-color: #f87171; color: #fca5a5; }
      .ts { color: #6b7280; margin-right: 6px; }
      .controls {
        padding: 6px 12px;
        display: flex;
        gap: 8px;
        border-top: 1px solid #2d2d5e;
      }
      button {
        background: #0076CE;
        color: #fff;
        border: none;
        border-radius: 4px;
        padding: 3px 10px;
        font-size: 10px;
        cursor: pointer;
        font-family: inherit;
      }
      button:hover { background: #005fa3; }
      button.secondary { background: #2d2d5e; }
      button.secondary:hover { background: #3d3d7e; }
    `;

    var panel = document.createElement("div");
    panel.className = "panel";

    var header = document.createElement("div");
    header.className = "header";
    header.innerHTML = `
      <div class="header-left">
        <div class="dot"></div>
        <span>Live Stream Signals — Demo</span>
      </div>
      <span style="font-size:10px;opacity:0.8">${SESSION_ID.slice(0, 20)}…</span>
    `;

    var status = document.createElement("div");
    status.className = "status";
    status.innerHTML = `
      <span>Events: <span class="stat" id="ev-count">0</span></span>
      <span>Sent: <span class="stat" id="sent-count">0</span></span>
      <span>Backend: <span class="stat" id="backend-status">checking…</span></span>
    `;

    var log = document.createElement("div");
    log.className = "log";

    var controls = document.createElement("div");
    controls.className = "controls";
    controls.innerHTML = `
      <button id="flush-btn">Flush now</button>
      <button id="clear-btn" class="secondary">Clear log</button>
      <button id="close-btn" class="secondary">Hide</button>
    `;

    panel.appendChild(header);
    panel.appendChild(status);
    panel.appendChild(log);
    panel.appendChild(controls);
    shadow.appendChild(style);
    shadow.appendChild(panel);

    _logEl = log;
    _statusEl = status;
    _panelEl = panel;

    // Wire buttons
    controls.querySelector("#flush-btn").addEventListener("click", function () {
      _flush("manual");
    });
    controls.querySelector("#clear-btn").addEventListener("click", function () {
      _panelLines = [];
      log.innerHTML = "";
    });
    controls.querySelector("#close-btn").addEventListener("click", function () {
      host.style.display = "none";
    });

    // Draggable
    var dragging = false, ox = 0, oy = 0;
    header.addEventListener("mousedown", function (e) {
      dragging = true;
      ox = e.clientX - host.offsetLeft;
      oy = e.clientY - host.offsetTop;
    });
    document.addEventListener("mousemove", function (e) {
      if (!dragging) return;
      host.style.left = (e.clientX - ox) + "px";
      host.style.bottom = "auto";
      host.style.top = (e.clientY - oy) + "px";
      host.style.right = "auto";
    });
    document.addEventListener("mouseup", function () { dragging = false; });
  }

  function _log(tier, line) {
    if (!_logEl) return;
    var cls = tier === "sys" ? "sys" : tier === "err" ? "err" : "t" + tier;
    var now = new Date().toTimeString().slice(0, 8);
    var div = document.createElement("div");
    div.className = "line " + cls;
    div.innerHTML = `<span class="ts">${now}</span>${_esc(line)}`;
    _logEl.appendChild(div);
    // Trim
    while (_logEl.children.length > PANEL_MAX_LINES) {
      _logEl.removeChild(_logEl.firstChild);
    }
    _logEl.scrollTop = _logEl.scrollHeight;
  }

  function _esc(s) {
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  function _updateStatus() {
    if (!_statusEl) return;
    var ec = _statusEl.querySelector("#ev-count");
    var sc = _statusEl.querySelector("#sent-count");
    if (ec) ec.textContent = _eventCount;
    if (sc) sc.textContent = _sentCount;
  }

  function _setBackendStatus(s, ok) {
    if (!_statusEl) return;
    var el = _statusEl.querySelector("#backend-status");
    if (el) {
      el.textContent = s;
      el.style.color = ok ? "#4ade80" : "#f87171";
    }
  }

  // -----------------------------------------------------------------------
  // Ping backend
  // -----------------------------------------------------------------------
  async function _pingBackend() {
    try {
      var r = await fetch(API_BASE + "/health", { signal: AbortSignal.timeout(2000) });
      if (r.ok) {
        _setBackendStatus("online", true);
        _log("sys", "Backend online at " + API_BASE);
      } else {
        _setBackendStatus("error " + r.status, false);
      }
    } catch (e) {
      _setBackendStatus("offline", false);
      _log("err", "Backend offline — events logged locally only");
      _log("err", "Fix: allow insecure content in Chrome site settings, then refresh");
    }
  }

  // -----------------------------------------------------------------------
  // Buffer & flush
  // -----------------------------------------------------------------------
  var _buffer = [];
  var _pageStart = Date.now();
  var _activeSeconds = 0;
  var _tabActive = !document.hidden;

  function elapsed() { return Math.round((Date.now() - _pageStart) / 1000); }
  function clean(s) { return String(s||"").replace(/[\r\n\t]+/g," ").trim().slice(0,200); }

  var _CTX_PATTERNS = [
    [/nav(igation)?|navbar|site-nav/i,"navigation"],
    [/paginat|page-nav/i,"pagination"],
    [/breadcrumb/i,"breadcrumb"],
    [/menu|dropdown/i,"menu"],
    [/header|masthead/i,"header"],
    [/footer/i,"footer"],
    [/promo|banner|hero|sale/i,"promo_banner"],
    [/product[-_]?card|item[-_]?card|tile/i,"product_card"],
    [/spec[-_]?section|tech[-_]?spec/i,"spec_section"],
    [/spec[-_]?item|spec[-_]?row/i,"spec_item"],
  ];

  function nearestContainer(el) {
    var cur = el;
    for (var d=0; d<10 && cur && cur!==document.body; d++) {
      var cls=(cur.className||"")+" "+(cur.getAttribute("data-testid")||"")+" "+(cur.id||"");
      for (var i=0;i<_CTX_PATTERNS.length;i++) if(_CTX_PATTERNS[i][0].test(cls)) return _CTX_PATTERNS[i][1];
      cur=cur.parentElement;
    }
    return "content";
  }

  function _record(tier, conf, eventType, content, ctx, dwellSecs) {
    try {
      _eventCount++;
      var parts = ["["+elapsed()+"s]","[T"+tier+" "+conf.toFixed(2)+"]",eventType.toUpperCase().replace(/_/g," ")];
      if (dwellSecs) parts.push(dwellSecs.toFixed(0)+"s on");
      if (content) parts.push('"'+clean(content)+'"');
      if (ctx && ctx!=="content") parts.push("("+ctx+")");
      var line = parts.join(" ");
      _buffer.push(line);
      _log(tier, line);
      _updateStatus();
      if (_buffer.length >= 20) _flush("buffer_full");
    } catch(e) {}
  }

  async function _flush(trigger) {
    try {
      if (_buffer.length === 0) return;
      var narrative = _buffer.join("\n");
      _buffer = [];

      // Re-read cookie in case React hook updated it during this session
      try { _seenProducts = JSON.parse(_getCookie("lss_products") || "[]"); } catch(e) {}
      var productContext = _seenProducts.length > 0
        ? "[0s] [T1 0.90] PRODUCTS BROWSED \"" + _seenProducts.join(" | ") + "\" (session_context)\n"
        : "";

      var payload = {
        session_id: SESSION_ID,
        visit_number: VISIT_NUMBER,
        page_url: location.href,
        page_title: document.title,
        referrer: document.referrer||"",
        active_seconds: _activeSeconds,
        total_events: _eventCount,
        trigger: trigger||"timer",
        narrative: productContext + narrative,
      };
      _log("sys", "Flushing "+narrative.split("\n").length+" events (trigger="+trigger+")");
      try {
        var r = await fetch(API_BASE+"/api/clickstream/ingest", {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body: JSON.stringify(payload),
          keepalive: true,
        });
        if (r.ok) {
          var data = await r.json();
          _sentCount++;
          _updateStatus();
          _log("sys", "ACK: acted="+data.acted+" delta="+data.delta+" signals="+data.signal_count);
          if (data.acted) _log("sys", "LLM inference triggered in background");
        } else {
          _log("err", "Server error: "+r.status);
        }
      } catch(e) {
        _log("err", "POST failed (mixed content blocked?): "+e.message);
      }
    } catch(e) {}
  }

  window._lssFlush = function(t) { _flush(t||"manual"); };
  window._lssBuffer = function() { return _buffer.slice(); };

  // Periodic flush
  setInterval(function() { _flush("timer"); }, 15000);

  // Active time
  setInterval(function() { if(_tabActive) _activeSeconds++; }, 1000);
  document.addEventListener("visibilitychange", function() {
    _tabActive = !document.hidden;
    _record(3, 0.40, _tabActive?"tab_visible":"tab_hidden","","",0);
  });

  // -----------------------------------------------------------------------
  // Event listeners
  // -----------------------------------------------------------------------

  // Scroll
  var _maxScroll=0;
  window.addEventListener("scroll", function() {
    try {
      var pct=Math.round(((window.scrollY+window.innerHeight)/document.body.scrollHeight)*100);
      if(pct>_maxScroll+15){_maxScroll=pct;_record(3,0.30,"scroll_depth",pct+"%","",0);}
    } catch(e){}
  },{passive:true});

  // Clicks
  var _lastClickTime=0, _lastClickTarget=null, _clickCount=0;
  document.addEventListener("click", function(e) {
    try {
      var t=e.target, now=Date.now();
      var ctx=nearestContainer(t);
      var label=clean(t.innerText||t.getAttribute("aria-label")||t.getAttribute("title")||"").slice(0,80);
      if(t===_lastClickTarget && now-_lastClickTime<500){
        _clickCount++;
        if(_clickCount>=3){ _record(1,0.85,"rage_click",label,ctx,0); setTimeout(()=>_flush("rage_click"),50); _clickCount=0; }
      } else { _clickCount=1; }
      _lastClickTarget=t; _lastClickTime=now;
      var isInteractive=t.tagName==="A"||t.tagName==="BUTTON"||t.tagName==="INPUT"||t.tagName==="SELECT"||t.getAttribute("role")==="button";
      if(isInteractive) _record(2,0.65,"click",label,ctx,0);
    } catch(e){}
  },true);

  // Text select & copy
  document.addEventListener("selectionchange", function() {
    try {
      var sel=window.getSelection();
      if(sel&&sel.toString().trim().length>5){
        var ctx=sel.anchorNode&&sel.anchorNode.parentElement?nearestContainer(sel.anchorNode.parentElement):"content";
        _record(1,0.80,"text_select",clean(sel.toString()),ctx,0);
      }
    } catch(e){}
  });
  document.addEventListener("copy", function() {
    try {
      var sel=window.getSelection();
      if(sel){var t=clean(sel.toString()); if(t.length>2){_record(1,0.88,"text_copy",t,"",0); setTimeout(()=>_flush("text_copy"),50);}}
    } catch(e){}
  });

  // Search / input
  var _inputDebounce={};
  document.addEventListener("input", function(e) {
    try {
      var t=e.target;
      var name=clean(t.name||t.placeholder||t.getAttribute("aria-label")||"");
      var val=clean(t.value||"");
      var ctx=nearestContainer(t);
      var key=name||"field";
      if(_inputDebounce[key]) clearTimeout(_inputDebounce[key]);
      _inputDebounce[key]=setTimeout(function(){
        var isSearch=t.type==="search"||/search/i.test(name)||t.getAttribute("role")==="searchbox";
        if(isSearch&&val.length>2){_record(1,0.90,"search_query",val,ctx,0); setTimeout(()=>_flush("search_query"),50);}
        else if(val.length>0) _record(2,0.60,"input_change",name+"->"+val,ctx,0);
      },600);
    } catch(e){}
  },true);

  // Multi-pass hover
  var _hoverCounts={}, _hoverTimers={};
  document.addEventListener("mouseover", function(e) {
    try {
      var t=e.target;
      var label=clean(t.getAttribute("aria-label")||t.innerText||"").slice(0,60);
      if(!label||label.length<3) return;
      _hoverCounts[label]=(_hoverCounts[label]||0)+1;
      if(_hoverCounts[label]>=2){
        if(_hoverTimers[label]) clearTimeout(_hoverTimers[label]);
        _hoverTimers[label]=setTimeout(function(){ _record(2,0.75,"multi_pass",label,nearestContainer(t),0); },1000);
      }
    } catch(e){}
  },{passive:true});

  // Idle
  var _idleTimer=null;
  function _resetIdle(){
    if(_idleTimer) clearTimeout(_idleTimer);
    _idleTimer=setTimeout(function(){
      _record(2,0.75,"idle_start","","",0);
      setTimeout(()=>_flush("idle_start"),100);
    },4000);
  }
  ["mousemove","keydown","scroll","click"].forEach(ev=>document.addEventListener(ev,_resetIdle,{passive:true}));
  _resetIdle();

  // Filter changes via URL diff
  var _lastParams=location.search;
  (function(){
    try{
      var origPush=history.pushState, origReplace=history.replaceState;
      history.pushState=function(){origPush.apply(history,arguments);_checkUrlChange();};
      history.replaceState=function(){origReplace.apply(history,arguments);_checkUrlChange();};
      window.addEventListener("popstate",_checkUrlChange);
    }catch(e){}
  })();
  function _checkUrlChange(){
    try{
      if(location.search!==_lastParams){
        var oldP=new URLSearchParams(_lastParams), newP=new URLSearchParams(location.search);
        newP.forEach(function(v,k){if(oldP.get(k)!==v) _record(1,0.85,"filter_applied",v,"("+k+")",0);});
        _lastParams=location.search;
        _flush("filter_change");
      }
    }catch(e){}
  }

  // Pagehide
  window.addEventListener("pagehide",function(){
    try{
      _record(2,0.50,"page_exit","","",0);
      if(_buffer.length===0) return;
      var narrative=_buffer.join("\n"); _buffer=[];
      navigator.sendBeacon(API_BASE+"/api/clickstream/ingest",new Blob([JSON.stringify({
        session_id:SESSION_ID,visit_number:VISIT_NUMBER,page_url:location.href,
        page_title:document.title,referrer:document.referrer||"",
        active_seconds:_activeSeconds,total_events:_eventCount,trigger:"pagehide",narrative
      })],{type:"application/json"}));
    }catch(e){}
  });

  // -----------------------------------------------------------------------
  // SSE nudge (if backend is up)
  // -----------------------------------------------------------------------
  try {
    var es = new EventSource(API_BASE+"/api/session/stream/"+SESSION_ID);
    es.addEventListener("nudge", function(e) {
      try {
        var data=JSON.parse(e.data);
        _log("sys","NUDGE received: "+data.action_type+" — "+data.message);
        _renderNudge(data);
      } catch(ex){}
    });
    es.onerror=function(){};
  } catch(e) {}

  function _renderNudge(data) {
    try {
      if (window.__lssNudge) {
        window.__lssNudge.show(data);
      }
    } catch(e) {}
  }

  // Load the React nudge bundle from the backend, then boot the demo
  function _loadBundle(cb) {
    if (window.__lssNudge) { cb(); return; }
    var s = document.createElement("script");
    s.src = API_BASE + "/static/nudge-panel.iife.js";
    s.onload = cb;
    s.onerror = function() { console.warn("[LSS] Could not load nudge bundle — is the backend running?"); cb(); };
    document.head.appendChild(s);
  }

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------
  _loadBundle(function() {
    _initPanel();
    _pingBackend();
    _log("sys", "Session: "+SESSION_ID);
    _log("sys", "Visit #"+VISIT_NUMBER+" on "+location.hostname);
    _log("sys", "Listening for events… interact with the page!");
  });

  console.log("[LiveStreamSignals] Demo active. Session:", SESSION_ID);
  console.log("  Manual flush: window._lssFlush()");
  console.log("  View buffer:  window._lssBuffer()");
})();
