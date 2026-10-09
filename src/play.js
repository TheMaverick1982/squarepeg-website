/* Square Peg Playground — the wheel, the debate poll, the confession checklist,
   the Pizza Lab builder.

   This file loads ONLY on /play/ pages. site.js is on every page on the site
   and is kept lean for mobile; none of this belongs in it.

   No dependencies, no build step beyond the same terser pass site.js gets.     */
(function () {
  "use strict";

  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  function track(name, data) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(Object.assign({ event: name }, data || {}));
  }

  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  var reduced = false;
  try {
    reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {}

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* ================================================================ WHEEL */

  (function wheel() {
    var app = $("#wheel-app");
    var cfgEl = $("#wheel-cfg");
    if (!app || !cfgEl) return;

    var WHEELS;
    try { WHEELS = JSON.parse(cfgEl.textContent); } catch (e) { return; }
    if (!WHEELS || !WHEELS.length) return;

    var disc = $("#wheel-disc");
    var out = $("#wheel-out");
    var spinBtn = $("#wheel-spin");
    var orderBtn = $("#wheel-order");
    var qEl = $("#wheel-q");
    var promptEl = $("#wheel-prompt");

    var current = WHEELS[0];
    var angle = 0;          // cumulative rotation, so the disc never jumps back
    var spinning = false;

    // Alternating wedges in the brand reds and ink. Drawn as a conic gradient
    // rather than canvas: it scales to any size, costs nothing, and prints.
    var COLORS = ["#D50117", "#1B1614", "#D85F0A", "#2A2422", "#B00113", "#3A3230"];

    function paint() {
      var n = current.items.length;
      var slice = 360 / n;
      var stops = [];
      for (var i = 0; i < n; i++) {
        stops.push(COLORS[i % COLORS.length] + " " + (i * slice) + "deg " + ((i + 1) * slice) + "deg");
      }
      disc.style.background = "conic-gradient(" + stops.join(",") + ")";

      // Labels, each rotated to sit in the middle of its wedge.
      var html = "";
      for (var j = 0; j < n; j++) {
        var mid = j * slice + slice / 2;
        // A label rotated past the horizontal would read upside down, so wedges
        // in the lower half anchor to the bottom and flip. Nothing on the wheel
        // is ever inverted, whatever the slice count.
        var flip = mid > 90 && mid < 270;
        html += '<span class="wheel-lab' + (flip ? " is-flip" : "") +
                '" style="transform:rotate(' + mid + 'deg)">' +
                '<i>' + esc(current.items[j][0]) + "</i></span>";
      }
      disc.innerHTML = html;
      disc.setAttribute("aria-label", current.name + ": " + n + " options");
    }

    function show(idx) {
      var item = current.items[idx];
      out.innerHTML = '<span class="wheel-win-eyebrow">The universe has spoken</span>' +
                      "<b>" + esc(item[0]) + "</b>" +
                      "<span>" + esc(item[1]) + "</span>";
      out.classList.add("is-in");
      orderBtn.hidden = false;
      spinBtn.textContent = "Spin again";
      track("wheel_result", { wheel: current.slug, result: item[0] });
    }

    function spin() {
      if (spinning) return;
      var n = current.items.length;
      var idx = Math.floor(Math.random() * n);
      var slice = 360 / n;
      // Land the chosen wedge under the pin at the top, with a little jitter so
      // it never stops dead centre and looks mechanical.
      var jitter = (Math.random() - 0.5) * (slice * 0.6);
      var target = 360 - (idx * slice + slice / 2) + jitter;

      out.classList.remove("is-in");
      orderBtn.hidden = true;

      if (reduced) {
        // No spin for anyone who asked not to be spun at. Same result, instantly.
        angle = target;
        disc.style.transition = "none";
        disc.style.transform = "rotate(" + angle + "deg)";
        show(idx);
        return;
      }

      spinning = true;
      spinBtn.disabled = true;
      angle += 360 * (4 + Math.floor(Math.random() * 3)) + ((target - (angle % 360)) + 360) % 360;
      disc.style.transition = "transform 3.4s cubic-bezier(.15,.9,.2,1)";
      disc.style.transform = "rotate(" + angle + "deg)";

      window.setTimeout(function () {
        spinning = false;
        spinBtn.disabled = false;
        show(idx);
      }, 3500);
    }

    function pick(slug) {
      for (var i = 0; i < WHEELS.length; i++) {
        if (WHEELS[i].slug === slug) { current = WHEELS[i]; break; }
      }
      qEl.textContent = current.name;
      promptEl.textContent = current.prompt;
      out.innerHTML = "";
      out.classList.remove("is-in");
      orderBtn.hidden = true;
      spinBtn.textContent = "Spin the wheel";
      paint();
    }

    $$(".wheel-tab").forEach(function (t) {
      t.addEventListener("click", function () {
        $$(".wheel-tab").forEach(function (o) {
          o.classList.remove("is-on");
          o.setAttribute("aria-selected", "false");
        });
        t.classList.add("is-on");
        t.setAttribute("aria-selected", "true");
        pick(t.getAttribute("data-wheel"));
      });
    });

    spinBtn.addEventListener("click", spin);
    paint();
  })();

  /* ================================================================= POLL
     The debate pages. One question, two options, results that were already in
     the HTML when the page arrived — we only repaint them after a vote.       */

  (function poll() {
    var el = $("#poll");
    if (!el) return;

    var name = el.getAttribute("data-poll");
    var endpoint = el.getAttribute("data-endpoint");
    var voteBox = $("#poll-vote");
    var results = $("#poll-results");
    var said = $("#poll-said");
    var key = "sp_poll_" + name;

    function paint(totals) {
      // totals: [{option, region, votes}]
      var sum = 0, by = {};
      totals.forEach(function (r) {
        by[r.option] = (by[r.option] || 0) + (+r.votes || 0);
        sum += +r.votes || 0;
      });
      if (!sum) return;
      $$("li[data-option]", results).forEach(function (li) {
        var o = li.getAttribute("data-option");
        var pct = Math.round(((by[o] || 0) / sum) * 100);
        $(".bar i", li).style.width = pct + "%";
        $(".bar-pct", li).textContent = pct + "%";
      });
      if (said) {
        said.textContent = sum === 1 ? "One vote so far. Yours."
                                     : sum.toLocaleString() + " votes so far.";
      }
      results.hidden = false;
    }

    function reveal() {
      voteBox.classList.add("is-done");
      results.hidden = false;
    }

    if (store.get(key)) {
      // Already voted on this device. Show them the numbers, not the buttons.
      reveal();
      var prev = $(".poll-btn[data-option='" + store.get(key) + "']", voteBox);
      if (prev) prev.classList.add("is-mine");
    }

    $$(".poll-btn", el).forEach(function (b) {
      b.addEventListener("click", function () {
        if (store.get(key)) return;
        var option = b.getAttribute("data-option");
        store.set(key, option);
        b.classList.add("is-mine");
        reveal();
        track("poll_vote", { poll: name, option: option });
        if (!endpoint) return;
        fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ poll: name, option: option })
        }).then(function (r) { return r.ok ? r.json() : null; })
          .then(function (d) { if (d && d.totals) paint(d.totals); })
          .catch(function () { /* the baked-in numbers are still on screen */ });
      });
    });
  })();

  /* ========================================================== CONFESSIONS
     Same engine, several options at once, and a verdict at the end.           */

  (function confessions() {
    var form = $("#conf");
    if (!form) return;

    var name = form.getAttribute("data-poll");
    var endpoint = form.getAttribute("data-endpoint");
    var go = $("#conf-go");
    var verdict = $("#conf-verdict");
    var key = "sp_confessed";

    var LINES = [
      [0, "Spotless. Suspiciously spotless, frankly."],
      [1, "One. Everyone has one."],
      [3, "Reasonable. You are among friends."],
      [6, "That is a pattern, not a slip."],
      [9, "We&rsquo;re going to need a bigger booth."],
      [12, "Genuinely impressive. Come in, we&rsquo;ll pretend we don&rsquo;t know."]
    ];

    function verdictFor(n) {
      var line = LINES[0][1];
      for (var i = 0; i < LINES.length; i++) if (n >= LINES[i][0]) line = LINES[i][1];
      return "<b>" + n + (n === 1 ? " confession" : " confessions") + "</b><span>" + line + "</span>";
    }

    function paint(totals) {
      var voters = {}, max = 0;
      totals.forEach(function (r) {
        voters[r.option] = (voters[r.option] || 0) + (+r.votes || 0);
        if (voters[r.option] > max) max = voters[r.option];
      });
      // Denominator is the most-ticked confession: "x% of people who confessed".
      if (!max) return;
      $$("li[data-option]", form).forEach(function (li) {
        var o = li.getAttribute("data-option");
        var pct = Math.round(((voters[o] || 0) / max) * 100);
        var slot = $("[data-pct]", li);
        if (slot) slot.textContent = pct + "% have";
      });
    }

    go.addEventListener("click", function () {
      if (store.get(key)) return;
      var picked = $$("input[name=c]:checked", form).map(function (i) { return i.value; });
      store.set(key, "1");
      go.disabled = true;
      $$("input[name=c]", form).forEach(function (i) { i.disabled = true; });
      verdict.innerHTML = verdictFor(picked.length);
      verdict.hidden = false;
      track("confession_submit", { count: picked.length });
      if (!endpoint || !picked.length) return;
      fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ poll: name, options: picked })
      }).then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { if (d && d.totals) paint(d.totals); })
        .catch(function () {});
    });

    if (store.get(key)) {
      go.disabled = true;
      go.textContent = "Already confessed";
      $$("input[name=c]", form).forEach(function (i) { i.disabled = true; });
    }
  })();

  /* ============================================================ PIZZA LAB */

  (function lab() {
    var form = $("#lab");
    if (!form) return;

    var max = parseInt(form.getAttribute("data-max"), 10) || 4;
    var endpoint = form.getAttribute("data-endpoint");
    var countEl = $("#lab-count");
    var preview = $("#lab-preview");
    var go = $("#lab-go");
    var note = $("#lab-note");

    function chosen() {
      return $$("input[name=topping]:checked", form).map(function (i) { return i.value; });
    }

    function build() {
      var t = chosen();
      countEl.textContent = t.length + " of " + max;
      // Lock the rest once they hit the cap, rather than letting them pick and
      // then telling them off.
      $$("input[name=topping]", form).forEach(function (i) {
        i.disabled = !i.checked && t.length >= max;
        i.closest(".lab-chip").classList.toggle("is-off", i.disabled);
      });

      var sauce = $("input[name=sauce]:checked", form);
      var cheese = $("input[name=cheese]:checked", form);
      var finish = $("input[name=finish]:checked", form);
      var name = ($("#lab-name").value || "").trim();

      var parts = [];
      if (sauce && sauce.value.indexOf("No sauce") !== 0) parts.push(sauce.value.toLowerCase());
      if (cheese) parts.push(cheese.value.toLowerCase());
      t.forEach(function (x) { parts.push(x.toLowerCase()); });

      var line = parts.join(", ");
      if (finish && finish.value.indexOf("Nothing") !== 0) line += ", finished with " + finish.value.toLowerCase();

      preview.innerHTML = '<span class="wheel-win-eyebrow">Your pizza</span><b>' +
        esc(name || "Still needs a name") + "</b><span>" + esc(line) + "</span>";
    }

    form.addEventListener("change", build);
    form.addEventListener("input", build);

    go.addEventListener("click", function () {
      var name = ($("#lab-name").value || "").trim();
      if (!name) { note.textContent = "Give it a name first."; $("#lab-name").focus(); return; }
      if (!chosen().length) { note.textContent = "Pick at least one topping."; return; }
      if (!endpoint) { note.textContent = "Submissions aren't open yet."; return; }

      go.disabled = true;
      note.textContent = "Sending…";
      fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name,
          by: ($("#lab-by").value || "").trim(),
          sauce: ($("input[name=sauce]:checked", form) || {}).value || "",
          cheese: ($("input[name=cheese]:checked", form) || {}).value || "",
          toppings: chosen(),
          finish: ($("input[name=finish]:checked", form) || {}).value || ""
        })
      }).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        form.innerHTML = '<div class="lab-done"><b>Got it.</b><span>One of us will read it ' +
          "before it goes anywhere. If it goes up for a vote, that happens within a few days.</span></div>";
        track("lab_submit", {});
      }).catch(function () {
        go.disabled = false;
        note.textContent = "That didn't go through. Try again in a moment.";
      });
    });

    build();
  })();
})();
