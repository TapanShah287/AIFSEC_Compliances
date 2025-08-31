
const Portal=(function(){
  async function jget(url){ const r=await fetch(url,{headers:{'Accept':'application/json'}}); if(!r.ok) throw new Error(await r.text()); return r.json();}
  async function jpost(url,body){ const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json','X-CSRFToken':getCsrf()},body:JSON.stringify(body)}); if(!r.ok) throw new Error(await r.text()); return r.json();}
  function getCsrf(){ const m=document.cookie.match(/csrftoken=([^;]+)/); return m?m[1]:''; }

  // Populate lists
  async function loadDashboard(){
    try{
      const [funds, investors, companies, tx] = await Promise.all([
        jget('/api/funds/'), jget('/api/investors/'), jget('/api/companies/'), jget('/api/transactions/recent/')
      ]);
      setText('#kpi-funds', funds.length); setText('#kpi-investors', investors.length); setText('#kpi-companies', companies.length);
      // KYC summary
      const ok=investors.filter(i=>i.kyc_status==='compliant').length; const pending=investors.length-ok;
      setText('#kyc-ok', ok); setText('#kyc-pending', pending);
      // Recent TX
      const tbody = document.querySelector('#tx-recent'); if(tbody){ tbody.innerHTML = (tx||[]).map(t=>`<tr class="hover:bg-gray-50">
        <td class="px-6 py-3">${t.date||t.purchase_date||t.redemption_date||''}</td>
        <td class="px-6 py-3">${t.type||''}</td>
        <td class="px-6 py-3">${t.fund_name||''}</td>
        <td class="px-6 py-3">${t.company_name||''}</td>
        <td class="px-6 py-3 text-right">${fmt(t.amount||t.net_amount||0)}</td>
      </tr>`).join(''); }
    }catch(e){ console.warn(e); }
  }

  async function loadFunds(){
    try{
      const data = await jget('/api/funds/');
      const tbody=document.querySelector('#funds-tbody');
      if(tbody){ tbody.innerHTML=data.map(f=>`<tr class="hover:bg-gray-50 cursor-pointer" onclick="location.href='/portal/funds/${f.id}/'">
        <td class="px-6 py-3">${f.name}</td>
        <td class="px-6 py-3">${f.category||''}</td>
        <td class="px-6 py-3">${f.inception_date||''}</td>
        <td class="px-6 py-3 text-right">${fmt(f.corpus||0)}</td>
      </tr>`).join(''); }
    }catch(e){ console.warn(e); }
  }

  async function loadCompanies(){
    try{
      const data = await jget('/api/companies/');
      const tbody=document.querySelector('#companies-tbody');
      if(tbody){ tbody.innerHTML=data.map(c=>`<tr class="hover:bg-gray-50">
        <td class="px-6 py-3">${c.name}</td><td class="px-6 py-3">${c.sector||''}</td><td class="px-6 py-3">${c.incorporation_date||''}</td>
      </tr>`).join(''); }
    }catch(e){ console.warn(e); }
  }

  async function loadInvestors(){
    try{
      const data = await jget('/api/investors/');
      const tbody=document.querySelector('#investors-tbody');
      if(tbody){ tbody.innerHTML=data.map(i=>`<tr class="hover:bg-gray-50">
        <td class="px-6 py-3">${i.name}</td><td class="px-6 py-3">${i.email||''}</td>
        <td class="px-6 py-3 text-center">${i.kyc_status==='compliant'
          ? '<span class="px-3 py-1 bg-success/20 text-success rounded-full text-xs font-semibold">Compliant</span>'
          : '<span class="px-3 py-1 bg-danger/20 text-danger rounded-full text-xs font-semibold">Pending</span>'}</td>
      </tr>`).join(''); }
    }catch(e){ console.warn(e); }
  }

  // Submit handlers
  async function submitFund(e){ e.preventDefault(); const p=Object.fromEntries(new FormData(e.target).entries());
    try{ const r=await jpost('/api/funds/', p); location.href='/portal/funds/'; } catch(ex){ showErr('#fund-add-error', ex); } }
  async function submitCompany(e){ e.preventDefault(); const p=Object.fromEntries(new FormData(e.target).entries());
    try{ const r=await jpost('/api/companies/', p); location.href='/portal/companies/'; } catch(ex){ showErr('#company-add-error', ex); } }
  async function submitInvestor(e){ e.preventDefault(); const p=Object.fromEntries(new FormData(e.target).entries());
    try{ const r=await jpost('/api/investors/', p); location.href='/portal/investors/'; } catch(ex){ showErr('#investor-add-error', ex); } }

  // helpers
  function setText(sel, val){ const el=document.querySelector(sel); if(el) el.textContent = val; }
  function showErr(sel, ex){ const el=document.querySelector(sel); if(el){ el.textContent = ex.message||'Failed'; el.classList.remove('hidden'); }}
  function fmt(n){ return new Intl.NumberFormat('en-IN', {maximumFractionDigits:2}).format(n); }

  // Auto-init
  document.addEventListener('DOMContentLoaded',()=>{
    const path = location.pathname;
    if(path==='/portal/' || path==='/portal') loadDashboard();
    if(path.startsWith('/portal/funds')) loadFunds();
    if(path.startsWith('/portal/companies')) loadCompanies();
    if(path.startsWith('/portal/investors')) loadInvestors();
  });

  return { submitFund, submitCompany, submitInvestor };
})();