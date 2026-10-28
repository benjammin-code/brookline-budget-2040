
(function () {
  var THEME_ACCENT = "var(--pine)";

  function fmtMoney(n, decimals) {
    decimals = decimals || 1;
    var abs = Math.abs(n);
    if (abs >= 1e6) return "$" + (n / 1e6).toFixed(decimals) + "M";
    if (abs >= 1e3) return "$" + (n / 1e3).toFixed(0) + "K";
    return "$" + n.toFixed(0);
  }
  function fmtMoneyFull(n) {
    return "$" + Math.round(n).toLocaleString("en-US");
  }
  function css(v) {
    return getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  }
  function svgEl(tag, attrs) {
    var el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }

  /* ---------------- SANKEY ---------------- */
  /* Debt exclusion is deliberately FIRST on both sides, in a single shared
     colour, so the two bands occupy the same top slice and read as the
     dollar-for-dollar pass-through they are. Same arrangement as the full
     five-fund chart above it (Ben, 2026-09-13). */
  var SANKEY_EXCL_COLOR = "--sankey-use-2";
  var sources = [
    { name: "Debt exclusion", value: 35379833, colorVar: SANKEY_EXCL_COLOR },
    { name: "Property Tax", value: 323924996, colorVar: "--sankey-src-1" },
    { name: "Local Receipts", value: 37633556, colorVar: "--sankey-src-2" },
    { name: "State Aid", value: 26693757, colorVar: "--sankey-src-3" },
    { name: "Free Cash", value: 18280805, colorVar: "--sankey-src-4" },
    { name: "Other Funds", value: 8755561, colorVar: "--sankey-src-5" }
  ];
  var uses = [
    { name: "Debt exclusion", value: 35379833, colorVar: SANKEY_EXCL_COLOR },
    { name: "Schools", value: 149801900, colorVar: "--sankey-use-1" },
    { name: "Departmental (Town)", value: 103486124, colorVar: "--sankey-use-3" },
    { name: "Employee Benefits", value: 99123428, colorVar: "--sankey-use-4" },
    { name: "Other Non-Departmental", value: 48831743, colorVar: "--sankey-use-5" },
    { name: "Other Debt Service", value: 14045480, colorVar: "--sankey-use-6" }
  ];
  var total = sources.reduce(function (a, s) { return a + s.value; }, 0);

  function drawSankey() {
    var svg = document.getElementById("sankey-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 500;
    var topPad = 34, botPad = 20;
    var usableH = H - topPad - botPad;
    var gap = 22;

    var colSrcX = 0, colSrcW = 250;
    var colPoolX = 420, colPoolW = 60;
    var colUseX = 660, colUseW = 200;

    function layout(items) {
      var y = topPad;
      var n = items.length;
      var totalGap = gap * (n - 1);
      items.forEach(function (it) {
        it.h = (it.value / total) * (usableH - totalGap);
        it.y0 = y;
        it.y1 = y + it.h;
        y = it.y1 + gap;
      });
    }
    layout(sources);
    layout(uses);

    // column headers
    svg.appendChild(svgEl("text", { x: colSrcX, y: 20, class: "sankey-col-head" })).textContent = "SOURCES";
    svg.appendChild(svgEl("text", { x: colUseX, y: 20, class: "sankey-col-head" })).textContent = "USES";
    var poolHead = svgEl("text", { x: colPoolX + colPoolW / 2, y: 20, class: "sankey-col-head", "text-anchor": "middle" });
    poolHead.textContent = "GENERAL FUND";
    svg.appendChild(poolHead);

    // pool bar
    svg.appendChild(svgEl("rect", {
      x: colPoolX, y: topPad, width: colPoolW, height: usableH,
      fill: css("--sankey-pool"), rx: 2
    }));

    function ribbon(x0, y0a, y0b, x1, y1a, y1b, color, opacity) {
      var mx = (x0 + x1) / 2;
      var d = "M" + x0 + "," + y0a +
        " C" + mx + "," + y0a + " " + mx + "," + y1a + " " + x1 + "," + y1a +
        " L" + x1 + "," + y1b +
        " C" + mx + "," + y1b + " " + mx + "," + y0b + " " + x0 + "," + y0b + " Z";
      return svgEl("path", { d: d, fill: color, opacity: opacity });
    }

    var tooltip = document.getElementById("sankey-tooltip");
    var wrap = document.getElementById("sankey-wrap");

    function showTip(evt, title, rows) {
      var html = '<div class="tt-title">' + title + '</div>';
      rows.forEach(function (r) {
        html += '<div class="tt-row"><span>' + r[0] + '</span><span>' + r[1] + '</span></div>';
      });
      tooltip.innerHTML = html;
      tooltip.style.opacity = 1;
      positionTip(evt);
    }
    function positionTip(evt) {
      var rect = wrap.getBoundingClientRect();
      var x = evt.clientX - rect.left + 14;
      var y = evt.clientY - rect.top + 14;
      tooltip.style.left = x + "px";
      tooltip.style.top = y + "px";
    }
    function hideTip() { tooltip.style.opacity = 0; }

    // source -> pool ribbons, stacked on pool's left edge in same order
    var poolInY = topPad;
    sources.forEach(function (s) {
      var h = (s.value / total) * usableH;
      var color = css(s.colorVar);
      var path = ribbon(colSrcX + colSrcW, s.y0, s.y1, colPoolX, poolInY, poolInY + h, color, 0.82);
      path.addEventListener("mousemove", function (e) {
        showTip(e, s.name, [["Amount", fmtMoneyFull(s.value)], ["Share of total", (s.value / total * 100).toFixed(1) + "%"]]);
      });
      path.addEventListener("mouseleave", hideTip);
      svg.appendChild(path);
      poolInY += h;

      // source node bar + label (two lines if there's room, one compact line if not)
      svg.appendChild(svgEl("rect", { x: colSrcX + colSrcW - 4, y: s.y0, width: 4, height: s.h, fill: color }));
      var cySrc = s.y0 + s.h / 2;
      if (s.h >= 30) {
        var lbl = svgEl("text", { x: colSrcX + colSrcW - 12, y: cySrc - 2, class: "sankey-label", "text-anchor": "end" });
        lbl.textContent = s.name;
        svg.appendChild(lbl);
        var pct = svgEl("text", { x: colSrcX + colSrcW - 12, y: cySrc + 13, class: "sankey-label pct", "text-anchor": "end" });
        pct.textContent = fmtMoney(s.value, 1) + " · " + (s.value / total * 100).toFixed(0) + "%";
        svg.appendChild(pct);
      } else {
        var one = svgEl("text", { x: colSrcX + colSrcW - 12, y: cySrc + 4, class: "sankey-label", "text-anchor": "end" });
        one.textContent = s.name + " — " + fmtMoney(s.value, 1);
        svg.appendChild(one);
      }
    });

    // pool -> use ribbons, stacked on pool's right edge
    var poolOutY = topPad;
    uses.forEach(function (u) {
      var h = (u.value / total) * usableH;
      var color = css(u.colorVar);
      var path = ribbon(colPoolX + colPoolW, poolOutY, poolOutY + h, colUseX, u.y0, u.y1, color, 0.82);
      path.addEventListener("mousemove", function (e) {
        showTip(e, u.name, [["Amount", fmtMoneyFull(u.value)], ["Share of total", (u.value / total * 100).toFixed(1) + "%"]]);
      });
      path.addEventListener("mouseleave", hideTip);
      svg.appendChild(path);
      poolOutY += h;

      svg.appendChild(svgEl("rect", { x: colUseX, y: u.y0, width: 4, height: u.h, fill: color }));
      var cyUse = u.y0 + u.h / 2;
      if (u.h >= 30) {
        var lbl = svgEl("text", { x: colUseX + 12, y: cyUse - 2, class: "sankey-label" });
        lbl.textContent = u.name;
        svg.appendChild(lbl);
        var pct = svgEl("text", { x: colUseX + 12, y: cyUse + 13, class: "sankey-label pct" });
        pct.textContent = fmtMoney(u.value, 1) + " · " + (u.value / total * 100).toFixed(0) + "%";
        svg.appendChild(pct);
      } else {
        var one = svgEl("text", { x: colUseX + 12, y: cyUse + 4, class: "sankey-label" });
        one.textContent = u.name + " — " + fmtMoney(u.value, 1);
        svg.appendChild(one);
      }
    });

    // total label under pool
    var tot = svgEl("text", {
      x: colPoolX + colPoolW / 2, y: H - 2, class: "sankey-label pct", "text-anchor": "middle"
    });
    tot.textContent = fmtMoney(total, 1) + " total";
    svg.appendChild(tot);

    // build table
    var tableWrap = document.getElementById("sankey-table");
    var html = '<table class="data-table"><thead><tr><th>Sources</th><th>Amount</th><th>Share</th><th>Uses</th><th>Amount</th><th>Share</th></tr></thead><tbody>';
    for (var i = 0; i < sources.length; i++) {
      var s = sources[i], u = uses[i];
      html += "<tr><td>" + s.name + "</td><td>" + fmtMoneyFull(s.value) + "</td><td>" + (s.value / total * 100).toFixed(1) + "%</td>";
      html += "<td>" + u.name + "</td><td>" + fmtMoneyFull(u.value) + "</td><td>" + (u.value / total * 100).toFixed(1) + "%</td></tr>";
    }
    html += "</tbody></table>";
    tableWrap.innerHTML = html;
  }

  /* ---------------- FUNDS SANKEY (3 columns: sources -> funds -> uses) ----
     FY2027: the General Fund as adopted by Town Meeting in May 2026
     (fy2027_adopted.py), the other funds from the FY2027 Financial Plan
     ("Fiscal Year 2027 Budget by Fund and Category"), CPA at its FY2024 actual.
     Two deliberate adjustments keep every dollar counted exactly once, both
     stated under the chart:
       1. The $4,019,498 the enterprise/revolving funds reimburse the
          General Fund is drawn as its own band from each fund to Employee
          Benefits (what it actually pays for). It is therefore removed from
          the General Fund's "Other Available Funds" source, where the
          budget books it, so it is not counted twice.
       2. The General Fund's own Recreation Department ($1,258,275) is split
          out of "Town Departments" and drawn into a shared "Recreation
          programs" node alongside the Recreation Revolving Fund's spending,
          which is what makes the tax subsidy of recreation visible.
     Debt exclusion carries its own colour end to end: it is property tax,
     but restricted by law to servicing specific voter-approved bonds.  */
  var FUND_META = {
    gf:   { name: "General Fund",            colorVar: "--sankey-src-1" },
    ws:   { name: "Water & Sewer",           colorVar: "--sankey-src-2" },
    rec:  { name: "Recreation Revolving",    colorVar: "--sankey-src-4" },
    golf: { name: "Golf Enterprise",         colorVar: "--sankey-src-3" },
    cpa:  { name: "Community Preservation",  colorVar: "--sankey-src-6" }
  };
  var DEBT_EXCL_COLOR = "--sankey-use-2";  // restricted pass-through

  var FUND_SOURCES = [
    // Debt exclusion is deliberately FIRST on both sides so it occupies the
    // top slice of the General Fund node coming in and going out, and so
    // renders as a straight horizontal band across all three columns -
    // reinforcing that it is property tax that never becomes general revenue.
    { fund: "gf",   name: "Property Tax (debt exclusion)", value: 35379833, restricted: true },
    { fund: "gf",   name: "Property Tax (operating levy)", value: 323924996 },
    { fund: "gf",   name: "Local Receipts", value: 37633556 },
    { fund: "gf",   name: "State Aid", value: 26693757 },
    { fund: "gf",   name: "Free Cash", value: 18280805 },
    { fund: "gf",   name: "Other Available Funds", value: 4736063 },
    { fund: "ws",   name: "Water & sewer charges", value: 35556714 },
    { fund: "rec",  name: "Recreation program fees", value: 5758564 },
    { fund: "golf", name: "Golf fees and other golf revenue", value: 3600250 },
    { fund: "cpa",  name: "1% surcharge + state match", value: 3473315 }
  ];

  var FUND_USES = [
    { fund: "gf",   use: "Debt exclusion debt service", value: 35379833, restricted: true },
    { fund: "gf",   use: "Schools", value: 149801900 },
    { fund: "gf",   use: "Town Departments", value: 102227849 },
    { fund: "gf",   use: "Employee Benefits", value: 95103930 },
    { fund: "gf",   use: "Other Non-Departmental", value: 48831743 },
    { fund: "gf",   use: "Other Debt Service", value: 14045480 },
    { fund: "gf",   use: "Recreation programs", value: 1258275 },
    { fund: "ws",   use: "Employee Benefits", value: 3000604, reimb: true },
    // The enterprise funds' own spending is shown as one bucket each: their
    // internal detail crowded the bottom of the chart without earning its
    // space. The composition is kept in the tooltip rather than lost.
    { fund: "ws",   use: "Water & Sewer operations", value: 32556110,
      note: "MWRA assessment $23.5M &middot; operations $5.3M &middot; debt service $2.9M &middot; capital $898K" },
    { fund: "rec",  use: "Employee Benefits", value: 709574, reimb: true },
    { fund: "rec",  use: "Recreation programs", value: 5048990 },
    { fund: "golf", use: "Employee Benefits", value: 309320, reimb: true },
    { fund: "golf", use: "Golf operations", value: 3290930,
      note: "operations $2.3M &middot; capital $756K &middot; debt service $242K" },
    { fund: "cpa",  use: "CPA projects", value: 3473315 }
  ];

  // Right-column order: General Fund categories first, then the shared
  // Recreation node, then each enterprise fund's own uses.
  var USE_ORDER = [
    "Debt exclusion debt service",
    "Schools", "Town Departments", "Employee Benefits", "Other Non-Departmental",
    "Other Debt Service", "Recreation programs",
    "Water & Sewer operations", "Golf operations", "CPA projects"
  ];
  var FUND_ORDER = ["gf", "ws", "rec", "golf", "cpa"];

  function drawFundsSankey() {
    var svg = document.getElementById("funds-sankey-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 860;
    var topPad = 30, botPad = 14;
    var usableH = H - topPad - botPad;

    var SRC_X = 236, FUND_X = 424, USE_X = 622;
    var SRC_W = 11, FUND_W = 15, USE_W = 11;

    var total = FUND_SOURCES.reduce(function (a, s) { return a + s.value; }, 0);
    var NODE_GAP = 5, FUND_GAP = 16;
    var nSrcGaps = FUND_SOURCES.length - 1, nUseGaps = USE_ORDER.length - 1;
    var maxGaps = Math.max(nSrcGaps * NODE_GAP, nUseGaps * NODE_GAP,
                           (FUND_ORDER.length - 1) * FUND_GAP);
    var scale = (usableH - maxGaps) / total;

    function layout(items, x, w, gap) {
      var y = topPad, out = [];
      items.forEach(function (it) {
        var h = Math.max(3.2, it.value * scale);
        out.push(Object.assign({}, it, { x: x, w: w, y0: y, h: h }));
        y += h + gap;
      });
      return out;
    }

    // --- middle column: funds ---
    var fundTotals = {};
    FUND_SOURCES.forEach(function (s) { fundTotals[s.fund] = (fundTotals[s.fund] || 0) + s.value; });
    var fundNodes = layout(FUND_ORDER.map(function (f) {
      return { id: f, name: FUND_META[f].name, value: fundTotals[f], colorVar: FUND_META[f].colorVar };
    }), FUND_X, FUND_W, FUND_GAP);
    var fundById = {};
    fundNodes.forEach(function (n) { fundById[n.id] = n; });

    // --- left column: sources, grouped in fund order ---
    var orderedSources = [];
    FUND_ORDER.forEach(function (f) {
      FUND_SOURCES.forEach(function (s) { if (s.fund === f) orderedSources.push(s); });
    });
    var srcNodes = layout(orderedSources, SRC_X, SRC_W, NODE_GAP);

    // --- right column: uses, aggregated by name ---
    var useTotals = {};
    FUND_USES.forEach(function (u) { useTotals[u.use] = (useTotals[u.use] || 0) + u.value; });
    var useNodes = layout(USE_ORDER.map(function (name) {
      return { name: name, value: useTotals[name] };
    }), USE_X, USE_W, NODE_GAP);
    var useByName = {};
    useNodes.forEach(function (n) { useByName[n.name] = n; });

    function ribbon(x0, y0, x1, y1, h0, h1) {
      var cx = (x0 + x1) / 2;
      return "M" + x0 + "," + y0 +
             "C" + cx + "," + y0 + " " + cx + "," + y1 + " " + x1 + "," + y1 +
             "L" + x1 + "," + (y1 + h1) +
             "C" + cx + "," + (y1 + h1) + " " + cx + "," + (y0 + h0) + " " + x0 + "," + (y0 + h0) + "Z";
    }

    var tooltip = document.getElementById("funds-sankey-tooltip");
    var wrap = document.getElementById("funds-sankey-wrap");
    function bindTip(el, html) {
      el.addEventListener("mousemove", function (e) {
        tooltip.innerHTML = html;
        tooltip.style.opacity = 1;
        var r = wrap.getBoundingClientRect();
        tooltip.style.left = (e.clientX - r.left + 14) + "px";
        tooltip.style.top = (e.clientY - r.top - 10) + "px";
      });
      el.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    }

    // --- links: sources -> funds ---
    var fundInOff = {};
    srcNodes.forEach(function (s) {
      var f = fundById[s.fund];
      var off = fundInOff[s.fund] || 0;
      var col = css(s.restricted ? DEBT_EXCL_COLOR : FUND_META[s.fund].colorVar);
      var p = svgEl("path", {
        d: ribbon(s.x + s.w, s.y0, f.x, f.y0 + off, s.h, s.h),
        fill: col, opacity: s.restricted ? 0.62 : 0.34
      });
      svg.appendChild(p);
      bindTip(p, '<div class="tt-title">' + s.name + '</div>' +
        '<div class="tt-row"><span>into ' + FUND_META[s.fund].name + '</span><span>' + fmtMoney(s.value) + '</span></div>' +
        (s.restricted ? '<div class="tt-row"><span>Restricted to bond repayment</span><span></span></div>' : ''));
      fundInOff[s.fund] = off + s.h;
    });

    // --- links: funds -> uses ---
    var fundOutOff = {}, useInOff = {};
    FUND_ORDER.forEach(function (fid) {
      USE_ORDER.forEach(function (uname) {
        FUND_USES.forEach(function (u) {
          if (u.fund !== fid || u.use !== uname) return;
          var f = fundById[fid], un = useByName[uname];
          var o1 = fundOutOff[fid] || 0, o2 = useInOff[uname] || 0;
          var h = Math.max(1.2, u.value * scale);
          var col = css(u.restricted ? DEBT_EXCL_COLOR : FUND_META[fid].colorVar);
          var p = svgEl("path", {
            d: ribbon(f.x + f.w, f.y0 + o1, un.x, un.y0 + o2, h, h),
            fill: col, opacity: u.restricted ? 0.62 : (u.reimb ? 0.6 : 0.34)
          });
          if (u.reimb) p.setAttribute("stroke", col), p.setAttribute("stroke-width", "0.6");
          svg.appendChild(p);
          bindTip(p, '<div class="tt-title">' + FUND_META[fid].name + " → " + uname + '</div>' +
            '<div class="tt-row"><span>' + (u.reimb ? "Reimburses the General Fund for fringe benefits" : "Amount") +
            '</span><span>' + fmtMoney(u.value) + '</span></div>' +
            (u.restricted ? '<div class="tt-row"><span>Legally restricted to this debt</span><span></span></div>' : '') +
            (u.note ? '<div class="tt-row"><span style="opacity:.75">' + u.note + '</span></div>' : ''));
          fundOutOff[fid] = o1 + h;
          useInOff[uname] = o2 + h;
        });
      });
    });

    // --- nodes ---
    // The General Fund is ~90% of the total, so on a true linear scale the
    // other four funds' nodes are only a few pixels tall and their labels
    // collide into an unreadable pile. Node geometry stays honest (linear,
    // with a 3.2px floor so nothing vanishes); the LABELS get pushed apart
    // and connected back to their node with a leader line where they moved.
    function placeLabels(nodes, minGap) {
      var items = nodes.map(function (n, i) {
        return { i: i, ideal: n.y0 + n.h / 2, y: n.y0 + n.h / 2 };
      }).sort(function (a, b) { return a.ideal - b.ideal; });
      for (var pass = 0; pass < 40; pass++) {
        var moved = false;
        for (var k = 1; k < items.length; k++) {
          var d = items[k].y - items[k - 1].y;
          if (d < minGap) {
            var push = (minGap - d) / 2;
            items[k - 1].y -= push; items[k].y += push; moved = true;
          }
        }
        if (items[0].y < 20) { var sh = 20 - items[0].y; items.forEach(function (it) { it.y += sh; }); moved = true; }
        var last = items[items.length - 1];
        if (last.y > H - 8) { var sh2 = last.y - (H - 8); items.forEach(function (it) { it.y -= sh2; }); moved = true; }
        if (!moved) break;
      }
      var out = [];
      items.forEach(function (it) { out[it.i] = it.y; });
      return out;
    }

    function drawColumn(nodes, colorOf, labelX, anchor, leaderFromX, leaderToX) {
      var ys = placeLabels(nodes, 23);
      nodes.forEach(function (n, i) {
        svg.appendChild(svgEl("rect", { x: n.x, y: n.y0, width: n.w, height: n.h,
                                        fill: css(colorOf(n)), rx: 2 }));
        var cy = n.y0 + n.h / 2, ly = ys[i];
        if (Math.abs(ly - cy) > 2.5) {
          svg.appendChild(svgEl("path", {
            d: "M" + leaderFromX + "," + cy + "L" + leaderToX + "," + ly,
            stroke: css("--rule"), "stroke-width": 0.7, fill: "none", opacity: 0.85
          }));
        }
        var t = svgEl("text", { x: labelX, y: ly + 3.5, class: "sankey-label",
                                "text-anchor": anchor, "font-size": "11.5" });
        t.textContent = n.name;
        svg.appendChild(t);
        var vt = svgEl("text", { x: labelX, y: ly + 14, class: "sankey-label pct",
                                 "text-anchor": anchor, "font-size": "10" });
        vt.textContent = fmtMoney(n.value);
        svg.appendChild(vt);
      });
    }

    drawColumn(srcNodes, function (n) {
      return n.restricted ? DEBT_EXCL_COLOR : FUND_META[n.fund].colorVar;
    }, SRC_X - 9, "end", SRC_X, SRC_X - 6);

    drawColumn(useNodes, function (n) {
      if (n.name === "Debt exclusion debt service") return DEBT_EXCL_COLOR;
      var owner = FUND_USES.filter(function (u) { return u.use === n.name; })
                           .sort(function (a, b) { return b.value - a.value; })[0].fund;
      return FUND_META[owner].colorVar;
    }, USE_X + USE_W + 9, "start", USE_X + USE_W, USE_X + USE_W + 6);

    // Fund labels sit vertically centred on their node (placeLabels' ideal
    // position is already the node centre, so tall nodes don't move at all);
    // only the small funds get pushed apart, and those get a leader line.
    var fundLabelYs = placeLabels(fundNodes, 17);
    fundNodes.forEach(function (n, i) {
      svg.appendChild(svgEl("rect", { x: n.x, y: n.y0, width: n.w, height: n.h,
                                      fill: css(n.colorVar), rx: 2 }));
      var cy = n.y0 + n.h / 2;
      if (Math.abs(fundLabelYs[i] - cy) > 2.5) {
        svg.appendChild(svgEl("path", {
          d: "M" + (n.x + n.w / 2) + "," + cy + "L" + (n.x + n.w / 2) + "," + fundLabelYs[i],
          stroke: css("--rule"), "stroke-width": 0.7, fill: "none", opacity: 0.7
        }));
      }
      var ly = fundLabelYs[i] + 3.5;
      var t = svgEl("text", { x: n.x + n.w / 2, y: ly, class: "sankey-label",
                              "text-anchor": "middle", "font-size": "11.5" });
      // Fund labels sit over the ribbons; a halo in the card colour keeps
      // them readable without hiding the flows underneath.
      t.setAttribute("stroke", css("--paper-card"));
      t.setAttribute("stroke-width", "3.5");
      t.setAttribute("paint-order", "stroke");
      t.setAttribute("stroke-linejoin", "round");
      t.textContent = n.name + "  " + fmtMoney(n.value);
      svg.appendChild(t);
    });

    // --- column headers ---
    [[SRC_X + SRC_W / 2, "WHERE IT COMES FROM"], [FUND_X + FUND_W / 2, "WHICH FUND"],
     [USE_X + USE_W + 9, "WHAT IT PAYS FOR"]].forEach(function (c, i) {
      var t = svgEl("text", { x: c[0], y: 12, class: "sankey-col-head",
                              "text-anchor": i === 0 ? "end" : (i === 2 ? "start" : "middle") });
      t.textContent = c[1];
      svg.appendChild(t);
    });
  }

  /* Expense composition, FY2005 vs FY2025, from
     output/brookline_historical_financials_fy05_25.csv (DLS Schedule A
     functional categories). CAGRs are computed over the full 20 years.

     Debt service is split into the part inside the levy limit and the part
     funded by voter-approved debt exclusions (the recap `debt_exclusions`
     line), because the combined figure grows at 5.17%/yr and reads as a
     fast-growing operating cost when it is neither: the excluded part is
     matched dollar-for-dollar by its own revenue, and within-levy debt
     service has grown at 1.06%/yr (Ben, 2026-09-13). */
  var expenseCategories = [
    { name: "Education", v05: 60438282, v25: 146446110, cagr: 0.045245, colorVar: "--sankey-use-1" },
    { name: "Benefits & Fixed Costs", v05: 30467373, v25: 89361296, cagr: 0.055275, colorVar: "--sankey-use-2" },
    { name: "Public Safety", v05: 25373371, v25: 43497816, cagr: 0.027317, colorVar: "--sankey-use-3" },
    { name: "Debt service (in levy)", v05: 11571032, v25: 14273918, cagr: 0.010552, colorVar: "--sankey-use-4" },
    { name: "Debt service (excluded)", v05: 1676384, v25: 22012492, cagr: 0.137404, colorVar: "--sankey-src-6" },
    { name: "Public Works", v05: 13742331, v25: 15080716, cagr: 0.004658, colorVar: "--sankey-use-5" },
    { name: "General Government", v05: 12211085, v25: 14585216, cagr: 0.008923, colorVar: "--sankey-use-6" },
    { name: "Culture & Recreation", v05: 6481806, v25: 8665288, cagr: 0.014622, colorVar: "--sankey-src-3" },
    { name: "Intergov. Assessments", v05: 5352984, v25: 7959725, cagr: 0.020035, colorVar: "--sankey-src-4" },
    { name: "Human Services", v05: 1652626, v25: 2793578, cagr: 0.026595, colorVar: "--sankey-src-5" }
  ];

  function drawExpenseGrowthChart() {
    var svg = document.getElementById("expense-growth-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 1060, H = 620;
    var topPad = 40, botPad = 30;
    var usableH = H - topPad - botPad;
    var gap = 11;
    var totalGap = gap * (expenseCategories.length - 1);
    var total25 = expenseCategories.reduce(function (a, c) { return a + c.v25; }, 0);
    var scale = (usableH - totalGap) / total25;

    var colAx = 250, colBx = 700;

    var yA = topPad, yB = topPad;
    expenseCategories.forEach(function (c) {
      c.h05 = c.v05 * scale;
      c.h25 = c.v25 * scale;
      c.yA0 = yA; c.yA1 = yA + c.h05; yA = c.yA1 + gap;
      c.yB0 = yB; c.yB1 = yB + c.h25; yB = c.yB1 + gap;
    });

    svg.appendChild(svgEl("text", { x: colAx, y: 20, class: "sankey-col-head", "text-anchor": "middle" })).textContent = "FY2005 · $169.0M";
    svg.appendChild(svgEl("text", { x: colBx, y: 20, class: "sankey-col-head", "text-anchor": "middle" })).textContent = "FY2025 · $364.7M";

    function ribbon(x0, y0a, y0b, x1, y1a, y1b, color, opacity) {
      var mx = (x0 + x1) / 2;
      var d = "M" + x0 + "," + y0a +
        " C" + mx + "," + y0a + " " + mx + "," + y1a + " " + x1 + "," + y1a +
        " L" + x1 + "," + y1b +
        " C" + mx + "," + y1b + " " + mx + "," + y0b + " " + x0 + "," + y0b + " Z";
      return svgEl("path", { d: d, fill: color, opacity: opacity });
    }

    var tooltip = document.getElementById("expense-growth-tooltip");
    var wrap = document.getElementById("expense-growth-wrap");
    function showTip(evt, c) {
      var html = '<div class="tt-title">' + c.name + '</div>' +
        '<div class="tt-row"><span>FY2005</span><span>' + fmtMoneyFull(c.v05) + '</span></div>' +
        '<div class="tt-row"><span>FY2025</span><span>' + fmtMoneyFull(c.v25) + '</span></div>' +
        '<div class="tt-row"><span>CAGR</span><span>' + (c.cagr * 100).toFixed(2) + '%/yr</span></div>';
      tooltip.innerHTML = html;
      tooltip.style.opacity = 1;
      var rect = wrap.getBoundingClientRect();
      tooltip.style.left = (evt.clientX - rect.left + 14) + "px";
      tooltip.style.top = (evt.clientY - rect.top + 14) + "px";
    }
    function hideTip() { tooltip.style.opacity = 0; }

    expenseCategories.forEach(function (c) {
      var color = css(c.colorVar);
      var path = ribbon(colAx + 22, c.yA0, c.yA1, colBx - 22, c.yB0, c.yB1, color, 0.82);
      path.addEventListener("mousemove", function (e) { showTip(e, c); });
      path.addEventListener("mouseleave", hideTip);
      svg.appendChild(path);

      svg.appendChild(svgEl("rect", { x: colAx - 22, y: c.yA0, width: 22, height: Math.max(c.h05, 1), fill: color }));
      svg.appendChild(svgEl("rect", { x: colBx, y: c.yB0, width: 22, height: Math.max(c.h25, 1), fill: color }));

      // left (FY2005) label
      var cyA = c.yA0 + c.h05 / 2;
      if (c.h05 >= 26) {
        var lblA = svgEl("text", { x: colAx - 28, y: cyA - 3, class: "sankey-label", "text-anchor": "end" });
        lblA.textContent = c.name;
        svg.appendChild(lblA);
        var pctA = svgEl("text", { x: colAx - 28, y: cyA + 11, class: "sankey-label pct", "text-anchor": "end" });
        pctA.textContent = fmtMoney(c.v05, 1);
        svg.appendChild(pctA);
      } else {
        var oneA = svgEl("text", { x: colAx - 28, y: cyA + 4, class: "sankey-label pct", "text-anchor": "end" });
        oneA.textContent = c.name + " — " + fmtMoney(c.v05, 1);
        svg.appendChild(oneA);
      }

      // right (FY2025) label, with CAGR
      var cyB = c.yB0 + c.h25 / 2;
      if (c.h25 >= 26) {
        var lblB = svgEl("text", { x: colBx + 28, y: cyB - 3, class: "sankey-label" });
        lblB.textContent = c.name;
        svg.appendChild(lblB);
        var pctB = svgEl("text", { x: colBx + 28, y: cyB + 11, class: "sankey-label pct" });
        pctB.textContent = fmtMoney(c.v25, 1) + "  ·  " + (c.cagr >= 0 ? "+" : "") + (c.cagr * 100).toFixed(2) + "%/yr";
        svg.appendChild(pctB);
      } else {
        var oneB = svgEl("text", { x: colBx + 28, y: cyB + 4, class: "sankey-label pct" });
        oneB.textContent = c.name + " — " + fmtMoney(c.v25, 1) + " (" + (c.cagr >= 0 ? "+" : "") + (c.cagr * 100).toFixed(2) + "%/yr)";
        svg.appendChild(oneB);
      }
    });

    var tableWrap = document.getElementById("expense-growth-table");
    var html = '<table class="data-table"><thead><tr><th>Category</th><th>FY2005</th><th>FY2025</th><th>CAGR</th></tr></thead><tbody>';
    expenseCategories.forEach(function (c) {
      html += "<tr><td>" + c.name + "</td><td>" + fmtMoneyFull(c.v05) + "</td><td>" + fmtMoneyFull(c.v25) + "</td><td>" + (c.cagr * 100).toFixed(2) + "%</td></tr>";
    });
    html += "</tbody></table>";
    tableWrap.innerHTML = html;
  }

  /* ---------------- LINE CHART ---------------- */
  var lineData = [{"fy": 2005, "total_expenditures_raw": 168967274.0, "total_expenditures_idx": 100.0, "benefits_raw": 30467373.0, "benefits_idx": 100.0, "education_raw": 60438282.0, "education_idx": 100.0, "cap_only_25pct_raw": 118186809.0, "cap_only_25pct_idx": 100.0, "levy_limit_allowed_raw": 118186809.0, "levy_limit_allowed_idx": 100.0, "total_revenue_raw": 167934717.0, "total_revenue_idx": 100.0, "no_override_raw": 118186809, "no_override_idx": 100.0}, {"fy": 2006, "total_expenditures_raw": 170248023.0, "total_expenditures_idx": 100.8, "benefits_raw": 29290151.0, "benefits_idx": 96.1, "education_raw": 62851151.0, "education_idx": 104.0, "cap_only_25pct_raw": 121141479.225, "cap_only_25pct_idx": 102.5, "levy_limit_allowed_raw": 123376018.0, "levy_limit_allowed_idx": 104.4, "total_revenue_raw": 168890619.0, "total_revenue_idx": 100.6, "no_override_raw": 123374424, "no_override_idx": 104.4}, {"fy": 2007, "total_expenditures_raw": 178526146.0, "total_expenditures_idx": 105.7, "benefits_raw": 32545112.0, "benefits_idx": 106.8, "education_raw": 65126712.0, "education_idx": 107.8, "cap_only_25pct_raw": 124170016.20562498, "cap_only_25pct_idx": 105.1, "levy_limit_allowed_raw": 128463615.0, "levy_limit_allowed_idx": 108.7, "total_revenue_raw": 178383652.0, "total_revenue_idx": 106.2, "no_override_raw": 128448468, "no_override_idx": 108.7}, {"fy": 2008, "total_expenditures_raw": 186716936.0, "total_expenditures_idx": 110.5, "benefits_raw": 34761771.0, "benefits_idx": 114.1, "education_raw": 68709239.0, "education_idx": 113.7, "cap_only_25pct_raw": 127274266.61076559, "cap_only_25pct_idx": 107.7, "levy_limit_allowed_raw": 134259886.0, "levy_limit_allowed_idx": 113.6, "total_revenue_raw": 185803513.0, "total_revenue_idx": 110.6, "no_override_raw": 134244360, "no_override_idx": 113.6}, {"fy": 2009, "total_expenditures_raw": 190655927.0, "total_expenditures_idx": 112.8, "benefits_raw": 35997394.0, "benefits_idx": 118.2, "education_raw": 73794431.0, "education_idx": 122.1, "cap_only_25pct_raw": 130456123.27603471, "cap_only_25pct_idx": 110.4, "levy_limit_allowed_raw": 145644644.0, "levy_limit_allowed_idx": 123.2, "total_revenue_raw": 192482479.0, "total_revenue_idx": 114.6, "no_override_raw": 139428730, "no_override_idx": 118.0}, {"fy": 2010, "total_expenditures_raw": 186354784.0, "total_expenditures_idx": 110.3, "benefits_raw": 39478782.0, "benefits_idx": 129.6, "education_raw": 74506548.0, "education_idx": 123.3, "cap_only_25pct_raw": 133717526.35793556, "cap_only_25pct_idx": 113.1, "levy_limit_allowed_raw": 151047972.0, "levy_limit_allowed_idx": 127.8, "total_revenue_raw": 195166931.0, "total_revenue_idx": 116.2, "no_override_raw": 144676660, "no_override_idx": 122.4}, {"fy": 2011, "total_expenditures_raw": 187248205.0, "total_expenditures_idx": 110.8, "benefits_raw": 37512887.0, "benefits_idx": 123.1, "education_raw": 77435614.0, "education_idx": 128.1, "cap_only_25pct_raw": 137060464.51688394, "cap_only_25pct_idx": 116.0, "levy_limit_allowed_raw": 156653255.0, "levy_limit_allowed_idx": 132.5, "total_revenue_raw": 197401346.0, "total_revenue_idx": 117.5, "no_override_raw": 150122660, "no_override_idx": 127.0}, {"fy": 2012, "total_expenditures_raw": 212923646.0, "total_expenditures_idx": 126.0, "benefits_raw": 54074007.0, "benefits_idx": 177.5, "education_raw": 80636512.0, "education_idx": 133.4, "cap_only_25pct_raw": 140486976.129806, "cap_only_25pct_idx": 118.9, "levy_limit_allowed_raw": 162553810.0, "levy_limit_allowed_idx": 137.5, "total_revenue_raw": 212032653.0, "total_revenue_idx": 126.3, "no_override_raw": 155859951, "no_override_idx": 131.9}, {"fy": 2013, "total_expenditures_raw": 211111637.0, "total_expenditures_idx": 124.9, "benefits_raw": 45542506.0, "benefits_idx": 149.5, "education_raw": 83991890.0, "education_idx": 139.0, "cap_only_25pct_raw": 143999150.53305116, "cap_only_25pct_idx": 121.8, "levy_limit_allowed_raw": 168537756.0, "levy_limit_allowed_idx": 142.6, "total_revenue_raw": 225013338.0, "total_revenue_idx": 134.0, "no_override_raw": 161676551, "no_override_idx": 136.8}, {"fy": 2014, "total_expenditures_raw": 213383728.0, "total_expenditures_idx": 126.3, "benefits_raw": 50186015.0, "benefits_idx": 164.7, "education_raw": 87479926.0, "education_idx": 144.7, "cap_only_25pct_raw": 147599129.29637742, "cap_only_25pct_idx": 124.9, "levy_limit_allowed_raw": 174686609.0, "levy_limit_allowed_idx": 147.8, "total_revenue_raw": 223722368.0, "total_revenue_idx": 133.2, "no_override_raw": 167653872, "no_override_idx": 141.9}, {"fy": 2015, "total_expenditures_raw": 221588977.0, "total_expenditures_idx": 131.1, "benefits_raw": 50885262.0, "benefits_idx": 167.0, "education_raw": 91894719.0, "education_idx": 152.0, "cap_only_25pct_raw": 151289107.52878684, "cap_only_25pct_idx": 128.0, "levy_limit_allowed_raw": 181154340.0, "levy_limit_allowed_idx": 153.3, "total_revenue_raw": 231276828.0, "total_revenue_idx": 137.7, "no_override_raw": 173945785, "no_override_idx": 147.2}, {"fy": 2016, "total_expenditures_raw": 233880347.0, "total_expenditures_idx": 138.4, "benefits_raw": 54609787.0, "benefits_idx": 179.2, "education_raw": 101064924.0, "education_idx": 167.2, "cap_only_25pct_raw": 155071335.2170065, "cap_only_25pct_idx": 131.2, "levy_limit_allowed_raw": 195438924.0, "levy_limit_allowed_idx": 165.4, "total_revenue_raw": 249427185.0, "total_revenue_idx": 148.5, "no_override_raw": 180385156, "no_override_idx": 152.6}, {"fy": 2017, "total_expenditures_raw": 245480837.0, "total_expenditures_idx": 145.3, "benefits_raw": 56010566.0, "benefits_idx": 183.8, "education_raw": 106968328.0, "education_idx": 177.0, "cap_only_25pct_raw": 158948118.59743166, "cap_only_25pct_idx": 134.5, "levy_limit_allowed_raw": 203036517.0, "levy_limit_allowed_idx": 171.8, "total_revenue_raw": 259094788.0, "total_revenue_idx": 154.3, "no_override_raw": 187606405, "no_override_idx": 158.7}, {"fy": 2018, "total_expenditures_raw": 257211170.0, "total_expenditures_idx": 152.2, "benefits_raw": 60824387.0, "benefits_idx": 199.6, "education_raw": 110623908.0, "education_idx": 183.0, "cap_only_25pct_raw": 162921821.56236744, "cap_only_25pct_idx": 137.9, "levy_limit_allowed_raw": 210376447.0, "levy_limit_allowed_idx": 178.0, "total_revenue_raw": 269899635.0, "total_revenue_idx": 160.7, "no_override_raw": 194560582, "no_override_idx": 164.6}, {"fy": 2019, "total_expenditures_raw": 270294659.0, "total_expenditures_idx": 160.0, "benefits_raw": 61594549.0, "benefits_idx": 202.2, "education_raw": 116389275.0, "education_idx": 192.6, "cap_only_25pct_raw": 166994867.1014266, "cap_only_25pct_idx": 141.3, "levy_limit_allowed_raw": 224812701.0, "levy_limit_allowed_idx": 190.2, "total_revenue_raw": 285287238.0, "total_revenue_idx": 169.9, "no_override_raw": 202025924, "no_override_idx": 170.9}, {"fy": 2020, "total_expenditures_raw": 284450665.0, "total_expenditures_idx": 168.3, "benefits_raw": 65533832.0, "benefits_idx": 215.1, "education_raw": 123764357.0, "education_idx": 204.8, "cap_only_25pct_raw": 171169738.77896225, "cap_only_25pct_idx": 144.8, "levy_limit_allowed_raw": 233198737.0, "levy_limit_allowed_idx": 197.3, "total_revenue_raw": 297528480.0, "total_revenue_idx": 177.2, "no_override_raw": 209842290, "no_override_idx": 177.6}, {"fy": 2021, "total_expenditures_raw": 297759258.0, "total_expenditures_idx": 176.2, "benefits_raw": 68065399.0, "benefits_idx": 223.4, "education_raw": 126667840.0, "education_idx": 209.6, "cap_only_25pct_raw": 175448982.2484363, "cap_only_25pct_idx": 148.5, "levy_limit_allowed_raw": 242349097.0, "levy_limit_allowed_idx": 205.1, "total_revenue_raw": 310021983.0, "total_revenue_idx": 184.6, "no_override_raw": 218408740, "no_override_idx": 184.8}, {"fy": 2022, "total_expenditures_raw": 315366130.0, "total_expenditures_idx": 186.6, "benefits_raw": 72160184.0, "benefits_idx": 236.8, "education_raw": 128842776.0, "education_idx": 213.2, "cap_only_25pct_raw": 179835206.8046472, "cap_only_25pct_idx": 152.2, "levy_limit_allowed_raw": 251866661.0, "levy_limit_allowed_idx": 213.1, "total_revenue_raw": 339419364.0, "total_revenue_idx": 202.1, "no_override_raw": 227327795, "no_override_idx": 192.3}, {"fy": 2023, "total_expenditures_raw": 325266407.0, "total_expenditures_idx": 192.5, "benefits_raw": 77360296.0, "benefits_idx": 253.9, "education_raw": 130884869.0, "education_idx": 216.6, "cap_only_25pct_raw": 184331086.97476336, "cap_only_25pct_idx": 156.0, "levy_limit_allowed_raw": 260823641.0, "levy_limit_allowed_idx": 220.7, "total_revenue_raw": 350331838.0, "total_revenue_idx": 208.6, "no_override_raw": 235671303, "no_override_idx": 199.4}, {"fy": 2024, "total_expenditures_raw": 343426310.0, "total_expenditures_idx": 203.3, "benefits_raw": 80309607.0, "benefits_idx": 263.6, "education_raw": 140247931.0, "education_idx": 232.1, "cap_only_25pct_raw": 188939364.14913243, "cap_only_25pct_idx": 159.9, "levy_limit_allowed_raw": 282862062.0, "levy_limit_allowed_idx": 239.3, "total_revenue_raw": 367822295.0, "total_revenue_idx": 219.0, "no_override_raw": 245097549, "no_override_idx": 207.4}, {"fy": 2025, "total_expenditures_raw": 364676155.0, "total_expenditures_idx": 215.8, "benefits_raw": 89361296.0, "benefits_idx": 293.3, "education_raw": 146446110.0, "education_idx": 242.3, "cap_only_25pct_raw": 193662848.25286072, "cap_only_25pct_idx": 163.9, "levy_limit_allowed_raw": 293111747.0, "levy_limit_allowed_idx": 248.0, "total_revenue_raw": 389982477.0, "total_revenue_idx": 232.2, "no_override_raw": 254403120, "no_override_idx": 215.3}];
  // Ordered to match each line's FY2025 endpoint position, top to bottom -
  // legend order mirrors chart order so there's no back-and-forth (Ben, 2026-09-01).
  var series = [
    { key: "benefits", label: "Employee benefits", colorVar: "--line-benefits", dash: null, width: 2 },
    { key: "levy_limit_allowed", label: "Levy limit, actually allowed (real new growth + overrides; excludes debt exclusion)", colorVar: "--line-levy-actual", dash: "9,3", width: 1.75 },
    { key: "education", label: "Education", colorVar: "--line-education", dash: null, width: 2 },
    { key: "total_revenue", label: "Total General Fund revenue (all sources, incl. debt exclusion)", colorVar: "--line-levy", dash: null, width: 3 },
    { key: "total_expenditures", label: "Total General Fund expenses (incl. debt service)", colorVar: "--line-total", dash: null, width: 3 },
    { key: "no_override", label: "Levy limit, 2.5% + new growth only, no override (excludes debt exclusion)", colorVar: "--line-no-override", dash: "2,2", width: 1.75 },
    { key: "cap_only_25pct", label: "Levy limit if capped at 2.5%/yr only (no new growth, no override; excludes debt exclusion)", colorVar: "--line-ref", dash: "4,4", width: 1.75 }
  ];

  /* ---------------- GROWTH WATERFALL (stacked area, FY2005-2025) ---------------- */
  // Reuses lineData's own cap_only_25pct_raw / no_override_raw / levy_limit_allowed_raw
  // series - no new data, just the same three counterfactuals restacked as
  // cumulative dollar bands instead of indexed lines (Ben, 2026-09-01: wanted
  // to see the FY05-25 property tax growth story - base / 2.5% / new growth /
  // overrides - as its own visualization, reconciled against his own
  // independently-built version of the same breakdown).
  var wfLayers = [
    { key: "base", label: "Base: property that existed in FY2005", colorVar: "--wf-base",
      lower: function () { return 0; }, upper: function () { return lineData[0].levy_limit_allowed_raw; } },
    { key: "pct25", label: "2.5%/yr automatic growth", colorVar: "--pine",
      lower: function (d) { return lineData[0].levy_limit_allowed_raw; }, upper: function (d) { return d.cap_only_25pct_raw; } },
    { key: "newgrowth", label: "New growth (construction + renovation)", colorVar: "--line-benefits",
      lower: function (d) { return d.cap_only_25pct_raw; }, upper: function (d) { return d.no_override_raw; } },
    { key: "overrides", label: "Overrides (compounded)", colorVar: "--copper",
      lower: function (d) { return d.no_override_raw; }, upper: function (d) { return d.levy_limit_allowed_raw; } }
  ];

  function drawWaterfallChart() {
    var svg = document.getElementById("waterfall-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 650, H = 480;
    // When the stat cards sit beside the chart (wide screens), stretch the chart
    // to their height so the box has no empty space under it, and draw a leader
    // from each band's FY2025 edge to its card (Ben, 2026-10-07). Units are
    // viewBox units; `k` converts screen pixels to them.
    var wrapEl = document.getElementById("waterfall-wrap");
    var statsEl = wrapEl.closest(".chart-row") && wrapEl.closest(".chart-row").querySelector(".waterfall-stats");
    var sideBySide = false, k = 1, svgTopPx = 0;
    if (statsEl && svg.getBoundingClientRect().width > 0) {
      var sr = statsEl.getBoundingClientRect(), wr = svg.getBoundingClientRect();
      sideBySide = sr.left >= wr.right - 1;
      if (sideBySide) {
        k = W / wr.width;
        // svg top sits below the wrap's margin; stats column runs from its own top
        var wrapTop = wrapEl.getBoundingClientRect().top;
        var hPx = sr.bottom - wrapTop;
        H = Math.max(480, Math.round(hPx * k));
        svgTopPx = wrapTop;
      }
    }
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    // right margin holds the FY2025 tick label, which is centred on the
    // plot's right edge and was clipping at 16px
    var m = { top: 16, right: 30, bottom: 30, left: 46 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;

    var years = lineData.map(function (d) { return d.fy; });
    var minY = years[0], maxY = years[years.length - 1];
    var vMax = 300000000;

    function x(fy) { return m.left + (fy - minY) / (maxY - minY) * iw; }
    function y(v) { return m.top + ih - (v / vMax) * ih; }

    for (var gv = 0; gv <= vMax; gv += 50000000) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(gv), y2: y(gv), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 10, y: y(gv) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      gl.textContent = "$" + (gv / 1e6).toFixed(0) + "M";
      svg.appendChild(gl);
    }
    [2005, 2010, 2015, 2020, 2025].forEach(function (yr) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      tl.textContent = "FY" + yr;
      svg.appendChild(tl);
    });

    var tooltip = document.getElementById("waterfall-tooltip");
    var wrap = document.getElementById("waterfall-wrap");
    function hideTip() { tooltip.style.opacity = 0; }

    wfLayers.forEach(function (layer) {
      var upperPts = lineData.map(function (d) { return x(d.fy) + "," + y(layer.upper(d)); });
      var lowerPts = lineData.slice().reverse().map(function (d) { return x(d.fy) + "," + y(layer.lower(d)); });
      var d3 = "M" + upperPts.join(" L") + " L" + lowerPts.join(" L") + " Z";
      var area = svgEl("path", { d: d3, fill: css(layer.colorVar), opacity: 0.85 });
      area.addEventListener("mousemove", function (e) {
        var rect = wrap.getBoundingClientRect();
        var d2025 = lineData[lineData.length - 1];
        var amt = layer.upper(d2025) - layer.lower(d2025);
        tooltip.innerHTML = '<div class="tt-title">' + layer.label + '</div>' +
          '<div class="tt-row"><span>FY2025 level</span><span>' + fmtMoney(layer.upper(d2025), 1) + '</span></div>' +
          '<div class="tt-row"><span>This layer\'s size</span><span>' + fmtMoney(amt, 1) + '</span></div>';
        tooltip.style.opacity = 1;
        tooltip.style.left = (e.clientX - rect.left + 14) + "px";
        tooltip.style.top = (e.clientY - rect.top + 14) + "px";
      });
      area.addEventListener("mouseleave", hideTip);
      svg.appendChild(area);
    });

    // top boundary line, for legibility against the gridlines
    var topPts = lineData.map(function (d) { return x(d.fy) + "," + y(d.levy_limit_allowed_raw); }).join(" L");
    svg.appendChild(svgEl("path", { d: "M" + topPts, fill: "none", stroke: css("--ink"), "stroke-width": 1.5 }));

    // leaders from each band's FY2025 edge to its stat card's top rule
    if (sideBySide) {
      var last = lineData[lineData.length - 1];
      var gapUnits = (statsEl.getBoundingClientRect().left - svg.getBoundingClientRect().right) * k;
      var xEnd = W + gapUnits - 2;
      statsEl.querySelectorAll(".wf-stat[data-layer]").forEach(function (card) {
        var key = card.getAttribute("data-layer"), vy;
        if (key === "top") vy = last.levy_limit_allowed_raw;
        else {
          var L = wfLayers.filter(function (l) { return l.key === key; })[0];
          if (!L) return;
          vy = (L.upper(last) + L.lower(last)) / 2;
        }
        var cardY = (card.getBoundingClientRect().top - svgTopPx) * k + 1.5;
        var x0 = x(maxY), y0 = y(vy), xm = x0 + 10;
        svg.appendChild(svgEl("circle", { cx: x0, cy: y0, r: 2.5, fill: css("--ink-muted") }));
        svg.appendChild(svgEl("path", { d: "M" + x0 + "," + y0 + " L" + xm + "," + y0 + " L" + (xEnd - 8) + "," + cardY + " L" + xEnd + "," + cardY,
          fill: "none", stroke: css("--ink-muted"), "stroke-width": 1, opacity: 0.8 }));
      });
    }
  }

  function drawLineChart() {
    var svg = document.getElementById("line-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 500;
    var m = { top: 24, right: 168, bottom: 34, left: 42 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;

    var years = lineData.map(function (d) { return d.fy; });
    var minY = years[0], maxY = years[years.length - 1];
    var allVals = [];
    lineData.forEach(function (d) {
      series.forEach(function (s) { allVals.push(d[s.key + "_idx"]); });
    });
    var vMax = Math.ceil(Math.max.apply(null, allVals) / 25) * 25;
    var vMin = 90;

    function x(fy) { return m.left + (fy - minY) / (maxY - minY) * iw; }
    function y(v) { return m.top + ih - (v - vMin) / (vMax - vMin) * ih; }

    // gridlines
    for (var gv = 100; gv <= vMax; gv += 50) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(gv), y2: y(gv), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 10, y: y(gv) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      gl.textContent = gv;
      svg.appendChild(gl);
    }
    // x ticks every 5 years
    [2005, 2010, 2015, 2020, 2025].forEach(function (yr) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      tl.textContent = "FY" + yr;
      svg.appendChild(tl);
    });

    // lines
    series.forEach(function (s) {
      var pts = lineData.map(function (d) { return x(d.fy) + "," + y(d[s.key + "_idx"]); }).join(" L");
      var path = svgEl("path", {
        d: "M" + pts,
        fill: "none",
        stroke: css(s.colorVar),
        "stroke-width": s.width,
        "stroke-linejoin": "round",
        "stroke-linecap": "round"
      });
      if (s.dash) path.setAttribute("stroke-dasharray", s.dash);
      svg.appendChild(path);
    });

    // end dots + labels, drawn after all lines so they sit on top - with
    // collision avoidance: two series can land within a couple index points
    // of each other (e.g. total expenditures 215.8 vs the no-override
    // counterfactual 215.3), which would otherwise render as one unreadable
    // stacked label (Ben, 2026-09-01).
    var lastD = lineData[lineData.length - 1];
    var endPoints = series.map(function (s) {
      return { s: s, trueY: y(lastD[s.key + "_idx"]), labelY: y(lastD[s.key + "_idx"]) };
    }).sort(function (a, b) { return a.trueY - b.trueY; });
    var MIN_LABEL_GAP = 13;
    for (var pass = 0; pass < 6; pass++) {
      var moved = false;
      for (var i = 1; i < endPoints.length; i++) {
        var d = endPoints[i].labelY - endPoints[i - 1].labelY;
        if (d < MIN_LABEL_GAP) {
          var push = (MIN_LABEL_GAP - d) / 2;
          endPoints[i - 1].labelY -= push;
          endPoints[i].labelY += push;
          moved = true;
        }
      }
      if (!moved) break;
    }
    endPoints.forEach(function (ep) {
      var s = ep.s;
      var dot = svgEl("circle", { cx: x(lastD.fy), cy: ep.trueY, r: 3, fill: css(s.colorVar) });
      svg.appendChild(dot);
      var txt = svgEl("text", {
        x: x(lastD.fy) + 10, y: ep.labelY + 4, class: "axis-label", "font-size": "12.5", fill: css("--ink")
      });
      txt.textContent = lastD[s.key + "_idx"].toFixed(0);
      svg.appendChild(txt);
    });

    // hover crosshair
    var hitRect = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" });
    var crosshair = svgEl("line", { y1: m.top, y2: m.top + ih, stroke: css("--ink-faint"), "stroke-width": 1, "stroke-dasharray": "3,3", opacity: 0 });
    svg.appendChild(crosshair);
    svg.appendChild(hitRect);

    var tooltip = document.getElementById("line-tooltip");
    var wrap = document.getElementById("line-wrap");

    hitRect.addEventListener("mousemove", function (e) {
      var rect = svg.getBoundingClientRect();
      var scale = W / rect.width;
      var mx = (e.clientX - rect.left) * scale;
      var fy = Math.round(minY + (mx - m.left) / iw * (maxY - minY));
      fy = Math.max(minY, Math.min(maxY, fy));
      var d = lineData[fy - minY];
      crosshair.setAttribute("x1", x(fy));
      crosshair.setAttribute("x2", x(fy));
      crosshair.setAttribute("opacity", 1);

      var html = '<div class="tt-title">FY' + fy + '</div>';
      series.forEach(function (s) {
        html += '<div class="tt-row"><span><span class="tt-swatch" style="background:' + css(s.colorVar) + '"></span>' + s.label.split(" (")[0] + '</span><span>' + d[s.key + "_idx"].toFixed(1) + '&nbsp;&middot;&nbsp;' + fmtMoney(d[s.key + "_raw"]) + '</span></div>';
      });
      tooltip.innerHTML = html;
      tooltip.style.opacity = 1;
      var wrect = wrap.getBoundingClientRect();
      var tx = e.clientX - wrect.left + 14;
      var ty = e.clientY - wrect.top - 10;
      tooltip.style.left = tx + "px";
      tooltip.style.top = ty + "px";
    });
    hitRect.addEventListener("mouseleave", function () {
      tooltip.style.opacity = 0;
      crosshair.setAttribute("opacity", 0);
    });

    // legend
    var legend = document.getElementById("line-legend");
    legend.innerHTML = "";
    series.forEach(function (s) {
      var item = document.createElement("div");
      item.className = "legend-item";
      var sw = document.createElement("span");
      sw.className = "legend-swatch";
      if (s.dash) {
        sw.style.background = "repeating-linear-gradient(90deg, " + css(s.colorVar) + " 0 5px, transparent 5px 9px)";
      } else {
        sw.style.background = css(s.colorVar);
      }
      item.appendChild(sw);
      var txt = document.createElement("span");
      txt.textContent = s.label;
      item.appendChild(txt);
      legend.appendChild(item);
    });

    // table
    var tableWrap = document.getElementById("line-table");
    var html2 = '<table class="data-table"><thead><tr><th>FY</th>';
    series.forEach(function (s) { html2 += "<th>" + s.label.split(" (")[0] + "</th>"; });
    html2 += "</tr></thead><tbody>";
    lineData.forEach(function (d) {
      html2 += "<tr><td>" + d.fy + "</td>";
      series.forEach(function (s) { html2 += "<td>" + d[s.key + "_idx"].toFixed(1) + "</td>"; });
      html2 += "</tr>";
    });
    html2 += "</tbody></table>";
    tableWrap.innerHTML = html2;
  }

  /* ---------------- UNFUNDED LIABILITIES ----------------
     Lifted verbatim from docs/part1_web.html (2026-09-08), where this
     chart lived before the restructure and was the only visual for the
     pension/OPEB story. Its data and draw code are unchanged; only its
     placement moved. */
  var pensionData = [
    [2014,184493444],[2015,220680561],[2016,219943037],[2017,213268118],[2018,239732913],
    [2019,213447748],[2020,190785613],[2021,125295756],[2022,185207594],[2023,170723706]
  ];
  var opebData = [
    [2017,254493372],[2018,262732400],[2019,247463419],[2020,253458013],
    [2021,221120770],[2022,237766628],[2023,189638079],[2024,201475979]
  ];

  function drawLiabilityChart() {
    var svg = document.getElementById("liab-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 420;
    var m = { top: 24, right: 24, bottom: 40, left: 60 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var minY = 2014, maxY = 2024;
    var vMax = 280e6, vMin = 100e6;
    function x(fy) { return m.left + (fy - minY) / (maxY - minY) * iw; }
    function y(v) { return m.top + ih - (v - vMin) / (vMax - vMin) * ih; }

    for (var gv = 100e6; gv <= vMax; gv += 40e6) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(gv), y2: y(gv), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 10, y: y(gv) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      gl.textContent = "$" + (gv / 1e6).toFixed(0) + "M";
      svg.appendChild(gl);
    }
    for (var yr = 2014; yr <= 2024; yr += 2) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      tl.textContent = yr;
      svg.appendChild(tl);
    }

    function series(data, colorVar) {
      var pts = data.map(function (d) { return x(d[0]) + "," + y(d[1]); }).join(" L");
      svg.appendChild(svgEl("path", { d: "M" + pts, fill: "none", stroke: css(colorVar), "stroke-width": 2.5, "stroke-linejoin": "round", "stroke-linecap": "round" }));
      data.forEach(function (d) { svg.appendChild(svgEl("circle", { cx: x(d[0]), cy: y(d[1]), r: 2.5, fill: css(colorVar) })); });
    }
    series(pensionData, "--line-education");
    series(opebData, "--line-levy");

    var tooltip = document.getElementById("liab-tooltip");
    var wrap = document.getElementById("liab-wrap");
    var hitRect = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" });
    svg.appendChild(hitRect);
    hitRect.addEventListener("mousemove", function (e) {
      var rect = svg.getBoundingClientRect();
      var scale = W / rect.width;
      var mx = (e.clientX - rect.left) * scale;
      var fy = Math.round(minY + (mx - m.left) / iw * (maxY - minY));
      fy = Math.max(minY, Math.min(maxY, fy));
      var p = pensionData.filter(function (d) { return d[0] === fy; })[0];
      var o = opebData.filter(function (d) { return d[0] === fy; })[0];
      var html = '<div class="tt-title">' + fy + '</div>';
      if (p) html += '<div class="tt-row"><span><span class="tt-swatch" style="background:' + css("--line-education") + '"></span>Pension liability</span><span>' + fmtMoney(p[1]) + '</span></div>';
      if (o) html += '<div class="tt-row"><span><span class="tt-swatch" style="background:' + css("--line-levy") + '"></span>OPEB liability</span><span>' + fmtMoney(o[1]) + '</span></div>';
      tooltip.innerHTML = html;
      tooltip.style.opacity = 1;
      var wrect = wrap.getBoundingClientRect();
      tooltip.style.left = (e.clientX - wrect.left + 14) + "px";
      tooltip.style.top = (e.clientY - wrect.top - 10) + "px";
    });
    hitRect.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });

    var legend = document.getElementById("liab-legend");
    legend.innerHTML = "";
    [["Net pension liability (measurement year)", "--line-education"], ["Net OPEB liability (fiscal year end)", "--line-levy"]].forEach(function (item) {
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(item[1]);
      el.appendChild(sw);
      var txt = document.createElement("span"); txt.textContent = item[0];
      el.appendChild(txt);
      legend.appendChild(el);
    });
  }

  /* ---------------- WHAT BROOKLINE CONTROLS ----------------
     Added 2026-09-13. Indexed to FY2005 = 100, all ex-debt-exclusion.
     Solid lines are revenue sources Brookline sets; dashed lines are set by
     the Legislature. The expense line is the benchmark both are measured
     against. Series built by scripts/automatic_revenue_vs_costs.py and the
     historical file; see that script's methodology doc. */
  var ctrlSeries = [
    { key: "allow", label: "Levy limit as it actually grew: 2.5% + new growth + overrides", short: "Levy + overrides", color: "--line-levy-actual", dash: false, actual: true, data: [[2005,100.0],[2006,104.4],[2007,108.7],[2008,113.6],[2009,123.2],[2010,127.8],[2011,132.5],[2012,137.5],[2013,142.6],[2014,147.8],[2015,153.3],[2016,165.4],[2017,171.8],[2018,178.0],[2019,190.2],[2020,197.3],[2021,205.1],[2022,213.1],[2023,220.7],[2024,239.3],[2025,248.0]] },
    { key: "levy",  label: "Levy limit: 2.5% + actual new growth, no overrides", short: "Levy, no overrides", color: "--line-education", dash: false, data: [[2005,100.0],[2006,104.4],[2007,108.7],[2008,113.6],[2009,118.0],[2010,122.4],[2011,127.0],[2012,131.9],[2013,136.8],[2014,141.9],[2015,147.2],[2016,152.6],[2017,158.7],[2018,164.6],[2019,170.9],[2020,177.6],[2021,184.8],[2022,192.3],[2023,199.4],[2024,207.4],[2025,215.3]] },
    { key: "fees",  label: "Fees the Town sets (service charges, permits, fines)", short: "Town-set fees", color: "--line-benefits", dash: false, data: [[2005,100.0],[2006,103.5],[2007,100.3],[2008,111.0],[2009,108.3],[2010,103.9],[2011,106.3],[2012,108.7],[2013,109.3],[2014,111.5],[2015,114.6],[2016,131.0],[2017,131.9],[2018,193.7],[2019,180.7],[2020,182.3],[2021,156.9],[2022,194.0],[2023,188.6],[2024,185.8],[2025,198.7]] },
    { key: "exp",   label: "Operating expenditure", short: "Operating expenditure", color: "--line-total", dash: false, bench: true, data: [[2005,100.0],[2006,100.8],[2007,105.8],[2008,110.7],[2009,113.0],[2010,110.4],[2011,111.2],[2012,126.6],[2013,125.2],[2014,126.9],[2015,131.8],[2016,139.2],[2017,146.1],[2018,153.1],[2019,159.5],[2020,166.6],[2021,170.0],[2022,176.4],[2023,182.1],[2024,193.0],[2025,204.8]] },
    { key: "stat",  label: "Levy limit: 2.5% only, no new growth", short: "2.5% only", color: "--line-levy", dash: true, data: [[2005,100.0],[2006,102.5],[2007,105.1],[2008,107.7],[2009,110.4],[2010,113.1],[2011,116.0],[2012,118.9],[2013,121.8],[2014,124.9],[2015,128.0],[2016,131.2],[2017,134.5],[2018,137.9],[2019,141.3],[2020,144.8],[2021,148.5],[2022,152.2],[2023,156.0],[2024,159.9],[2025,163.9]] },
    { key: "aid",   label: "State aid", short: "State aid", color: "--line-no-override", dash: true, data: [[2005,100.0],[2006,102.0],[2007,113.7],[2008,116.3],[2009,110.9],[2010,101.6],[2011,85.9],[2012,84.5],[2013,91.8],[2014,99.0],[2015,104.5],[2016,113.4],[2017,116.8],[2018,120.8],[2019,131.4],[2020,134.7],[2021,132.7],[2022,136.7],[2023,140.1],[2024,142.1],[2025,148.3]] }
  ];

  function drawControlChart() {
    var svg = document.getElementById("control-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 460;
    // Right margin carries a direct label per line, ordered top-to-bottom to
    // match the lines themselves, the same arrangement as the line chart
    // above (Ben, 2026-09-13).
    var m = { top: 24, right: 232, bottom: 40, left: 56 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var minY = 2005, maxY = 2025, vMin = 80, vMax = 255;
    function x(fy) { return m.left + (fy - minY) / (maxY - minY) * iw; }
    function y(v) { return m.top + ih - (v - vMin) / (vMax - vMin) * ih; }

    for (var gv = 100; gv <= vMax; gv += 25) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(gv), y2: y(gv), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 10, y: y(gv) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      gl.textContent = gv;
      svg.appendChild(gl);
    }
    for (var yr = 2005; yr <= 2025; yr += 5) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      tl.textContent = "FY" + yr;
      svg.appendChild(tl);
    }

    // draw the benchmark last so it sits on top
    var ordered = ctrlSeries.filter(function (s) { return !s.bench; }).concat(ctrlSeries.filter(function (s) { return s.bench; }));
    ordered.forEach(function (s) {
      var pts = s.data.map(function (p) { return x(p[0]) + "," + y(p[1]); }).join(" L");
      var attrs = {
        d: "M" + pts, fill: "none", stroke: css(s.color),
        "stroke-width": s.bench ? 3.2 : (s.actual ? 2.6 : 2.2),
        "stroke-linejoin": "round", "stroke-linecap": "round"
      };
      if (s.dash) attrs["stroke-dasharray"] = "6 4";
      svg.appendChild(svgEl("path", attrs));
    });

    // Direct labels at the right edge, nudged apart so two lines finishing
    // close together (operating expenditure at 205 and town-set fees at 199)
    // don't render as one stacked block.
    var ends = ctrlSeries.map(function (s) {
      var last = s.data[s.data.length - 1];
      return { s: s, val: last[1], trueY: y(last[1]), labelY: y(last[1]) };
    }).sort(function (a, b) { return a.trueY - b.trueY; });
    var GAP = 15;
    for (var pass = 0; pass < 8; pass++) {
      var moved = false;
      for (var i = 1; i < ends.length; i++) {
        var gapNow = ends[i].labelY - ends[i - 1].labelY;
        if (gapNow < GAP) {
          var push = (GAP - gapNow) / 2;
          ends[i - 1].labelY -= push;
          ends[i].labelY += push;
          moved = true;
        }
      }
      if (!moved) break;
    }
    ends.forEach(function (ep) {
      var s = ep.s, lx = x(maxY);
      // leader from the line's true endpoint across to its nudged label
      svg.appendChild(svgEl("circle", { cx: lx, cy: ep.trueY, r: 3, fill: css(s.color) }));
      svg.appendChild(svgEl("path", {
        d: "M" + lx + "," + ep.trueY + " L" + (lx + 10) + "," + ep.trueY +
           " L" + (lx + 16) + "," + ep.labelY + " L" + (lx + 22) + "," + ep.labelY,
        fill: "none", stroke: css(s.color), "stroke-width": 1, opacity: 0.5
      }));
      var lbl = svgEl("text", {
        x: lx + 27, y: ep.labelY + 4, "font-size": "11.5",
        fill: css(s.color), "font-weight": s.bench || s.actual ? "600" : "500"
      });
      lbl.textContent = (s.short || s.label) + "  " + ep.val.toFixed(0);
      svg.appendChild(lbl);
    });

    var legend = document.getElementById("control-legend");
    if (legend) {
      legend.innerHTML = "";
      ctrlSeries.forEach(function (s) {
        var el = document.createElement("div");
        el.className = "legend-item";
        var sw = document.createElement("span");
        sw.className = "legend-swatch";
        sw.style.background = css(s.color);
        if (s.dash) sw.style.opacity = "0.55";
        el.appendChild(sw);
        var txt = document.createElement("span");
        txt.textContent = s.label + (s.dash ? "  (set by the state)" :
                                     (s.actual ? "  (what actually happened)" : ""));
        el.appendChild(txt);
        legend.appendChild(el);
      });
    }
  }


  /* ---------------- WHEN A NEW HOME COVERS ITS COSTS ----------------
     Added 2026-09-29. Breakeven school-age children per home by assessed value,
     FY2027 and FY2040, from scripts/housing_unit_breakeven.py (driver-model
     costs: $866 Town services and $16,837 per added student in FY2027). Below
     a line the home's property tax covers its costs; above it, it does not. */
  var unitBeData = [[200000,0.0697,0.0533],[225000,0.0847,0.0654],[250000,0.0998,0.0776],[275000,0.1149,0.0897],[300000,0.13,0.1018],[325000,0.1451,0.1139],[350000,0.1601,0.1261],[375000,0.1752,0.1382],[400000,0.1903,0.1503],[425000,0.2054,0.1624],[450000,0.2205,0.1745],[475000,0.2355,0.1867],[500000,0.2506,0.1988],[525000,0.2657,0.2109],[550000,0.2808,0.223],[575000,0.2959,0.2352],[600000,0.311,0.2473],[625000,0.326,0.2594],[650000,0.3411,0.2715],[675000,0.3562,0.2837],[700000,0.3713,0.2958],[725000,0.3864,0.3079],[750000,0.4014,0.32],[775000,0.4165,0.3321],[800000,0.4316,0.3443],[825000,0.4467,0.3564],[850000,0.4618,0.3685],[875000,0.4768,0.3806],[900000,0.4919,0.3928],[925000,0.507,0.4049],[950000,0.5221,0.417],[975000,0.5372,0.4291],[1000000,0.5522,0.4412],[1025000,0.5673,0.4534],[1050000,0.5824,0.4655],[1075000,0.5975,0.4776],[1100000,0.6126,0.4897],[1125000,0.6277,0.5019],[1150000,0.6427,0.514],[1175000,0.6578,0.5261],[1200000,0.6729,0.5382],[1225000,0.688,0.5504],[1250000,0.7031,0.5625],[1275000,0.7181,0.5746],[1300000,0.7332,0.5867],[1325000,0.7483,0.5988],[1350000,0.7634,0.611],[1375000,0.7785,0.6231],[1400000,0.7935,0.6352],[1425000,0.8086,0.6473],[1450000,0.8237,0.6595],[1475000,0.8388,0.6716],[1500000,0.8539,0.6837],[1525000,0.8689,0.6958],[1550000,0.884,0.708],[1575000,0.8991,0.7201],[1600000,0.9142,0.7322]];
  var unitBeMarkers = [
    { v: 434283, label: "Apartment, 9+ units", row: 0 },
    { v: 672850, label: "Apartment, 4-8 units", row: 1 },
    { v: 794300, label: "New construction, mean", row: 0 },
    { v: 1175950, label: "Condominium", row: 0 }
  ];
  // Enrolled students per unit in ten Brookline buildings built since 2015, Fall
  // 2025, read from the Town's ERSC report chart (reference document 3a). The
  // single-family average is the FY2025 roll's 4,584 single-family parcels
  // (use code 101), off the right edge of the chart: it breaks even at 1.64.
  var unitBeObserved = [0.03, 0.06, 0.07, 0.13, 0.16, 0.18, 0.25, 0.25, 0.40, 0.56];
  var UNITBE_SINGLE_FAMILY = 2779670;
  // Owner-occupied homes are taxed on their value less the residential exemption
  // ($354,974 in FY2026, Town of Brookline), so their breakeven is the same line
  // moved right by that amount. Breakeven is linear in value, so interpolate.
  var RES_EXEMPTION = 354974;
  function unitBeAt(v, idx) {
    var a = unitBeData[0], b = unitBeData[unitBeData.length - 1];
    return a[idx] + (v - a[0]) * (b[idx] - a[idx]) / (b[0] - a[0]);
  }
  function drawUnitBreakevenChart() {
    var svg = document.getElementById("unitbe-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    // Labels for the reference homes sit under the axis (Ben, 2026-10-07); the
    // right margin holds the ten observed buildings.
    var W = 900, H = 500;
    var m = { top: 30, right: 130, bottom: 92, left: 60 };
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var xMin = 200000, xMax = 1600000, yMax = 0.8;
    function x(v) { return m.left + (v - xMin) / (xMax - xMin) * iw; }
    function y(c) { return m.top + ih - c / yMax * ih; }
    for (var gc = 0; gc <= yMax + 1e-9; gc += 0.2) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(gc), y2: y(gc), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 10, y: y(gc) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      gl.textContent = gc.toFixed(1);
      svg.appendChild(gl);
    }
    for (var gv = 200000; gv <= xMax; gv += 200000) {
      var tl = svgEl("text", { x: x(gv), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      tl.textContent = gv >= 1e6 ? "$" + (gv / 1e6).toFixed(1) + "M" : "$" + (gv / 1e3).toFixed(0) + "K";
      svg.appendChild(tl);
    }
    var xl = svgEl("text", { x: m.left + iw / 2, y: H - 6, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
    xl.textContent = "Assessed value per home";
    svg.appendChild(xl);
    var yl = svgEl("text", { x: 4, y: m.top - 16, class: "tick-label", "text-anchor": "start", "font-size": "11" });
    yl.textContent = "Children per home";
    svg.appendChild(yl);

    // shaded "does not cover" region above the FY2027 line
    var upper = unitBeData.map(function (d) { return x(d[0]) + "," + y(Math.min(d[1], yMax)); });
    svg.appendChild(svgEl("path", { d: "M" + x(xMin) + "," + y(yMax) + " L" + upper.join(" L") + " L" + x(xMax) + "," + y(yMax) + " Z", fill: css("--line-levy"), opacity: 0.08 }));

    // the model's average and the observed range
    svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(0.244), y2: y(0.244), stroke: css("--line-ref"), "stroke-width": 1.5, "stroke-dasharray": "5,4" }));
    var al = svgEl("text", { x: m.left + iw - 4, y: y(0.244) + 16, class: "tick-label", "text-anchor": "end", "font-size": "11" });
    al.textContent = "Forecast average, 0.24 children";
    svg.appendChild(al);

    // markers for reference homes, labels staggered in two rows under the axis
    unitBeMarkers.forEach(function (mk) {
      svg.appendChild(svgEl("line", { x1: x(mk.v), x2: x(mk.v), y1: m.top, y2: m.top + ih, stroke: css("--ink-faint"), "stroke-width": 1, "stroke-dasharray": "2,3" }));
      var t = svgEl("text", { x: x(mk.v), y: m.top + ih + 44 + mk.row * 16, "text-anchor": "middle", "font-size": "11.5",
        fill: css("--ink-muted"), "font-family": css("--font-mono") });
      t.textContent = mk.label;
      svg.appendChild(t);
    });
    var sf = svgEl("text", { x: m.left + iw, y: m.top + ih + 60, "text-anchor": "end", "font-size": "11.5",
      fill: css("--ink-muted"), "font-family": css("--font-mono") });
    sf.textContent = "Single-family average, " + fmtMoney(UNITBE_SINGLE_FAMILY, 2) + ", breaks even at 1.7 \u2192";
    svg.appendChild(sf);

    // the ten observed buildings, as a strip in the right margin
    var sx = m.left + iw + 62;
    svg.appendChild(svgEl("line", { x1: sx, x2: sx, y1: y(unitBeObserved[0]), y2: y(unitBeObserved[unitBeObserved.length - 1]),
      stroke: css("--ink-faint"), "stroke-width": 1 }));
    unitBeObserved.forEach(function (c, i) {
      var dup = unitBeObserved.indexOf(c) !== i ? 5 : (unitBeObserved.lastIndexOf(c) !== i ? -5 : 0);
      svg.appendChild(svgEl("circle", { cx: sx + dup, cy: y(c), r: 4, fill: css("--ink-muted"), stroke: css("--paper"), "stroke-width": 1 }));
    });
    ["Ten recent", "Brookline", "buildings"].forEach(function (s, i) {
      var tt = svgEl("text", { x: sx, y: y(unitBeObserved[unitBeObserved.length - 1]) - 46 + i * 14, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      tt.textContent = s;
      svg.appendChild(tt);
    });

    function series(idx, colorVar, dash) {
      var pts = unitBeData.filter(function (d) { return d[idx] <= yMax; }).map(function (d) { return x(d[0]) + "," + y(d[idx]); }).join(" L");
      var a = { d: "M" + pts, fill: "none", stroke: css(colorVar), "stroke-width": 2.5, "stroke-linejoin": "round", "stroke-linecap": "round" };
      if (dash) a["stroke-dasharray"] = "7,5";
      svg.appendChild(svgEl("path", a));
    }
    series(1, "--line-education", false);
    series(2, "--line-levy", true);
    // owner-occupied with the residential exemption, FY2027
    var ex = unitBeData.filter(function (d) { return unitBeAt(d[0] - RES_EXEMPTION, 1) >= 0; })
      .map(function (d) { return x(d[0]) + "," + y(Math.max(unitBeAt(d[0] - RES_EXEMPTION, 1), 0)); }).join(" L");
    svg.appendChild(svgEl("path", { d: "M" + ex, fill: "none", stroke: css("--line-benefits"), "stroke-width": 2.5,
      "stroke-dasharray": "2,4", "stroke-linecap": "round" }));

    var r1 = svgEl("text", { x: x(830000), y: y(0.74), class: "tick-label", "font-size": "12" });
    r1.textContent = "Costs more than it pays";
    svg.appendChild(r1);
    var r2 = svgEl("text", { x: x(1250000), y: y(0.12), class: "tick-label", "font-size": "12" });
    r2.textContent = "Pays its way";
    svg.appendChild(r2);

    var tooltip = document.getElementById("unitbe-tooltip");
    var wrap = document.getElementById("unitbe-wrap");
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" });
    svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var rect = svg.getBoundingClientRect();
      var mx = (e.clientX - rect.left) * (W / rect.width);
      var v = xMin + (mx - m.left) / iw * (xMax - xMin);
      var d = unitBeData.reduce(function (a, b) { return Math.abs(b[0] - v) < Math.abs(a[0] - v) ? b : a; });
      tooltip.innerHTML = '<div class="tt-title">' + fmtMoneyFull(d[0]) + ' a home</div>' +
        '<div class="tt-row"><span>Breaks even, FY2027</span><span>' + d[1].toFixed(2) + ' children</span></div>' +
        '<div class="tt-row"><span>Breaks even, FY2040</span><span>' + d[2].toFixed(2) + ' children</span></div>' +
        '<div class="tt-row"><span>Owner-occupied, FY2027</span><span>' + Math.max(unitBeAt(d[0] - RES_EXEMPTION, 1), 0).toFixed(2) + ' children</span></div>';
      tooltip.style.opacity = 1;
      var wrect = wrap.getBoundingClientRect();
      tooltip.style.left = (e.clientX - wrect.left + 14) + "px";
      tooltip.style.top = (e.clientY - wrect.top - 10) + "px";
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });

    var legend = document.getElementById("unitbe-legend");
    legend.innerHTML = "";
    [["Breakeven when the home opens (FY2027)", "--line-education"], ["Breakeven in FY2040", "--line-levy"], ["Owner-occupied, with the residential exemption (FY2027)", "--line-benefits"], ["Forecast average, 0.244 children per new home: a standard per-bedroom schedule applied to Brookline's housing mix", "--line-ref"], ["Dots: enrolled students per home in ten Brookline buildings built since 2015 (Town ERSC report, Fall 2025)", "--ink-muted"]].forEach(function (item) {
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(item[1]);
      el.appendChild(sw);
      var txt = document.createElement("span"); txt.textContent = item[0];
      el.appendChild(txt);
      legend.appendChild(el);
    });
    var tbl = document.getElementById("unitbe-table");
    if (tbl) {
      var h = '<table><thead><tr><th>Assessed value</th><th>Breakeven children, FY2027</th><th>FY2040</th><th>Owner-occupied, FY2027</th></tr></thead><tbody>';
      unitBeData.filter(function (d) { return d[0] % 100000 === 0; }).forEach(function (d) {
        h += '<tr><td>' + fmtMoneyFull(d[0]) + '</td><td>' + d[1].toFixed(2) + '</td><td>' + d[2].toFixed(2) + '</td><td>' + Math.max(unitBeAt(d[0] - RES_EXEMPTION, 1), 0).toFixed(2) + '</td></tr>';
      });
      tbl.innerHTML = h + '</tbody></table>';
    }
  }

  /* ---------------- WHAT DECIDES THE 2040 BUDGET ----------------
     Added 2026-09-29. Change in the FY2040 annual balance when one assumption
     moves from the base case, from output/expense_driver_forecast_sensitivity_fy40.csv.
     The dashed line marks the base case's whole FY2040 room (decisionsRoom): a bar
     reaching past it on the left uses all of it. */
  var decisionsRoom = 12.0;
  var decisionsData = [{"label":"Enrollment rebounds, staff follow","v":-47.9,"kind":"outside"},{"label":"Pay 1 point higher, all staff","v":-42.3,"kind":"decide"},{"label":"School pay at schools' forecast","v":-32.2,"kind":"decide"},{"label":"Health premiums 10% a year","v":-30.4,"kind":"outside"},{"label":"School staff held at FY2027 level","v":-27.8,"kind":"decide"},{"label":"Chestnut Hill inside trend","v":-5.8,"kind":"growth"},{"label":"Capital at the Town's table, about 6%","v":2.9,"kind":"decide"},{"label":"Faster growth, housing-led","v":5.6,"kind":"growth"},{"label":"School staff follow enrollment","v":9.5,"kind":"decide"},{"label":"Health premiums 6.5% a year","v":19.4,"kind":"outside"},{"label":"Pay half a point lower","v":19.4,"kind":"decide"},{"label":"School & safety pay at target","v":20.0,"kind":"decide"},{"label":"Faster growth, housing + commercial","v":23.3,"kind":"growth"},{"label":"Pension savings kept, not OPEB","v":34.6,"kind":"decide"},{"label":"Retiree health payoff money spent","v":43.0,"kind":"decide"},{"label":"Faster growth, commercial-led","v":46.1,"kind":"growth"}];
  var decisionsKinds = { decide: ["Brookline decides", "--pine"], growth: ["Growth (zoning, permitting)", "--line-no-override"], outside: ["Set mostly outside Brookline", "--line-ref"] };
  function drawDecisionsChart() {
    var svg = document.getElementById("decisions-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, rowH = 28;
    var m = { top: 30, right: 60, bottom: 36, left: 250 };
    var H = m.top + m.bottom + rowH * decisionsData.length;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var iw = W - m.left - m.right;
    var vMin = -62, vMax = 62;
    function x(v) { return m.left + (v - vMin) / (vMax - vMin) * iw; }
    for (var gv = -60; gv <= vMax; gv += 20) {
      svg.appendChild(svgEl("line", { x1: x(gv), x2: x(gv), y1: m.top - 6, y2: H - m.bottom, class: "gridline" }));
      var gl = svgEl("text", { x: x(gv), y: H - m.bottom + 18, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      gl.textContent = (gv > 0 ? "+" : gv < 0 ? "−" : "") + "$" + Math.abs(gv) + "M";
      svg.appendChild(gl);
    }
    svg.appendChild(svgEl("line", { x1: x(0), x2: x(0), y1: m.top - 6, y2: H - m.bottom, stroke: css("--ink"), "stroke-width": 1 }));
    svg.appendChild(svgEl("line", { x1: x(-decisionsRoom), x2: x(-decisionsRoom), y1: m.top - 14, y2: H - m.bottom, stroke: css("--line-levy"), "stroke-width": 1.5, "stroke-dasharray": "5,4" }));
    var rl = svgEl("text", { x: x(-decisionsRoom) - 6, y: m.top - 16, class: "tick-label", "text-anchor": "end", "font-size": "11" });
    rl.textContent = "Uses all the FY2040 room";
    svg.appendChild(rl);
    var tooltip = document.getElementById("decisions-tooltip");
    var wrap = document.getElementById("decisions-wrap");
    decisionsData.forEach(function (d, i) {
      var cy = m.top + i * rowH + rowH / 2;
      var lab = svgEl("text", { x: m.left - 10, y: cy + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      lab.textContent = d.label;
      svg.appendChild(lab);
      var x0 = x(Math.min(0, d.v)), w = Math.abs(x(d.v) - x(0));
      var bar = svgEl("rect", { x: x0, y: cy - 9, width: w, height: 18, rx: 2, fill: css(decisionsKinds[d.kind][1]) });
      svg.appendChild(bar);
      var vl = svgEl("text", { x: d.v < 0 ? x(d.v) - 6 : x(d.v) + 6, y: cy + 4, class: "tick-label", "text-anchor": d.v < 0 ? "end" : "start", "font-size": "11" });
      vl.textContent = (d.v > 0 ? "+" : "−") + "$" + Math.abs(d.v).toFixed(1) + "M";
      svg.appendChild(vl);
      bar.addEventListener("mousemove", function (e) {
        tooltip.innerHTML = '<div class="tt-title">' + d.label + '</div><div class="tt-row"><span>' + decisionsKinds[d.kind][0] + '</span><span>' + vl.textContent + ' a year in FY2040</span></div>';
        tooltip.style.opacity = 1;
        var wrect = wrap.getBoundingClientRect();
        tooltip.style.left = (e.clientX - wrect.left + 14) + "px";
        tooltip.style.top = (e.clientY - wrect.top - 10) + "px";
      });
      bar.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    });
    var legend = document.getElementById("decisions-legend");
    legend.innerHTML = "";
    Object.keys(decisionsKinds).forEach(function (k) {
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(decisionsKinds[k][1]);
      el.appendChild(sw);
      var txt = document.createElement("span"); txt.textContent = decisionsKinds[k][0];
      el.appendChild(txt);
      legend.appendChild(el);
    });
  }

  /* ---------------- NEW GROWTH: ROOM AT FOUR RATES, AND BY MIX ----------------
     Added 2026-10-06 for docs/new_growth.md. Both data sets are printed by
     scripts/new_growth_page_data.js (dashboard engine, base case, today's mix /
     each mix at +0.7 point); rerun it and paste whenever the forecast changes. */
  var growthPathsYears = [2027,2028,2029,2030,2031,2032,2033,2034,2035,2036,2037,2038,2039,2040];
  var growthPathsData = [{"k":-3,"rate":0.94,"room":[0,-1.5,1.3,4.4,2.4,3.6,4.7,5.9,4.9,3.9,1.9,0,-4.1,-8.8],"neg":2028},{"k":0,"rate":1.23,"room":[0,0.8,4.5,8.8,8,10.4,13,15.7,16.2,16.9,16.7,16.6,14.5,12],"neg":""},{"k":3,"rate":1.53,"room":[0,2.1,6.7,12,12.2,15.8,19.5,23.5,25.4,27.6,28.9,30.5,30.2,29.5],"neg":""},{"k":8,"rate":2.04,"room":[0,4.4,10.4,17.3,19.4,24.8,30.7,36.9,41.3,46,50.1,49.9,52.6,55.2],"neg":""}];
  var growthPathsStyle = {
    "-3": ["0.94%, 0.3 point slower", "--line-levy"],
    "0": ["1.23%, base case", "--line-total"],
    "3": ["1.53%, 0.3 point faster", "--line-benefits"],
    "8": ["2.03%, the 80th percentile", "--line-education"]
  };
  function sgn(v, d) { return (v < 0 ? "−" : "") + "$" + Math.abs(v).toFixed(d == null ? 1 : d) + "M"; }
  function drawGrowthPathsChart() {
    var svg = document.getElementById("gpaths-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 440;
    var m = { top: 24, right: 130, bottom: 40, left: 60 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var Y = growthPathsYears, vMin = -20, vMax = 70;
    function x(yr) { return m.left + (yr - Y[0]) / (Y[Y.length - 1] - Y[0]) * iw; }
    function y(v) { return m.top + ih - (v - vMin) / (vMax - vMin) * ih; }
    for (var gv = -20; gv <= vMax; gv += 10) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(gv), y2: y(gv), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 10, y: y(gv) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      gl.textContent = gv === 0 ? "$0" : sgn(gv, 0);
      svg.appendChild(gl);
    }
    svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(0), y2: y(0), stroke: css("--ink"), "stroke-width": 1 }));
    var zl = svgEl("text", { x: m.left + 6, y: y(0) + 16, class: "tick-label", "font-size": "11" });
    zl.textContent = "Below this line, spending outruns revenue";
    svg.appendChild(zl);
    Y.forEach(function (yr) {
      if ((yr - 2027) % 2 !== 1 && yr !== 2040) return;
      var t = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      t.textContent = "FY" + yr;
      svg.appendChild(t);
    });
    growthPathsData.forEach(function (d) {
      var st = growthPathsStyle[String(d.k)];
      var pts = d.room.map(function (v, i) { return x(Y[i]) + "," + y(v); }).join(" L");
      svg.appendChild(svgEl("path", { d: "M" + pts, fill: "none", stroke: css(st[1]), "stroke-width": d.k === 0 ? 3 : 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
      var last = d.room[d.room.length - 1];
      svg.appendChild(svgEl("circle", { cx: x(Y[Y.length - 1]), cy: y(last), r: 4, fill: css(st[1]), stroke: css("--paper-card"), "stroke-width": 2 }));
      var lab = svgEl("text", { x: x(Y[Y.length - 1]) + 10, y: y(last) + 4, class: "tick-label", "font-size": "11" });
      lab.textContent = st[0].split(",")[0] + "  " + sgn(last);
      svg.appendChild(lab);
    });
    svg.setAttribute("aria-label", "Line chart of revenue minus spending each year, FY" + Y[0] + " to FY" + Y[Y.length - 1] +
      ", at four new growth rates. In FY" + Y[Y.length - 1] + ": " + growthPathsData.map(function (d) {
        return growthPathsStyle[String(d.k)][0] + ", " + sgn(d.room[d.room.length - 1]) + (d.neg ? " (room runs out in FY" + d.neg + ")" : "");
      }).join("; ") + ".");
    var tooltip = document.getElementById("gpaths-tooltip");
    var wrap = document.getElementById("gpaths-wrap");
    var cross = svgEl("line", { y1: m.top, y2: m.top + ih, stroke: css("--ink-faint"), "stroke-width": 1, "stroke-dasharray": "3,3", opacity: 0 });
    svg.appendChild(cross);
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw + 10, height: ih, fill: "transparent" });
    svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var rect = svg.getBoundingClientRect();
      var mx = (e.clientX - rect.left) * (W / rect.width);
      var i = Math.max(0, Math.min(Y.length - 1, Math.round((mx - m.left) / iw * (Y.length - 1))));
      cross.setAttribute("x1", x(Y[i])); cross.setAttribute("x2", x(Y[i])); cross.setAttribute("opacity", 1);
      var h = '<div class="tt-title">FY' + Y[i] + ' room</div>';
      growthPathsData.slice().reverse().forEach(function (d) {
        h += '<div class="tt-row"><span>' + growthPathsStyle[String(d.k)][0] + '</span><span>' + sgn(d.room[i]) + '</span></div>';
      });
      tooltip.innerHTML = h;
      tooltip.style.opacity = 1;
      var wrect = wrap.getBoundingClientRect();
      tooltip.style.left = Math.min(e.clientX - wrect.left + 14, wrect.width - 260) + "px";
      tooltip.style.top = (e.clientY - wrect.top - 10) + "px";
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; cross.setAttribute("opacity", 0); });
    var legend = document.getElementById("gpaths-legend");
    legend.innerHTML = "";
    growthPathsData.slice().reverse().forEach(function (d) {
      var st = growthPathsStyle[String(d.k)];
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(st[1]);
      el.appendChild(sw);
      var txt = document.createElement("span"); txt.textContent = st[0];
      el.appendChild(txt);
      legend.appendChild(el);
    });
    var tbl = document.getElementById("gpaths-table");
    if (tbl) {
      var t = '<table><thead><tr><th>Year</th>' + growthPathsData.map(function (d) { return '<th>' + growthPathsStyle[String(d.k)][0] + '</th>'; }).join("") + '</tr></thead><tbody>';
      Y.forEach(function (yr, i) {
        t += '<tr><td>FY' + yr + '</td>' + growthPathsData.map(function (d) { return '<td>' + sgn(d.room[i]) + '</td>'; }).join("") + '</tr>';
      });
      tbl.innerHTML = t + '</tbody></table>';
    }
  }

  var growthMixData = [{"mix":"mix","rev":67.7,"cost":24.4,"net":43.3,"homes":1036,"students":253},{"mix":"commercial","rev":67.2,"cost":21.2,"net":46.1,"homes":66,"students":16},{"mix":"even","rev":68.6,"cost":45.3,"net":23.3,"homes":2947,"students":720},{"mix":"housing","rev":70,"cost":64.4,"net":5.6,"homes":5825,"students":1422}];
  var growthMixLabels = { mix: "Today's mix", commercial: "New commercial space", even: "Half homes, half commercial", housing: "New homes only" };
  function drawGrowthMixChart() {
    var svg = document.getElementById("gmix-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, rowH = 56;
    var m = { top: 20, right: 120, bottom: 36, left: 210 };
    var H = m.top + m.bottom + rowH * growthMixData.length;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("aria-label", "Bar chart of what faster new growth at the 80th-percentile rate adds by FY2040, by kind of growth: " +
      growthMixData.map(function (d) { return growthMixLabels[d.mix] + ", added tax $" + d.rev.toFixed(1) + " million, added costs $" + d.cost.toFixed(1) +
        " million, net $" + d.net.toFixed(1) + " million"; }).join("; ") + ".");
    var iw = W - m.left - m.right, vMin = -70, vMax = 70;
    function x(v) { return m.left + (v - vMin) / (vMax - vMin) * iw; }
    for (var gv = -60; gv <= vMax; gv += 20) {
      svg.appendChild(svgEl("line", { x1: x(gv), x2: x(gv), y1: m.top - 6, y2: H - m.bottom, class: "gridline" }));
      var gl = svgEl("text", { x: x(gv), y: H - m.bottom + 18, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      gl.textContent = (gv > 0 ? "+" : gv < 0 ? "−" : "") + "$" + Math.abs(gv) + "M";
      svg.appendChild(gl);
    }
    svg.appendChild(svgEl("line", { x1: x(0), x2: x(0), y1: m.top - 6, y2: H - m.bottom, stroke: css("--ink"), "stroke-width": 1 }));
    var nh = svgEl("text", { x: W - m.right + 14, y: m.top - 6, class: "tick-label", "font-size": "11" });
    nh.textContent = "Net, FY2040";
    svg.appendChild(nh);
    var tooltip = document.getElementById("gmix-tooltip");
    var wrap = document.getElementById("gmix-wrap");
    growthMixData.forEach(function (d, i) {
      var cy = m.top + i * rowH + rowH / 2;
      var lab = svgEl("text", { x: m.left - 12, y: cy + 4, class: "tick-label", "text-anchor": "end", "font-size": "12" });
      lab.textContent = growthMixLabels[d.mix];
      svg.appendChild(lab);
      var bars = [
        svgEl("rect", { x: x(0) + 1, y: cy - 10, width: Math.max(x(d.rev) - x(0) - 1, 1), height: 20, rx: 2, fill: css("--pine") }),
        svgEl("rect", { x: x(-d.cost), y: cy - 10, width: Math.max(x(0) - x(-d.cost) - 1, 1), height: 20, rx: 2, fill: css("--line-levy") })
      ];
      bars.forEach(function (b) { svg.appendChild(b); });
      // a long cost bar leaves no room for its label before the row label, so it goes inside the bar
      var inside = x(-d.cost) - 64 < m.left;
      var cl = svgEl("text", inside ? { x: x(-d.cost) + 6, y: cy + 4, "text-anchor": "start", "font-size": "11", fill: "#fff", "font-family": css("--font-mono") }
                                    : { x: x(-d.cost) - 6, y: cy + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      cl.textContent = "−$" + d.cost.toFixed(1) + "M";
      svg.appendChild(cl);
      var net = svgEl("text", { x: W - m.right + 14, y: cy + 5, class: "tick-label", "font-size": "13", "font-weight": "600" });
      net.textContent = "+$" + d.net.toFixed(1) + "M";
      svg.appendChild(net);
      bars.forEach(function (b) {
        b.addEventListener("mousemove", function (e) {
          tooltip.innerHTML = '<div class="tt-title">' + growthMixLabels[d.mix] + '</div>' +
            '<div class="tt-row"><span>Added tax</span><span>+$' + d.rev.toFixed(1) + 'M</span></div>' +
            '<div class="tt-row"><span>Added costs</span><span>−$' + d.cost.toFixed(1) + 'M</span></div>' +
            '<div class="tt-row"><span>Net</span><span>+$' + d.net.toFixed(1) + 'M</span></div>' +
            '<div class="tt-row"><span>Added homes / students</span><span>' + d.homes.toLocaleString("en-US") + ' / ' + d.students.toLocaleString("en-US") + '</span></div>';
          tooltip.style.opacity = 1;
          var wrect = wrap.getBoundingClientRect();
          tooltip.style.left = Math.min(e.clientX - wrect.left + 14, wrect.width - 260) + "px";
          tooltip.style.top = (e.clientY - wrect.top - 10) + "px";
        });
        b.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
      });
    });
    var legend = document.getElementById("gmix-legend");
    legend.innerHTML = "";
    [["Added costs (schools, Town services, benefits)", "--line-levy"], ["Added tax and other revenue", "--pine"]].forEach(function (item) {
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(item[1]);
      el.appendChild(sw);
      var txt = document.createElement("span"); txt.textContent = item[0];
      el.appendChild(txt);
      legend.appendChild(el);
    });
    var tbl = document.getElementById("gmix-table");
    if (tbl) {
      var t = '<table><thead><tr><th>Added growth comes from</th><th>Added tax</th><th>Added costs</th><th>Net</th><th>Added homes</th><th>Added students</th></tr></thead><tbody>';
      growthMixData.forEach(function (d) {
        t += '<tr><td>' + growthMixLabels[d.mix] + '</td><td>$' + d.rev.toFixed(1) + 'M</td><td>$' + d.cost.toFixed(1) + 'M</td><td>$' + d.net.toFixed(1) + 'M</td><td>' + d.homes.toLocaleString("en-US") + '</td><td>' + d.students.toLocaleString("en-US") + '</td></tr>';
      });
      tbl.innerHTML = t + '</tbody></table>';
    }
  }

  /* ---------------- HOUSING AND SCHOOL SEATS ----------------
     Added 2026-10-06 for docs/new_growth.md. Data printed by scripts/new_growth_page_data.js
     (section 3): enrollment against the FY2027 level the schools are staffed for, and what
     more housing adds to FY2040 under two staffing assumptions. */
  var seatsHist = [[2010,6472],[2011,6627],[2012,6875],[2013,7112],[2014,7288],[2015,7508],[2016,7668],[2017,7695],[2018,7801],[2019,7855],[2020,7777],[2021,6891],[2022,6928],[2023,7060],[2024,7039],[2025,7023],[2026,6949]];
  var seatsProj = [[2027,6833],[2028,6662],[2029,6501],[2030,6402],[2031,6262],[2032,6171],[2033,6054],[2034,5926],[2035,5806],[2036,5680],[2037,5584],[2038,5469],[2039,5435],[2040,5400]];
  var seatsCM = [[2027,6833],[2028,6802],[2029,6849],[2030,6964],[2031,7032],[2032,7157],[2033,7255],[2034,7354]];
  var seatsNesdec = [[2027,6833],[2028,6642],[2029,6563],[2030,6520],[2031,6420],[2032,6358],[2033,6271],[2034,6180]];
  var seatsBase = [[2027,0],[2028,108],[2029,217],[2030,328],[2031,439],[2032,639],[2033,838],[2034,1038],[2035,1149],[2036,1260],[2037,1370],[2038,1480],[2039,1589],[2040,1698]];
  var seatsLevel = 6833;
  var seatsRoom = [[2027,0],[2028,702],[2029,1359],[2030,1764],[2031,2338],[2032,2709],[2033,3188],[2034,3713],[2035,4204],[2036,4723],[2037,5113],[2038,5585],[2039,5724],[2040,5869]];
  var housingFillData = [{"homes":2133,"staffed":-1.2,"fill":8.2,"enroll":5921},{"homes":5087,"staffed":4.2,"fill":16.7,"enroll":6642},{"homes":9781,"staffed":13.1,"fill":25.6,"enroll":7788}];
  function drawSeatsChart() {
    var svg = document.getElementById("seats-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 400;
    var m = { top: 24, right: 150, bottom: 40, left: 60 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var y0 = 2010, y1 = 2040, vMin = 5500, vMax = 8000;
    function x(yr) { return m.left + (yr - y0) / (y1 - y0) * iw; }
    function y(v) { return m.top + ih - (v - vMin) / (vMax - vMin) * ih; }
    for (var gv = 5500; gv <= vMax; gv += 500) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(gv), y2: y(gv), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 10, y: y(gv) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      gl.textContent = gv.toLocaleString("en-US");
      svg.appendChild(gl);
    }
    [2010, 2015, 2020, 2025, 2030, 2035, 2040].forEach(function (yr) {
      var t = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      t.textContent = "FY" + yr;
      svg.appendChild(t);
    });
    // shaded: seats in classes kept at the FY2027 level that the decline leaves open
    var top = seatsProj.map(function (d) { return x(d[0]) + "," + y(seatsLevel); });
    var bot = seatsProj.slice().reverse().map(function (d) { return x(d[0]) + "," + y(d[1]); });
    svg.appendChild(svgEl("path", { d: "M" + top.join(" L") + " L" + bot.join(" L") + " Z", fill: css("--line-education"), opacity: 0.16 }));
    svg.appendChild(svgEl("line", { x1: x(2027), x2: x(2040), y1: y(seatsLevel), y2: y(seatsLevel), stroke: css("--line-education"), "stroke-width": 2, "stroke-dasharray": "6,4" }));
    var hp = seatsHist.map(function (d) { return x(d[0]) + "," + y(d[1]); }).join(" L");
    svg.appendChild(svgEl("path", { d: "M" + hp, fill: "none", stroke: css("--line-total"), "stroke-width": 2.5, "stroke-linejoin": "round" }));
    var pp = [seatsHist[seatsHist.length - 1]].concat(seatsProj).map(function (d) { return x(d[0]) + "," + y(d[1]); }).join(" L");
    svg.appendChild(svgEl("path", { d: "M" + pp, fill: "none", stroke: css("--line-total"), "stroke-width": 2.5, "stroke-dasharray": "2,4", "stroke-linecap": "round" }));
    function lab(tx, ty, txt, anchor) {
      var t = svgEl("text", { x: tx, y: ty, class: "tick-label", "font-size": "11", "text-anchor": anchor || "start" });
      t.textContent = txt; svg.appendChild(t);
    }
    // the School Department's forecast, for comparison
    var cp = seatsCM.map(function (d) { return x(d[0]) + "," + y(d[1]); }).join(" L");
    svg.appendChild(svgEl("path", { d: "M" + cp, fill: "none", stroke: css("--line-levy-actual"), "stroke-width": 2.5, "stroke-dasharray": "7,5", "stroke-linecap": "round" }));
    // NESDEC's forecast as published, before the base case replaced its estimated births with counted ones
    var np = seatsNesdec.map(function (d) { return x(d[0]) + "," + y(d[1]); }).join(" L");
    svg.appendChild(svgEl("path", { d: "M" + np, fill: "none", stroke: css("--line-ref"), "stroke-width": 2, "stroke-dasharray": "4,4", "stroke-linecap": "round" }));
    var nl = seatsNesdec[seatsNesdec.length - 1];
    svg.appendChild(svgEl("circle", { cx: x(nl[0]), cy: y(nl[1]), r: 3.5, fill: css("--line-ref") }));
    lab(x(nl[0]) + 8, y(nl[1]) - 8, "NESDEC as published, " + nl[1].toLocaleString("en-US"));
    var cl = seatsCM[seatsCM.length - 1];
    svg.appendChild(svgEl("circle", { cx: x(cl[0]), cy: y(cl[1]), r: 4, fill: css("--line-levy-actual") }));
    var pk = seatsHist.filter(function (d) { return d[0] === 2019; })[0];
    svg.appendChild(svgEl("circle", { cx: x(pk[0]), cy: y(pk[1]), r: 4, fill: css("--line-total") }));
    lab(x(pk[0]), y(pk[1]) - 10, "FY2019 peak, " + pk[1].toLocaleString("en-US"), "middle");
    lab(x(2040) + 8, y(seatsLevel) + 4, "Staffed for, FY2027");
    lab(x(2040) + 8, y(seatsLevel) + 18, seatsLevel.toLocaleString("en-US") + " students");
    var last = seatsProj[seatsProj.length - 1];
    lab(x(2040) + 8, y(last[1]) + 4, "Projected, " + last[1].toLocaleString("en-US"));
    lab(x(2035.5), y((seatsLevel + 6187) / 2) + 4, "Empty seats", "middle");
    lab(x(cl[0]), y(cl[1]) - 10, "School Department's forecast, " + cl[1].toLocaleString("en-US"), "middle");
    var tooltip = document.getElementById("seats-tooltip"), wrap = document.getElementById("seats-wrap");
    var all = seatsHist.concat(seatsProj);
    var cross = svgEl("line", { y1: m.top, y2: m.top + ih, stroke: css("--ink-faint"), "stroke-width": 1, "stroke-dasharray": "3,3", opacity: 0 });
    svg.appendChild(cross);
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" });
    svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var rect = svg.getBoundingClientRect(), mx = (e.clientX - rect.left) * (W / rect.width);
      var yr = Math.max(y0, Math.min(y1, Math.round(y0 + (mx - m.left) / iw * (y1 - y0))));
      var d = all.filter(function (q) { return q[0] === yr; })[0];
      if (!d) return;
      cross.setAttribute("x1", x(yr)); cross.setAttribute("x2", x(yr)); cross.setAttribute("opacity", 1);
      var h = '<div class="tt-title">FY' + yr + (yr > 2026 ? ", projected" : "") + '</div><div class="tt-row"><span>Enrollment</span><span>' + d[1].toLocaleString("en-US") + '</span></div>';
      var rr = seatsRoom.filter(function (q) { return q[0] === yr; })[0];
      var cm = seatsCM.filter(function (q) { return q[0] === yr; })[0];
      if (cm && yr > 2027) h += '<div class="tt-row"><span>School Department\'s forecast</span><span>' + cm[1].toLocaleString("en-US") + '</span></div>';
      var ns = seatsNesdec.filter(function (q) { return q[0] === yr; })[0];
      if (ns && yr > 2027) h += '<div class="tt-row"><span>NESDEC as published</span><span>' + ns[1].toLocaleString("en-US") + '</span></div>';
      if (rr && rr[1] > 0) h += '<div class="tt-row"><span>Empty seats</span><span>' + (seatsLevel - d[1]).toLocaleString("en-US") + '</span></div><div class="tt-row"><span>Homes beyond the trend that fill them</span><span>about ' + (Math.round(rr[1] / 100) * 100).toLocaleString("en-US") + '</span></div>';
      tooltip.innerHTML = h; tooltip.style.opacity = 1;
      var wrect = wrap.getBoundingClientRect();
      tooltip.style.left = Math.min(e.clientX - wrect.left + 14, wrect.width - 280) + "px";
      tooltip.style.top = (e.clientY - wrect.top - 10) + "px";
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; cross.setAttribute("opacity", 0); });
    var legend = document.getElementById("seats-legend");
    legend.innerHTML = "";
    [["Enrollment, actual then projected (NESDEC, the base case)", "--line-total"], ["School Department's forecast (Cropper-McKibben, 2023)", "--line-levy-actual"], ["NESDEC's forecast as published (2023), before the births update", "--line-ref"], ["FY2027 level, what the schools are staffed for", "--line-education"]].forEach(function (item) {
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(item[1]);
      el.appendChild(sw); var t = document.createElement("span"); t.textContent = item[0]; el.appendChild(t);
      legend.appendChild(el);
    });
    var tbl = document.getElementById("seats-table");
    if (tbl) {
      var t = '<table><thead><tr><th>Year</th><th>Enrollment (base case)</th><th>School Department\'s forecast</th><th>NESDEC as published</th><th>Empty seats vs FY2027</th><th>Homes beyond trend that fill them</th></tr></thead><tbody>';
      all.forEach(function (d) {
        var rr = seatsRoom.filter(function (q) { return q[0] === d[0]; })[0];
        var cm = seatsCM.filter(function (q) { return q[0] === d[0]; })[0];
        var ns = seatsNesdec.filter(function (q) { return q[0] === d[0]; })[0];
        t += '<tr><td>FY' + d[0] + (d[0] > 2026 ? " (projected)" : "") + '</td><td>' + d[1].toLocaleString("en-US") + '</td><td>' + (cm ? cm[1].toLocaleString("en-US") : "") + '</td><td>' + (ns ? ns[1].toLocaleString("en-US") : "") + '</td><td>' + (rr ? (seatsLevel - d[1]).toLocaleString("en-US") : "") + '</td><td>' + (rr ? rr[1].toLocaleString("en-US") : "") + '</td></tr>';
      });
      tbl.innerHTML = t + '</tbody></table>';
    }
  }

  /* ---------------- NET PER HOME, BOTH WAYS (added 2026-10-06) ----------------
     Tax at FY2025 values and the FY2026 rate; Town services $866 and students at 0.244 a
     home, costing $16,975 (usual estimate) or $7,758 (filling empty seats, with special education), FY2027. */
  var homeNetData = [
    { label: "Apartment, building of 9+ units", value: "$434,000", tax: 4447 },
    { label: "Typical new home, apartments and condominiums", value: "$585,000", tax: 5990 },
    { label: "Apartment, building of 4–8 units", value: "$673,000", tax: 6890 },
    { label: "Average new-construction project", value: "$794,000", tax: 8134 },
    { label: "Condominium", value: "$1,176,000", tax: 12042 }
  ];
  var homeNetKinds = [["usual", "Usual estimate: new staff for every student", "--line-benefits", 16975], ["fill", "Children fill empty seats", "--line-education", 7758]];
  function drawHomeNetChart() {
    var svg = document.getElementById("hnet-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, rowH = 62;
    var m = { top: 26, right: 70, bottom: 34, left: 250 };
    var H = m.top + m.bottom + rowH * homeNetData.length;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var iw = W - m.left - m.right, vMin = -2000, vMax = 12000;
    function x(v) { return m.left + (v - vMin) / (vMax - vMin) * iw; }
    for (var gv = -2000; gv <= vMax; gv += 2000) {
      svg.appendChild(svgEl("line", { x1: x(gv), x2: x(gv), y1: m.top - 6, y2: H - m.bottom, class: "gridline" }));
      var gl = svgEl("text", { x: x(gv), y: H - m.bottom + 18, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      gl.textContent = (gv < 0 ? "−$" : gv > 0 ? "+$" : "$") + Math.abs(gv / 1000) + (gv ? "K" : "");
      svg.appendChild(gl);
    }
    svg.appendChild(svgEl("line", { x1: x(0), x2: x(0), y1: m.top - 14, y2: H - m.bottom, stroke: css("--ink"), "stroke-width": 1.5 }));
    var l0 = svgEl("text", { x: x(0) - 6, y: m.top - 12, class: "tick-label", "text-anchor": "end", "font-size": "11" }); l0.textContent = "costs the Town"; svg.appendChild(l0);
    var l1 = svgEl("text", { x: x(0) + 6, y: m.top - 12, class: "tick-label", "font-size": "11" }); l1.textContent = "pays for itself"; svg.appendChild(l1);
    var tooltip = document.getElementById("hnet-tooltip"), wrap = document.getElementById("hnet-wrap");
    homeNetData.forEach(function (d, i) {
      var cy = m.top + i * rowH + rowH / 2;
      var a = svgEl("text", { x: m.left - 12, y: cy - 3, class: "tick-label", "text-anchor": "end", "font-size": "12" }); a.textContent = d.label; svg.appendChild(a);
      var b = svgEl("text", { x: m.left - 12, y: cy + 13, class: "tick-label", "text-anchor": "end", "font-size": "11" }); b.textContent = d.value + " · tax $" + d.tax.toLocaleString("en-US"); svg.appendChild(b);
      homeNetKinds.forEach(function (k, j) {
        var v = Math.round(d.tax - 866 - 0.244 * k[3]);
        var by = cy - 19 + j * 20;
        var x0 = x(Math.min(0, v)), w = Math.max(Math.abs(x(v) - x(0)), 1);
        var r = svgEl("rect", { x: x0, y: by, width: w, height: 17, rx: 2, fill: css(k[2]) });
        svg.appendChild(r);
        var t = svgEl("text", { x: v < 0 ? x(v) - 6 : x(v) + 6, y: by + 13, class: "tick-label", "font-size": "11", "text-anchor": v < 0 ? "end" : "start" });
        t.textContent = (v < 0 ? "−$" : "+$") + Math.abs(v).toLocaleString("en-US");
        svg.appendChild(t);
        r.addEventListener("mousemove", function (e) {
          tooltip.innerHTML = '<div class="tt-title">' + d.label + ' (' + d.value + ')</div>' +
            '<div class="tt-row"><span>Property tax</span><span>$' + d.tax.toLocaleString("en-US") + '</span></div>' +
            '<div class="tt-row"><span>Town services</span><span>−$866</span></div>' +
            '<div class="tt-row"><span>Schools (0.244 children × $' + k[3].toLocaleString("en-US") + ')</span><span>−$' + Math.round(0.244 * k[3]).toLocaleString("en-US") + '</span></div>' +
            '<div class="tt-row"><span>' + k[1] + '</span><span>' + t.textContent + ' a year</span></div>';
          tooltip.style.opacity = 1;
          var wrect = wrap.getBoundingClientRect();
          tooltip.style.left = Math.min(e.clientX - wrect.left + 14, wrect.width - 300) + "px";
          tooltip.style.top = (e.clientY - wrect.top - 10) + "px";
        });
        r.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
      });
    });
    var legend = document.getElementById("hnet-legend");
    legend.innerHTML = "";
    homeNetKinds.forEach(function (k) {
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(k[2]);
      el.appendChild(sw); var t = document.createElement("span"); t.textContent = k[1]; el.appendChild(t);
      legend.appendChild(el);
    });
    var tbl = document.getElementById("hnet-table");
    if (tbl) {
      var t = '<table><thead><tr><th>Type of home</th><th>Assessed value</th><th>Property tax</th><th>Net, usual estimate</th><th>Net, children fill empty seats</th></tr></thead><tbody>';
      homeNetData.forEach(function (d) {
        var u = Math.round(d.tax - 866 - 0.244 * 16837), f = Math.round(d.tax - 866 - 0.244 * 2477);
        t += '<tr><td>' + d.label + '</td><td>' + d.value + '</td><td>$' + d.tax.toLocaleString("en-US") + '</td><td>' + (u < 0 ? "−$" : "+$") + Math.abs(u).toLocaleString("en-US") + '</td><td>+$' + f.toLocaleString("en-US") + '</td></tr>';
      });
      tbl.innerHTML = t + '</tbody></table>';
    }
  }

  function drawHousingFillChart() {
    // simplified 2026-10-06: two cases, vertical columns
    var svg = document.getElementById("hfill-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 340;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var m = { top: 30, right: 30, bottom: 64, left: 70 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom, vMax = 40;
    function y(v) { return m.top + ih - v / vMax * ih; }
    for (var gv = 0; gv <= vMax; gv += 10) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(gv), y2: y(gv), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 10, y: y(gv) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      gl.textContent = "$" + gv + "M"; svg.appendChild(gl);
    }
    var cases = housingFillData.slice(0, 2);
    var hr = function (n) { return "About " + (Math.round(n / 100) * 100).toLocaleString("en-US"); };
    svg.setAttribute("aria-label", "Bar chart of what extra homes add to the FY2040 budget after their costs. " + hr(cases[0].homes) +
      " extra homes, as many as the empty seats hold, add $" + cases[0].staffed.toFixed(1) + " million a year under the usual estimate and $" +
      cases[0].fill.toFixed(1) + " million if their children fill empty seats. " + hr(cases[1].homes) + " extra homes, more than the seats hold, add $" +
      cases[1].staffed.toFixed(1) + " million and $" + cases[1].fill.toFixed(1) + " million.");
    var kinds = [["staffed", "Usual estimate: new staff for every student", "--line-benefits"], ["fill", "Children fill empty seats", "--line-education"]];
    var groupW = iw / cases.length, barW = 110;
    cases.forEach(function (d, i) {
      var cx = m.left + groupW * (i + 0.5);
      kinds.forEach(function (k, j) {
        var v = d[k[0]], bx = cx - barW - 6 + j * (barW + 12);
        svg.appendChild(svgEl("rect", { x: bx, y: y(v), width: barW, height: y(0) - y(v), rx: 2, fill: css(k[2]) }));
        var t = svgEl("text", { x: bx + barW / 2, y: y(v) - 8, class: "tick-label", "text-anchor": "middle", "font-size": "13", "font-weight": "600" });
        t.textContent = "+$" + v.toFixed(1) + "M"; svg.appendChild(t);
      });
      var a = svgEl("text", { x: cx, y: H - m.bottom + 24, class: "tick-label", "text-anchor": "middle", "font-size": "13", "font-weight": "600" });
      a.textContent = "About " + (Math.round(d.homes / 100) * 100).toLocaleString("en-US") + " extra homes"; svg.appendChild(a);
      var b = svgEl("text", { x: cx, y: H - m.bottom + 42, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      b.textContent = i === 0 ? "about as many as the empty seats hold" : "more than the empty seats hold"; svg.appendChild(b);
    });
    var legend = document.getElementById("hfill-legend");
    legend.innerHTML = "";
    kinds.forEach(function (k) {
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(k[2]);
      el.appendChild(sw); var t = document.createElement("span"); t.textContent = k[1]; el.appendChild(t);
      legend.appendChild(el);
    });
  }


  // Homes that fill the seats opened by the decline, at three children-per-home rates.
  // seatsRoom is in homes at the forecast's average (seatsSPH); convert back to students first.
  var seatsSPH = 0.2442;
  var seatsRates = [
    [0.11, "0.11 children a home (the Town's figure for recent apartments)", "--line-benefits"],
    [seatsSPH, seatsSPH.toFixed(2) + " (the forecast's average new home)", "--line-education"],
    [0.56, "0.56 (family-sized rentals)", "--line-levy-actual"]
  ];
  function drawSeatsHomesChart() {
    var svg = document.getElementById("shomes-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 400;
    var m = { top: 20, right: 190, bottom: 40, left: 64 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var y0 = 2027, y1 = 2040, vMax = 11000;
    function x(yr) { return m.left + (yr - y0) / (y1 - y0) * iw; }
    function y(v) { return m.top + ih - v / vMax * ih; }
    for (var gv = 0; gv <= vMax; gv += 2000) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(gv), y2: y(gv), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 10, y: y(gv) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      gl.textContent = gv.toLocaleString("en-US"); svg.appendChild(gl);
    }
    [2027, 2030, 2035, 2040].forEach(function (yr) {
      var t = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      t.textContent = "FY" + yr; svg.appendChild(t);
    });
    var students = seatsRoom.map(function (d) { return [d[0], d[1] * seatsSPH]; });
    var base = {}; seatsBase.forEach(function (d) { base[d[0]] = d[1]; });
    // the base case's own new homes, already in the enrollment forecast
    var bt = seatsBase.map(function (d) { return x(d[0]) + "," + y(d[1]); });
    svg.appendChild(svgEl("path", { d: "M" + x(y0) + "," + y(0) + " L" + bt.join(" L") + " L" + x(y1) + "," + y(0) + " Z", fill: css("--line-ref"), opacity: 0.35 }));
    var bl = svgEl("text", { x: x(2036.5), y: y(base[2037] / 2) + 4, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
    bl.textContent = "Base case homes"; svg.appendChild(bl);
    seatsRates.forEach(function (r) {
      var pts = students.map(function (d) { return x(d[0]) + "," + y(base[d[0]] + d[1] / r[0]); }).join(" L");
      svg.appendChild(svgEl("path", { d: "M" + pts, fill: "none", stroke: css(r[2]), "stroke-width": r[0] === seatsSPH ? 3 : 2, "stroke-linejoin": "round" }));
      var last = base[y1] + students[students.length - 1][1] / r[0];
      svg.appendChild(svgEl("circle", { cx: x(y1), cy: y(last), r: 4, fill: css(r[2]) }));
      var t = svgEl("text", { x: x(y1) + 9, y: y(last) + 4, class: "tick-label", "font-size": "11" });
      t.textContent = "about " + (Math.round(last / 100) * 100).toLocaleString("en-US") + " in total";
      svg.appendChild(t);
    });
    var tooltip = document.getElementById("shomes-tooltip"), wrap = document.getElementById("shomes-wrap");
    var cross = svgEl("line", { y1: m.top, y2: m.top + ih, stroke: css("--ink-faint"), "stroke-width": 1, "stroke-dasharray": "3,3", opacity: 0 });
    svg.appendChild(cross);
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" });
    svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var rect = svg.getBoundingClientRect(), mx = (e.clientX - rect.left) * (W / rect.width);
      var i = Math.max(0, Math.min(students.length - 1, Math.round((mx - m.left) / iw * (y1 - y0))));
      var d = students[i];
      cross.setAttribute("x1", x(d[0])); cross.setAttribute("x2", x(d[0])); cross.setAttribute("opacity", 1);
      var h = '<div class="tt-title">FY' + d[0] + ': ' + Math.round(d[1]).toLocaleString("en-US") + ' open seats</div>' +
        '<div class="tt-row"><span>Base case homes since FY2027</span><span>' + base[d[0]].toLocaleString("en-US") + '</span></div>';
      seatsRates.slice().reverse().forEach(function (r) {
        h += '<div class="tt-row"><span>Total at ' + r[0].toFixed(2) + ' children a home</span><span>' + (Math.round((base[d[0]] + d[1] / r[0]) / 10) * 10).toLocaleString("en-US") + '</span></div>';
      });
      tooltip.innerHTML = h; tooltip.style.opacity = 1;
      var wrect = wrap.getBoundingClientRect();
      tooltip.style.left = Math.min(e.clientX - wrect.left + 14, wrect.width - 300) + "px";
      tooltip.style.top = (e.clientY - wrect.top - 10) + "px";
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; cross.setAttribute("opacity", 0); });
    var legend = document.getElementById("shomes-legend");
    legend.innerHTML = "";
    [[0, "Base case: about 166 a year plus the approved Chestnut Hill plan", "--line-ref"]].concat(seatsRates).forEach(function (r) {
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(r[2]);
      el.appendChild(sw); var t = document.createElement("span"); t.textContent = r[0] ? "Plus homes filling open seats, " + r[1] : r[1]; el.appendChild(t);
      legend.appendChild(el);
    });
    var tbl = document.getElementById("shomes-table");
    if (tbl) {
      var t = '<table><thead><tr><th>Year</th><th>Open seats</th><th>Base case homes</th>' + seatsRates.map(function (r) { return '<th>Total at ' + r[0].toFixed(2) + '</th>'; }).join("") + '</tr></thead><tbody>';
      students.forEach(function (d) {
        t += '<tr><td>FY' + d[0] + '</td><td>' + Math.round(d[1]).toLocaleString("en-US") + '</td><td>' + base[d[0]].toLocaleString("en-US") + '</td>' + seatsRates.map(function (r) { return '<td>' + Math.round(base[d[0]] + d[1] / r[0]).toLocaleString("en-US") + '</td>'; }).join("") + '</tr>';
      });
      tbl.innerHTML = t + '</tbody></table>';
    }
  }


  /* ---------------- DATA TABLES for charts drawn without one (added 2026-10-07) ---- */
  function fillTable(id, head, rows) {
    var el = document.getElementById(id); if (!el) return;
    var t = '<table class="data-table"><thead><tr>' + head.map(function (h) { return '<th scope="col">' + h + '</th>'; }).join("") +
      '</tr></thead><tbody>';
    rows.forEach(function (r) { t += '<tr>' + r.map(function (c, i) { return i === 0 ? '<th scope="row">' + c + '</th>' : '<td>' + c + '</td>'; }).join("") + '</tr>'; });
    el.innerHTML = t + '</tbody></table>';
  }
  function fillExtraTables() {
    var M = function (v) { return "$" + (v / 1e6).toFixed(1) + "M"; };
    var base = lineData[0].levy_limit_allowed_raw;
    fillTable("waterfall-table", ["Year", "FY2005 base", "2.5% a year", "New growth", "Overrides", "Levy limit"],
      lineData.map(function (d) {
        return ["FY" + d.fy, M(base), M(d.cap_only_25pct_raw - base), M(d.no_override_raw - d.cap_only_25pct_raw),
                M(d.levy_limit_allowed_raw - d.no_override_raw), M(d.levy_limit_allowed_raw)];
      }));
    var yrs = [];
    pensionData.concat(opebData).forEach(function (p) { if (yrs.indexOf(p[0]) < 0) yrs.push(p[0]); });
    yrs.sort();
    var find = function (arr, y) { var r = arr.filter(function (p) { return p[0] === y; })[0]; return r ? M(r[1]) : "&ndash;"; };
    fillTable("liab-table", ["Year", "Net pension liability (Town share)", "Net OPEB liability"],
      yrs.map(function (y) { return [y, find(pensionData, y), find(opebData, y)]; }));
    var cyears = ctrlSeries[0].data.map(function (p) { return p[0]; });
    fillTable("control-table", ["Year"].concat(ctrlSeries.map(function (s) { return s.short; })),
      cyears.map(function (y) {
        return ["FY" + y].concat(ctrlSeries.map(function (s) { var r = s.data.filter(function (p) { return p[0] === y; })[0]; return r ? r[1].toFixed(1) : "&ndash;"; }));
      }));
    fillTable("decisions-table", ["Assumption", "Change in FY2040 balance", "Who sets it"],
      decisionsData.map(function (d) { return [d.label, (d.v >= 0 ? "+" : "&minus;") + "$" + Math.abs(d.v).toFixed(1) + "M", decisionsKinds[d.kind][0]]; }));
    fillTable("hfill-table", ["Extra homes by FY2040", "Usual estimate: new staff for every student", "Children fill empty seats"],
      housingFillData.slice(0, 2).map(function (d) { return [d.homes.toLocaleString("en-US"), "+$" + d.staffed.toFixed(1) + "M", "+$" + d.fill.toFixed(1) + "M"]; }));
  }


  /* ================= SITE CHARTS (added 2026-10-07) =================
     Drawn from window.SITE_DATA, which scripts/build_pages.py injects from
     output/site_data.json (scripts/site_facts.js), so their numbers come from
     the model at build time rather than being typed in. Each no-ops when its
     <svg> or SITE_DATA is absent. */
  var SD = window.SITE_DATA || null;
  var KIND = {
    decide: ["Brookline decides", "--pine"],
    growth: ["Growth (zoning, permitting)", "--line-no-override"],
    outside: ["Set mostly outside Brookline", "--line-ref"],
    past: ["Past obligations", "--line-levy-actual"],
    other: ["Other", "--wf-base"]
  };
  var fmtM1 = function (v) { return (v < 0 ? "−" : "") + "$" + Math.abs(v).toFixed(1) + "M"; };
  var fmtS1 = function (v) { return (v >= 0 ? "+" : "−") + "$" + Math.abs(v).toFixed(1) + "M"; };
  function kindLegend(id, kinds) {
    var legend = document.getElementById(id); if (!legend) return;
    legend.innerHTML = "";
    kinds.forEach(function (k) {
      var el = document.createElement("div"); el.className = "legend-item";
      var sw = document.createElement("span"); sw.className = "legend-swatch"; sw.style.background = css(KIND[k][1]);
      sw.style.height = "10px";
      el.appendChild(sw); var t = document.createElement("span"); t.textContent = KIND[k][0]; el.appendChild(t);
      legend.appendChild(el);
    });
  }
  function tipAt(tooltip, wrap, e, html) {
    tooltip.innerHTML = html; tooltip.style.opacity = 1;
    var wr = wrap.getBoundingClientRect();
    tooltip.style.left = (e.clientX - wr.left + 14) + "px"; tooltip.style.top = (e.clientY - wr.top - 10) + "px";
  }

  // ---- OUTLOOK: room each year, with and without the May 2026 override
  function drawOutlookChart() {
    var svg = document.getElementById("outlook-svg");
    if (!svg || !SD) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var W = 900, H = 380, m = { top: 24, right: 150, bottom: 40, left: 56 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var A = SD.room, B = SD.roomOverride, y0 = A[0][0], y1 = A[A.length - 1][0];
    var all = A.concat(B).map(function (d) { return d[1]; });
    var lo = Math.floor(Math.min.apply(null, all) / 10) * 10, hi = Math.ceil(Math.max.apply(null, all) / 10) * 10;
    var x = function (yr) { return m.left + (yr - y0) / (y1 - y0) * iw; };
    var y = function (v) { return m.top + (hi - v) / (hi - lo) * ih; };
    for (var g = lo; g <= hi; g += 10) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(g), y2: y(g), class: "gridline", stroke: g === 0 ? css("--ink-faint") : null }));
      var t = svgEl("text", { x: m.left - 8, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" });
      t.textContent = (g < 0 ? "−$" : "$") + Math.abs(g) + "M"; svg.appendChild(t);
    }
    for (var yr = y0; yr <= y1; yr += 2) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
      tl.textContent = "FY" + String(yr).slice(2); svg.appendChild(tl);
    }
    svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(0), y2: y(0), stroke: css("--ink-muted"), "stroke-width": 1.2 }));
    function line(D, color, dash, label) {
      var d = "M" + D.map(function (p) { return x(p[0]) + "," + y(p[1]); }).join(" L");
      var a = { d: d, fill: "none", stroke: css(color), "stroke-width": 2.5, "stroke-linejoin": "round" };
      if (dash) a["stroke-dasharray"] = "6,5";
      svg.appendChild(svgEl("path", a));
      var last = D[D.length - 1];
      var lt = svgEl("text", { x: x(last[0]) + 8, y: y(last[1]) + 4, class: "tick-label", "font-size": "11.5", fill: css("--ink") });
      lt.textContent = label + " " + fmtS1(last[1]); svg.appendChild(lt);
    }
    line(B, "--line-levy", true, "Without the override");
    line(A, "--pine", false, "Base case");
    var tooltip = document.getElementById("outlook-tooltip"), wrap = document.getElementById("outlook-wrap");
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" }); svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var r = svg.getBoundingClientRect(), mx = (e.clientX - r.left) * (W / r.width);
      var i = Math.max(0, Math.min(A.length - 1, Math.round((mx - m.left) / iw * (y1 - y0))));
      tipAt(tooltip, wrap, e, '<div class="tt-title">FY' + A[i][0] + '</div><div class="tt-row"><span>Base case</span><span>' + fmtS1(A[i][1]) +
        '</span></div><div class="tt-row"><span>Without the override</span><span>' + fmtS1(B[i][1]) + '</span></div>');
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    var maxA = A.slice(5, 13).reduce(function (a, b) { return Math.max(a, b[1]); }, -1e9), minA = A.slice(5, 13).reduce(function (a, b) { return Math.min(a, b[1]); }, 1e9);
    svg.setAttribute("aria-label", "Line chart of revenue minus spending each year, FY" + y0 + " to FY" + y1 + ". In the base case it is near zero in FY2026 and FY2027, between " +
      fmtM1(minA) + " and " + fmtM1(maxA) + " a year from FY2031 to FY2038, and " + fmtS1(A[A.length - 1][1]) + " in FY" + y1 + ". Without the May 2026 override's revenue it is negative from FY" + (B.filter(function (d) { return d[1] < 0; })[0] || [y1])[0] + " and reaches " +
      fmtS1(B[B.length - 1][1]) + " by FY" + y1 + ".");
    var leg = document.getElementById("outlook-legend");
    if (leg) leg.innerHTML = '<div class="legend-item"><span class="legend-swatch" style="background:' + css("--pine") + '"></span><span>Base case, with the override</span></div>' +
      '<div class="legend-item"><span class="legend-swatch" style="background:' + css("--line-levy") + '"></span><span>Without the override’s revenue</span></div>';
    fillTable("outlook-table", ["Year", "Base case", "Without the override"], A.map(function (d, i) { return ["FY" + d[0], fmtS1(d[1]), fmtS1(B[i][1])]; }));
  }

  // ---- WHAT DECIDES: FY2040 and FY2035, on one scale, colored by who decides (FY2035 replaced the
  // 15-year total on 2026-10-15: same units as FY2040, and the pair shows timing; the total stays in the table)
  function drawDecideChart() {
    var svg = document.getElementById("decide-svg");
    if (!svg || !SD) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var rows = SD.decisions, rowH = 32, W = 900;
    var m = { top: 48, bottom: 12, left: 330 }, gap = 40, pw = (W - m.left - gap - 10) / 2;
    var H = m.top + m.bottom + rowH * rows.length;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var mx = Math.max.apply(null, rows.map(function (r) { return Math.max(Math.abs(r.fy40), Math.abs(r.fy35)); }));
    var panels = [{ x0: m.left, key: "fy40", max: mx, title: "FY2040, per year" }, { x0: m.left + pw + gap, key: "fy35", max: mx, title: "FY2035, per year" }];
    panels.forEach(function (p) {
      var cx = p.x0 + pw / 2;
      var tt = svgEl("text", { x: cx, y: 17, class: "tick-label", "text-anchor": "middle", "font-size": "14", "font-weight": "600", fill: css("--ink") });
      tt.textContent = p.title; svg.appendChild(tt);
      var w1 = svgEl("text", { x: p.x0, y: 37, class: "tick-label", "font-size": "12" }); w1.textContent = "← worse"; svg.appendChild(w1);
      var w2 = svgEl("text", { x: p.x0 + pw, y: 37, class: "tick-label", "font-size": "12", "text-anchor": "end" }); w2.textContent = "better →"; svg.appendChild(w2);
      svg.appendChild(svgEl("line", { x1: cx, x2: cx, y1: m.top - 4, y2: H - m.bottom, stroke: css("--ink-muted"), "stroke-width": 1 }));
    });
    var tooltip = document.getElementById("decide-tooltip"), wrap = document.getElementById("decide-wrap");
    rows.forEach(function (r, i) {
      var cy = m.top + i * rowH + rowH / 2;
      var lab = svgEl("text", { x: m.left - 12, y: cy + 5, "text-anchor": "end", "font-size": "14", fill: css("--ink") });
      lab.textContent = r.label.length > 46 ? r.label.slice(0, 44) + "…" : r.label; svg.appendChild(lab);
      panels.forEach(function (p) {
        var v = r[p.key], cx = p.x0 + pw / 2, len = Math.abs(v) / p.max * (pw / 2 - 62);
        var bx = v >= 0 ? cx : cx - len;
        svg.appendChild(svgEl("rect", { x: bx, y: cy - 9, width: Math.max(len, 1), height: 18, rx: 3, fill: css(KIND[r.kind][1]) }));
        var vt = svgEl("text", { x: v >= 0 ? cx + len + 5 : cx - len - 5, y: cy + 5, "text-anchor": v >= 0 ? "start" : "end", class: "tick-label", "font-size": "13" });
        vt.textContent = fmtS1(v); svg.appendChild(vt);
      });
      var hit = svgEl("rect", { x: 0, y: cy - rowH / 2, width: W, height: rowH, fill: "transparent" }); svg.appendChild(hit);
      hit.addEventListener("mousemove", function (e) {
        tipAt(tooltip, wrap, e, '<div class="tt-title">' + r.label + '</div><div class="tt-row"><span>' + r.base + '</span></div><div class="tt-row"><span>FY2035</span><span>' + fmtS1(r.fy35) +
          '</span></div><div class="tt-row"><span>FY2040</span><span>' + fmtS1(r.fy40) +
          '</span></div><div class="tt-row"><span>FY2026–40 total</span><span>' + fmtS1(r.total) + '</span></div><div class="tt-row"><span>' + KIND[r.kind][0] + '</span></div>');
      });
      hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    });
    kindLegend("decide-legend", ["decide", "outside", "growth"]);
    svg.setAttribute("aria-label", "Bar chart of how much each assumption changes the budget's balance in FY2040 and in FY2035, per year. " +
      rows.map(function (r) { return r.label + ", " + fmtS1(r.fy40) + " in FY2040 and " + fmtS1(r.fy35) + " in FY2035 (" + KIND[r.kind][0].toLowerCase() + ")"; }).join("; ") + ".");
    fillTable("decide-table", ["Assumption", "Base case", "FY2035", "FY2040", "FY2026–40 total", "Who decides"],
      rows.map(function (r) { return [r.label, r.base.replace(/^base: /, ""), fmtS1(r.fy35), fmtS1(r.fy40), fmtS1(r.total), KIND[r.kind][0]]; }));
  }

  // ---- WHERE THE $177 MILLION WENT, by cause, colored by who sets it
  function drawCausesChart() {
    var svg = document.getElementById("causes-svg");
    if (!svg || !SD) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var rows = SD.causes, rowH = 34, W = 900, m = { top: 10, bottom: 10, left: 250, right: 130 };
    var H = m.top + m.bottom + rowH * rows.length;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var mx = Math.max.apply(null, rows.map(function (r) { return r.v; })), iw = W - m.left - m.right;
    var x0 = m.left + 14;
    var tooltip = document.getElementById("causes-tooltip"), wrap = document.getElementById("causes-wrap");
    svg.appendChild(svgEl("line", { x1: x0, x2: x0, y1: m.top, y2: H - m.bottom, stroke: css("--ink-muted") }));
    rows.forEach(function (r, i) {
      var cy = m.top + i * rowH + rowH / 2, len = Math.abs(r.v) / mx * (iw - 20);
      var lab = svgEl("text", { x: m.left - 6, y: cy + 4, "text-anchor": "end", "font-size": "12.5", fill: css("--ink") }); lab.textContent = r.label; svg.appendChild(lab);
      svg.appendChild(svgEl("rect", { x: r.v >= 0 ? x0 : x0 - len, y: cy - 10, width: Math.max(len, 1.5), height: 20, rx: 3, fill: css(KIND[r.kind][1]) }));
      var vt = svgEl("text", { x: x0 + Math.max(len, 1.5) + 8, y: cy + 4, class: "tick-label", "font-size": "11.5" });
      vt.textContent = fmtM1(r.v) + " · " + Math.round(r.v / SD.causesTotal * 100) + "%"; svg.appendChild(vt);
      var hit = svgEl("rect", { x: 0, y: cy - rowH / 2, width: W, height: rowH, fill: "transparent" }); svg.appendChild(hit);
      hit.addEventListener("mousemove", function (e) {
        tipAt(tooltip, wrap, e, '<div class="tt-title">' + r.label + ' · ' + fmtM1(r.v) + '</div>' +
          r.parts.map(function (p) { return '<div class="tt-row"><span>' + p[0] + '</span><span>' + fmtM1(p[1]) + '</span></div>'; }).join(""));
      });
      hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    });
    kindLegend("causes-legend", ["decide", "outside", "past", "growth", "other"]);
    svg.setAttribute("aria-label", "Bar chart of the " + fmtM1(SD.causesTotal) + " increase in annual General Fund spending from FY2011 to FY2025, by cause: " +
      rows.map(function (r) { return r.label + " " + fmtM1(r.v) + " (" + Math.round(r.v / SD.causesTotal * 100) + "%)"; }).join(", ") + ".");
    var trs = [];
    rows.forEach(function (r) { trs.push(["<strong>" + r.label + "</strong>", "<strong>" + fmtM1(r.v) + "</strong>", KIND[r.kind][0]]);
      r.parts.forEach(function (p) { trs.push(["&nbsp;&nbsp;" + p[0], fmtM1(p[1]), ""]); }); });
    fillTable("causes-table", ["Cause", "Added to annual spending", "Who sets it"], trs);
  }

  // ---- ENROLLMENT FORECASTS' KEY ASSUMPTIONS: births, and enrollment per birth (in-migration)
  // Each forecast's enrollment per birth is measured against its own births assumption
  // (scripts/build_enrollment_workbook.py -> output/enrollment_assumptions.json).
  var EA_SERIES = [["actual", "Actual", "--line-total", ""], ["base", "Base case", "--line-total", "2,4"],
                   ["nesdec", "NESDEC", "--line-benefits", "4,4"], ["cm", "Cropper-McKibben (the schools' forecast)", "--line-levy-actual", "7,5"]];
  function drawEnrollAssumeChart() {
    var svg = document.getElementById("eassume-svg");
    if (!svg || !SD || !SD.enrollAssume) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var E = SD.enrollAssume, W = 900, H = 400, gap = 70, m = { top: 34, right: 16, bottom: 40, left: 52 };
    var pw = (W - m.left - m.right - gap) / 2, ih = H - m.top - m.bottom;
    var panels = [
      { key: "births", title: "Births to Brookline residents, by year", x0: 2005, x1: 2034, lo: 350, hi: 750, step: 100,
        fmt: function (v) { return Math.round(v).toLocaleString("en-US"); } },
      { key: "perBirth", title: "Students per birth (enrollment / 13 years of births)", x0: 2005, x1: 2040, lo: 0.7, hi: 1.0, step: 0.05,
        fmt: function (v) { return v.toFixed(2); } }
    ];
    panels.forEach(function (P, k) {
      var left = m.left + k * (pw + gap);
      var x = function (yr) { return left + (yr - P.x0) / (P.x1 - P.x0) * pw; };
      var y = function (v) { return m.top + (P.hi - v) / (P.hi - P.lo) * ih; };
      var t = svgEl("text", { x: left, y: 16, "font-size": "13", "font-weight": "600", fill: css("--ink") }); t.textContent = P.title; svg.appendChild(t);
      for (var g = P.lo; g <= P.hi + 1e-9; g += P.step) {
        svg.appendChild(svgEl("line", { x1: left, x2: left + pw, y1: y(g), y2: y(g), class: "gridline" }));
        var gl = svgEl("text", { x: left - 6, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); gl.textContent = P.fmt(g); svg.appendChild(gl);
      }
      for (var yr = P.x0; yr <= P.x1; yr += 5) {
        var tl = svgEl("text", { x: x(yr), y: m.top + ih + 20, class: "tick-label", "text-anchor": "middle", "font-size": "11" });
        tl.textContent = (k === 1 ? "FY" : "") + String(yr).slice(2); svg.appendChild(tl);
      }
      EA_SERIES.forEach(function (s) {
        var D = E[P.key][s[0]]; if (!D || !D.length) return;
        var a = { d: "M" + D.map(function (p) { return x(p[0]) + "," + y(p[1]); }).join(" L"), fill: "none", stroke: css(s[2]),
                  "stroke-width": s[0] === "actual" ? 2.5 : 2.2, "stroke-linejoin": "round", "stroke-linecap": "round" };
        if (s[3]) a["stroke-dasharray"] = s[3];
        svg.appendChild(svgEl("path", a));
      });
    });
    var leg = document.getElementById("eassume-legend");
    if (leg) leg.innerHTML = EA_SERIES.map(function (s) {
      return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(s[2]) + (s[3] ? ';opacity:.7' : '') + '"></span><span>' + s[1] + (s[3] ? " (dashed)" : "") + '</span></div>';
    }).join("");
    var last = function (key, s) { var D = E[key][s]; return D[D.length - 1]; };
    svg.setAttribute("aria-label", "Two line charts. Births: actual births fell from about 690 a year in 2008 to 13 to 422 in 2023, 443 in 2024 and 423 in 2025; " +
      "NESDEC estimated about 500 a year from 2023, Cropper-McKibben about 588 to 628, and the base case holds " + Math.round(last("births", "base")[1]) +
      ". Students per birth, each forecast against its own births: " + last("perBirth", "actual")[1].toFixed(2) + " in FY" + last("perBirth", "actual")[0] +
      ", rising to " + last("perBirth", "nesdec")[1].toFixed(2) + " (NESDEC) and " + last("perBirth", "cm")[1].toFixed(2) + " (Cropper-McKibben) by FY2034 and " +
      last("perBirth", "base")[1].toFixed(2) + " in the base case by FY2040.");
    var yrs = {}; ["births", "perBirth"].forEach(function (k) { EA_SERIES.forEach(function (s) { (E[k][s[0]] || []).forEach(function (p) { yrs[p[0]] = 1; }); }); });
    var rows = Object.keys(yrs).map(Number).sort(function (a, b) { return a - b; }).map(function (yr) {
      var get = function (k, s, f) { var p = (E[k][s] || []).filter(function (q) { return q[0] === yr; })[0]; return p ? f(p[1]) : ""; };
      var n0 = function (v) { return Math.round(v).toLocaleString("en-US"); }, n2 = function (v) { return v.toFixed(2); };
      return [String(yr), get("births", "actual", n0), get("births", "nesdec", n0), get("births", "cm", n0), get("births", "base", n0),
              get("perBirth", "actual", n2), get("perBirth", "nesdec", n2), get("perBirth", "cm", n2), get("perBirth", "base", n2)];
    });
    fillTable("eassume-table", ["Year", "Births, actual", "Births, NESDEC", "Births, Cropper-McKibben", "Births, base case",
      "Per birth, actual", "Per birth, NESDEC", "Per birth, Cropper-McKibben", "Per birth, base case"], rows);
  }

  // Births alone, actual against what each enrollment forecast assumes, with direct labels:
  // the earliest reading of school enrollment, for the forecast page's "what to watch".
  function drawBirthsWatchChart() {
    var svg = document.getElementById("births-watch-svg");
    if (!svg || !SD || !SD.enrollAssume) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var E = SD.enrollAssume.births, W = 900, H = 380, m = { top: 24, right: 200, bottom: 44, left: 60 }, x0 = 2005, x1 = 2034, lo = 300, hi = 750;
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var x = function (yr) { return m.left + (yr - x0) / (x1 - x0) * iw; }, y = function (v) { return m.top + (hi - v) / (hi - lo) * ih; };
    for (var g = lo; g <= hi; g += 100) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(g), y2: y(g), class: "gridline" }));
      var gl = svgEl("text", { x: m.left - 8, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); gl.textContent = g; svg.appendChild(gl);
    }
    for (var yr = 2005; yr <= x1; yr += 5) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tl.textContent = String(yr); svg.appendChild(tl);
    }
    var names = { actual: "Actual births", base: "Base case", nesdec: "NESDEC", cm: "School Department's forecast" }, ends = [];
    EA_SERIES.forEach(function (s) {
      var D = E[s[0]]; if (!D || !D.length) return;
      var a = { d: "M" + D.map(function (p) { return x(p[0]) + "," + y(p[1]); }).join(" L"), fill: "none", stroke: css(s[2]),
                "stroke-width": s[0] === "actual" ? 3.2 : 2.2, "stroke-linejoin": "round", "stroke-linecap": "round" };
      if (s[3]) a["stroke-dasharray"] = s[3];
      svg.appendChild(svgEl("path", a));
      var L = D[D.length - 1];
      ends.push({ x: x(L[0]), y: y(L[1]), col: css(s[2]), bold: s[0] === "actual", text: names[s[0]] + ", " + Math.round(L[1]) + (s[0] === "actual" ? " in " + L[0] : "") });
    });
    var act = E.actual[E.actual.length - 1];
    svg.appendChild(svgEl("circle", { cx: x(act[0]), cy: y(act[1]), r: 5, fill: css("--line-total") }));
    ends.sort(function (p, q) { return p.y - q.y; });
    ends.forEach(function (e, k) { e.ly = k ? Math.max(e.y, ends[k - 1].ly + 16) : e.y; });
    ends.forEach(function (e) {
      // the actual line ends mid-chart, so its label sits below the point rather than to its right
      var t = e.bold ? svgEl("text", { x: e.x, y: e.y + 24, "text-anchor": "middle", "font-size": "13", "font-weight": "700", fill: e.col })
                     : svgEl("text", { x: e.x + 10, y: e.ly + 4, "font-size": "12", fill: e.col });
      t.textContent = e.text; svg.appendChild(t);
    });
    var leg = document.getElementById("births-watch-legend");
    if (leg) leg.innerHTML = EA_SERIES.map(function (s) {
      return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(s[2]) + (s[3] ? ';opacity:.7' : '') + '"></span><span>' + names[s[0]] + (s[3] ? " (dashed)" : "") + '</span></div>';
    }).join("");
    var lastOf = function (k) { var D = E[k]; return Math.round(D[D.length - 1][1]); };
    svg.setAttribute("aria-label", "Line chart of births to Brookline residents, " + E.actual[0][0] + " to " + act[0] + ", and what each enrollment forecast assumes. Actual births fell from about 690 a year in 2008 to 13 to " +
      act[1] + " in " + act[0] + ". The base case holds " + lastOf("base") + " a year, NESDEC assumed about " + lastOf("nesdec") + ", and the School Department's forecast about " + lastOf("cm") + ".");
    var yrs = {}; EA_SERIES.forEach(function (s) { (E[s[0]] || []).forEach(function (p) { yrs[p[0]] = 1; }); });
    fillTable("births-watch-table", ["Year", "Actual", "Base case", "NESDEC", "School Department's forecast"],
      Object.keys(yrs).map(Number).sort(function (a, b) { return a - b; }).map(function (yr) {
        return [String(yr)].concat(["actual", "base", "nesdec", "cm"].map(function (k) { var p = (E[k] || []).filter(function (q) { return q[0] === yr; })[0]; return p ? String(Math.round(p[1])) : "&ndash;"; }));
      }));
  }

  // ---- BIRTHS BY TOWN GROUP, indexed to the 2005-09 average (families_by_town.py)
  var BT_SERIES = [["Brookline", "Brookline", "--line-total", ""], ["Neighboring cities and inner suburbs", "Neighboring cities and inner suburbs", "--line-benefits", "4,4"],
                   ["Family suburbs", "Family suburbs", "--line-levy-actual", "7,5"], ["Massachusetts", "Massachusetts", "--line-ref", "2,4"]];
  function drawBirthsTownsChart() {
    var svg = document.getElementById("birthstowns-svg");
    if (!svg || !SD || !SD.townFamilies) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var F = SD.townFamilies, W = 900, H = 360, m = { top: 20, right: 60, bottom: 40, left: 50 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom, x0 = 2005, x1 = 2023, lo = 60, hi = 110;
    var x = function (yr) { return m.left + (yr - x0) / (x1 - x0) * iw; }, y = function (v) { return m.top + (hi - v) / (hi - lo) * ih; };
    for (var g = lo; g <= hi; g += 10) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(g), y2: y(g), class: "gridline" }));
      var t = svgEl("text", { x: m.left - 8, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); t.textContent = g; svg.appendChild(t);
    }
    for (var yr = x0; yr <= x1; yr += 3) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tl.textContent = yr; svg.appendChild(tl);
    }
    BT_SERIES.forEach(function (s) {
      var D = F.birthsIndex[s[0]];
      var a = { d: "M" + D.map(function (p) { return x(p[0]) + "," + y(p[1]); }).join(" L"), fill: "none", stroke: css(s[2]),
                "stroke-width": s[0] === "Brookline" ? 2.8 : 2.2, "stroke-linejoin": "round" };
      if (s[3]) a["stroke-dasharray"] = s[3];
      svg.appendChild(svgEl("path", a));
      var last = D[D.length - 1], lt = svgEl("text", { x: x(last[0]) + 6, y: y(last[1]) + 4, class: "tick-label", "font-size": "11.5", fill: css("--ink") });
      lt.textContent = Math.round(last[1]); svg.appendChild(lt);
    });
    var leg = document.getElementById("birthstowns-legend");
    if (leg) leg.innerHTML = BT_SERIES.map(function (s) {
      return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(s[2]) + '"></span><span>' + s[1] + (s[3] ? " (dashed)" : "") + '</span></div>';
    }).join("");
    var avg = function (k, a, b) { var D = F.birthsIndex[k].filter(function (p) { return p[0] >= a && p[0] <= b; }); return D.reduce(function (t, p) { return t + p[1]; }, 0) / D.length; };
    svg.setAttribute("aria-label", "Line chart of births to residents, 2005 to 2023, indexed so each group's 2005 to 2009 average equals 100. Average for 2019 to 2023: " +
      BT_SERIES.map(function (s) { return s[1] + " " + Math.round(avg(s[0], 2019, 2023)); }).join(", ") + ".");
    fillTable("birthstowns-table", ["Year"].concat(BT_SERIES.map(function (s) { return s[1] + ", births (index)"; })),
      F.birthsRaw.Brookline.map(function (p, i) {
        return [String(p[0])].concat(BT_SERIES.map(function (s) {
          return F.birthsRaw[s[0]][i][1].toLocaleString("en-US") + " (" + Math.round(F.birthsIndex[s[0]][i][1]) + ")"; }));
      }));
  }

  // ---- KINDERGARTEN PER BIRTH against the share of homes that are family-sized (families_by_town.py)
  function drawKpbHousingChart() {
    var svg = document.getElementById("kpbhousing-svg");
    if (!svg || !SD || !SD.townFamilies) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var T = SD.townFamilies.towns, W = 900, H = 420, m = { top: 20, right: 30, bottom: 52, left: 60 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom, xl = 0.3, xh = 1.0, yl = 0.4, yh = 2.2;
    var x = function (v) { return m.left + (v - xl) / (xh - xl) * iw; }, y = function (v) { return m.top + (yh - v) / (yh - yl) * ih; };
    for (var g = 0.4; g <= yh + 1e-9; g += 0.2) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(g), y2: y(g), class: "gridline" }));
      var t = svgEl("text", { x: m.left - 8, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); t.textContent = g.toFixed(1); svg.appendChild(t);
    }
    for (var v = xl; v <= xh + 1e-9; v += 0.1) {
      var tl = svgEl("text", { x: x(v), y: m.top + ih + 20, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tl.textContent = Math.round(v * 100) + "%"; svg.appendChild(tl);
    }
    var xt = svgEl("text", { x: m.left + iw / 2, y: H - 8, class: "tick-label", "text-anchor": "middle", "font-size": "12" });
    xt.textContent = "Share of houses and condos that are family-sized (6+ rooms, about 3+ bedrooms)"; svg.appendChild(xt);
    var yt = svgEl("text", { x: 14, y: m.top + ih / 2, class: "tick-label", "text-anchor": "middle", "font-size": "12", transform: "rotate(-90 14 " + (m.top + ih / 2) + ")" });
    yt.textContent = "Kindergartners per birth"; svg.appendChild(yt);
    svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(1), y2: y(1), stroke: css("--ink-muted"), "stroke-dasharray": "3,3" }));
    T.forEach(function (d) {
      var bk = d.town === "Brookline";
      svg.appendChild(svgEl("circle", { cx: x(d.family_sized_share), cy: y(d.k_per_birth), r: bk ? 7 : 5, fill: css(bk ? "--line-total" : "--line-benefits") }));
      var right = d.family_sized_share < 0.9;
      var lb = svgEl("text", { x: x(d.family_sized_share) + (right ? 10 : -10), y: y(d.k_per_birth) + 4, "text-anchor": right ? "start" : "end",
                               "font-size": bk ? "13" : "11.5", "font-weight": bk ? "600" : "400", fill: css("--ink") });
      lb.textContent = d.town; svg.appendChild(lb);
    });
    svg.setAttribute("aria-label", "Scatter chart of twelve towns: share of homes that are family-sized against kindergartners per birth. " +
      T.map(function (d) { return d.town + " " + Math.round(d.family_sized_share * 100) + "% and " + d.k_per_birth.toFixed(2); }).join("; ") + ".");
    fillTable("kpbhousing-table", ["Town", "Births, 2020", "Kindergarten, fall 2025", "Kindergartners per birth", "Family-sized share of homes",
                                   "Median sale, family-sized home, 2023–25", "Households with children"],
      T.slice().sort(function (a, b) { return a.family_sized_share - b.family_sized_share; }).map(function (d) {
        return [d.town, d.births_2020.toLocaleString("en-US"), d.k_fall2025.toLocaleString("en-US"), d.k_per_birth.toFixed(2),
                Math.round(d.family_sized_share * 100) + "%", "$" + (d.median_sale_family_sized / 1e6).toFixed(2) + "M", Math.round(d.hh_with_children * 100) + "%"];
      }));
  }

  // ---- STUDENTS PER HOME by bedrooms, for each kind of home (pums_children_per_home.py), with the
  //      Town's count in new developments (ERSC Final Report) placed at their average bedrooms
  var SPH_KINDS = [["house", "Houses", "--pine", 0.12], ["condo", "Condominiums (owned)", "--line-benefits", 0],
                   ["apartment", "Apartments (rented)", "--line-levy-actual", -0.12]];
  var SPH_BEDS = { 1: "0 or 1", 2: "2", 3: "3", 4: "4 or more" };
  function drawStudentsBedroomsChart() {
    var svg = document.getElementById("sphbeds-svg");
    if (!svg || !SD || !SD.studentsPerHome) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var S = SD.studentsPerHome, W = 900, H = 420, m = { top: 20, right: 150, bottom: 52, left: 60 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom, xl = 0.6, xh = 4.4, yl = 0, yh = 0.8;
    var x = function (b) { return m.left + (b - xl) / (xh - xl) * iw; }, y = function (v) { return m.top + (yh - v) / (yh - yl) * ih; };
    var tooltip = document.getElementById("sphbeds-tooltip"), wrap = document.getElementById("sphbeds-wrap");
    for (var g = 0; g <= yh + 1e-9; g += 0.2) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(g), y2: y(g), class: "gridline" }));
      var t = svgEl("text", { x: m.left - 8, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); t.textContent = g.toFixed(1); svg.appendChild(t);
    }
    [1, 2, 3, 4].forEach(function (b) {
      var tl = svgEl("text", { x: x(b), y: m.top + ih + 20, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tl.textContent = SPH_BEDS[b]; svg.appendChild(tl);
    });
    var xt = svgEl("text", { x: m.left + iw / 2, y: H - 8, class: "tick-label", "text-anchor": "middle", "font-size": "12" });
    xt.textContent = "Bedrooms per home (new developments: their average)"; svg.appendChild(xt);
    var yt = svgEl("text", { x: 14, y: m.top + ih / 2, class: "tick-label", "text-anchor": "middle", "font-size": "12", transform: "rotate(-90 14 " + (m.top + ih / 2) + ")" });
    yt.textContent = "Public school students per home"; svg.appendChild(yt);
    var tip = function (el, html) {
      el.addEventListener("mousemove", function (e) { tipAt(tooltip, wrap, e, html); });
      el.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    };
    // the forecast's figure
    svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(0.244), y2: y(0.244), stroke: css("--ink-muted"), "stroke-dasharray": "3,3" }));
    var fl = svgEl("text", { x: m.left + iw + 6, y: y(0.244) + 4, class: "tick-label", "font-size": "11.5" }); fl.textContent = "Forecast: 0.244"; svg.appendChild(fl);
    // every home together: the schedule
    svg.appendChild(svgEl("path", { d: "M" + S.all.map(function (r) { return x(r.beds) + "," + y(r.v); }).join(" L"), fill: "none",
                                    stroke: css("--line-total"), "stroke-width": 2.5, "stroke-linejoin": "round" }));
    var la = S.all[S.all.length - 1], al = svgEl("text", { x: x(la.beds) + 12, y: y(la.v) + 4, "font-size": "12", "font-weight": "600", fill: css("--ink") });
    al.textContent = "All homes"; svg.appendChild(al);
    // the Town's count in developments built since 2015
    S.devs.forEach(function (d) {
      var c = svgEl("circle", { cx: x(d.beds), cy: y(d.v), r: 6, fill: "none", stroke: css("--line-ref"), "stroke-width": 2 });
      svg.appendChild(c);
      tip(c, "<strong>Development " + d.dev + "</strong>" + (d.note ? " (" + d.note.replace(/ \(chart label\)/, "") + ")" : "") +
             "<br>" + d.beds.toFixed(2) + " bedrooms on average<br>" + d.v.toFixed(2) + " enrolled students per home, fall 2025");
    });
    // each kind of home, with its 90% range
    SPH_KINDS.forEach(function (k) {
      S.rows.filter(function (r) { return r.kind === k[0]; }).forEach(function (r) {
        var cx = x(r.beds + k[3]);
        svg.appendChild(svgEl("line", { x1: cx, x2: cx, y1: y(r.lo), y2: y(r.hi), stroke: css(k[2]), "stroke-width": 2, opacity: 0.5 }));
        var c = svgEl("circle", { cx: cx, cy: y(r.v), r: 5.5, fill: css(k[2]), stroke: css("--paper"), "stroke-width": 1.5 });
        svg.appendChild(c);
        tip(c, "<strong>" + k[1] + ", " + SPH_BEDS[r.beds] + " bedrooms</strong><br>" + r.v.toFixed(2) + " students per home (" +
               r.lo.toFixed(2) + " to " + r.hi.toFixed(2) + ")<br>" + r.n + " households surveyed");
      });
    });
    var leg = document.getElementById("sphbeds-legend");
    if (leg) leg.innerHTML = '<div class="legend-item"><span class="legend-swatch" style="background:' + css("--line-total") + '"></span><span>All homes</span></div>' +
      SPH_KINDS.map(function (k) { return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(k[2]) + '"></span><span>' + k[1] + '</span></div>'; }).join("") +
      '<div class="legend-item"><span class="legend-swatch" style="background:transparent;border:2px solid ' + css("--line-ref") + ';border-radius:50%;width:10px;height:10px"></span><span>Brookline developments since 2015 (hollow)</span></div>';
    svg.setAttribute("aria-label", "Chart of public school students per home by bedrooms. All homes: " +
      S.all.map(function (r) { return SPH_BEDS[r.beds] + " bedrooms " + r.v.toFixed(2); }).join(", ") +
      ". Houses, condominiums and apartments with the same bedrooms fall close together. Ten Brookline developments built since 2015, averaging 1.2 to 3 bedrooms, hold 0.03 to 0.56 students per home.");
    fillTable("sphbeds-table", ["Kind of home", "0 or 1 bedroom", "2 bedrooms", "3 bedrooms", "4 or more"],
      [["All homes", S.all]].concat(SPH_KINDS.map(function (k) { return [k[1], S.rows.filter(function (r) { return r.kind === k[0]; })]; }))
        .map(function (p) {
          return [p[0]].concat([1, 2, 3, 4].map(function (b) {
            var r = p[1].filter(function (q) { return q.beds === b; })[0];
            return r ? r.v.toFixed(2) + " (" + r.lo.toFixed(2) + "–" + r.hi.toFixed(2) + ")" : "too few";
          }));
        }));
  }

  // ---- OWNERS BY AGE, CENSUS TO CENSUS (householder_age_turnover.py): each age group ten years on,
  //      and how many are no longer owners. Counts are net (see the page), not households followed.
  var HT_AGES = [["45-54", "45 to 54", "--line-benefits"], ["55-64", "55 to 64", "--line-education"],
                 ["65-74", "65 to 74", "--line-levy-actual"], ["75+", "75 and over", "--line-no-override"]];
  function drawOwnerFlowChart() {
    var svg = document.getElementById("ownerflow-svg");
    if (!svg || !SD || !SD.homesTurnover) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var T = SD.homesTurnover, YRS = ["2000", "2010", "2020", "2030", "2040"], NC = YRS.length, COLS = [0, 1, 2, 3, 4], PROJ = 3;
    var cnt = function (i) {   // owners by age in column i; 75+ kept as its two parts. 2040 has no 45-54 (it needs 2030's 35-44)
      var o = i < PROJ ? T.owners[YRS[i]] : T["projected_" + YRS[i]];
      return { "45-54": o["45-54"] || 0, "55-64": o["55-64"], "65-74": o["65-74"], "75-84": o["75-84"], "85+": o["85+"], "75+": o["75-84"] + o["85+"] };
    };
    // flows from column i to i+1: [from, to, stayed]
    var flows = function (i) {
      var a = cnt(i), b = cnt(i + 1);
      return [["45-54", "55-64", b["55-64"]], ["55-64", "65-74", b["65-74"]], ["65-74", "75+", b["75-84"]], ["75+", "75+", b["85+"]]]
        .map(function (f) { return { from: f[0], to: f[1], src: a[f[0]], stay: Math.min(f[2], a[f[0]]), dest: f[2], left: Math.max(a[f[0]] - f[2], 0) }; });
    };
    var exits = COLS.map(function (i) { return i ? flows(i - 1).reduce(function (t, f) { return t + f.left; }, 0) : 0; });
    var exits55 = COLS.map(function (i) { return i ? flows(i - 1).reduce(function (t, f) { return t + (f.from === "45-54" ? 0 : f.left); }, 0) : 0; });
    var W = 900, H = 560, m = { top: 44, right: 108, bottom: 62, left: 96 }, nw = 16, gap = 10, xgap = 26;
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var tot = COLS.map(function (i) { var c = cnt(i); return c["45-54"] + c["55-64"] + c["65-74"] + c["75+"] + exits[i]; });
    var k = (ih - 3 * gap - xgap) / Math.max.apply(null, tot);
    var X = function (i) { return m.left + i * (iw - nw) / (NC - 1); };
    var tooltip = document.getElementById("ownerflow-tooltip"), wrap = document.getElementById("ownerflow-wrap");
    var tip = function (el, html) {
      el.addEventListener("mousemove", function (e) { tipAt(tooltip, wrap, e, html); });
      el.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    };
    var n0 = function (v) { return Math.round(v).toLocaleString("en-US"); };
    var label = function (a) { return HT_AGES.filter(function (g) { return g[0] === a; })[0][1].toLowerCase(); };
    // node positions
    var pos = COLS.map(function (i) {
      var c = cnt(i), y = m.top, p = {};
      HT_AGES.forEach(function (g) { p[g[0]] = { y0: y, h: c[g[0]] * k }; y += c[g[0]] * k + gap; });
      p.exit = { y0: y - gap + xgap, h: exits[i] * k };
      return p;
    });
    var ribbon = function (x0, y0, h0, x1, y1, h1) {
      var mx = (x0 + x1) / 2;
      return "M" + x0 + "," + y0 + " C" + mx + "," + y0 + " " + mx + "," + y1 + " " + x1 + "," + y1 +
             " L" + x1 + "," + (y1 + h1) + " C" + mx + "," + (y1 + h1) + " " + mx + "," + (y0 + h0) + " " + x0 + "," + (y0 + h0) + " Z";
    };
    var labels = [], LT = 0.8;   // rate labels sit 80% of the way along each band, past where the gray bands cross
    var bez = function (a, b, t) { return a + (b - a) * (3 * t * t - 2 * t * t * t); };   // the ribbon's curve, both control points at mid-x
    var grays = [], colored = [];
    COLS.slice(0, NC - 1).forEach(function (i) {
      var x0 = X(i) + nw, x1 = X(i + 1), proj = i + 1 >= PROJ, exitOff = 0, inOff = {};
      flows(i).forEach(function (f) {
        if (!f.src) return;
        var s = pos[i][f.from], d = pos[i + 1][f.to], color = css(HT_AGES.filter(function (g) { return g[0] === f.from; })[0][2]);
        var dy = d.y0 + (inOff[f.to] || 0);
        inOff[f.to] = (inOff[f.to] || 0) + f.dest * k;
        var p = svgEl("path", { d: ribbon(x0, s.y0, f.stay * k, x1, dy, f.dest * k), fill: color, opacity: proj ? 0.28 : 0.45 });
        colored.push(p);
        var rate = f.dest / f.src, toLab = f.from === "75+" ? "85 and over" : f.to === "75+" ? "75 to 84" : label(f.to);
        tip(p, '<div class="tt-title">Owners ' + label(f.from) + ' in ' + YRS[i] + '</div>' +
               '<div class="tt-row"><span>Owners then</span><span>' + n0(f.src) + '</span></div>' +
               '<div class="tt-row"><span>Owners ' + toLab + ' in ' + YRS[i + 1] + (proj ? " (projected)" : "") + '</span><span>' + n0(f.dest) + '</span></div>' +
               '<div class="tt-row"><span>Still owning, net</span><span>' + Math.round(rate * 100) + '%</span></div>');
        labels.push({ x: x0 + (x1 - x0) * LT, y: bez(s.y0 + f.stay * k / 2, dy + f.dest * k / 2, LT), t: Math.round(rate * 100) + "%", proj: proj });
        if (f.left > 0) {
          var e = pos[i + 1].exit, q = svgEl("path", { d: ribbon(x0, s.y0 + f.stay * k, f.left * k, x1, e.y0 + exitOff, f.left * k),
                                                       fill: css("--ink-muted"), opacity: proj ? 0.12 : 0.2 });
          exitOff += f.left * k;
          grays.push(q);
          tip(q, '<div class="tt-title">Owners ' + label(f.from) + ' in ' + YRS[i] + '</div>' +
                 '<div class="tt-row"><span>No longer owning ten years later, net</span><span>' + n0(f.left) + '</span></div>' +
                 '<div class="tt-row"><span>Share</span><span>' + Math.round((1 - rate) * 100) + '%</span></div>');
        }
      });
    });
    grays.forEach(function (q) { svg.appendChild(q); });     // gray under colored, so the bands stay readable
    colored.forEach(function (p) { svg.appendChild(p); });
    // nodes
    COLS.forEach(function (i) {
      var c = cnt(i), proj = i >= PROJ;
      HT_AGES.forEach(function (g) {
        if (!c[g[0]]) return;
        var p = pos[i][g[0]], r = svgEl("rect", { x: X(i), y: p.y0, width: nw, height: Math.max(p.h, 1), rx: 2, fill: css(g[2]), opacity: proj ? 0.55 : 1 });
        svg.appendChild(r);
        tip(r, '<div class="tt-title">Owners ' + g[1].toLowerCase() + ', ' + YRS[i] + (proj ? " (projected)" : "") + '</div><div class="tt-row"><span>Households</span><span>' + n0(c[g[0]]) + '</span></div>' +
               (g[0] === "75+" ? '<div class="tt-row"><span>75 to 84</span><span>' + n0(c["75-84"]) + '</span></div><div class="tt-row"><span>85 and over</span><span>' + n0(c["85+"]) + '</span></div>' : "") +
               (g[0] === "45-54" && i ? '<div>Owners who were 35 to 44 ten years earlier, and owners who arrived, are not drawn.</div>' : ""));
      });
      if (i) {
        var e = pos[i].exit, r = svgEl("rect", { x: X(i), y: e.y0, width: nw, height: e.h, rx: 2, fill: css("--ink-muted"), opacity: proj ? 0.45 : 0.8 });
        svg.appendChild(r);
        tip(r, '<div class="tt-title">No longer owning, ' + YRS[i - 1] + ' to ' + YRS[i] + (proj ? " (projected)" : "") + '</div><div class="tt-row"><span>Households, net</span><span>' + n0(exits[i]) +
               '</span></div><div class="tt-row"><span>Of which 55 and over</span><span>' + n0(exits55[i]) + '</span></div>');
        var t = svgEl("text", { x: X(i) + nw / 2, y: e.y0 + e.h + 16, "text-anchor": "middle", class: "tick-label", "font-size": "11.5" });
        t.textContent = (proj ? "About " : "") + n0(Math.round(exits55[i] / (proj ? 10 : 1)) * (proj ? 10 : 1)) + " aged 55+"; svg.appendChild(t);
        var t2 = svgEl("text", { x: X(i) + nw / 2, y: e.y0 + e.h + 30, "text-anchor": "middle", class: "tick-label", "font-size": "11" });
        t2.textContent = (proj ? "projected, " : "") + "about " + n0(Math.round(exits55[i] / 100) * 10) + " a year"; svg.appendChild(t2);
      }
      var hd = svgEl("text", { x: X(i) + nw / 2, y: 18, "text-anchor": "middle", "font-size": "13", "font-weight": "600", fill: css(proj ? "--ink-muted" : "--ink") });
      hd.textContent = YRS[i]; svg.appendChild(hd);
      if (proj) { var pj = svgEl("text", { x: X(i) + nw / 2, y: 33, "text-anchor": "middle", class: "tick-label", "font-size": "11" }); pj.textContent = "projected"; svg.appendChild(pj); }
    });
    // rates on the ribbons, over everything
    labels.forEach(function (l) {
      var t = svgEl("text", { x: l.x, y: l.y + 4, "text-anchor": "middle", "font-size": "12", "font-weight": "600", fill: css(l.proj ? "--ink-muted" : "--ink"),
                              stroke: css("--paper-card"), "stroke-width": 3.5, "paint-order": "stroke", "stroke-linejoin": "round", "pointer-events": "none" });
      t.textContent = l.t; svg.appendChild(t);
    });
    // age labels, both sides
    HT_AGES.forEach(function (g) {
      [[0, X(0) - 8, "end"], [NC - 1, X(NC - 1) + nw + 8, "start"]].forEach(function (s) {
        if (!cnt(s[0])[g[0]]) return;
        var p = pos[s[0]][g[0]], t = svgEl("text", { x: s[1], y: p.y0 + p.h / 2 + 4, "text-anchor": s[2], "font-size": "12", fill: css("--ink") });
        t.textContent = g[1]; svg.appendChild(t);
      });
    });
    var lt = svgEl("text", { x: X(NC - 1) + nw + 8, y: pos[NC - 1].exit.y0 + pos[NC - 1].exit.h / 2 + 4, "font-size": "12", fill: css("--ink-muted") });
    lt.textContent = "No longer owning"; svg.appendChild(lt);
    var a = T.still_owning;
    svg.setAttribute("aria-label", "Flow chart of Brookline owner households by age of householder in 2000, 2010, 2020 and projected for 2030. Share of each age group still owning ten years later, 2000 to 2010 and 2010 to 2020: " +
      HT_AGES.map(function (g) { return g[1] + " " + Math.round(a["2000"][g[0]] * 100) + "% and " + Math.round(a["2010"][g[0]] * 100) + "%"; }).join(", ") +
      ". Owners aged 55 and over no longer owning: " + n0(exits55[1]) + " in the 2000s, " + n0(exits55[2]) + " in the 2010s, about " + n0(exits55[3]) + " projected for the 2020s and " + n0(exits55[4]) + " for the 2030s.");
    var rows = [];
    HT_AGES.forEach(function (g) {
      [0, 1, 2, 3].forEach(function (i) {
        var f = flows(i).filter(function (q) { return q.from === g[0]; })[0];
        if (!f.src) return;
        var pj = i + 1 >= PROJ;
        rows.push([g[1] + " in " + YRS[i] + (i >= PROJ ? " (projected)" : ""), n0(f.src), (pj ? "about " : "") + n0(f.dest) + (pj ? " (projected)" : ""), Math.round(f.dest / f.src * 100) + "%" + (pj ? " (average of the two)" : "")]);
      });
    });
    fillTable("ownerflow-table", ["Owners", "Households", "Same group ten years later", "Still owning, net"], rows);
  }

  // ---- STUDENTS IN A FAMILY-SIZED HOME, BY HOW LONG THE HOUSEHOLD HAS LIVED THERE (one survey, one point in time)
  function drawYearsInHomeChart() {
    var svg = document.getElementById("yearsinhome-svg");
    if (!svg || !SD || !SD.homesTurnover) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var T = SD.homesTurnover, S = T.students_by_years_in_home, N = T.students_by_years_in_home_records;
    var bars = [["Owners 55 and over", T.students_older_owners_leaving, T.older_owners_leaving_records, "--ink-muted"],
                ["Moved in within the past 2 years", S["0-1"], N["0-1"], "--pine"], ["Moved in 2 to 4 years ago", S["2-4"], N["2-4"], "--pine"],
                ["Moved in 5 to 9 years ago", S["5-9"], N["5-9"], "--pine"], ["Moved in 10 to 19 years ago", S["10-19"], N["10-19"], "--pine"]];
    var rowH = 44, W = 900, m = { top: 10, bottom: 34, left: 290, right: 80 }, H = m.top + m.bottom + rowH * bars.length, hi = 1.2;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var iw = W - m.left - m.right, x = function (v) { return m.left + v / hi * iw; };
    var tooltip = document.getElementById("yearsinhome-tooltip"), wrap = document.getElementById("yearsinhome-wrap");
    for (var g = 0; g <= hi + 1e-9; g += 0.2) {
      svg.appendChild(svgEl("line", { x1: x(g), x2: x(g), y1: m.top, y2: H - m.bottom, class: "gridline" }));
      var t = svgEl("text", { x: x(g), y: H - m.bottom + 18, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); t.textContent = g.toFixed(1); svg.appendChild(t);
    }
    bars.forEach(function (b, i) {
      var cy = m.top + i * rowH + rowH / 2;
      var lab = svgEl("text", { x: m.left - 10, y: cy + 4, "text-anchor": "end", "font-size": "13", fill: css("--ink") }); lab.textContent = b[0]; svg.appendChild(lab);
      svg.appendChild(svgEl("rect", { x: m.left, y: cy - 12, width: x(b[1]) - m.left, height: 24, rx: 3, fill: css(b[3]) }));
      var vt = svgEl("text", { x: x(b[1]) + 8, y: cy + 4, class: "tick-label", "font-size": "12" }); vt.textContent = b[1].toFixed(2); svg.appendChild(vt);
      var hit = svgEl("rect", { x: 0, y: cy - rowH / 2, width: W, height: rowH, fill: "transparent" }); svg.appendChild(hit);
      hit.addEventListener("mousemove", function (e) {
        tipAt(tooltip, wrap, e, '<div class="tt-title">' + b[0] + '</div><div class="tt-row"><span>Public school students per home</span><span>' + b[1].toFixed(2) +
          '</span></div><div class="tt-row"><span>Households surveyed</span><span>' + b[2] + '</span></div>');
      });
      hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    });
    svg.setAttribute("aria-label", "Bar chart of public school students per home with three or more bedrooms: " + bars.map(function (b) { return b[0] + " " + b[1].toFixed(2); }).join(", ") + ".");
    fillTable("yearsinhome-table", ["Households in homes with 3 or more bedrooms", "Public school students per home", "Households surveyed"],
      bars.map(function (b) { return [b[0], b[1].toFixed(2), String(b[2])]; }));
  }

  // ---- WHO SETS IT: the same $177 million grouped by who controls each cause
  var WHO_LABELS = { outside: "Outside Brookline", decide: "Brookline's own decisions", past: "Past obligations",
                     growth: "Growth in homes and commercial space", other: "Other" };
  var WHO_NOTES = { outside: "Inflation in pay, prices and premiums; state, county and MBTA assessments",
                    decide: "Staffing levels, borrowing, retiree health prefunding, pay above or below the national benchmark",
                    past: "Paying down the pension shortfall on a fixed schedule",
                    growth: "Staff and services for new homes and commercial space, which zoning and permitting shape",
                    other: "Other benefits such as Medicare tax and workers' compensation, and reconciling items" };
  function drawWhoSetsChart() {
    var svg = document.getElementById("whosets-svg");
    if (!svg || !SD || !SD.whoSets) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var rows = SD.whoSets, rowH = 40, W = 900, m = { top: 10, bottom: 10, left: 280, right: 130 };
    var H = m.top + m.bottom + rowH * rows.length;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var mx = Math.max.apply(null, rows.map(function (r) { return r.v; })), iw = W - m.left - m.right, x0 = m.left + 14;
    var tooltip = document.getElementById("whosets-tooltip"), wrap = document.getElementById("whosets-wrap");
    svg.appendChild(svgEl("line", { x1: x0, x2: x0, y1: m.top, y2: H - m.bottom, stroke: css("--ink-muted") }));
    rows.forEach(function (r, i) {
      var cy = m.top + i * rowH + rowH / 2, len = Math.abs(r.v) / mx * (iw - 20);
      var lab = svgEl("text", { x: m.left - 6, y: cy + 4, "text-anchor": "end", "font-size": "13", fill: css("--ink") }); lab.textContent = WHO_LABELS[r.kind]; svg.appendChild(lab);
      svg.appendChild(svgEl("rect", { x: x0, y: cy - 12, width: Math.max(len, 1.5), height: 24, rx: 3, fill: css(KIND[r.kind][1]) }));
      var vt = svgEl("text", { x: x0 + Math.max(len, 1.5) + 8, y: cy + 4, class: "tick-label", "font-size": "12" });
      vt.textContent = fmtM1(r.v) + " · " + Math.round(r.v / SD.causesTotal * 100) + "%"; svg.appendChild(vt);
      var hit = svgEl("rect", { x: 0, y: cy - rowH / 2, width: W, height: rowH, fill: "transparent" }); svg.appendChild(hit);
      hit.addEventListener("mousemove", function (e) {
        tipAt(tooltip, wrap, e, '<div class="tt-title">' + WHO_LABELS[r.kind] + ' · ' + fmtM1(r.v) + '</div><div>' + WHO_NOTES[r.kind] + '</div>');
      });
      hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    });
    svg.setAttribute("aria-label", "Bar chart of the " + fmtM1(SD.causesTotal) + " increase in annual General Fund spending from FY2011 to FY2025, grouped by who sets it: " +
      rows.map(function (r) { return WHO_LABELS[r.kind] + " " + fmtM1(r.v) + " (" + Math.round(r.v / SD.causesTotal * 100) + "%)"; }).join(", ") + ".");
    fillTable("whosets-table", ["Who sets it", "Added to annual spending", "What it includes"],
      rows.map(function (r) { return [WHO_LABELS[r.kind], fmtM1(r.v) + " (" + Math.round(r.v / SD.causesTotal * 100) + "%)", WHO_NOTES[r.kind]]; }));
  }

  // ---- SCHOOL STAFF AND ENROLLMENT, indexed to FY2011
  function drawStaffEnrollChart() {
    var svg = document.getElementById("staffenroll-svg");
    if (!svg || !SD) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var D = SD.staffEnroll, W = 900, H = 360, m = { top: 20, right: 150, bottom: 40, left: 50 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var base = D.filter(function (d) { return d[0] === 2011; })[0];
    var idx = D.map(function (d) { return [d[0], d[1] / base[1] * 100, d[2] / base[2] * 100]; });
    var y0 = D[0][0], y1 = D[D.length - 1][0], lo = 80, hi = 150;
    var x = function (yr) { return m.left + (yr - y0) / (y1 - y0) * iw; }, y = function (v) { return m.top + (hi - v) / (hi - lo) * ih; };
    for (var g = lo; g <= hi; g += 10) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(g), y2: y(g), class: "gridline" }));
      var t = svgEl("text", { x: m.left - 8, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); t.textContent = g; svg.appendChild(t);
    }
    for (var yr = y0; yr <= y1; yr += 3) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tl.textContent = "FY" + String(yr).slice(2); svg.appendChild(tl);
    }
    [[2, "--pine", "Staff"], [1, "--line-benefits", "Enrollment"]].forEach(function (s) {
      svg.appendChild(svgEl("path", { d: "M" + idx.map(function (p) { return x(p[0]) + "," + y(p[s[0]]); }).join(" L"), fill: "none", stroke: css(s[1]), "stroke-width": 2.5 }));
      var last = idx[idx.length - 1], lt = svgEl("text", { x: x(last[0]) + 8, y: y(last[s[0]]) + 4, class: "tick-label", "font-size": "11.5", fill: css("--ink") });
      lt.textContent = s[2] + " " + Math.round(last[s[0]]); svg.appendChild(lt);
    });
    var tooltip = document.getElementById("staffenroll-tooltip"), wrap = document.getElementById("staffenroll-wrap");
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" }); svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var r = svg.getBoundingClientRect(), mx = (e.clientX - r.left) * (W / r.width), i = Math.max(0, Math.min(D.length - 1, Math.round((mx - m.left) / iw * (y1 - y0))));
      tipAt(tooltip, wrap, e, '<div class="tt-title">FY' + D[i][0] + '</div><div class="tt-row"><span>Enrollment</span><span>' + D[i][1].toLocaleString("en-US") +
        '</span></div><div class="tt-row"><span>Staff (FTE)</span><span>' + Math.round(D[i][2]).toLocaleString("en-US") + '</span></div>');
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    var pk = idx.reduce(function (a, b) { return b[2] > a[2] ? b : a; }), pe = idx.reduce(function (a, b) { return b[1] > a[1] ? b : a; }), last = idx[idx.length - 1];
    svg.setAttribute("aria-label", "Line chart of school staff and enrollment, indexed to FY2011 equals 100, FY" + y0 + " to FY" + y1 + ". Staff peaks at " + Math.round(pk[2]) + " in FY" + pk[0] +
      " and is " + Math.round(last[2]) + " in FY" + y1 + "; enrollment peaks at " + Math.round(pe[1]) + " in FY" + pe[0] + " and is " + Math.round(last[1]) + " in FY" + y1 + ".");
    var leg = document.getElementById("staffenroll-legend");
    if (leg) leg.innerHTML = '<div class="legend-item"><span class="legend-swatch" style="background:' + css("--pine") + '"></span><span>School staff (full-time equivalent)</span></div>' +
      '<div class="legend-item"><span class="legend-swatch" style="background:' + css("--line-benefits") + '"></span><span>Enrollment</span></div>';
    fillTable("staffenroll-table", ["Year", "Enrollment", "Staff (FTE)", "Students per staff"],
      D.map(function (d) { return ["FY" + d[0], d[1].toLocaleString("en-US"), Math.round(d[2]).toLocaleString("en-US"), (d[1] / d[2]).toFixed(2)]; }));
  }

  // ---- TOWN AND SCHOOL EMPLOYEES BY DEPARTMENT, history and base case (site_facts.js)
  var EMP_SERIES = [["Schools", 6, "--line-education"], ["Public Safety", 2, "--pine"], ["Public Works", 3, "--line-levy-actual"],
                    ["General Government", 1, "--line-benefits"], ["Culture & Recreation", 5, "--line-levy"], ["Human Services", 4, "--line-ref"]];
  function drawEmployeesChart() {
    var svg = document.getElementById("employees-svg");
    if (!svg || !SD || !SD.employees) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var D = SD.employees, W = 900, H = 400, m = { top: 20, right: 170, bottom: 40, left: 56 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var y0 = D[0][0], y1 = D[D.length - 1][0], hi = 2400;
    var x = function (yr) { return m.left + (yr - y0) / (y1 - y0) * iw; }, y = function (v) { return m.top + (hi - v) / hi * ih; };
    var f0 = D.filter(function (d) { return d[7] === 1; })[0];
    if (f0) {
      svg.appendChild(svgEl("rect", { x: x(f0[0] - 0.5), y: m.top, width: x(y1) - x(f0[0] - 0.5), height: ih, fill: css("--pine-tint"), opacity: 0.5 }));
      var ft = svgEl("text", { x: x(f0[0] - 0.5) + 6, y: m.top + 14, class: "tick-label", "font-size": "11.5" }); ft.textContent = "Forecast"; svg.appendChild(ft);
    }
    for (var g = 0; g <= hi; g += 400) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(g), y2: y(g), class: "gridline" }));
      var t = svgEl("text", { x: m.left - 8, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); t.textContent = g.toLocaleString("en-US"); svg.appendChild(t);
    }
    for (var yr = y0; yr <= y1; yr += 4) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tl.textContent = "FY" + String(yr).slice(2); svg.appendChild(tl);
    }
    var below = D.map(function () { return 0; }), labs = [];
    EMP_SERIES.forEach(function (sr) {
      var top = D.map(function (d, i) { return below[i] + d[sr[1]]; });
      var path = "M" + D.map(function (d, i) { return x(d[0]) + "," + y(top[i]); }).join(" L") +
        " L" + D.slice().reverse().map(function (d, j) { var i = D.length - 1 - j; return x(d[0]) + "," + y(below[i]); }).join(" L") + " Z";
      svg.appendChild(svgEl("path", { d: path, fill: css(sr[2]), opacity: 0.85, stroke: css("--ink-faint"), "stroke-width": 0.5 }));
      var li = D.length - 1;
      labs.push({ y: y((top[li] + below[li]) / 2) + 4, text: sr[0] + " " + Math.round(D[li][sr[1]]).toLocaleString("en-US") });
      below = top;
    });
    // labels at the right edge, nudged apart where thin bands sit close together
    labs.sort(function (p, q) { return q.y - p.y; });
    for (var k = 1; k < labs.length; k++) labs[k].y = Math.min(labs[k].y, labs[k - 1].y - 14);
    labs.forEach(function (l) {
      var lt = svgEl("text", { x: x(y1) + 8, y: l.y, class: "tick-label", "font-size": "11.5", fill: css("--ink") });
      lt.textContent = l.text; svg.appendChild(lt);
    });
    var tot = function (d) { return EMP_SERIES.reduce(function (a, sr) { return a + d[sr[1]]; }, 0); };
    var tooltip = document.getElementById("employees-tooltip"), wrap = document.getElementById("employees-wrap");
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" }); svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var r = svg.getBoundingClientRect(), mx = (e.clientX - r.left) * (W / r.width), i = Math.max(0, Math.min(D.length - 1, Math.round((mx - m.left) / iw * (y1 - y0))));
      tipAt(tooltip, wrap, e, '<div class="tt-title">FY' + D[i][0] + (D[i][7] ? " (forecast)" : "") + '</div>' +
        EMP_SERIES.map(function (sr) { return '<div class="tt-row"><span>' + sr[0] + '</span><span>' + Math.round(D[i][sr[1]]).toLocaleString("en-US") + '</span></div>'; }).join("") +
        '<div class="tt-row"><span>Total</span><span>' + Math.round(tot(D[i])).toLocaleString("en-US") + '</span></div>');
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    var at = function (yy) { return D.filter(function (d) { return d[0] === yy; })[0]; };
    var a = D[0], b = at(2027), c = D[D.length - 1];
    svg.setAttribute("aria-label", "Stacked area chart of Town and school employees by department, FY" + y0 + " to FY" + y1 + ". Total " +
      Math.round(tot(a)).toLocaleString("en-US") + " in FY" + y0 + ", " + Math.round(tot(b)).toLocaleString("en-US") + " in FY2027 and " + Math.round(tot(c)).toLocaleString("en-US") +
      " in FY" + y1 + " in the base case. Public Safety " + Math.round(a[2]) + " in FY" + y0 + ", " + Math.round(b[2]) + " in FY2027 and " + Math.round(c[2]) + " in FY" + y1 +
      "; schools " + Math.round(a[6]) + ", " + Math.round(b[6]) + " and " + Math.round(c[6]) + ".");
    var leg = document.getElementById("employees-legend");
    if (leg) leg.innerHTML = EMP_SERIES.map(function (sr) { return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(sr[2]) + '"></span><span>' + sr[0] + '</span></div>'; }).join("");
    fillTable("employees-table", ["Year"].concat(EMP_SERIES.map(function (sr) { return sr[0]; })).concat(["Total"]),
      D.map(function (d) { return ["FY" + d[0] + (d[7] ? " (forecast)" : "")].concat(EMP_SERIES.map(function (sr) { return Math.round(d[sr[1]]).toLocaleString("en-US"); })).concat([Math.round(tot(d)).toLocaleString("en-US")]); }));
  }

  // ---- WHAT NEW HOMES DO TO THE BUDGET, YEAR BY YEAR (growth_links.py), added 2026-10-11
  // One helper draws the four time charts: bars and lines by year, an optional right axis.
  // spec: { id, rows, xLabel(r), left: [lo, hi, step, fmt], right: [lo, hi, step, fmt] or null,
  //         series: [{ name, col, kind: "bar"|"line", axis: "left"|"right", color, dash, fmt }], aria, note }
  function drawYearChart(spec) {
    var svg = document.getElementById(spec.id + "-svg");
    if (!svg) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var R = spec.rows, W = 900, H = 380, m = { top: 24, right: spec.endLabels ? 150 : spec.right ? 70 : 30, bottom: 44, left: 70 };
    var iw = W - m.left - m.right, ih = H - m.top - m.bottom, n = R.length, slot = iw / n;
    var xc = function (i) { return m.left + slot * (i + 0.5); };
    var ax = function (a) { return function (v) { return m.top + (a[1] - v) / (a[1] - a[0]) * ih; }; };
    var yl = ax(spec.left), yr = spec.right ? ax(spec.right) : null;
    for (var g = spec.left[0]; g <= spec.left[1] + 1e-9; g += spec.left[2]) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: yl(g), y2: yl(g), class: "gridline" }));
      var t = svgEl("text", { x: m.left - 8, y: yl(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); t.textContent = spec.left[3](g); svg.appendChild(t);
    }
    if (spec.right) for (var g2 = spec.right[0]; g2 <= spec.right[1] + 1e-9; g2 += spec.right[2]) {
      var t2 = svgEl("text", { x: m.left + iw + 8, y: yr(g2) + 4, class: "tick-label", "font-size": "11" }); t2.textContent = spec.right[3](g2); svg.appendChild(t2);
    }
    var every = n > 14 ? 2 : 1;
    R.forEach(function (r, i) {
      if (i % every) return;
      var tl = svgEl("text", { x: xc(i), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tl.textContent = spec.xLabel(r); svg.appendChild(tl);
    });
    var bars = spec.series.filter(function (s) { return s.kind === "bar"; }), bw = Math.min(28, slot * 0.7 / Math.max(1, bars.length));
    bars.forEach(function (s, k) {
      var y = s.axis === "right" ? yr : yl;
      R.forEach(function (r, i) {
        if (r[s.col] == null) return;
        var x0 = xc(i) - bw * bars.length / 2 + bw * k;
        svg.appendChild(svgEl("rect", { x: x0, y: y(r[s.col]), width: bw - 2, height: Math.max(0, y(spec[s.axis][0]) - y(r[s.col])), fill: css(s.color), opacity: 0.85 }));
      });
    });
    // Lines marked muted are drawn thin and gray first, so the emphasized ones sit on top.
    var lines = spec.series.filter(function (s) { return s.kind === "line"; }), ends = [];
    lines.filter(function (s) { return s.muted; }).concat(lines.filter(function (s) { return !s.muted; })).forEach(function (s) {
      var y = s.axis === "right" ? yr : yl, d = "", pen = false, col = css(s.muted ? "--ink-faint" : s.color), lastI = -1;
      R.forEach(function (r, i) {
        if (r[s.col] == null) { pen = false; return; }
        d += (pen ? " L" : " M") + xc(i) + "," + y(r[s.col]); pen = true; lastI = i;
        if (!s.muted) svg.appendChild(svgEl("circle", { cx: xc(i), cy: y(r[s.col]), r: s.width > 3 ? 3.6 : 3, fill: col }));
      });
      var a = { d: d, fill: "none", stroke: col, "stroke-width": s.muted ? 1.8 : (s.width || 2.6), "stroke-linejoin": "round" };
      if (s.dash) a["stroke-dasharray"] = "6,4";
      svg.appendChild(svgEl("path", a));
      if (spec.endLabels && s.endLabel && lastI >= 0) ends.push({ s: s, x: xc(lastI), y: y(R[lastI][s.col]), col: col, text: s.endLabel(R[lastI][s.col]) });
    });
    // Direct labels at each line's end, nudged apart so none overlap.
    ends.sort(function (p, q) { return p.y - q.y; });
    ends.forEach(function (e, k) { e.ly = k ? Math.max(e.y, ends[k - 1].ly + 15) : e.y; });
    ends.forEach(function (e) {
      var t = svgEl("text", { x: e.x + 10, y: e.ly + 4, "font-size": e.s.muted ? "11.5" : "13", "font-weight": e.s.muted ? "400" : "700", fill: e.s.muted ? css("--ink-muted") : e.col });
      t.textContent = e.text; svg.appendChild(t);
    });
    if (spec.note) spec.note(svg, xc, yl, m, ih);
    var tooltip = document.getElementById(spec.id + "-tooltip"), wrap = document.getElementById(spec.id + "-wrap");
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" }); svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var b = svg.getBoundingClientRect(), mx = (e.clientX - b.left) * (W / b.width), i = Math.max(0, Math.min(n - 1, Math.floor((mx - m.left) / slot)));
      tipAt(tooltip, wrap, e, '<div class="tt-title">' + spec.xLabel(R[i]) + '</div>' + spec.series.map(function (s) {
        return '<div class="tt-row"><span>' + s.name + '</span><span>' + (R[i][s.col] == null ? "&ndash;" : s.fmt(R[i][s.col])) + '</span></div>'; }).join(""));
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    var leg = document.getElementById(spec.id + "-legend");
    if (leg) leg.innerHTML = spec.series.map(function (s) {
      return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(s.muted ? "--ink-faint" : s.color) + '"></span><span>' + s.name + (spec.right ? (s.axis === "right" ? " (right scale)" : " (left scale)") : "") + '</span></div>'; }).join("");
    svg.setAttribute("aria-label", spec.aria);
    fillTable(spec.id + "-table", [spec.xHead].concat(spec.series.map(function (s) { return s.name; })),
      R.map(function (r) { return [spec.xLabel(r)].concat(spec.series.map(function (s) { return r[s.col] == null ? "&ndash;" : s.fmt(r[s.col]); })); }));
  }
  var glM = function (v) { return "$" + Math.round(v) + "M"; }, glN = function (v) { return Math.round(v).toLocaleString("en-US"); };
  // Permits above a shared time axis, the new growth they became below it, placed in the fiscal
  // year it was taxed (July to June), with an arrow from each permit year to its fiscal year so
  // the lag reads directly off the chart.
  function drawGlRevenueChart() {
    var svg = document.getElementById("gl-revenue-svg");
    if (!svg || !SD || !SD.growthLinks) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    // rows: [permit calendar year, taxable permits $M, real estate new growth $M certified three fiscal years on,
    //        expected $M where not yet certified, that FY, the base case's real estate new growth $M for that FY]
    var R = SD.growthLinks.revenue_re, F = { ratio_min: SD.growthLinks.revenue_re_ratio[0], ratio_max: SD.growthLinks.revenue_re_ratio[1] };
    var W = 900, H = 520, m = { top: 34, right: 24, bottom: 52, left: 64 }, band = 70, ph = (H - m.top - m.bottom - band) / 2, hi = 450;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var t0 = R[0][0], t1 = R[R.length - 1][4] + 0.5, iw = W - m.left - m.right;
    var x = function (t) { return m.left + (t - t0) / (t1 - t0) * iw; };
    var topBase = m.top + ph, botBase = topBase + band;
    var yu = function (v) { return topBase - v / hi * ph; }, yd = function (v) { return botBase + v / hi * ph; };
    var defs = svgEl("defs", {}), mk = svgEl("marker", { id: "gl-arrow", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" });
    mk.appendChild(svgEl("path", { d: "M0,0 L10,5 L0,10 z", fill: css("--ink-muted") })); defs.appendChild(mk); svg.appendChild(defs);
    [0, 200, 400].forEach(function (g) {
      [[yu, "end"], [yd, "end"]].forEach(function (a) {
        svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: a[0](g), y2: a[0](g), class: "gridline" }));
        var t = svgEl("text", { x: m.left - 8, y: a[0](g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); t.textContent = "$" + g + "M"; svg.appendChild(t);
      });
    });
    var lab = function (txt, yy) { var t = svgEl("text", { x: m.left + 4, y: yy, "font-size": "12.5", fill: css("--ink") }); t.textContent = txt; svg.appendChild(t); };
    lab("Construction permitted, by calendar year", m.top - 14);
    lab("Real estate new growth it became, by the fiscal year it was first taxed", H - 6);
    // calendar years along the band between the panels
    for (var yr = t0; yr <= R[R.length - 1][0]; yr++) {
      if (yr + 1 <= t1) { var tl = svgEl("text", { x: x(yr + 0.5), y: topBase + 15, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tl.textContent = String(yr); svg.appendChild(tl); }
    }
    R.forEach(function (r) {
      svg.appendChild(svgEl("rect", { x: x(r[0] + 0.12), y: yu(r[1]), width: x(r[0] + 0.88) - x(r[0] + 0.12), height: topBase - yu(r[1]), fill: css("--line-ref"), opacity: 0.85 }));
      var v = r[2] != null ? r[2] : r[3], cert = r[2] != null, a = r[4] - 0.5;
      var bar = { x: x(a + 0.12), y: botBase, width: x(a + 0.88) - x(a + 0.12), height: yd(v) - botBase, fill: css("--pine"), "fill-opacity": cert ? 0.9 : 0.22 };
      if (!cert) { bar.stroke = css("--pine"); bar["stroke-dasharray"] = "5,3"; bar["stroke-width"] = 1.5; }
      svg.appendChild(svgEl("rect", bar));
      var fl = svgEl("text", { x: x(a + 0.5), y: yd(hi) + 16, class: "tick-label", "text-anchor": "middle", "font-size": "10.5" }); fl.textContent = "FY" + String(r[4]).slice(2); svg.appendChild(fl);
    });
    // the base case's new growth for the years not yet certified, as a bracket across the bar
    R.forEach(function (r) {
      if (r[5] == null) return;
      var a = r[4] - 0.5, yy = yd(r[5]);
      svg.appendChild(svgEl("line", { x1: x(a + 0.08), x2: x(a + 0.92), y1: yy, y2: yy, stroke: css("--line-levy"), "stroke-width": 3 }));
      ["Base case", glM(r[5])].forEach(function (txt, k) {
        var bt = svgEl("text", { x: x(a + 0.5), y: yy + 15 + 13 * k, "text-anchor": "middle", "font-size": "11", "font-weight": "700", fill: css("--line-levy") });
        bt.textContent = txt; svg.appendChild(bt);
      });
    });
    // arrows drawn last, from the foot of each permit bar to the head of its fiscal-year bar
    R.forEach(function (r, i) {
      var xa = x(r[0] + 0.5), xb = x(r[4]), ya = topBase + 22, yb = botBase - 3;
      svg.appendChild(svgEl("path", { d: "M" + xa + "," + ya + " L" + xb + "," + yb,
        fill: "none", stroke: css(i === 0 ? "--ink" : "--ink-muted"), "stroke-width": i === 0 ? 1.8 : 1.1, opacity: i === 0 ? 1 : 0.7, "marker-end": "url(#gl-arrow)" }));
    });
    var first = R[0], nx = x(R[R.length - 1][0] + 1.1);
    [["How to read it: the " + first[0] + " permits", 0], ["were valued on January 1, " + (first[0] + 2) + ",", 16], ["and first taxed in FY" + first[4] + ",", 32], ["from July " + (first[0] + 2) + ".", 48]].forEach(function (l) {
      var t = svgEl("text", { x: nx, y: m.top + 14 + l[1], "font-size": "11.5", fill: css("--ink-muted") }); t.textContent = l[0]; svg.appendChild(t);
    });
    var tooltip = document.getElementById("gl-revenue-tooltip"), wrap = document.getElementById("gl-revenue-wrap");
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: H - m.top - m.bottom, fill: "transparent" }); svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var b = svg.getBoundingClientRect(), mx = (e.clientX - b.left) * (W / b.width), my = (e.clientY - b.top) * (H / b.height), t = t0 + (mx - m.left) / iw * (t1 - t0);
      // above the band, the permit year under the pointer; below it, the fiscal year
      var r = my < topBase + band / 2 ? R.filter(function (q) { return t >= q[0] && t < q[0] + 1; })[0] : R.filter(function (q) { return t >= q[4] - 0.5 && t < q[4] + 0.5; })[0];
      if (!r) { tooltip.style.opacity = 0; return; }
      var v = r[2] != null ? r[2] : r[3];
      tipAt(tooltip, wrap, e, '<div class="tt-title">' + r[0] + ' permits &rarr; FY' + r[4] + '</div>' +
        '<div class="tt-row"><span>Construction permitted</span><span>' + glM(r[1]) + '</span></div>' +
        '<div class="tt-row"><span>' + (r[2] != null ? "New growth certified" : "Expected, not yet certified") + '</span><span>' + glM(v) + '</span></div>' +
        (r[5] != null ? '<div class="tt-row"><span>Base case</span><span>' + glM(r[5]) + '</span></div>' : '') +
        '<div class="tt-row"><span>Per permitted dollar</span><span>' + Math.round(v / r[1] * 100) + ' cents</span></div>');
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    var leg = document.getElementById("gl-revenue-legend");
    if (leg) leg.innerHTML = [["--line-ref", 0.85, "Construction permitted that year"], ["--pine", 0.9, "Real estate new growth the state certified"], ["--pine", 0.25, "Expected from permits, not yet certified"], ["--line-levy", 1, "What the base case assumes"]].map(function (l) {
      return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(l[0]) + ';opacity:' + l[1] + '"></span><span>' + l[2] + '</span></div>'; }).join("");
    var act = R.filter(function (r) { return r[2] != null; }), ex = R.filter(function (r) { return r[3] != null; });
    svg.setAttribute("aria-label", "Chart of construction permitted in Brookline each calendar year, " + R[0][0] + " to " + R[R.length - 1][0] + ", with arrows to the fiscal year in which it was first taxed as real estate new growth, about two and a half years later. " +
      act.map(function (r) { return r[0] + " permits $" + Math.round(r[1]) + " million, FY" + r[4] + " new growth $" + Math.round(r[2]) + " million"; }).join("; ") +
      ". Not yet certified: " + ex.map(function (r) { return r[0] + " permits $" + Math.round(r[1]) + " million, about $" + Math.round(r[3]) + " million expected in FY" + r[4] + ", against $" + Math.round(r[5]) + " million in the base case"; }).join("; ") +
      ". New growth has run " + Math.round(F.ratio_min * 100) + " to " + Math.round(F.ratio_max * 100) + " cents per permitted dollar.");
    fillTable("gl-revenue-table", ["Permits issued", "Construction permitted", "New growth fiscal year", "Real estate new growth certified", "Expected from permits", "Base case"],
      R.map(function (r) { return [String(r[0]), glM(r[1]), "FY" + r[4], r[2] == null ? "&ndash;" : glM(r[2]), r[3] == null ? "&ndash;" : glM(r[3]), r[5] == null ? "&ndash;" : glM(r[5])]; }));
  }
  function drawGlServicesChart() {
    if (!SD || !SD.growthLinks) return;
    // rows: [fy, homes, homes is a Census count, police and fire, other Town, school staff, enrollment, homes on the assessment rolls]
    var S = SD.growthLinks.services, b = S[0];
    var R = S.map(function (r) { return [r[0], r[1] / b[1] * 100, r[3] / b[3] * 100, r[4] / b[4] * 100, r[5] / b[5] * 100, r[6] / b[6] * 100, r[2], r[7] == null ? null : r[7] / b[1] * 100]; });
    var one = function (v) { return Math.round(v); }, e = R[R.length - 1], last = S[S.length - 1];
    var pct = function (v) { var d = Math.round(v - 100); return (d > 0 ? "+" : d < 0 ? "\u2212" : "") + Math.abs(d) + "%"; };
    drawYearChart({ id: "gl-services", rows: R, xHead: "Year", xLabel: function (r) { return "FY" + String(r[0]).slice(2); },
      left: [80, 140, 10, one], right: null, endLabels: true,
      series: [{ name: "Homes, Census trend", col: 1, kind: "line", axis: "left", color: "--line-no-override", dash: true, fmt: one, width: 3.4, endLabel: function (v) { return "Homes " + pct(v); } },
               { name: "Homes, assessment rolls", col: 7, kind: "line", axis: "left", color: "--line-no-override", fmt: one, width: 3.4 },
               { name: "Students", col: 5, kind: "line", axis: "left", color: "--line-levy-actual", fmt: one, endLabel: function (v) { return "Students " + pct(v); } },
               { name: "School staff", col: 4, kind: "line", axis: "left", color: "--line-education", muted: true, fmt: one, endLabel: function (v) { return "School staff " + pct(v); } },
               { name: "Police and fire positions", col: 2, kind: "line", axis: "left", color: "--line-levy", fmt: one, width: 3.4, endLabel: function (v) { return "Police and fire " + pct(v); } },
               { name: "Other Town department positions", col: 3, kind: "line", axis: "left", color: "--line-benefits", muted: true, fmt: one, endLabel: function (v) { return "Other Town " + pct(v); } }],
      note: function (svg, xc, yl) {
        R.forEach(function (r, i) {
          if (!r[6]) return;
          svg.appendChild(svgEl("circle", { cx: xc(i), cy: yl(r[1]), r: 6.5, fill: "none", stroke: css("--ink"), "stroke-width": 1.6 }));
          var t = svgEl("text", { x: xc(i), y: yl(r[1]) - 12, class: "tick-label", "text-anchor": "middle", "font-size": "11", fill: css("--ink") }); t.textContent = "Census count"; svg.appendChild(t);
        });
      },
      aria: "Line chart, FY" + b[0] + " to FY" + last[0] + ", each line set to 100 in FY" + b[0] + ". Homes by the Census: " + glN(b[1]) + " in 2010 and " + glN(S.filter(function (r) { return r[0] === 2020; })[0][1]) +
        " in 2020, estimated in between and after. Students " + glN(b[6]) + " to " + glN(last[6]) + "; school staff " + Math.round(b[5]) + " to " + Math.round(last[5]) +
        "; police and fire positions " + Math.round(b[3]) + " to " + Math.round(last[3]) + "; other Town department positions " + Math.round(b[4]) + " to " + Math.round(last[4]) + "." });
    fillTable("gl-services-table", ["Year", "Homes, Census trend", "Homes, assessment rolls", "Students", "School staff", "Police and fire positions", "Other Town department positions"],
      S.map(function (r) { return ["FY" + r[0], glN(r[1]) + (r[2] ? " (Census)" : " (estimate)"), r[7] == null ? "&ndash;" : glN(r[7]), glN(r[6]), r[5].toFixed(1), r[3].toFixed(1), r[4].toFixed(1)]; }));
  }
  // How far ahead each reading looks: a timeline in years from when the reading is in hand.
  // rows: { label, wait: years between the event and the reading (shown left of 0),
  //         strong: [from, to] where it predicts closely, loose: [from, to] where it still informs, note }
  function drawGlLeadsChart() {
    var svg = document.getElementById("gl-leads-svg");
    if (!svg || !SD || !SD.growthLinks || !SD.growthLinks.leads) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var L = SD.growthLinks.leads, W = 900, rowH = 62, m = { top: 40, right: 24, bottom: 46, left: 210 };
    var H = m.top + m.bottom + rowH * L.length, iw = W - m.left - m.right, x0 = -2, x1 = 16;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var x = function (v) { return m.left + (v - x0) / (x1 - x0) * iw; };
    for (var g = 0; g <= x1; g += 2) {
      svg.appendChild(svgEl("line", { x1: x(g), x2: x(g), y1: m.top - 8, y2: H - m.bottom, class: "gridline" }));
      var t = svgEl("text", { x: x(g), y: H - m.bottom + 18, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); t.textContent = g === 0 ? "Now" : "+" + g; svg.appendChild(t);
    }
    var xt = svgEl("text", { x: x(7), y: H - 8, class: "tick-label", "text-anchor": "middle", "font-size": "12" }); xt.textContent = "Years after the reading is in hand"; svg.appendChild(xt);
    svg.appendChild(svgEl("line", { x1: x(0), x2: x(0), y1: m.top - 14, y2: H - m.bottom, stroke: css("--ink"), "stroke-width": 1.5 }));
    var k1 = svgEl("text", { x: x(-1), y: m.top - 18, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); k1.textContent = "Waiting for it"; svg.appendChild(k1);
    L.forEach(function (r, i) {
      var cy = m.top + rowH * i + rowH / 2 - 6;
      var lab = svgEl("text", { x: m.left - 12, y: cy + 4, "text-anchor": "end", "font-size": "13", fill: css("--ink") }); lab.textContent = r.label; svg.appendChild(lab);
      if (r.wait) svg.appendChild(svgEl("rect", { x: x(-r.wait), y: cy - 5, width: x(0) - x(-r.wait), height: 10, fill: css("--ink-faint"), opacity: 0.35 }));
      if (r.loose) svg.appendChild(svgEl("rect", { x: x(r.loose[0]), y: cy - 9, width: Math.max(4, x(r.loose[1]) - x(r.loose[0])), height: 18, rx: 3, fill: css("--pine"), opacity: 0.28 }));
      if (r.strong) svg.appendChild(svgEl("rect", { x: x(r.strong[0]), y: cy - 9, width: Math.max(6, x(r.strong[1]) - x(r.strong[0])), height: 18, rx: 3, fill: css("--pine") }));
      var nt = svgEl("text", { x: x(r.noteAt) + 4, y: cy + 24, "font-size": "11.5", class: "tick-label", fill: css("--ink-muted") }); nt.textContent = r.note; svg.appendChild(nt);
    });
    var leg = document.getElementById("gl-leads-legend");
    if (leg) leg.innerHTML = [["--ink-faint", 0.35, "Delay before the number is published"], ["--pine", 1, "What it predicts closely"], ["--pine", 0.28, "What it still informs, more loosely"]].map(function (l) {
      return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(l[0]) + ';opacity:' + l[1] + '"></span><span>' + l[2] + '</span></div>'; }).join("");
    svg.setAttribute("aria-label", "Timeline of how far ahead each reading looks. " + L.map(function (r) { return r.label + ": " + r.text; }).join(" ") );
    fillTable("gl-leads-table", ["Reading", "How far ahead it looks"], L.map(function (r) { return [r.label, r.text]; }));
  }
  function drawGlEnrollChart() {
    if (!SD || !SD.growthLinks) return;
    var R = SD.growthLinks.enrollment;
    drawYearChart({ id: "gl-enroll", rows: R, xHead: "Fall", xLabel: function (r) { return String(r[0]); },
      left: [0, 800, 100, glN], right: null,
      series: [{ name: "New housing units authorized", col: 3, kind: "bar", axis: "left", color: "--line-ref", fmt: glN },
               { name: "Births five years earlier", col: 2, kind: "line", axis: "left", color: "--line-levy", dash: true, fmt: glN },
               { name: "Kindergartners", col: 1, kind: "line", axis: "left", color: "--pine", fmt: glN }],
      aria: "Chart of Brookline kindergartners each fall, " + R[0][0] + " to " + R[R.length - 1][0] + ", resident births five years earlier, and new housing units authorized by building permit. " +
        "Kindergarten tracked births: " + R.map(function (r) { return r[0] + ", " + r[1] + " kindergartners, " + (r[2] == null ? "births n/a" : r[2] + " births") + ", " + (r[3] == null ? "units n/a" : r[3] + " units"); }).join("; ") + "." });
  }
  function drawGlSalesChart() {
    if (!SD || !SD.growthLinks) return;
    var R = SD.growthLinks.sales;
    drawYearChart({ id: "gl-sales", rows: R, xHead: "Year", xLabel: function (r) { return String(r[0]); },
      left: [0, 250, 50, glN], right: [0.7, 1.05, 0.05, function (v) { return v.toFixed(2); }],
      series: [{ name: "Single-family homes sold", col: 1, kind: "bar", axis: "left", color: "--line-ref", fmt: glN },
               { name: "Kindergartners per birth five years earlier", col: 2, kind: "line", axis: "right", color: "--pine", fmt: function (v) { return v == null ? "&ndash;" : v.toFixed(2); } }],
      aria: "Chart of single-family home sales in Brookline each year, " + R[0][0] + " to " + R[R.length - 1][0] + ", and kindergartners that fall per resident birth five years earlier. " +
        R.map(function (r) { return r[0] + ": " + r[1] + " sales, " + (r[2] == null ? "n/a" : r[2].toFixed(2)); }).join("; ") + "." });
  }
  function drawGlTownsChart() {
    var svg = document.getElementById("gl-towns-svg");
    if (!svg || !SD || !SD.growthLinks) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var T = SD.growthLinks.towns, F = SD.growthLinks.towns_fit, C = SD.growthLinks.summary.children;
    var W = 900, H = 420, m = { top: 20, right: 30, bottom: 50, left: 64 }, iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var x0 = -5, x1 = 40, y0 = -40, y1 = 40;
    var x = function (v) { return m.left + (Math.max(x0, Math.min(x1, v)) - x0) / (x1 - x0) * iw; }, y = function (v) { return m.top + (y1 - Math.max(y0, Math.min(y1, v))) / (y1 - y0) * ih; };
    for (var g = y0; g <= y1; g += 10) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(g), y2: y(g), class: "gridline" }));
      var t = svgEl("text", { x: m.left - 8, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); t.textContent = (g > 0 ? "+" : "") + g + "%"; svg.appendChild(t);
    }
    for (var gx = 0; gx <= x1; gx += 10) {
      var tx = svgEl("text", { x: x(gx), y: m.top + ih + 20, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tx.textContent = "+" + gx + "%"; svg.appendChild(tx);
    }
    var xl = svgEl("text", { x: m.left + iw / 2, y: H - 8, class: "tick-label", "text-anchor": "middle", "font-size": "12" }); xl.textContent = "Growth in homes, 2010 to 2020"; svg.appendChild(xl);
    var yt = svgEl("text", { x: 14, y: m.top + ih / 2, class: "tick-label", "text-anchor": "middle", "font-size": "12", transform: "rotate(-90 14 " + (m.top + ih / 2) + ")" }); yt.textContent = "Change in children under 18"; svg.appendChild(yt);
    T.forEach(function (p) {
      if (p[0] === "brookline") return;
      svg.appendChild(svgEl("circle", { cx: x(p[1]), cy: y(p[2]), r: 3.2, fill: css("--line-ref"), opacity: 0.55 }));
    });
    // fitted line: children change = a + b x growth in homes
    svg.appendChild(svgEl("line", { x1: x(0), y1: y((F[0] + F[1] * 0) * 100), x2: x(x1), y2: y((F[0] + F[1] * x1 / 100) * 100), stroke: css("--pine"), "stroke-width": 2.6 }));
    // where the line would be if an added home brought as many children as an existing one
    svg.appendChild(svgEl("line", { x1: x(0), y1: y(F[0] * 100), x2: x(x1), y2: y((F[0] + 1 * x1 / 100) * 100), stroke: css("--line-levy"), "stroke-width": 2, "stroke-dasharray": "6,4" }));
    var bk = T.filter(function (p) { return p[0] === "brookline"; })[0];
    if (bk) {
      svg.appendChild(svgEl("circle", { cx: x(bk[1]), cy: y(bk[2]), r: 6, fill: css("--pine"), stroke: css("--paper"), "stroke-width": 1.5 }));
      var bl = svgEl("text", { x: x(bk[1]) + 10, y: y(bk[2]) + 4, class: "tick-label", "font-size": "12", fill: css("--ink") }); bl.textContent = "Brookline"; svg.appendChild(bl);
    }
    var tooltip = document.getElementById("gl-towns-tooltip"), wrap = document.getElementById("gl-towns-wrap");
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" }); svg.appendChild(hit);
    var title = function (k) { return k.replace(/\b\w/g, function (c) { return c.toUpperCase(); }); };
    hit.addEventListener("mousemove", function (e) {
      var b = svg.getBoundingClientRect(), mx = (e.clientX - b.left) * (W / b.width), my = (e.clientY - b.top) * (H / b.height);
      var best = null, bd = 1e9;
      T.forEach(function (p) { var d = Math.pow(x(p[1]) - mx, 2) + Math.pow(y(p[2]) - my, 2); if (d < bd) { bd = d; best = p; } });
      if (!best || bd > 400) { tooltip.style.opacity = 0; return; }
      tipAt(tooltip, wrap, e, '<div class="tt-title">' + title(best[0]) + '</div><div class="tt-row"><span>Homes</span><span>' + (best[1] >= 0 ? "+" : "") + best[1].toFixed(1) +
        '%</span></div><div class="tt-row"><span>Children</span><span>' + (best[2] >= 0 ? "+" : "") + best[2].toFixed(1) + '%</span></div>');
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    var leg = document.getElementById("gl-towns-legend");
    if (leg) leg.innerHTML = [["--line-ref", "A city or town"], ["--pine", "Fitted line: " + C.children_per_added_home.toFixed(2) + " children per added home"],
      ["--line-levy", "If added homes matched existing ones (" + C.children_per_existing_home.toFixed(2) + ")"]].map(function (l) {
      return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(l[0]) + '"></span><span>' + l[1] + '</span></div>'; }).join("");
    svg.setAttribute("aria-label", "Scatter chart of " + T.length + " Massachusetts cities and towns: growth in homes from 2010 to 2020 against the change in residents under 18. " +
      "Towns that added more homes lost fewer children or gained more, but the fitted line rises about half as steeply as it would if added homes held as many children as existing ones: about " +
      C.children_per_added_home.toFixed(2) + " children per added home against " + C.children_per_existing_home.toFixed(2) + " per existing home. Brookline: homes " +
      (bk ? "+" + bk[1].toFixed(1) + "%, children +" + bk[2].toFixed(1) + "%" : "") + ".");
    fillTable("gl-towns-table", ["City or town", "Growth in homes, 2010 to 2020", "Change in children under 18"],
      T.slice().sort(function (a, b) { return b[1] - a[1]; }).map(function (p) { return [title(p[0]), p[1].toFixed(1) + "%", p[2].toFixed(1) + "%"]; }));
  }

  // ---- A TYPICAL TAX BILL TO FY2040, four paths (tax_bill_paths.py)
  var BILL_PATHS = [["base", "Base case", "--pine", false], ["override", "Another override", "--line-levy", false],
                    ["baker", "Baker School debt exclusion", "--line-levy-actual", true], ["growth", "Faster new growth", "--line-benefits", true]];
  var BILL_HOMES = { single_family: "single-family home", two_family: "two-family home", condo: "condominium", apartment: "rental apartment" };
  var $0 = function (v) { return "$" + Math.round(v).toLocaleString("en-US"); };
  // average growth a year over the whole forecast, FY2026 to FY2040
  function billCagr(v) { return (Math.pow(v[v.length - 1] / v[0], 1 / (v.length - 1)) - 1) * 100; }
  function billCagrText(v) { return billCagr(v).toFixed(1) + "% a year"; }
  // One line chart of a bill on the four paths; the median-home chart and the calculator share it.
  // ids: prefix of the svg, tooltip, wrap, legend and table elements; what: the bill's description.
  function drawBillLines(ids, b0, what) {
    var svg = document.getElementById(ids + "-svg");
    if (!svg) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var TB = SD.taxBills, Y = TB.years;
    var W = 900, H = 380, m = { top: 20, right: 210, bottom: 40, left: 70 }, iw = W - m.left - m.right, ih = H - m.top - m.bottom;
    var all = []; BILL_PATHS.forEach(function (p) { TB.paths[p[0]].forEach(function (v) { all.push(v * b0); }); });
    var steps = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000];
    var span = Math.max.apply(null, all) * 1.02 - b0 * 0.95, step = steps.find(function (s) { return span / s <= 8; }) || 200000;
    var lo = Math.floor(b0 * 0.95 / step) * step, hi = Math.ceil(Math.max.apply(null, all) * 1.02 / step) * step;
    var x = function (yr) { return m.left + (yr - Y[0]) / (Y[Y.length - 1] - Y[0]) * iw; }, y = function (v) { return m.top + (hi - v) / (hi - lo) * ih; };
    for (var g = lo; g <= hi; g += step) {
      svg.appendChild(svgEl("line", { x1: m.left, x2: m.left + iw, y1: y(g), y2: y(g), class: "gridline" }));
      var t = svgEl("text", { x: m.left - 8, y: y(g) + 4, class: "tick-label", "text-anchor": "end", "font-size": "11" }); t.textContent = $0(g); svg.appendChild(t);
    }
    for (var yr = Y[0]; yr <= Y[Y.length - 1]; yr += 2) {
      var tl = svgEl("text", { x: x(yr), y: m.top + ih + 22, class: "tick-label", "text-anchor": "middle", "font-size": "11" }); tl.textContent = "FY" + String(yr).slice(2); svg.appendChild(tl);
    }
    var ends = [];
    BILL_PATHS.forEach(function (p) {
      var D = TB.paths[p[0]].map(function (v, i) { return [Y[i], v * b0]; });
      var a = { d: "M" + D.map(function (q) { return x(q[0]) + "," + y(q[1]); }).join(" L"), fill: "none", stroke: css(p[2]), "stroke-width": p[0] === "base" ? 3 : 2.2, "stroke-linejoin": "round" };
      if (p[3]) a["stroke-dasharray"] = "6,4";
      svg.appendChild(svgEl("path", a));
      ends.push({ v: D[D.length - 1][1], label: p[1], color: p[2] });
    });
    ends.sort(function (a, b) { return b.v - a.v; });
    var lastY = -1e9;
    ends.forEach(function (e) {
      var yy = Math.max(y(e.v) + 4, lastY + 14); lastY = yy;
      var lt = svgEl("text", { x: x(Y[Y.length - 1]) + 8, y: yy, class: "tick-label", "font-size": "11.5", fill: css("--ink") });
      lt.textContent = e.label + " " + $0(e.v); svg.appendChild(lt);
    });
    var tooltip = document.getElementById(ids + "-tooltip"), wrap = document.getElementById(ids + "-wrap");
    var hit = svgEl("rect", { x: m.left, y: m.top, width: iw, height: ih, fill: "transparent" }); svg.appendChild(hit);
    hit.addEventListener("mousemove", function (e) {
      var r = svg.getBoundingClientRect(), mx = (e.clientX - r.left) * (W / r.width), i = Math.max(0, Math.min(Y.length - 1, Math.round((mx - m.left) / iw * (Y.length - 1))));
      tipAt(tooltip, wrap, e, '<div class="tt-title">FY' + Y[i] + ', ' + what + '</div>' +
        BILL_PATHS.map(function (p) { return '<div class="tt-row"><span>' + p[1] + '</span><span>' + $0(TB.paths[p[0]][i] * b0) + '</span></div>'; }).join(""));
    });
    hit.addEventListener("mouseleave", function () { tooltip.style.opacity = 0; });
    var leg = document.getElementById(ids + "-legend");
    if (leg) leg.innerHTML = BILL_PATHS.map(function (p) {
      return '<div class="legend-item"><span class="legend-swatch" style="background:' + css(p[2]) + '"></span><span>' + p[1] + ': ' + billCagrText(TB.paths[p[0]]) + '</span></div>';
    }).join("");
    var j = Y.length - 1;
    svg.setAttribute("aria-label", "Line chart of " + what + "'s tax bill, FY" + Y[0] + " to FY" + Y[j] + ", for a home whose value moves with the town average. It starts at " + $0(b0) +
      ". In FY" + Y[j] + " it is " + BILL_PATHS.map(function (p) { return $0(TB.paths[p[0]][j] * b0) + " in the " + p[1].toLowerCase() + " path, up " + billCagrText(TB.paths[p[0]]); }).join("; ") + ".");
    fillTable(ids + "-table", ["Year"].concat(BILL_PATHS.map(function (p) { return p[1]; })),
      Y.map(function (yy, i) { return ["FY" + yy].concat(BILL_PATHS.map(function (p) { return $0(TB.paths[p[0]][i] * b0); })); })
        .concat([["Growth a year, FY" + Y[0] + "&ndash;" + String(Y[j]).slice(2)].concat(BILL_PATHS.map(function (p) { return billCagr(TB.paths[p[0]]).toFixed(1) + "%"; }))]));
  }
  function drawTaxBillChart() {
    if (!SD || !SD.taxBills) return;
    var sel = document.getElementById("taxbill-home"), home = sel ? sel.value : "single_family";
    drawBillLines("taxbill", SD.taxBills.medians[home][1], (home === "apartment" ? "the average " : "the median ") + BILL_HOMES[home]);
  }
  (function () { var s = document.getElementById("taxbill-home"); if (s) s.addEventListener("change", drawTaxBillChart); })();

  // ---- YOUR BILL: a small calculator on the same four paths
  function updateBillCalc() {
    var out = document.getElementById("billcalc-out");
    if (!out || !SD || !SD.taxBills) return;
    var TB = SD.taxBills, mode = document.querySelector('input[name="billcalc-mode"]:checked');
    var v = parseFloat((document.getElementById("billcalc-value").value || "").replace(/[$,\s]/g, ""));
    var owner = document.getElementById("billcalc-owner").checked;
    var billIn = parseFloat((document.getElementById("billcalc-bill").value || "").replace(/[$,\s]/g, ""));
    var b0 = mode && mode.value === "bill" ? billIn : (isFinite(v) ? Math.max(v - (owner ? TB.exemption : 0), 0) * TB.rate : NaN);
    var chart = document.getElementById("billcalc-chart");
    if (!isFinite(b0) || b0 <= 0) { out.innerHTML = "<p>Enter an assessed value or a FY2026 bill to see it projected.</p>"; if (chart) chart.hidden = true; return; }
    if (chart) { chart.hidden = false; drawBillLines("billcalc", b0, "your home"); }
    var cols = [2026, 2030, 2035, 2040], Y = TB.years;
    var h = "<p><strong>FY2026 bill: " + $0(b0) + ".</strong> Projected, for a home whose value moves with the town average:</p>" +
      '<table class="data-table"><thead><tr><th scope="col">Path</th>' + cols.map(function (c) { return '<th scope="col">FY' + c + "</th>"; }).join("") +
      '<th scope="col">Growth a year</th></tr></thead><tbody>';
    BILL_PATHS.forEach(function (p) {
      h += '<tr><th scope="row">' + p[1] + "</th>" + cols.map(function (c) { return "<td>" + $0(TB.paths[p[0]][Y.indexOf(c)] * b0) + "</td>"; }).join("") +
        "<td>" + billCagr(TB.paths[p[0]]).toFixed(1) + "%</td></tr>";
    });
    out.innerHTML = h + "</tbody></table>";
  }
  (function () {
    ["billcalc-value", "billcalc-owner", "billcalc-bill"].forEach(function (id) {
      var el = document.getElementById(id); if (el) el.addEventListener("input", updateBillCalc);
    });
    document.querySelectorAll('input[name="billcalc-mode"]').forEach(function (el) {
      el.addEventListener("change", function () {
        var byBill = el.value === "bill" && el.checked;
        document.getElementById("billcalc-by-value").hidden = byBill;
        document.getElementById("billcalc-by-bill").hidden = !byBill;
        updateBillCalc();
      });
    });
  })();

  function render() {
    drawSankey();
    drawFundsSankey();
    drawExpenseGrowthChart();
    drawLineChart();
    drawWaterfallChart();
    drawLiabilityChart();
    drawControlChart();
    drawUnitBreakevenChart();
    drawDecisionsChart();
    drawGrowthPathsChart();
    drawGrowthMixChart();
    drawSeatsChart();
    drawHousingFillChart();
    drawSeatsHomesChart();
    drawHomeNetChart();
    fillExtraTables();
    drawOutlookChart();
    drawDecideChart();
    drawCausesChart();
    drawWhoSetsChart();
    drawEnrollAssumeChart();
    drawBirthsWatchChart();
    drawBirthsTownsChart();
    drawKpbHousingChart();
    drawStudentsBedroomsChart();
    drawOwnerFlowChart();
    drawYearsInHomeChart();
    drawStaffEnrollChart();
    drawEmployeesChart();
    drawGlRevenueChart();
    drawGlServicesChart();
    drawGlEnrollChart();
    drawGlTownsChart();
    drawGlSalesChart();
    drawGlLeadsChart();
    drawTaxBillChart();
    updateBillCalc();
  }
  render();
  // the waterfall measures its stat cards, whose height depends on the web fonts
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(drawWaterfallChart);
  window.addEventListener("resize", function () {
    clearTimeout(window.__rt);
    window.__rt = setTimeout(render, 150);
  });

  // theme change redraw (colors are CSS vars, resolved at draw time)
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);
  }
  // redraw for print, so a dark-mode reader's charts print in the light palette
  if (window.matchMedia) {
    var pm = window.matchMedia("print");
    if (pm.addEventListener) pm.addEventListener("change", render);
  }
  window.addEventListener("beforeprint", render);
  window.addEventListener("afterprint", render);

  // table toggles
  document.querySelectorAll(".toggle-table-btn").forEach(function (btn) {
    btn.setAttribute("aria-expanded", "false");
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.dataset.target);
      var open = target.classList.toggle("open");
      btn.textContent = open ? "Hide data table" : "Show data table";
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });
})();
