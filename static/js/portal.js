
const Portal = (() => {
  const qs = (s)=>document.querySelector(s);
  const safe = (v)=> (v==null? "": String(v));
  const num = (v)=> isNaN(+v)? 0 : +v;
  const json = async (url, opts={}) => {
    const res = await fetch(url, {headers:{"Accept":"application/json","Content-Type":"application/json"}, credentials:"same-origin", ...opts});
    const txt = await res.text(); const data = txt? JSON.parse(txt): {};
    if(!res.ok){ throw new Error(data.detail || res.statusText || txt) }
    return data;
  };
  const jget = (url)=> json(url);
  const jpost = (url, body)=> json(url, {method:"POST", body: JSON.stringify(body)});
  const jpatch = (url, body)=> json(url, {method:"PATCH", body: JSON.stringify(body)});

  // DASHBOARD
  async function renderKPIs(){
    try{
      const [funds, investors, companies, tasks] = await Promise.all([jget("/api/funds/"), jget("/api/investors/"), jget("/api/companies/"), jget("/api/compliance/tasks/")]);
      const len = (x)=> Array.isArray(x)? x.length : (x.results||[]).length;
      qs("#kpi-funds").textContent = len(funds);
      qs("#kpi-investors").textContent = len(investors);
      qs("#kpi-companies").textContent = len(companies);
      qs("#kpi-tasks").textContent = len(tasks);
      const list = (Array.isArray(investors)?investors:(investors.results||[]));
      const ok = list.filter(x=> String(x.kyc_status).toLowerCase()==="compliant").length;
      const pct = list.length? Math.round(ok*100/list.length):0;
      qs("#kyc-bar").style.width = pct+"%"; qs("#kyc-bar").textContent = pct+"%";
      qs("#kyc-ok").textContent = ok; qs("#kyc-pending").textContent = (list.length-ok);
    }catch(e){ console.warn("KPIs error", e); }
  }
  async function renderRecentTransactions(){
    try{
      const [purchases, redemptions] = await Promise.all([jget("/api/transactions/purchases/"), jget("/api/transactions/redemptions/")]);
      const pr = (purchases.results||purchases)||[];
      const rr = (redemptions.results||redemptions)||[];
      const items = [
        ...pr.map(x=>({...x, _type:"Purchase", date:x.purchase_date, rate:x.purchase_rate})),
        ...rr.map(x=>({...x, _type:"Redemption", date:x.redemption_date, rate:x.redemption_rate})),
      ].sort((a,b)=> String(b.date).localeCompare(String(a.date))).slice(0,10);
      const body = qs("#tbl-recent");
      if(body) body.innerHTML = items.map(x=>`<tr>
        <td><span class="badge bg-${x._type==='Purchase'?'success':'danger'}">${x._type}</span></td>
        <td>${safe(x.fund)}</td><td>${safe(x.investee_company)}</td>
        <td class="text-end">${safe(x.quantity)}</td><td class="text-end">${safe(x.rate)}</td><td>${safe(x.date)}</td>
      </tr>`).join("") || `<tr><td class="text-secondary" colspan="6">No transactions.</td></tr>`;
      const pb = qs("#purchases-body"); if(pb) pb.innerHTML = pr.map(x=> `<tr><td>${x.id}</td><td>${x.fund}</td><td>${x.investee_company}</td><td class="text-end">${x.quantity}</td><td class="text-end">${x.purchase_rate}</td><td>${x.purchase_date}</td></tr>`).join("");
      const rb = qs("#redemptions-body"); if(rb) rb.innerHTML = rr.map(x=> `<tr><td>${x.id}</td><td>${x.fund}</td><td>${x.investee_company}</td><td class="text-end">${x.quantity}</td><td class="text-end">${x.redemption_rate}</td><td>${x.redemption_date}</td></tr>`).join("");
      // FIFO panel
      const fifo = computeFIFO(pr, rr);
      const fp = qs("#fifo-panel"); if(fp) fp.innerHTML = `Realised P/L: <strong>${fifo.realised.toFixed(2)}</strong> • Remaining Units: ${fifo.remainingUnits} • Remaining Cost: ${fifo.remainingCost.toFixed(2)}`;
    }catch(e){ const body=qs("#tbl-recent"); if(body) body.innerHTML = `<tr><td class="text-danger">${e.message}</td></tr>`; }
  }

  // INVESTORS
  async function renderInvestorsList(sel){
    const data = await jget("/api/investors/"); const rows=(data.results||data)||[];
    qs(sel).innerHTML = rows.map(x=>`<tr>
      <td>${x.id}</td><td>${safe(x.name)}</td><td>${safe(x.pan)}</td><td>${safe(x.contact_email||x.email)}</td>
      <td>${String(x.kyc_status).toLowerCase()==='compliant' ? '<span class="badge bg-success">Compliant</span>' : '<span class="badge bg-warning text-dark">Pending</span>'}</td>
      <td class="text-end"><a class="btn btn-sm btn-outline-light" href="/portal/investors/${x.id}/"><i class="bi bi-eye"></i> View</a></td>
    </tr>`).join("") || `<tr><td colspan="6" class="text-secondary">No investors.</td></tr>`;
  }
  function idFromPath(){ const p = location.pathname.split('/').filter(Boolean); return +p[p.length-1]; }
  async function renderInvestorDetail(sel){
    const id = idFromPath(); const x = await jget(`/api/investors/${id}/`);
    qs(sel).innerHTML = `<div class="card border-0 shadow-sm"><div class="card-body">
      <div class="d-flex justify-content-between align-items-center mb-1"><h3 class="mb-0">${safe(x.name)}</h3>
        <div>${String(x.kyc_status).toLowerCase()==='compliant' ? '<span class="badge bg-success">KYC Compliant</span>' : '<span class="badge bg-warning text-dark">KYC Pending</span>'}</div></div>
      <div class="row g-3">
        <div class="col-sm-3"><div class="text-secondary small">PAN</div><div class="h6">${safe(x.pan)}</div></div>
        <div class="col-sm-3"><div class="text-secondary small">Email</div><div class="h6">${safe(x.contact_email||x.email)}</div></div>
        <div class="col-sm-3"><div class="text-secondary small">Phone</div><div class="h6">${safe(x.phone||'—')}</div></div>
        <div class="col-sm-3"><div class="text-secondary small">Type</div><div class="h6">${safe(x.investor_type||'—')}</div></div>
      </div>
      <div class="mt-3"><button class="btn btn-outline-light btn-sm" onclick="Portal.generateKYCForm(${id})"><i class="bi bi-file-earmark-text"></i> Generate KYC Form</button></div>
      <div id="kyc-block" class="text-secondary small mt-3">Status: ${safe(x.kyc_status||'Unknown')}</div>
    </div></div>`;
  }
  async function submitInvestorOnboarding(e){
    e.preventDefault(); const f=e.target; const obj=Object.fromEntries(new FormData(f).entries());
    try{ const r=await jpost("/api/investors/", obj); location.href = `/portal/investors/${r.id||""}/`; }
    catch(ex){ const el=document.getElementById("onboard-error"); el.textContent=ex.message; el.classList.remove("d-none"); }
  }
  async function submitKYC(e){
    e.preventDefault(); const f=e.target; const obj=Object.fromEntries(new FormData(f).entries());
    const id = idFromPath();
    try{ await jpatch(`/api/investors/${id}/`, obj); bootstrap.Modal.getInstance(document.getElementById("modalKYC")).hide(); renderInvestorDetail("#investor-detail"); }
    catch(ex){ const el=document.getElementById("kyc-error"); el.textContent=ex.message; el.classList.remove("d-none"); }
  }
  async function generateKYCForm(id){
    try{ const r = await jpost(`/api/compliance/documents/`, {type:"kyc_form", investor:id}); alert("KYC form generated."); }
    catch(ex){ alert("DocGen failed: "+ex.message); }
  }

  // COMPANIES
  async function renderCompaniesList(sel){
    const data = await jget("/api/companies/"); const rows=(data.results||data)||[];
    qs(sel).innerHTML = rows.map(x=>`<tr>
      <td>${x.id}</td><td>${safe(x.name)}</td><td>${safe(x.cin)}</td><td>${safe(x.incorporation_date)}</td><td>${safe(x.sector)}</td>
      <td class="text-end"><a class="btn btn-sm btn-outline-light" href="/portal/companies/${x.id}/"><i class="bi bi-eye"></i> View</a></td>
    </tr>`).join("") || `<tr><td colspan="6" class="text-secondary">No companies.</td></tr>`;
  }
  async function renderCompanyDetail(headSel){
    const id = idFromPath();
    const x = await jget(`/api/companies/${id}/`);
    qs(headSel).innerHTML = `<div class="card border-0 shadow-sm"><div class="card-body">
      <h3 class="mb-1">${safe(x.name)}</h3>
      <div class="row g-3"><div class="col-sm-3"><div class="text-secondary small">CIN</div><div class="h6">${safe(x.cin)}</div></div>
      <div class="col-sm-3"><div class="text-secondary small">Incorp.</div><div class="h6">${safe(x.incorporation_date)}</div></div>
      <div class="col-sm-3"><div class="text-secondary small">Sector</div><div class="h6">${safe(x.sector)}</div></div></div>
    </div></div>`;
    try{
      const [hold, actions, fins, vals] = await Promise.all([jget(`/api/companies/${id}/financials/holdings`), jget(`/api/companies/${id}/corporate-actions/`), jget(`/api/companies/${id}/financials/`), jget(`/api/companies/${id}/valuations/`)]);
      const hb = qs("#tbl-shareholding"); if(hb) hb.innerHTML = (hold.results||hold||[]).map(h=>`<tr><td>${safe(h.share_class||h.type||'—')}</td><td class="text-end">${safe(h.shares)}</td><td class="text-end">${safe(h.face_value)}</td></tr>`).join("") || `<tr><td class="text-secondary">No data</td></tr>`;
      const cb = qs("#corp-actions"); if(cb) cb.innerHTML = (actions.results||actions||[]).map(a=> `<div class="item"><strong>${safe(a.date)}</strong> • ${safe(a.action_type)} — ${safe(a.notes||'')}</div>`).join("") || `<div class="text-secondary">No actions</div>`;
      const fb = qs("#tbl-financials"); if(fb) fb.innerHTML = (fins.results||fins||[]).slice(0,2).map(f=> `<tr><td>${safe(f.year)}</td><td class="text-end">${safe(f.revenue)}</td><td class="text-end">${safe(f.ebitda||f.ebidta)}</td><td class="text-end">${safe(f.finance_cost)}</td><td class="text-end">${safe(f.pat)}</td><td class="text-end">${safe(f.eps)}</td></tr>`).join("") || `<tr><td class="text-secondary">No financials</td></tr>`;
      const vv = qs("#valuation"); if(vv){ const vr = (vals.results||vals||[])[0]; vv.innerHTML = vr ? `Per-share value: <strong>${safe(vr.per_share_value || vr.value)}</strong>` : "No valuation available."; }
    }catch(e){ console.warn("Company subdata:",e); }
  }

  // FUNDS
  async function renderFundsList(sel){
    const data = await jget("/api/funds/"); const rows=(data.results||data)||[];
    qs(sel).innerHTML = rows.map(x=>`<tr>
      <td>${x.id}</td><td>${safe(x.name)}</td><td>${safe(x.category)}</td><td>${safe(x.corpus)}</td><td>${safe(x.inception_date)}</td><td>${safe(x.nav||'—')}</td>
      <td class="text-end"><a class="btn btn-sm btn-outline-light" href="/portal/funds/${x.id}/"><i class="bi bi-speedometer"></i> Dashboard</a></td>
    </tr>`).join("") || `<tr><td colspan="7" class="text-secondary">No funds.</td></tr>`;
  }
  async function renderFundDetail(sel){
    const id = idFromPath(); const f = await jget(`/api/funds/${id}/`);
    qs(sel).innerHTML = `<div class="card border-0 shadow-sm"><div class="card-body">
      <div class="d-flex justify-content-between align-items-center">
        <div><h3 class="mb-0">${safe(f.name)}</h3><div class="text-secondary small">Category: ${safe(f.category)} • Inception: ${safe(f.inception_date)} • Closure: ${safe(f.tentative_closure_date||'—')}</div></div>
        <div class="text-end"><div class="kpi-sub">NAV</div><div class="h4 mb-0">${safe(f.nav||'—')}</div></div>
      </div>
    </div></div>`;
    // load commitments, portfolio, activity
    try{
      const [commits, purchases, redemptions, valuations] = await Promise.all([jget(`/api/funds/${id}/commitments/`), jget("/api/transactions/purchases/"), jget("/api/transactions/redemptions/"), jget("/api/companies/valuations/")]);
      // commitments table
      const cb = qs("#tbl-commit"); const cl = (commits.results||commits||[]).map(c=>{
        const draw = num(c.drawdown||c.drawn||0); const bal = num(c.amount||c.commitment||0)-draw;
        return `<tr><td>${safe(c.investor_name||c.investor||'Investor')}</td><td class="text-end">${safe(c.amount||c.commitment)}</td><td class="text-end">${draw.toFixed(2)}</td><td class="text-end">${bal.toFixed(2)}</td></tr>`;
      }).join("");
      if(cb) cb.innerHTML = cl || `<tr><td class="text-secondary">No commitments</td></tr>`;
      // portfolio: naive compute from purchases-redemptions + valuation map
      const pr = (purchases.results||purchases||[]).filter(x=> +x.fund===+id);
      const rr = (redemptions.results||redemptions||[]).filter(x=> +x.fund===+id);
      const units = {}; const cost = {};
      pr.forEach(x=>{ const k=x.investee_company; units[k]=(units[k]||0)+num(x.quantity); cost[k]=(cost[k]||0)+num(x.quantity)*num(x.purchase_rate); });
      rr.forEach(x=>{ const k=x.investee_company; const q=num(x.quantity); const r=num(x.redemption_rate); const u=units[k]||0; const c=cost[k]||0; const avg = u? c/u : 0; units[k]=u-q; cost[k]=c-avg*q; });
      const valmap = {}; (valuations.results||valuations||[]).forEach(v=>{ valmap[v.share_capital||v.company||v.company_id] = num(v.per_share_value||v.value||0); });
      const pb = qs("#tbl-portfolio");
      if(pb){
        let html=""; let totalMV=0,totalCost=0;
        for(const k of Object.keys(units)){
          const u = units[k]; if(u<=0) continue;
          const c = cost[k]||0; const ps = valmap[k]||0; const mv = u*ps; totalMV+=mv; totalCost+=c;
          html += `<tr><td>${k}</td><td class="text-end">${u}</td><td class="text-end">${c.toFixed(2)}</td><td class="text-end">${mv.toFixed(2)}</td><td class="text-end">${(mv-c).toFixed(2)}</td></tr>`;
        }
        pb.innerHTML = html || `<tr><td class="text-secondary">No holdings</td></tr>`;
        const navc = qs("#nav-card"); if(navc) navc.innerHTML = `Current Value: <strong>${totalMV.toFixed(2)}</strong><br>Cost: <strong>${totalCost.toFixed(2)}</strong><br>Cash Balance (est.): <strong>${(num(f.corpus||0)-totalCost).toFixed(2)}</strong>`;
      }
      // activity
      const ab = qs("#fund-activity"); if(ab){
        const items=[...pr.map(x=>({d:x.purchase_date, t:`Buy ${x.quantity} @ ${x.purchase_rate} • Co ${x.investee_company}`})), ...rr.map(x=>({d:x.redemption_date, t:`Sell ${x.quantity} @ ${x.redemption_rate} • Co ${x.investee_company}`}))].sort((a,b)=> String(b.d).localeCompare(String(a.d))).slice(0,6);
        ab.innerHTML = items.map(i=>`<div>• <strong>${i.d}</strong> — ${i.t}</div>`).join("") || "No recent activity.";
      }
    }catch(e){ console.warn("Fund detail subdata:",e); }
  }

  // TRANSACTIONS submit
  const getForm = (e)=> Object.fromEntries(new FormData(e.target).entries());
  async function submitPurchase(e){ e.preventDefault(); const p=getForm(e); p.quantity=+p.quantity; p.purchase_rate=+p.purchase_rate;
    try{ await jpost("/api/transactions/purchases/", p); bootstrap.Modal.getInstance(document.getElementById("modalAddPurchase")).hide(); renderRecentTransactions(); }
    catch(ex){ const el=qs("#purchase-error"); el.textContent=ex.message; el.classList.remove("d-none"); }
  }
  async function submitRedemption(e){ e.preventDefault(); const p=getForm(e); p.quantity=+p.quantity; p.redemption_rate=+p.redemption_rate;
    try{ await jpost("/api/transactions/redemptions/", p); bootstrap.Modal.getInstance(document.getElementById("modalAddRedemption")).hide(); renderRecentTransactions(); }
    catch(ex){ const el=qs("#redemption-error"); el.textContent=ex.message; el.classList.remove("d-none"); }
  }
  async function submitDrawdown(e){ e.preventDefault(); const p=getForm(e);
    try{ await jpost("/api/transactions/capital-calls/", p); bootstrap.Modal.getInstance(document.getElementById("modalDrawdown")).hide(); alert("Drawdown saved"); }
    catch(ex){ const el=qs("#drawdown-error"); el.textContent=ex.message; el.classList.remove("d-none"); }
  }
  async function submitDistribution(e){ e.preventDefault(); const p=getForm(e);
    try{ await jpost("/api/transactions/distributions/", p); bootstrap.Modal.getInstance(document.getElementById("modalDistribution")).hide(); alert("Distribution saved"); }
    catch(ex){ const el=qs("#distribution-error"); el.textContent=ex.message; el.classList.remove("d-none"); }
  }

  // COMPLIANCE
  async function renderTasksList(sel){
    const data = await jget("/api/compliance/tasks/"); const rows=(data.results||data)||[];
    qs(sel).innerHTML = rows.map(x=>`<tr><td>${x.id}</td><td>${safe(x.title)}</td><td>${safe(x.related_model)}</td><td>${safe(x.related_id)}</td><td>${safe(x.due_date)}</td><td>${safe(x.status)}</td></tr>`).join("") || `<tr><td class="text-secondary">No tasks</td></tr>`;
  }
  async function submitTask(e){ e.preventDefault(); const p=getForm(e);
    try{ await jpost("/api/compliance/tasks/", p); bootstrap.Modal.getInstance(document.getElementById("modalAddTask")).hide(); renderTasksList("#tasks-body"); }
    catch(ex){ const el=qs("#task-error"); el.textContent=ex.message; el.classList.remove("d-none"); }
  }

  // FIFO helper
  function computeFIFO(buys, sells){
    const lots=[]; let realised=0;
    (buys||[]).forEach(b=> lots.push({q:num(b.quantity), cost:num(b.purchase_rate)}));
    (sells||[]).forEach(s=>{
      let q=num(s.quantity), px=num(s.redemption_rate);
      while(q>0 && lots.length){
        const lot = lots[0]; const take = Math.min(q, lot.q);
        realised += (px - lot.cost) * take;
        lot.q -= take; q -= take;
        if(lot.q<=0) lots.shift();
      }
    });
    const remainingUnits = lots.reduce((a,b)=>a+b.q,0);
    const remainingCost = lots.reduce((a,b)=>a+b.q*b.cost,0);
    return {realised, remainingUnits, remainingCost};
  }

  // boot
  window.addEventListener('DOMContentLoaded', ()=>{ renderKPIs(); renderRecentTransactions(); });

  return { renderInvestorsList, renderInvestorDetail, submitInvestorOnboarding, submitKYC, generateKYCForm,
           renderCompaniesList, renderCompanyDetail,
           renderFundsList, renderFundDetail,
           renderRecentTransactions, renderTasksList,
           submitPurchase, submitRedemption, submitDrawdown, submitDistribution, submitTask, submitFund, submitCompany };
})();


  // CREATE FUND / COMPANY
  async function submitFund(e){ e.preventDefault(); const p=Object.fromEntries(new FormData(e.target).entries());
    try{ const r = await jpost("/api/funds/", p); location.href = `/portal/funds/${r.id||""}/`; }
    catch(ex){ const el=document.getElementById("fund-add-error"); if(el){ el.textContent = ex.message; el.classList.remove("d-none"); } }
  }
  async function submitCompany(e){ e.preventDefault(); const p=Object.fromEntries(new FormData(e.target).entries());
    try{ const r = await jpost("/api/companies/", p); location.href = `/portal/companies/${r.id||""}/`; }
    catch(ex){ const el=document.getElementById("company-add-error"); if(el){ el.textContent = ex.message; el.classList.remove("d-none"); } }
  }
