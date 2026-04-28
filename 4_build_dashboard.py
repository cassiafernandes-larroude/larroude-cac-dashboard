#!/usr/bin/env python3
"""
Step 4 — Build self-contained interactive HTML dashboard for CAC by product by day.
NEW: period selector (28D / 60D / 90D) — todos os blocos recalculam ao trocar.

Usage:
  python 4_build_dashboard.py --country br
  python 4_build_dashboard.py --country us
"""

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent

CONFIGS = {
    "br": {
        "input":   "cac_by_product.json",
        "output":  "dashboard_cac_br.html",
        "title":   "Larroude BR — CAC por Produto",
        "header":  "LARROUDE BR — CAC POR PRODUTO",
        "sub":     "Top 15 por volume + Top 15 menor CAC · Meta Ads BR (3 contas) + Shopify BR",
        "currency_symbol": "R$",
        "shop_label":   "Meta Ads (3 contas BR)",
        "fx_note":      "USD→BRL fixo: 5.10 (conta act_1735567560524487 reporta em USD)",
        "lang":         "pt-BR",
        "js_locale":    "pt-BR",
    },
    "us": {
        "input":   "cac_by_product_us.json",
        "output":  "dashboard_cac_us.html",
        "title":   "Larroude US — CAC por Produto",
        "header":  "LARROUDE US — CAC POR PRODUTO",
        "sub":     "Top 15 por volume + Top 15 menor CAC · Meta Ads US (3 contas) + Shopify US",
        "currency_symbol": "$",
        "shop_label":   "Meta Ads (3 contas US)",
        "fx_note":      "Sem conversão · todas as 3 contas + Shopify reportam em USD",
        "lang":         "pt-BR",
        "js_locale":    "en-US",
    },
}


