/* Square Peg Pizzeria — site behavior. No dependencies. */
(function () {
  "use strict";
  var LOCS = [];
  try { LOCS = JSON.parse(document.getElementById("sp-locs").textContent); } catch (e) {}
  var CFG = {};
  try { CFG = JSON.parse(document.getElementById("sp-cfg").textContent); } catch (e) {}
  var DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  var TZ = "America/New_York";
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function bySlug(s) { for (var i = 0; i < LOCS.length; i++) if (LOCS[i].slug === s) return LOCS[i]; return null; }
  function track(name, data) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(Object.assign({ event: name }, data || {}));
    if (window.fbq && name === "order_click") window.fbq("trackCustom", "OrderClick", data);
  }

  /* ---------- Open-now logic (all locations are US Eastern time) ---------- */
  function nowET() {
    var parts = new Intl.DateTimeFormat("en-US", { timeZone: TZ, weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(new Date());
    var o = {};
    parts.forEach(function (p) { o[p.type] = p.value; });
    return { day: DAYS.indexOf(o.weekday), mins: (parseInt(o.hour, 10) % 24) * 60 + parseInt(o.minute, 10) };
  }
  function toMin(t) { var a = t.split(":"); return +a[0] * 60 + +a[1]; }
  function fmt(t) {
    var m = toMin(t), hh = Math.floor(m / 60) % 24, mm = m % 60;
    if (hh === 0 && mm === 0) return "midnight";
    var ap = hh >= 12 ? "pm" : "am", h12 = hh % 12 || 12;
    return h12 + (mm ? ":" + (mm < 10 ? "0" : "") + mm : "") + ap;
  }
  function status(loc) {
    var n = nowET();
    // check yesterday's late-night window first
    var yKey = DAYS[(n.day + 6) % 7], y = loc.hours[yKey];
    if (y) {
      var yo = toMin(y[0]), yc = toMin(y[1]);
      if (yc <= yo && n.mins < yc) return { open: true, label: "Open · till " + fmt(y[1]), soon: yc - n.mins <= 45 };
    }
    var t = loc.hours[DAYS[n.day]];
    if (t) {
      var o = toMin(t[0]), c = toMin(t[1]); if (c <= o) c += 1440;
      if (n.mins >= o && n.mins < c) return { open: true, label: (c - n.mins <= 45 ? "Closing soon · " : "Open · till ") + fmt(t[1]), soon: c - n.mins <= 45 };
      if (n.mins < o) return { open: false, label: "Opens " + fmt(t[0]) + " today" };
    }
    for (var i = 1; i <= 7; i++) {
      var d = DAYS[(n.day + i) % 7], hrs = loc.hours[d];
      if (hrs) return { open: false, label: "Closed · opens " + (i === 1 ? "tomorrow " : d + " ") + fmt(hrs[0]) };
    }
    return { open: false, label: "Closed" };
  }
  function paintStatus(el, loc) {
    var s = status(loc);
    el.textContent = s.label;
    el.classList.remove("is-open", "is-closed", "is-soon");
    el.classList.add(s.open ? (s.soon ? "is-soon" : "is-open") : "is-closed");
  }
  function paintAll() {
    $$("[data-status]").forEach(function (el) { var l = bySlug(el.getAttribute("data-status")); if (l) paintStatus(el, l); });
    var n = nowET();
    $$(".hours tr[data-day]").forEach(function (tr) { tr.classList.toggle("today", tr.getAttribute("data-day") === DAYS[n.day]); });
  }

  /* ---------- Distance ---------- */
  var userPos = null;
  function miles(a, b) {
    var R = 3958.8, r = Math.PI / 180, dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r;
    var x = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
    return 2 * R * Math.asin(Math.sqrt(x));
  }
  function locate(cb) {
    if (!navigator.geolocation) { cb(false); return; }
    navigator.geolocation.getCurrentPosition(function (p) {
      userPos = { lat: p.coords.latitude, lng: p.coords.longitude };
      cb(true);
    }, function () { cb(false); }, { maximumAge: 600000, timeout: 8000 });
  }
  function sortedLocs() {
    var pref = store.get("sp_loc");
    var list = LOCS.slice();
    if (userPos) list.sort(function (a, b) { return miles(userPos, a) - miles(userPos, b); });
    else if (pref) list.sort(function (a, b) { return (b.slug === pref) - (a.slug === pref); });
    return list;
  }

  /* ---------- Preferred location ---------- */
  function setPref(slug) {
    store.set("sp_loc", slug);
    personalize();
  }
  function personalize() {
    var l = bySlug(store.get("sp_loc"));
    if (!l) return;
    $$("[data-for-loc]").forEach(function (el) { el.textContent = "· " + (l.short || l.name); });
    var sel = $("#quick-loc");
    if (sel && !sel.value) { sel.value = l.slug; updateQuick(); }
    var call = $("#mbar-call");
    if (call) { call.href = "tel:" + l.tel; call.removeAttribute("data-open-picker"); }
  }

  /* ---------- Picker sheet ---------- */
  var sheet = $("#picker");
  var mode = "order";
  function renderPicker() {
    var list = $("#picker-list"); if (!list) return;
    var pref = store.get("sp_loc");
    list.innerHTML = "";
    sortedLocs().forEach(function (l) {
      var row = document.createElement("div");
      row.className = "pick" + (l.slug === pref ? " is-pref" : "");
      var d = userPos ? '<span class="note">' + miles(userPos, l).toFixed(1) + " mi</span>" : "";
      var action = mode === "call"
        ? '<a class="btn btn--sm" href="tel:' + l.tel + '" data-pick="' + l.slug + '" data-track="call_click">Call</a>'
        : '<a class="btn btn--sm" href="' + l.order + '" data-pick="' + l.slug + '" data-track="' + (mode === "menu" ? "menu_click" : "order_click") + '" data-src="picker" rel="noopener">' + (mode === "menu" ? "View menu" : "Order") + '</a>';
      row.innerHTML =
        '<div class="pick-name">' + (l.short || l.name) + "</div>" +
        '<div class="pick-addr">' + l.street + ", " + l.city + ", " + l.state + "</div>" +
        '<div class="pick-meta"><span class="status" data-status="' + l.slug + '"></span>' + d +
        (mode === "call" ? "" : '<a class="pick-call" href="tel:' + l.tel + '">' + l.phone + "</a>") + "</div>" + action;
      list.appendChild(row);
    });
    paintAll();
  }
  function openPicker(m) {
    mode = m || "order";
    var t = $("#picker-title"); if (t) t.textContent = mode === "call" ? "Call a Peg" : mode === "menu" ? "Whose menu?" : "Pick your Peg";
    var sub = $("#picker-sub"); if (sub) sub.textContent = mode === "menu" ? "Menus & prices vary a little by location" : mode === "call" ? "Tap to call" : "Pickup or delivery, chosen at checkout";
    renderPicker();
    if (sheet && sheet.showModal) { sheet.showModal(); track("picker_open", { mode: mode }); }
    else location.href = CFG.locationsUrl;
  }
  document.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target.closest("[data-open-picker],[data-pick],[data-track],[data-close],#geo-sheet,#geo-quick,.map-btn,.menu-toggle") : null;
    if (!t) return;
    if (t.hasAttribute("data-open-picker")) { e.preventDefault(); openPicker(t.getAttribute("data-open-picker")); return; }
    if (t.hasAttribute("data-close")) { sheet && sheet.close(); return; }
    if (t.id === "geo-sheet" || t.id === "geo-quick") {
      e.preventDefault();
      var orig = t.textContent; t.textContent = "Finding you…";
      locate(function (ok) {
        t.textContent = ok ? "Sorted by distance" : "Location unavailable. Pick from the list";
        if (ok) {
          renderPicker();
          var near = sortedLocs()[0];
          var sel = $("#quick-loc");
          if (sel && t.id === "geo-quick") { sel.value = near.slug; updateQuick(); setPref(near.slug); }
          sortGrid();
        } else setTimeout(function () { t.textContent = orig; }, 3000);
      });
      return;
    }
    if (t.classList.contains("map-btn")) {
      var box = t.parentNode, f = document.createElement("iframe");
      f.src = t.getAttribute("data-map"); f.title = "Map"; f.loading = "lazy"; f.referrerPolicy = "no-referrer-when-downgrade";
      box.appendChild(f); t.remove(); return;
    }
    if (t.classList.contains("menu-toggle")) {
      var d = $("#drawer"), open = d.classList.toggle("open");
      t.setAttribute("aria-expanded", open ? "true" : "false"); return;
    }
    if (t.hasAttribute("data-pick")) setPref(t.getAttribute("data-pick"));
    if (t.hasAttribute("data-track")) track(t.getAttribute("data-track"), { location: t.getAttribute("data-pick") || t.getAttribute("data-loc") || "", source: t.getAttribute("data-src") || "" });
  });
  if (sheet) sheet.addEventListener("click", function (e) { if (e.target === sheet) sheet.close(); });

  /* ---------- Quick order bar ---------- */
  function updateQuick() {
    var sel = $("#quick-loc"); if (!sel) return;
    var l = bySlug(sel.value), go = $("#quick-order"), call = $("#quick-call"), info = $("#quick-info"), st = $("#quick-status");
    if (!l) { go.setAttribute("data-open-picker", "order"); go.href = CFG.locationsUrl; return; }
    go.removeAttribute("data-open-picker");
    go.href = l.order; go.setAttribute("data-pick", l.slug);
    go.querySelector("span").textContent = "Order from " + (l.short || l.name);
    call.href = "tel:" + l.tel; call.setAttribute("data-pick", l.slug);
    info.href = l.url;
    st.innerHTML = '<span class="status" data-status="' + l.slug + '"></span> ' + l.street + ", " + l.city;
    paintAll();
  }
  var qs = $("#quick-loc");
  if (qs) qs.addEventListener("change", function () { updateQuick(); if (qs.value) setPref(qs.value); });

  /* ---------- Sort location grid by distance ---------- */
  function sortGrid() {
    if (!userPos) return;
    $$(".loc-grid--all").forEach(function (grid) {
      var cards = $$(".loc-card[data-slug]", grid), cta = $(".loc-cta", grid);
      cards.sort(function (a, b) { return miles(userPos, bySlug(a.dataset.slug)) - miles(userPos, bySlug(b.dataset.slug)); });
      cards.forEach(function (c, i) {
        var d = c.querySelector(".dist"); if (d) d.textContent = miles(userPos, bySlug(c.dataset.slug)).toFixed(1) + " mi away";
        c.classList.toggle("is-near", i === 0);
        grid.appendChild(c);
      });
      if (cta) grid.appendChild(cta);
    });
  }

  /* ---------- Chat widget: load after the page is idle so it never slows first paint ---------- */
  function loadChat() {
    if (!CFG.chatSrc || window.__spChat) return;
    window.__spChat = true;
    var s = document.createElement("script");
    s.src = CFG.chatSrc; s.defer = true;
    s.setAttribute("data-widget-id", CFG.chatId);
    document.body.appendChild(s);
  }
  function whenIdle(fn, ms) {
    var run = function () { ("requestIdleCallback" in window) ? requestIdleCallback(fn, { timeout: 3000 }) : setTimeout(fn, 1); };
    if (document.readyState === "complete") setTimeout(run, ms); else addEventListener("load", function () { setTimeout(run, ms); });
  }
  whenIdle(loadChat, 2500);
  ["pointerdown", "keydown", "scroll"].forEach(function (ev) { addEventListener(ev, function once() { removeEventListener(ev, once); whenIdle(loadChat, 400); }, { passive: true }); });

  /* ---------- Prefill forms from ?location= ---------- */
  function prefill() {
    var m = (location.search + location.hash).match(/[?&]location=([a-z0-9-]+)/);
    var l = m && bySlug(m[1]);
    if (!l) return;
    $$('select[name="location"]').forEach(function (s) { s.value = l.name; });
  }

  /* ---------- Contact form → Supabase ---------- */
  document.addEventListener("submit", function (e) {
    var f = e.target, table = f.getAttribute("data-supabase");
    if (!table) return;
    e.preventDefault();
    var fd = new FormData(f);
    if (fd.get("company_website")) { location.href = CFG.thanksUrl; return; }
    var btn = f.querySelector('[type="submit"]');
    if (!CFG.supabaseUrl || !CFG.supabaseKey) { alert("This form isn't connected yet. Please call your location or email us."); return; }
    var row = {
      first_name: fd.get("first_name") || null, last_name: fd.get("last_name") || null,
      email: fd.get("email") || null, phone: fd.get("phone") || null,
      topic: fd.get("event_type") || null, location: fd.get("location") || null,
      message: fd.get("notes") || null, page: location.pathname
    };
    if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
    fetch(CFG.supabaseUrl.replace(/\/$/, "") + "/rest/v1/" + table, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: CFG.supabaseKey, Authorization: "Bearer " + CFG.supabaseKey, Prefer: "return=minimal" },
      body: JSON.stringify(row)
    }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      track("contact_submit", { topic: row.topic || "", location: row.location || "" });
      location.href = CFG.thanksUrl;
    }).catch(function () {
      if (btn) { btn.disabled = false; btn.textContent = "Try again"; }
      alert("Sorry, that didn't go through. Please try again, or call your location.");
    });
  });

  /* ---------- Init ---------- */
  prefill();
  addEventListener("hashchange", prefill);
  paintAll();
  personalize();
  updateQuick();
  setInterval(paintAll, 60000);
})();
