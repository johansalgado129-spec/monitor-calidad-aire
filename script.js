(() => {
  const cfg = window.APP_CONFIG || { API_BASE: "" };
  const $ = (sel) => document.querySelector(sel);
  const apiBase = (cfg.API_BASE || "").replace(/\/$/, "");

  const menuBtn = $("#menuBtn");
  const mainNav = $("#mainNav");
  menuBtn?.addEventListener("click", () => {
    const open = mainNav.classList.toggle("open");
    menuBtn.setAttribute("aria-expanded", String(open));
  });
  mainNav?.querySelectorAll("a").forEach(a => a.addEventListener("click", () => mainNav.classList.remove("open")));

  function fmt(value, digits = 1) {
    const n = value == null || value === "" ? NaN : Number(value);
    return Number.isFinite(n) ? n.toFixed(digits) : "—";
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"}[c]));
  }

  function formatDate(value) {
    if (!value) return "—";
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? value : new Intl.DateTimeFormat("es-CO", {dateStyle:"medium", timeStyle:"short"}).format(d);
  }

  function api(path) {
    return `${apiBase}${path}`;
  }

  async function fetchJson(path) {
    const res = await fetch(api(path), {headers:{Accept:"application/json"}});
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body.detail || `Error HTTP ${res.status}`);
    return body;
  }

  function whoText(oms) {
    if (!oms || typeof oms !== "object") return "Sin referencia compatible";
    const labels = {pm25:"PM2.5", no2:"NO₂", o3:"O₃"};
    const parts = Object.entries(oms)
      .filter(([,v]) => v)
      .map(([k,v]) => `${labels[k] || k}: ${v.estado}`);
    return parts.length ? parts.join(" · ") : "Sin referencia compatible";
  }

  function adapt(json) {
    const m = json.mediciones || {};
    return {
      city: json.ciudad || "Ciudad consultada",
      date: json.fecha,
      source: json.fuente || "OpenAQ API v3",
      pm25: m.pm25_24h_ug_m3,
      no2: m.no2_24h_ug_m3,
      o3: m.o3_8h_ug_m3,
      aqi: json.aqi,
      category: json.categoria || "Sin clasificación",
      who: whoText(json.oms),
      message: json.recomendacion || json.nota || "Consulta procesada por el backend.",
      stations: Array.isArray(json.estaciones_utilizadas) ? json.estaciones_utilizadas.length : 0,
    };
  }

  function renderPollutants(data) {
    const items = [
      ["PM2.5", data.pm25, "µg/m³", "Promedio aproximado de 24 horas."],
      ["NO₂", data.no2, "µg/m³", "Promedio aproximado de 24 horas para referencia OMS."],
      ["O₃", data.o3, "µg/m³", "Promedio aproximado de 8 horas."],
    ];
    $("#pollutantGrid").innerHTML = items.map(([name,value,unit,desc]) => `
      <article class="pollutant-card">
        <div class="top"><h3>${name}</h3><span class="tag">OpenAQ</span></div>
        <div><span class="pollutant-value">${fmt(value)}</span><span class="pollutant-unit">${unit}</span></div>
        <p>${desc}</p>
      </article>`).join("");

    const numeric = items.map(x => x[1] == null ? NaN : Number(x[1])).filter(Number.isFinite);
    const max = Math.max(...numeric, 1);
    $("#barsChart").innerHTML = items.map(([n,v]) => {
      const num = v == null ? NaN : Number(v);
      const width = Number.isFinite(num) ? Math.max(4, (num/max)*100) : 0;
      return `<div class="bar-row"><strong>${n}</strong><div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div><div class="bar-value">${fmt(v)} µg/m³</div></div>`;
    }).join("");
  }

  function renderResult(data) {
    $("#resultsTitle").textContent = `Calidad del aire en ${data.city}`;
    $("#sourceLabel").textContent = data.source;
    $("#aqiValue").textContent = Number.isFinite(Number(data.aqi)) ? String(data.aqi) : "—";
    $("#aqiCategory").textContent = data.category;
    $("#aqiMessage").textContent = data.message;
    $("#metaCity").textContent = data.city;
    $("#metaDate").textContent = formatDate(data.date);
    $("#whoStatus").textContent = data.who;
    $("#stationCount").textContent = String(data.stations || 0);
    const pct = Math.min(100, Math.max(0, (Number(data.aqi) || 0) / 500 * 100));
    $("#aqiGauge").style.background = `conic-gradient(var(--blue-700) 0 ${pct}%,#e7eff5 ${pct}% 100%)`;
    renderPollutants(data);
  }

  async function renderHistory() {
    try {
      const payload = await fetchJson("/api/historial");
      const rows = payload.historial || [];
      $("#historyBody").innerHTML = rows.slice(0,50).map(r => `
        <tr>
          <td>${escapeHtml(formatDate(r.fecha))}</td><td>${escapeHtml(r.ciudad ?? "")}</td><td>${escapeHtml(r.aqi ?? "")}</td><td>${escapeHtml(r.categoria ?? "")}</td>
          <td>${escapeHtml(r.pm25_24h_ug_m3 ?? "—")}</td><td>${escapeHtml(r.no2_24h_ug_m3 ?? "—")}</td><td>${escapeHtml(r.o3_8h_ug_m3 ?? "—")}</td>
        </tr>`).join("");
      $("#emptyHistory").style.display = rows.length ? "none" : "block";
    } catch (err) {
      $("#historyBody").innerHTML = "";
      $("#emptyHistory").style.display = "block";
      $("#emptyHistory").textContent = `Historial no disponible: ${err.message}`;
    }
  }

  async function checkBackend() {
    const el = $("#backendStatus");
    try {
      const payload = await fetchJson("/salud");
      el.textContent = payload.openaq_configurada ? "Backend activo; OpenAQ configurado" : "Backend activo; falta configurar OPENAQ_API_KEY";
      el.classList.add("ok");
    } catch (err) {
      el.textContent = "Backend no disponible";
      el.classList.remove("ok");
    }
  }

  $("#queryForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const city = $("#cityInput").value.trim();
    const status = $("#queryStatus");
    const btn = $("#queryBtn");
    if (!city) return;
    btn.disabled = true;
    status.textContent = "Consultando OpenAQ desde el backend Python…";
    try {
      const json = await fetchJson(`/api/ciudad/${encodeURIComponent(city)}`);
      renderResult(adapt(json));
      await renderHistory();
      status.textContent = "Consulta completada y registrada en el historial.";
      location.hash = "resultados";
    } catch (err) {
      status.textContent = `No fue posible completar la consulta: ${err.message}`;
    } finally {
      btn.disabled = false;
    }
  });

  $("#downloadCsv").addEventListener("click", () => {
    window.location.href = api("/api/historial.csv");
  });

  checkBackend();
  renderHistory();
})();
