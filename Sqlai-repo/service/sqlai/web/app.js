/* SQL.AI web app. Every decision comes from the server; this file only renders it. */
(function () {
  "use strict";

  var TOKEN_KEY = "sqlai-token";
  var S = { token: null, me: null, tab: "work", catalog: null, last: null };

  var EXAMPLES = [
    { label: "Average CSAT by ticket category", tables: ["tickets"],
      sql: "SELECT category, ROUND(AVG(csat), 2) AS avg_csat, COUNT(*) AS tickets\nFROM tickets\nWHERE csat IS NOT NULL\nGROUP BY category\nORDER BY avg_csat" },
    { label: "Revenue by region in Q3 2026", tables: ["orders"],
      sql: "SELECT region, ROUND(SUM(amount), 2) AS revenue\nFROM orders\nWHERE order_date >= '2026-07-01' AND order_date < '2026-10-01'\nGROUP BY region\nORDER BY revenue DESC" },
    { label: "Revenue by month in 2026", tables: ["orders"],
      sql: "SELECT strftime(order_date, '%Y-%m') AS period, ROUND(SUM(amount), 2) AS revenue\nFROM orders\nWHERE order_date >= '2026-01-01'\nGROUP BY strftime(order_date, '%Y-%m')\nORDER BY period" },
    { label: "Customer contact list", tables: ["customers"], purpose: "Customer support",
      sql: "SELECT customer_id, full_name, email, phone, tier\nFROM customers\nORDER BY customer_id" },
    { label: "Average salary by department", tables: ["employees"],
      sql: "SELECT department, COUNT(*) AS headcount, ROUND(AVG(salary), 0) AS avg_salary\nFROM employees\nGROUP BY department\nORDER BY avg_salary DESC" },
    { label: "Try a write (blocked)", tables: [],
      sql: "DELETE FROM orders" }
  ];

  // ---------------------------------------------------------------- utilities
  function $(id) { return document.getElementById(id); }
  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function initials(n) { return n.split(" ").map(function (p) { return p[0]; }).join("").slice(0, 2); }
  function toast(msg) {
    var t = $("toast"); t.textContent = msg; t.hidden = false;
    clearTimeout(toast.t); toast.t = setTimeout(function () { t.hidden = true; }, 3500);
  }
  var MONEY = /revenue|amount|salary|spend|order_value/i;
  function fmt(k, v) {
    if (v == null) return '<span class="muted">null</span>';
    if (typeof v === "number") {
      var s = v.toLocaleString(undefined, { maximumFractionDigits: 2 });
      return MONEY.test(k) ? "$" + s : s;
    }
    return esc(v);
  }
  function isProtected(v) { return v === "suppressed" || /^<\d+$/.test(String(v)); }

  // ---------------------------------------------------------------- API
  function api(path, opts) {
    opts = opts || {};
    var headers = { "Accept": "application/json" };
    if (S.token) headers["Authorization"] = "Bearer " + S.token;
    if (opts.body) headers["Content-Type"] = "application/json";
    return fetch(path, { method: opts.method || "GET", headers: headers, body: opts.body ? JSON.stringify(opts.body) : undefined, cache: "no-store" })
      .then(function (res) {
        return res.json().catch(function () { return {}; }).then(function (j) {
          if (res.status === 401) { signOut(true); throw { code: "UNAUTHENTICATED", message: "Your session ended. Sign in again." }; }
          if (!res.ok) { var e = (j && j.error) || {}; throw { status: res.status, code: e.code || "ERROR", message: e.message || "The request failed (" + res.status + ")." }; }
          return j;
        });
      }, function () {
        throw { code: "NETWORK", message: "Couldn't reach the SQL.AI service. Check that it's running." };
      });
  }

  // ---------------------------------------------------------------- sign-in
  function showSignin() {
    $("app").hidden = true; $("signin").hidden = false;
    api("/v1/dev/users").then(function (users) {
      $("user-list").innerHTML = users.map(function (u) {
        return '<button type="button" data-token="' + esc(u.token) + '"><span class="avatar" aria-hidden="true">' + esc(initials(u.name)) +
          '</span><span><b>' + esc(u.name) + '</b><span class="r">' + esc(u.title) + "</span></span></button>";
      }).join("");
    }).catch(function () {
      $("signin-lede").textContent = "Sign-in through your company's identity provider isn't configured in this environment.";
      $("user-list").innerHTML = "";
    });
  }
  function signIn(token) {
    S.token = token;
    try { sessionStorage.setItem(TOKEN_KEY, token); } catch (e) {}
    api("/v1/me").then(function (me) {
      S.me = me;
      $("signin").hidden = true; $("app").hidden = false;
      $("me-name").textContent = me.name; $("me-role").textContent = me.titles.join(", ");
      $("me-av").textContent = initials(me.name);
      $("pv-chip").textContent = "Policy " + me.policy_version + " · server enforced";
      $("audit-admin").hidden = !me.audit_all;
      renderExamples(); loadCatalog(); health(); renderGate(null); renderResults(null);
      setTab(S.tab);
    }).catch(function (e) { if (e.code !== "UNAUTHENTICATED") toast(e.message); });
  }
  function signOut(expired) {
    S.token = null; S.me = null; S.last = null;
    try { sessionStorage.removeItem(TOKEN_KEY); } catch (e) {}
    showSignin();
    if (expired) toast("Your session ended. Sign in again.");
  }
  function health() {
    api("/healthz").then(function (h) {
      $("health-chip").className = "chip ok server-chip";
      $("health-chip").textContent = "Service OK · policy " + h.policy_version + " · " + h.policy_digest;
    }).catch(function () {
      $("health-chip").className = "chip bad server-chip"; $("health-chip").textContent = "Service unreachable";
    });
  }

  // ---------------------------------------------------------------- tabs
  var TABS = ["work", "catalog", "audit"];
  function setTab(t) {
    if (TABS.indexOf(t) < 0) t = "work";
    S.tab = t;
    Array.prototype.forEach.call(document.querySelectorAll("#tabs button"), function (b) {
      var on = b.dataset.tab === t; b.setAttribute("aria-selected", String(on)); b.tabIndex = on ? 0 : -1;
    });
    TABS.forEach(function (v) { $("view-" + v).hidden = v !== t; });
    if (t === "audit") loadAudit();
    if (t === "catalog") renderCatalog();
  }

  // ---------------------------------------------------------------- workbench
  function renderExamples() {
    var mine = EXAMPLES.filter(function (e) { return e.tables.every(function (t) { return S.me.tables.indexOf(t) >= 0; }); });
    $("examples").innerHTML = mine.map(function (e, i) {
      return '<button type="button" data-ex="' + EXAMPLES.indexOf(e) + '">' + esc(e.label) + "</button>";
    }).join("") || '<span class="note">Your role has no data tables. Use the Audit log tab.</span>';
    if (mine.length && !$("sql").value) { $("sql").value = mine[0].sql; }
  }
  function loadCatalog() {
    return api("/v1/catalog").then(function (c) {
      S.catalog = c;
      $("purpose").innerHTML = '<option value="">Not specified</option>' + c.purposes.map(function (p) {
        return "<option>" + esc(p) + "</option>";
      }).join("");
      if (S.tab === "catalog") renderCatalog();
    }).catch(function (e) { toast(e.message); });
  }
  var ICON = { pass: "✓", applied: "≡", held: "⏱", blocked: "✕", idle: "·" };
  var ICLASS = { pass: "pass", applied: "mod", held: "hold", blocked: "block", idle: "idle" };
  var WORD = { pass: "Passed", applied: "Applied", held: "Held", blocked: "Blocked", idle: "Not run" };
  function renderGate(r) {
    var rules = r ? r.rules : [];
    $("checks").innerHTML = rules.length ? rules.map(function (x) {
      return '<li><span class="ico ' + ICLASS[x.state] + '" aria-hidden="true">' + ICON[x.state] + '</span><div><div class="t">' +
        esc(x.id + " " + x.name) + ' <span class="sr">' + WORD[x.state] + '</span></div><div class="d">' + esc(x.detail) + "</div></div></li>";
    }).join("") : '<li><span class="ico idle" aria-hidden="true">·</span><div><div class="t">No query yet</div><div class="d">Each rule\'s result appears here after the server decides.</div></div></li>';
    var gs = $("gate-state");
    if (!r) { gs.className = "chip mute"; gs.textContent = "Waiting"; $("verdict").innerHTML = ""; return; }
    var m = { allowed: ["ok", "Allowed", "ok"], modified: ["ok", "Allowed", "ok"], held: ["warn", "Held", "hold"], blocked: ["bad", "Blocked", "block"], error: ["mute", "Error", "err"] }[r.decision];
    gs.className = "chip " + m[0]; gs.textContent = m[1];
    $("verdict").innerHTML = '<div class="verdict ' + m[2] + '" role="status">' + esc(r.message) + '</div>';
  }
  function barChart(rows, li, vi, vname) {
    var max = Math.max.apply(null, rows.map(function (r) { return typeof r[vi] === "number" ? r[vi] : 0; })) || 1;
    return '<div class="bars">' + rows.map(function (r) {
      var v = r[vi], w = typeof v === "number" ? Math.max(0, v / max * 100) : 0;
      return '<div class="lab" title="' + esc(r[li]) + '">' + esc(r[li]) + '</div><div class="track"><div class="fill" data-w="' + w.toFixed(1) +
        '"></div></div><div class="val">' + fmt(vname, v) + "</div>";
    }).join("") + "</div>";
  }
  function renderResults(r) {
    var box = $("results"), chips = $("res-chips"), trust = $("trust");
    chips.innerHTML = ""; trust.innerHTML = "";
    if (!r) { box.innerHTML = '<div class="empty">Run a query to see results here.</div>'; return; }
    if (r.decision === "blocked") {
      box.innerHTML = '<div class="empty">Nothing ran. ' + esc(r.message) +
        (r.access_tables && r.access_tables.length ? "<br>Access requests for " + esc(r.access_tables.join(", ")) + " arrive with the approval workflow in Phase 2." : "") + "</div>";
      return;
    }
    if (r.decision === "error") { box.innerHTML = '<div class="empty">' + esc(r.message) + "</div>"; return; }
    if (r.decision === "held") {
      var a = r.approval || {};
      box.innerHTML = '<div class="empty stack"><div><b>' + esc(a.reason || "Held for approval") + "</b></div>" +
        '<div>Eligible approvers:</div><div class="approvers">' + (a.eligible_approvers || []).map(function (u) { return '<span class="chip warn">' + esc(u) + "</span>"; }).join("") +
        '</div><div class="note">' + esc(a.note || "") + "</div><div class=\"note\">Request " + esc(r.request_id) + " · audit entry #" + esc(r.audit.seq) + "</div></div>";
      return;
    }
    var t = r.trust || {}, masked = t.masked_columns || {}, rounded = t.rounded_columns || [];
    chips.innerHTML = '<span class="chip ok">Within policy</span>' +
      (Object.keys(masked).length ? '<span class="chip data">Masked: ' + esc(Object.keys(masked).join(", ")) + "</span>" : "") +
      (t.suppressed_values ? '<span class="chip data">' + t.suppressed_values + " suppressed</span>" : "") +
      '<span class="chip mute">' + r.row_count + " row" + (r.row_count === 1 ? "" : "s") + "</span>";
    if (!r.rows.length) { box.innerHTML = '<div class="empty">The query ran but returned no rows for your scope.</div>'; return; }
    var cols = r.columns;
    function numCol(i) { return r.rows.every(function (x) { return x[i] == null || typeof x[i] === "number" || isProtected(x[i]); }); }
    var li = -1, vi = -1;
    cols.forEach(function (c, i) { if (li < 0 && !numCol(i)) li = i; });
    cols.forEach(function (c, i) { if (vi < 0 && i !== li && numCol(i) && !/_id$/.test(c) && r.rows.some(function (x) { return typeof x[i] === "number"; })) vi = i; });
    var chart = (li >= 0 && vi >= 0 && r.rows.length >= 2 && r.rows.length <= 24)
      ? '<figure class="fig"><figcaption class="eyebrow">' + esc(cols[vi].replace(/_/g, " ")) + " by " + esc(cols[li].replace(/_/g, " ")) + "</figcaption>" + barChart(r.rows, li, vi, cols[vi]) + "</figure>" : "";
    var head = cols.map(function (c, i) {
      return '<th scope="col" class="' + (numCol(i) ? "num" : "") + '">' + esc(c) + (masked[c] ? " · masked" : rounded.indexOf(c) >= 0 ? " · rounded" : "") + "</th>";
    }).join("");
    var body = r.rows.map(function (x) {
      return "<tr>" + x.map(function (v, i) {
        return '<td class="' + (numCol(i) ? "num " : "") + (masked[cols[i]] || isProtected(v) ? "masked" : "") + '">' + fmt(cols[i], v) + "</td>";
      }).join("") + "</tr>";
    }).join("");
    box.innerHTML = chart + '<div class="tbl-box"><table><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table></div>";
    Array.prototype.forEach.call(box.querySelectorAll(".fill[data-w]"), function (el) { el.style.width = el.dataset.w + "%"; });
    var items = [
      ["Rows in scope", t.rows_in_scope], ["Masking", Object.keys(masked).map(function (k) { return k + " (" + masked[k].replace(/_/g, " ") + ")"; }).join(", ") || (rounded.length ? "True values aggregated, then rounded: " + rounded.join(", ") : "None")],
      ["Small groups", t.suppressed_values ? t.suppressed_values + " value(s) suppressed" : "None suppressed"],
      ["Rules applied", (t.rules_applied || []).join(", ") || "None changed the result"],
      ["Policy", t.policy_version + (t.purpose ? " · purpose: " + t.purpose : "")],
      ["Audit", "Entry #" + r.audit.seq + " · request " + r.request_id]
    ];
    trust.innerHTML = '<div class="trust"><h3>How this answer was produced</h3><dl>' + items.map(function (i) {
      return "<dt>" + esc(i[0]) + "</dt><dd>" + esc(i[1]) + "</dd>";
    }).join("") + "</dl></div>";
  }
  function run() {
    var sql = $("sql").value.trim();
    $("run-err").textContent = "";
    if (!sql) { $("run-err").textContent = "Write a query or pick an example first."; $("sql").focus(); return; }
    var btn = $("run-btn"); btn.disabled = true; btn.innerHTML = '<span class="spin" aria-hidden="true"></span> Running…';
    api("/v1/queries", { method: "POST", body: { sql: sql, purpose: $("purpose").value || null } }).then(function (r) {
      S.last = r; renderGate(r); renderResults(r);
      if (window.matchMedia("(max-width:960px)").matches) $("results-panel").scrollIntoView({ behavior: "smooth", block: "start" });
    }).catch(function (e) {
      if (e.code === "UNAUTHENTICATED") return;
      renderGate(null); renderResults(null);
      $("run-err").textContent = e.status === 503 ? e.message + " Nothing was run or returned." : e.message;
    }).then(function () { btn.disabled = false; btn.textContent = "Run under policy"; });
  }

  // ---------------------------------------------------------------- catalog
  function renderCatalog() {
    if (!S.catalog) return;
    var tables = S.catalog.tables, names = Object.keys(tables);
    var clsChip = { Public: "mute", Confidential: "gate", PII: "warn", Restricted: "bad" };
    $("catalog").innerHTML = names.length ? names.map(function (t) {
      var info = tables[t];
      return '<article class="panel pad stack"><div class="req-top"><div><h3><code>' + esc(t) + '</code></h3><div class="note">Domain: ' + esc(info.domain) +
        '</div></div><span class="chip ok">' + esc(info.rows === "All" ? "All rows" : info.rows) + '</span></div><div class="tbl-box free"><table><thead><tr><th scope="col">Column</th><th scope="col">Type</th><th scope="col">Class</th><th scope="col">You see</th></tr></thead><tbody>' +
        Object.keys(info.columns).map(function (c) {
          var col = info.columns[c];
          return "<tr><td><code>" + esc(c) + '</code></td><td class="muted">' + esc(col.type) + '</td><td><span class="chip ' + (clsChip[col["class"]] || "mute") + '">' + esc(col["class"]) +
            "</span></td><td>" + (col.you_see === "visible" ? "Visible" : '<span class="masked mono">' + esc(col.you_see.replace(/_/g, " ")) + "</span>") + "</td></tr>";
        }).join("") + "</tbody></table></div></article>";
    }).join("") : '<div class="panel empty">Your role doesn\'t have access to any data tables.</div>';
  }

  // ---------------------------------------------------------------- audit
  function loadAudit() {
    $("audit-note").textContent = "Loading…";
    api("/v1/audit?limit=200").then(function (j) {
      $("audit-lede").textContent = j.scope === "all" ? "Everyone's activity, newest first. Each entry is hashed together with the one before it." : "Your activity, newest first. Security and data admins see everyone's.";
      $("audit-note").textContent = j.records.length + " entries";
      var oc = { allowed: "ok", modified: "ok", blocked: "bad", held: "warn", alert: "bad", info: "mute", error: "mute" };
      $("audit-table").innerHTML = '<thead><tr><th scope="col" class="num">#</th><th scope="col">Time (UTC)</th><th scope="col">User</th><th scope="col">Event</th><th scope="col">Outcome</th><th scope="col">Detail</th><th scope="col">SQL (redacted)</th><th scope="col" class="num">Rows</th><th scope="col">Hash</th></tr></thead><tbody>' +
        (j.records.length ? j.records.map(function (e) {
          return '<tr><td class="num">' + e.seq + "</td><td>" + esc(e.ts.replace("T", " ").slice(0, 19)) + "</td><td>" + esc(e.actor) + "</td><td>" + esc(e.action) +
            '</td><td><span class="chip ' + (oc[e.outcome] || "mute") + '">' + esc(e.outcome) + '</span></td><td class="wrap">' + esc(e.detail) +
            '</td><td class="wrap"><code class="small">' + esc(e.sql_redacted.length > 160 ? e.sql_redacted.slice(0, 160) + "…" : e.sql_redacted) +
            '</code></td><td class="num">' + (e.row_count == null ? "" : e.row_count) + '</td><td class="hash" title="' + esc(e.hash) + '">' + esc(e.hash.slice(0, 10)) + "</td></tr>";
        }).join("") : '<tr><td colspan="9" class="muted">No entries yet.</td></tr>') + "</tbody>";
    }).catch(function (e) { $("audit-note").textContent = e.message; });
  }
  function verify() {
    api("/v1/audit/verify", { method: "POST" }).then(function (j) {
      var ok = j.chain.ok && j.checkpoints.ok, c = $("chain-state");
      c.className = "chip " + (ok ? "ok" : "bad");
      c.textContent = ok ? "Intact · " + j.chain.entries + " entries" : (j.chain.ok ? "Checkpoint mismatch: " + j.checkpoints.reason : "Broken at entry #" + j.chain.broken_at);
      loadAudit();
    }).catch(function (e) { toast(e.message); });
  }
  function checkpoint() {
    api("/v1/audit/checkpoint", { method: "POST" }).then(function (j) {
      toast(j.checkpoint ? "Checkpoint written for entries " + j.checkpoint.from_seq + "–" + j.checkpoint.to_seq + "." : "No new entries since the last checkpoint.");
    }).catch(function (e) { toast(e.message); });
  }

  // ---------------------------------------------------------------- wiring
  document.addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    if (b.dataset.token) { signIn(b.dataset.token); return; }
    if (b.dataset.tab) { setTab(b.dataset.tab); return; }
    if (b.dataset.ex != null) {
      var ex = EXAMPLES[+b.dataset.ex]; $("sql").value = ex.sql; $("purpose").value = ex.purpose || ""; $("sql").focus(); return;
    }
    switch (b.id) {
      case "signout-btn": signOut(false); break;
      case "verify-btn": verify(); break;
      case "checkpoint-btn": checkpoint(); break;
      case "audit-refresh": loadAudit(); break;
    }
  });
  $("run-form").addEventListener("submit", function (e) { e.preventDefault(); run(); });
  $("sql").addEventListener("keydown", function (e) { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(); } });
  $("tabs").addEventListener("keydown", function (e) {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    var i = TABS.indexOf(S.tab), n = (i + (e.key === "ArrowRight" ? 1 : -1) + TABS.length) % TABS.length;
    setTab(TABS[n]); $("tab-" + TABS[n]).focus(); e.preventDefault();
  });

  var saved = null;
  try { saved = sessionStorage.getItem(TOKEN_KEY); } catch (e) {}
  if (saved) signIn(saved); else showSignin();
})();
