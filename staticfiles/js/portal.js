
const Portal = (() => {
  function qs(s){return document.querySelector(s)}
  function ce(tag,cls){const e=document.createElement(tag); if(cls)e.className=cls; return e}
  const safe = (v) => (v === null || v === undefined) ? "" : String(v);
  async function jget(url){const res=await fetch(url,{headers:{"Accept":"application/json"}}); if(!res.ok) throw new Error(`${res.status} ${res.statusText}`); return res.json();}
  async function jpost(url, payload){
    const res = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json","Accept":"application/json"}, body: JSON.stringify(payload)});
    const text = await res.text();
    let data; try{ data = text ? JSON.parse(text) : {}; }catch{ data = {raw:text}; }
    if(!res.ok){ const msg = data.detail || JSON.stringify(data); throw new Error(msg); }
    return data;
  }
  function renderRows(tbodySel, rows, makeRow){
    const tb = qs(tbodySel);
    tb.innerHTML = rows.length ? rows.map(makeRow).join("") : `<tr><td class="text-secondary">No records</td></tr>`;
  }

  // KPI + recent on dashboard
  async function renderKPIs(){
    try{
      const [funds, investors, companies, tasks] = await Promise.all([jget("/api/funds/"), jget("/api/investors/"), jget("/api/companies/"), jget("/api/compliance/tasks/")]);
      qs("#kpi-funds").textContent = (funds.results || funds || []).length || (Array.isArray(funds)?funds.length:0);
      qs("#kpi-investors").textContent = (investors.results || investors || []).length || (Array.isArray(investors)?investors.length:0);
      qs("#kpi-companies").textContent = (companies.results || companies || []).length || (Array.isArray(companies)?companies.length:0);
      qs("#kpi-tasks").textContent = (tasks.results || tasks || []).length || (Array.isArray(tasks)?tasks.length:0);
    }catch(e){ console.warn("KPI load failed",e); }
  }
  async function renderRecentTransactions(){
    try{
      const [purchases, redemptions] = await Promise.all([jget("/api/transactions/purchases/"), jget("/api/transactions/redemptions/")]);
      const pr = (Array.isArray(purchases)?purchases:purchases.results)||[];
      const rr = (Array.isArray(redemptions)?redemptions:redemptions.results)||[];
      const items = [
        ...pr.map(x=>({...x, _type:"Purchase", date:x.purchase_date, rate:x.purchase_rate})),
        ...rr.map(x=>({...x, _type:"Redemption", date:x.redemption_date, rate:x.redemption_rate})),
      ].sort((a,b)=> String(b.date).localeCompare(String(a.date))).slice(0,10);
      const body = qs("#tbl-recent"); if(body){
        body.innerHTML = items.map(x=>`<tr>
          <td><span class="badge bg-${x._type==='Purchase'?'success':'danger'}">${x._type}</span></td>
          <td>${safe(x.fund)}</td><td>${safe(x.investee_company)}</td>
          <td class="text-end">${safe(x.quantity)}</td><td class="text-end">${safe(x.rate)}</td><td>${safe(x.date)}</td>
        </tr>`).join("") || `<tr><td class="text-secondary" colspan="6">No transactions.</td></tr>`;
      }
      const pb = qs("#purchases-body"); if(pb) pb.innerHTML = pr.map(x=>`<tr>
        <td>${safe(x.id)}</td><td>${safe(x.fund)}</td><td>${safe(x.investee_company)}</td>
        <td class="text-end">${safe(x.quantity)}</td><td class="text-end">${safe(x.purchase_rate)}</td><td>${safe(x.purchase_date)}</td>
      </tr>`).join("");
      const rb = qs("#redemptions-body"); if(rb) rb.innerHTML = rr.map(x=>`<tr>
        <td>${safe(x.id)}</td><td>${safe(x.fund)}</td><td>${safe(x.investee_company)}</td>
        <td class="text-end">${safe(x.quantity)}</td><td class="text-end">${safe(x.redemption_rate)}</td><td>${safe(x.redemption_date)}</td>
      </tr>`).join("");
    }catch(e){ const body=qs("#tbl-recent"); if(body) body.innerHTML = `<tr><td class="text-danger">${e.message}</td></tr>`; }
  }

  // Lists
  async function renderFundsList(sel){
    const data = await jget("/api/funds/"); const rows=(Array.isArray(data)?data:data.results)||[];
    renderRows(sel, rows, (x)=>`<tr>
      <td>${safe(x.id)}</td><td>${safe(x.name)}</td><td>${safe(x.category)}</td>
      <td>${safe(x.corpus)}</td><td>${safe(x.inception_date)}</td>
      <td class="text-end"><a class="btn btn-sm btn-outline-light" href="/portal/funds/${x.id}/"><i class="bi bi-eye"></i> View</a></td>
    </tr>`);
  }
  async function renderInvestorsList(sel){
    const data = await jget("/api/investors/"); const rows=(Array.isArray(data)?data:data.results)||[];
    renderRows(sel, rows, (x)=>`<tr>
      <td>${safe(x.id)}</td><td>${safe(x.name)}</td><td>${safe(x.pan)}</td><td>${safe(x.contact_email||x.email)}</td><td>${safe(x.kyc_status)}</td>
      <td class="text-end"><a class="btn btn-sm btn-outline-light" href="/portal/investors/${x.id}/"><i class="bi bi-eye"></i> View</a></td>
    </tr>`);
  }
  async function renderCompaniesList(sel){
    const data = await jget("/api/companies/"); const rows=(Array.isArray(data)?data:data.results)||[];
    renderRows(sel, rows, (x)=>`<tr>
      <td>${safe(x.id)}</td><td>${safe(x.name)}</td><td>${safe(x.cin)}</td><td>${safe(x.incorporation_date)}</td><td>${safe(x.sector)}</td>
      <td class="text-end"><a class="btn btn-sm btn-outline-light" href="/portal/companies/${x.id}/"><i class="bi bi-eye"></i> View</a></td>
    </tr>`);
  }
  async function renderTasksList(sel){
    const data = await jget("/api/compliance/tasks/"); const rows=(Array.isArray(data)?data:data.results)||[];
    renderRows(sel, rows, (x)=>`<tr>
      <td>${safe(x.id)}</td><td>${safe(x.title)}</td><td>${safe(x.related_model)}</td><td>${safe(x.related_id)}</td><td>${safe(x.due_date)}</td><td>${safe(x.status)}</td>
    </tr>`);
  }

  // Detail pages
  function currentIdFromPath(){ const parts = location.pathname.split("/").filter(Boolean); return parseInt(parts[parts.length-1]) }
  async function renderFundDetail(sel){
    const id = currentIdFromPath();
    const x = await jget(`/api/funds/${id}/`);
    const el = qs(sel);
    el.innerHTML = `<div class="card border-0 shadow-sm">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h3 class="mb-0">${safe(x.name)}</h3>
          <span class="badge bg-secondary">${safe(x.category)}</span>
        </div>
        <div class="row g-3">
          <div class="col-sm-3"><div class="text-secondary small">Corpus</div><div class="h5">${safe(x.corpus)}</div></div>
          <div class="col-sm-3"><div class="text-secondary small">Inception</div><div class="h5">${safe(x.inception_date)}</div></div>
          <div class="col-sm-3"><div class="text-secondary small">Closure</div><div class="h5">${safe(x.tentative_closure_date||'—')}</div></div>
          <div class="col-sm-3"><div class="text-secondary small">NAV</div><div class="h5">${safe(x.nav||'—')}</div></div>
        </div>
      </div>
    </div>`;
  }
  async function renderInvestorDetail(sel){
    const id = currentIdFromPath(); const x = await jget(`/api/investors/${id}/`);
    qs(sel).innerHTML = `<div class="card border-0 shadow-sm"><div class="card-body">
      <h3 class="mb-2">${safe(x.name)}</h3>
      <div class="row g-3">
        <div class="col-sm-3"><div class="text-secondary small">PAN</div><div class="h5">${safe(x.pan)}</div></div>
        <div class="col-sm-3"><div class="text-secondary small">Email</div><div class="h5">${safe(x.contact_email||x.email)}</div></div>
        <div class="col-sm-3"><div class="text-secondary small">KYC</div><div class="h5">${safe(x.kyc_status)}</div></div>
        <div class="col-sm-3"><div class="text-secondary small">Type</div><div class="h5">${safe(x.investor_type||'—')}</div></div>
      </div>
    </div></div>`;
  }
  async function renderCompanyDetail(sel){
    const id = currentIdFromPath(); const x = await jget(`/api/companies/${id}/`);
    qs(sel).innerHTML = `<div class="card border-0 shadow-sm"><div class="card-body">
      <h3 class="mb-2">${safe(x.name)}</h3>
      <div class="row g-3">
        <div class="col-sm-3"><div class="text-secondary small">CIN</div><div class="h5">${safe(x.cin)}</div></div>
        <div class="col-sm-3"><div class="text-secondary small">Incorporation</div><div class="h5">${safe(x.incorporation_date)}</div></div>
        <div class="col-sm-3"><div class="text-secondary small">Sector</div><div class="h5">${safe(x.sector)}</div></div>
      </div>
    </div></div>`;
  }

  // Submit modals
  function collectFormData(form){
    const fd = new FormData(form); const obj={}; for(const [k,v] of fd.entries()) obj[k]=v; return obj;
  }
  async function submitPurchase(e){
    e.preventDefault(); const frm=e.target; const err=qs("#purchase-error"); err.classList.add("d-none");
    try{
      const payload = collectFormData(frm);
      payload.quantity = Number(payload.quantity); payload.purchase_rate = Number(payload.purchase_rate);
      await jpost("/api/transactions/purchases/", payload);
      frm.reset(); bootstrap.Modal.getInstance(document.getElementById("modalAddPurchase")).hide();
      // refresh
      if(qs("#purchases-body")||qs("#tbl-recent")) renderRecentTransactions();
    }catch(ex){ err.textContent = ex.message; err.classList.remove("d-none"); }
  }
  async function submitRedemption(e){
    e.preventDefault(); const frm=e.target; const err=qs("#redemption-error"); err.classList.add("d-none");
    try{
      const payload = collectFormData(frm);
      payload.quantity = Number(payload.quantity); payload.redemption_rate = Number(payload.redemption_rate);
      await jpost("/api/transactions/redemptions/", payload);
      frm.reset(); bootstrap.Modal.getInstance(document.getElementById("modalAddRedemption")).hide();
      if(qs("#redemptions-body")||qs("#tbl-recent")) renderRecentTransactions();
    }catch(ex){ err.textContent = ex.message; err.classList.remove("d-none"); }
  }

  // boot
  window.addEventListener('DOMContentLoaded', ()=>{ renderKPIs(); renderRecentTransactions(); });

  return { renderFundsList, renderInvestorsList, renderCompaniesList, renderTasksList,
    renderFundDetail, renderInvestorDetail, renderCompanyDetail,
    renderRecentTransactions, submitPurchase, submitRedemption };
})();
