document.addEventListener('DOMContentLoaded',async()=>{
 const root=document.querySelector('[data-threshold-explorer]');if(!root)return;
 try{const rows=await(await fetch(root.dataset.source)).json();const slider=root.querySelector('input');
 const draw=()=>{const row=rows[Number(slider.value)];root.querySelector('[data-value]').textContent=Number(row.threshold).toFixed(2);root.querySelector('[data-cost]').textContent=Number(row.cost_per_trip).toFixed(3);root.querySelector('[data-fp]').textContent=Number(row.fp).toLocaleString();root.querySelector('[data-fn]').textContent=Number(row.fn).toLocaleString();};slider.addEventListener('input',draw);draw();
 }catch(error){root.querySelector('[data-status]').textContent='Threshold table could not load. The static chart below contains the same evidence.';}
});