def build(country):
    cfg = CONFIGS[country]
    data = json.loads((ROOT / cfg["input"]).read_text(encoding="utf-8"))

    js_currency = json.dumps({
        "symbol": cfg["currency_symbol"],
        "locale": cfg["js_locale"],
    })

    generated_at = data.get("generated_at") or date.today().isoformat()

    html = f"""<!DOCTYPE html>
<html lang="{cfg['lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{cfg['title']}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f1f5f9;color:#1e293b;line-height:1.4}}
.hdr{{background:#0f172a;color:#fff;padding:18px 32px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.hdr-title{{font-size:20px;font-weight:700;letter-spacing:-.5px}}
.hdr-sub{{font-size:12px;opacity:.65;margin-top:3px}}
.hdr-right{{text-align:right;font-size:11px;opacity:.55}}
.main{{max-width:1700px;margin:0 auto;padding:20px 28px}}
.toolbar-row{{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin-bottom:18px;background:#fff;border-radius:10px;padding:14px 18px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.nav{{display:flex;gap:10px}}
.nav a{{padding:8px 18px;border-radius:8px;background:#f8fafc;color:#475569;text-decoration:none;font-weight:600;font-size:13px;border:1.5px solid #e2e8f0}}
.nav a.act{{background:#0f172a;color:#fff;border-color:#0f172a}}
.nav a:hover:not(.act){{border-color:#059669;color:#059669}}
.period-group{{display:flex;gap:6px;align-items:center;margin-left:auto}}
.period-lbl{{font-size:12px;font-weight:600;color:#475569;margin-right:4px}}
.pbtn{{padding:7px 14px;border:1.5px solid #e2e8f0;background:#fff;border-radius:6px;cursor:pointer;font-size:12.5px;font-weight:600;color:#475569;transition:all .12s}}
.pbtn:hover{{border-color:#059669;color:#059669}}
.pbtn.act{{background:#059669;color:#fff;border-color:#059669}}
.window-tag{{font-size:11px;color:#64748b;margin-left:10px;padding-left:10px;border-left:1.5px solid #e2e8f0}}
.kgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin-bottom:18px}}
.kcard{{background:#fff;border-radius:10px;padding:16px 14px;box-shadow:0 1px 3px rgba(0,0,0,.06);border-left:3px solid #059669}}
.klbl{{font-size:10.5px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px}}
.kval{{font-size:22px;font-weight:700;color:#0f172a;line-height:1.1;margin-bottom:5px}}
.ksub{{font-size:11px;color:#64748b}}
.ccard{{background:#fff;border-radius:10px;padding:18px 20px;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:18px}}
.ccard h3{{font-size:14px;font-weight:700;color:#0f172a;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}}
.ccard h3 .sub{{font-size:11px;color:#64748b;font-weight:500}}
.ccard h3 .pill{{font-size:10.5px;font-weight:700;padding:3px 10px;border-radius:100px;letter-spacing:.5px;text-transform:uppercase}}
.pill-a{{background:#dbeafe;color:#1e40af}}
.pill-b{{background:#dcfce7;color:#166534}}
.tbl{{width:100%;border-collapse:collapse;font-size:12.5px}}
.tbl th{{text-align:left;padding:9px 10px;border-bottom:2px solid #e2e8f0;font-weight:600;color:#475569;cursor:pointer;user-select:none;white-space:nowrap}}
.tbl th:hover{{color:#059669}}
.tbl td{{padding:8px 10px;border-bottom:1px solid #f1f5f9;color:#334155}}
.tbl td.r{{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}}
.tbl tr{{cursor:pointer}}
.tbl tr:hover td{{background:#f8fafc}}
.tbl tr.sel td{{background:#ecfdf5}}
.bar{{height:14px;background:#dcfce7;border-radius:3px;display:inline-block;vertical-align:middle;margin-right:6px}}
.heat{{font-size:10.5px;border-collapse:collapse;font-variant-numeric:tabular-nums}}
.heat-wrap{{overflow:auto;max-width:100%;max-height:600px}}
.heat th, .heat td{{padding:5px 6px;text-align:center;border:1px solid #f1f5f9;white-space:nowrap}}
.heat th{{background:#f8fafc;color:#64748b;font-weight:600;position:sticky;top:0;z-index:1}}
.heat td.lbl{{text-align:left;background:#fff;font-weight:500;color:#0f172a;position:sticky;left:0;z-index:2;max-width:240px;overflow:hidden;text-overflow:ellipsis;cursor:pointer}}
.heat td.lbl.sel{{background:#ecfdf5}}
.heat th.dh{{font-size:9.5px;color:#94a3b8;font-weight:500}}
.heat tr.sep td{{background:#f1f5f9;font-size:10px;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:.5px;text-align:left;padding:6px 8px;border:1px solid #e2e8f0;position:sticky;left:0;z-index:1}}
.note{{font-size:11px;color:#94a3b8;line-height:1.6;background:#f8fafc;padding:12px 16px;border-radius:8px;border-left:3px solid #94a3b8;margin-top:8px}}
.note b{{color:#475569}}
.legend{{display:flex;align-items:center;gap:8px;font-size:10.5px;color:#64748b;margin-top:8px;flex-wrap:wrap}}
.legend-bar{{height:10px;width:120px;background:linear-gradient(90deg,#10b981,#fbbf24,#ef4444);border-radius:4px}}
.toolbar{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px}}
.toolbar select{{padding:6px 10px;border:1.5px solid #e2e8f0;border-radius:6px;font-size:12px;color:#334155;background:#fff;cursor:pointer}}
canvas{{display:block;width:100%!important;height:340px!important}}
</style>
</head>
<body>
<div class="hdr">
  <div>
    <div class="hdr-title">{cfg['header']}</div>
    <div class="hdr-sub">{cfg['sub']}</div>
  </div>
  <div class="hdr-right">Gerado: {generated_at}<br>{cfg['fx_note']}</div>
</div>

<div class="main">
  <div class="toolbar-row">
    <div class="nav">
      <a href="dashboard_cac_br.html" class="{'act' if country=='br' else ''}">🇧🇷 Brasil</a>
      <a href="dashboard_cac_us.html" class="{'act' if country=='us' else ''}">🇺🇸 United States</a>
    </div>
    <div class="period-group">
      <span class="period-lbl">Período:</span>
      <button class="pbtn" data-period="28">28D</button>
      <button class="pbtn" data-period="60">60D</button>
      <button class="pbtn" data-period="90">90D</button>
      <span class="window-tag" id="window-tag">—</span>
    </div>
  </div>

  <div class="kgrid">
    <div class="kcard">
      <div class="klbl">CAC Blended · Top Volume</div>
      <div class="kval" id="k-cac-vol">—</div>
      <div class="ksub" id="k-cac-vol-sub">—</div>
    </div>
    <div class="kcard" style="border-left-color:#10b981">
      <div class="klbl">CAC Blended · Menor CAC</div>
      <div class="kval" id="k-cac-low">—</div>
      <div class="ksub" id="k-cac-low-sub">—</div>
    </div>
    <div class="kcard" style="border-left-color:#3b82f6">
      <div class="klbl">Spend Total</div>
      <div class="kval" id="k-spend">—</div>
      <div class="ksub">{cfg['shop_label']}</div>
    </div>
    <div class="kcard" style="border-left-color:#8b5cf6">
      <div class="klbl">Spend Top Volume</div>
      <div class="kval" id="k-spend-vol">—</div>
      <div class="ksub" id="k-spend-vol-sub">—</div>
    </div>
    <div class="kcard" style="border-left-color:#f59e0b">
      <div class="klbl">Spend Menor CAC</div>
      <div class="kval" id="k-spend-low">—</div>
      <div class="ksub" id="k-spend-low-sub">—</div>
    </div>
    <div class="kcard" style="border-left-color:#ec4899">
      <div class="klbl">Pedidos no Período</div>
      <div class="kval" id="k-orders">—</div>
      <div class="ksub">Todos os produtos</div>
    </div>
  </div>

  <div class="ccard">
    <h3>
      <span><span class="pill pill-a">A · Volume</span> &nbsp; Top 15 Produtos · por Unidades Vendidas</span>
      <span class="sub">Clique no cabeçalho para ordenar · Clique numa linha para destacar</span>
    </h3>
    <table class="tbl" id="tbl-units">
      <thead>
        <tr>
          <th data-sort="rank">#</th>
          <th data-sort="title">Produto</th>
          <th data-sort="units" class="r">Unidades</th>
          <th data-sort="revenue" class="r">Receita</th>
          <th data-sort="new_customers" class="r">Novos Clientes</th>
          <th data-sort="allocated_spend" class="r">Spend Alocado</th>
          <th data-sort="cac" class="r">CAC</th>
          <th data-sort="ratio" class="r">Receita/Cliente</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="ccard">
    <h3>
      <span><span class="pill pill-b">B · Eficiência</span> &nbsp; Top 15 Produtos · Menor CAC</span>
      <span class="sub" id="filter-sub">—</span>
    </h3>
    <table class="tbl" id="tbl-lowcac">
      <thead>
        <tr>
          <th data-sort="rank">#</th>
          <th data-sort="title">Produto</th>
          <th data-sort="cac" class="r">CAC</th>
          <th data-sort="new_customers" class="r">Novos Clientes</th>
          <th data-sort="allocated_spend" class="r">Spend Alocado</th>
          <th data-sort="units" class="r">Unidades</th>
          <th data-sort="revenue" class="r">Receita</th>
          <th data-sort="ratio" class="r">Receita/Cliente</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="ccard">
    <h3>Tendência Diária · CAC por Produto
      <span class="sub">Selecione um produto da união A∪B</span>
    </h3>
    <div class="toolbar">
      <label style="font-size:12px;color:#475569;font-weight:600">Produto:</label>
      <select id="prodSel"></select>
      <label style="font-size:12px;color:#475569;font-weight:600;margin-left:14px">Métrica:</label>
      <select id="metricSel">
        <option value="cac">CAC ({cfg['currency_symbol']})</option>
        <option value="new_customers">Novos Clientes</option>
        <option value="spend">Spend Alocado ({cfg['currency_symbol']})</option>
        <option value="revenue">Receita ({cfg['currency_symbol']})</option>
        <option value="units">Unidades</option>
      </select>
    </div>
    <canvas id="trendChart"></canvas>
  </div>

  <div class="ccard">
    <h3>Matriz Diária · CAC por Produto × Dia
      <span class="sub">Verde = CAC baixo · Vermelho = CAC alto · Cinza = sem novo cliente</span>
    </h3>
    <div class="heat-wrap">
      <table class="heat" id="heat">
        <thead><tr id="heat-head"></tr></thead>
        <tbody id="heat-body"></tbody>
      </table>
    </div>
    <div class="legend">
      <span>CAC menor</span><div class="legend-bar"></div><span>CAC maior</span>
      <span style="margin-left:24px;display:inline-block;width:14px;height:14px;background:#f1f5f9;border-radius:3px;vertical-align:middle"></span>
      <span>Sem novo cliente</span>
    </div>
  </div>

  <div class="note">
    <b>Metodologia.</b> CAC = (spend alocado ao produto) ÷ (novos clientes que compraram o produto).
    <br><b>Spend alocado:</b> o spend total diário do Meta Ads é distribuído entre TODOS os produtos proporcionalmente à fatia de receita de cada produto no dia. {cfg['fx_note']}.
    <br><b>Novo cliente:</b> pedido onde <code>customer.numberOfOrders == 1</code>. Se o pedido tem múltiplos produtos, todos contam +1.
    <br><b>Tabela B (menor CAC):</b> filtrada por mínimo de novos clientes que escala com a janela (≥20 em 28D, ≥43 em 60D, ≥64 em 90D) — proporcional ao tempo, anti-ruído.
    <br><b>Limitações:</b> (1) atribuição proporcional não é uma medição direta campaign-to-product; (2) clientes "novos" cujo segundo pedido aconteça antes da consulta podem ser perdidos; (3) Google Ads não está incluído.
  </div>
</div>

<script>
const DATA = {json.dumps(data, ensure_ascii=False)};
const CCY = {js_currency};

const fmtMoney=v=>v==null?'—':CCY.symbol+' '+v.toLocaleString(CCY.locale,{{maximumFractionDigits:0}});
const fmtInt=v=>v==null?'—':v.toLocaleString(CCY.locale);
const fmtPct=v=>(v*100).toFixed(1)+'%';
const fmtDate=s=>{{const [y,m,d]=s.split('-');return `${{d}}/${{m}}`}};

let currentPeriod = '28';
let selPid = null;
let sortStateA = {{key:'rank', dir:1}};
let sortStateB = {{key:'rank', dir:1}};
let chart = null;

function getPeriod(){{ return DATA.periods[currentPeriod]; }}

function cacRange(period){{
  let mn=Infinity,mx=-Infinity;
  period.products.forEach(p=>p.daily.forEach(x=>{{if(x.cac!=null){{mn=Math.min(mn,x.cac);mx=Math.max(mx,x.cac)}}}}));
  return [mn,mx];
}}
function colorForCac(c, mn, mx){{
  if(c==null) return '#f1f5f9';
  const t=Math.max(0,Math.min(1,(c-mn)/(mx-mn||1)));
  if(t<0.5){{
    const k=t/0.5;
    const r=Math.round(16+(251-16)*k), g=Math.round(185+(191-185)*k), b=Math.round(129+(36-129)*k);
    return `rgb(${{r}},${{g}},${{b}})`;
  }} else {{
    const k=(t-0.5)/0.5;
    const r=Math.round(251+(239-251)*k), g=Math.round(191+(68-191)*k), b=Math.round(36+(68-36)*k);
    return `rgb(${{r}},${{g}},${{b}})`;
  }}
}}

function tableRows(period, ids){{
  const byId = Object.fromEntries(period.products.map(p=>[p.product_id, p]));
  return ids.map((pid,i)=>{{
    const p = byId[pid];
    if(!p) return null;
    return {{
      ...p,
      rank: i+1,
      ratio: p.new_customers ? p.revenue/p.new_customers : null,
    }};
  }}).filter(Boolean);
}}

function sortRows(rows, state){{
  const arr=rows.slice();
  arr.sort((a,b)=>{{
    const av=a[state.key], bv=b[state.key];
    if(av==null&&bv==null) return 0;
    if(av==null) return 1; if(bv==null) return -1;
    if(typeof av==='string') return state.dir*(av.localeCompare(bv));
    return state.dir*(av-bv);
  }});
  return arr;
}}

function renderKPIs(){{
  const p = getPeriod();
  const s = p.summary;
  document.getElementById('k-cac-vol').textContent = fmtMoney(s.top15_units_blended_cac);
  document.getElementById('k-cac-vol-sub').textContent = `15 mais vendidos · ${{fmtInt(s.top15_units_new_customers)}} novos`;
  document.getElementById('k-cac-low').textContent = fmtMoney(s.top15_lowcac_blended_cac);
  document.getElementById('k-cac-low-sub').textContent = `15 mais eficientes · ${{fmtInt(s.top15_lowcac_new_customers)}} novos`;
  document.getElementById('k-spend').textContent = fmtMoney(s.total_marketing_spend);
  document.getElementById('k-spend-vol').textContent = fmtMoney(s.top15_units_allocated_spend);
  document.getElementById('k-spend-vol-sub').textContent = fmtPct(s.top15_units_allocated_spend / (s.total_marketing_spend||1)) + ' do total';
  document.getElementById('k-spend-low').textContent = fmtMoney(s.top15_lowcac_allocated_spend);
  document.getElementById('k-spend-low-sub').textContent = fmtPct(s.top15_lowcac_allocated_spend / (s.total_marketing_spend||1)) + ' do total';
  document.getElementById('k-orders').textContent = fmtInt(s.total_orders_in_window);
  document.getElementById('window-tag').textContent = `Janela ${{p.window_start}} → ${{p.window_end}}`;
  document.getElementById('filter-sub').textContent = `Filtro: ≥ ${{s.min_new_customers_lowcac_filter}} novos clientes em ${{s.days}}D (anti-ruído) · Clique para destacar`;
}}

function renderTableA(){{
  const p = getPeriod();
  const body=document.querySelector('#tbl-units tbody');
  const rows = sortRows(tableRows(p, p.summary.top15_units_ids), sortStateA);
  const maxUnits = Math.max(...rows.map(r=>r.units), 1);
  const [mn,mx] = cacRange(p);
  body.innerHTML = rows.map(r=>{{
    const sel = r.product_id===selPid ? 'sel' : '';
    const barW = Math.round(60*r.units/maxUnits);
    const cacColor = r.cac==null ? '#94a3b8' : colorForCac(r.cac, mn, mx);
    return `<tr class="${{sel}}" data-pid="${{r.product_id}}">
      <td>${{r.rank}}</td>
      <td>${{r.title}}</td>
      <td class="r"><span class="bar" style="width:${{barW}}px;background:#bbf7d0"></span>${{fmtInt(r.units)}}</td>
      <td class="r">${{fmtMoney(r.revenue)}}</td>
      <td class="r">${{fmtInt(r.new_customers)}}</td>
      <td class="r">${{fmtMoney(r.allocated_spend)}}</td>
      <td class="r" style="font-weight:700;color:${{cacColor}}">${{fmtMoney(r.cac)}}</td>
      <td class="r">${{fmtMoney(r.ratio)}}</td>
    </tr>`;
  }}).join('');
  body.querySelectorAll('tr').forEach(tr=>tr.onclick=()=>selectProduct(tr.dataset.pid));
}}

function renderTableB(){{
  const p = getPeriod();
  const body=document.querySelector('#tbl-lowcac tbody');
  const rows = sortRows(tableRows(p, p.summary.top15_lowcac_ids), sortStateB);
  const [mn,mx] = cacRange(p);
  body.innerHTML = rows.map(r=>{{
    const sel = r.product_id===selPid ? 'sel' : '';
    const cacColor = r.cac==null ? '#94a3b8' : colorForCac(r.cac, mn, mx);
    return `<tr class="${{sel}}" data-pid="${{r.product_id}}">
      <td>${{r.rank}}</td>
      <td>${{r.title}}</td>
      <td class="r" style="font-weight:700;color:${{cacColor}}">${{fmtMoney(r.cac)}}</td>
      <td class="r">${{fmtInt(r.new_customers)}}</td>
      <td class="r">${{fmtMoney(r.allocated_spend)}}</td>
      <td class="r">${{fmtInt(r.units)}}</td>
      <td class="r">${{fmtMoney(r.revenue)}}</td>
      <td class="r">${{fmtMoney(r.ratio)}}</td>
    </tr>`;
  }}).join('');
  body.querySelectorAll('tr').forEach(tr=>tr.onclick=()=>selectProduct(tr.dataset.pid));
}}

function renderProductSelect(){{
  const p = getPeriod();
  const A = p.summary.top15_units_ids;
  const B = p.summary.top15_lowcac_ids;
  const unionIds = [...new Set([...A, ...B])];
  const byId = Object.fromEntries(p.products.map(x=>[x.product_id,x]));
  const sel = document.getElementById('prodSel');
  sel.innerHTML = unionIds.map(pid=>{{
    const prod = byId[pid];
    if(!prod) return '';
    const inA=A.includes(pid), inB=B.includes(pid);
    const tag = inA&&inB ? '[A·B]' : inA ? '[A]' : '[B]';
    return `<option value="${{pid}}">${{tag}} ${{prod.title}}</option>`;
  }}).join('');

  // Adjust selection: if current selPid not in current period, reset to first
  if(!unionIds.includes(selPid)) {{
    selPid = unionIds[0];
  }}
  sel.value = selPid;
}}

function renderTrend(){{
  const p = getPeriod();
  const prod = p.products.find(x=>x.product_id===selPid);
  if(!prod){{
    if(chart){{ chart.destroy(); chart = null; }}
    return;
  }}
  const metric = document.getElementById('metricSel').value;
  const labels = p.dates.map(fmtDate);
  const data = prod.daily.map(d=>d[metric]);
  const isMoney = ['cac','spend','revenue'].includes(metric);
  const color = metric==='cac' ? '#ef4444' : metric==='new_customers'?'#059669' : metric==='spend'?'#3b82f6' : metric==='revenue'?'#f59e0b' : '#8b5cf6';

  if(chart) chart.destroy();
  const ctx = document.getElementById('trendChart').getContext('2d');
  chart = new Chart(ctx, {{
    type:'line',
    data:{{ labels, datasets:[{{label:prod.title, data, borderColor:color, backgroundColor:color+'22', tension:0.25, spanGaps:true, pointRadius:p.dates.length<=30?3:1.5, pointHoverRadius:6}}]}},
    options:{{
      responsive:true, maintainAspectRatio:false,
      plugins:{{
        legend:{{display:true,position:'top',labels:{{font:{{size:12}}}}}},
        tooltip:{{callbacks:{{label:c=>{{const v=c.parsed.y; return c.dataset.label+': '+(isMoney?fmtMoney(v):fmtInt(v))}}}}}}
      }},
      scales:{{
        y:{{beginAtZero:true,ticks:{{callback:v=>isMoney?fmtMoney(v):fmtInt(v),font:{{size:11}}}}}},
        x:{{ticks:{{font:{{size:9.5}},maxRotation:60,minRotation:45,autoSkip:true,maxTicksLimit:30}}}}
      }}
    }}
  }});
}}

function renderHeat(){{
  const p = getPeriod();
  const A = p.summary.top15_units_ids;
  const B = p.summary.top15_lowcac_ids;
  const byId = Object.fromEntries(p.products.map(x=>[x.product_id,x]));
  const [mn,mx] = cacRange(p);

  const head = document.getElementById('heat-head');
  const body = document.getElementById('heat-body');
  head.innerHTML = `<th class="dh" style="text-align:left;min-width:240px;position:sticky;left:0;background:#f8fafc;z-index:3">Produto</th>` +
    p.dates.map(d=>`<th class="dh">${{fmtDate(d)}}</th>`).join('');

  const renderGroup=(ids, label)=>{{
    let html=`<tr class="sep"><td colspan="${{p.dates.length+1}}">${{label}}</td></tr>`;
    html += ids.map(pid=>{{
      const prod = byId[pid];
      if(!prod) return '';
      const sel = pid===selPid ? 'sel' : '';
      const cells = prod.daily.map(x=>{{
        const c = x.cac;
        const bg = colorForCac(c, mn, mx);
        const txt = c==null ? (x.units>0?'·':'') : fmtMoney(c).replace(CCY.symbol+' ','');
        const tip = `${{x.date}} | unidades:${{x.units}} | novos:${{x.new_customers}} | spend:${{fmtMoney(x.spend)}} | CAC:${{fmtMoney(c)}}`;
        const fg = c==null ? '#94a3b8' : 'rgba(15,23,42,0.85)';
        return `<td title="${{tip}}" style="background:${{bg}};color:${{fg}};font-weight:${{c==null?400:600}}">${{txt}}</td>`;
      }}).join('');
      return `<tr><td class="lbl ${{sel}}" data-pid="${{pid}}" title="${{prod.title}}">${{prod.title.length>40?prod.title.slice(0,40)+'…':prod.title}}</td>${{cells}}</tr>`;
    }}).join('');
    return html;
  }};

  const aOnly = A;
  const bOnly = B.filter(p=>!A.includes(p));
  let html = renderGroup(aOnly, 'A · Top 15 por Volume');
  if(bOnly.length) html += renderGroup(bOnly, 'B · Menor CAC (não em A)');
  body.innerHTML = html;
  body.querySelectorAll('td.lbl').forEach(td=>td.onclick=()=>selectProduct(td.dataset.pid));
}}

function selectProduct(pid){{
  selPid = pid;
  document.getElementById('prodSel').value = pid;
  renderTableA();
  renderTableB();
  renderHeat();
  renderTrend();
}}

function renderAll(){{
  renderKPIs();
  renderProductSelect();
  renderTableA();
  renderTableB();
  renderHeat();
  renderTrend();
}}

function setPeriod(period){{
  currentPeriod = period;
  document.querySelectorAll('.pbtn').forEach(b=>{{
    b.classList.toggle('act', b.dataset.period === period);
  }});
  // Reset sort to default rank when changing period
  sortStateA = {{key:'rank', dir:1}};
  sortStateB = {{key:'rank', dir:1}};
  renderAll();
}}

document.querySelectorAll('.pbtn').forEach(b=>{{
  b.onclick = ()=>setPeriod(b.dataset.period);
}});
document.querySelectorAll('#tbl-units th').forEach(th=>{{
  th.onclick=()=>{{
    const k=th.dataset.sort;
    if(sortStateA.key===k) sortStateA.dir=-sortStateA.dir;
    else sortStateA={{key:k, dir:(k==='rank'||k==='title')?1:-1}};
    renderTableA();
  }};
}});
document.querySelectorAll('#tbl-lowcac th').forEach(th=>{{
  th.onclick=()=>{{
    const k=th.dataset.sort;
    if(sortStateB.key===k) sortStateB.dir=-sortStateB.dir;
    else sortStateB={{key:k, dir:(k==='rank'||k==='title')?1:-1}};
    renderTableB();
  }};
}});
document.getElementById('prodSel').onchange = (e)=>selectProduct(e.target.value);
document.getElementById('metricSel').onchange = ()=>renderTrend();

setPeriod('28');
</script>
</body>
</html>
"""
    out = ROOT / cfg["output"]
    out.write_text(html, encoding="utf-8")
    print(f"[{country.upper()}] OK Dashboard escrito -> {out}  ({out.stat().st_size/1024:.1f} KB)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", choices=["br","us"], default="br")
    args = parser.parse_args()
    build(args.country)


if __name__ == "__main__":
    main()
