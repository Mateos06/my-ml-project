/* Exhibition controls. Analytical outputs are read from immutable exported assets. */
(() => {
  'use strict';
  const root=document.querySelector('.taxi-lab');if(!root)return;
  const $=id=>document.getElementById(id), all=selector=>Array.from(document.querySelectorAll(selector));
  const fmt=n=>Number(n).toLocaleString('en-US'), pct=(n,d=1)=>(100*n).toFixed(d)+'%';
  const esc=v=>String(v??'Unknown').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const table=(rows,columns)=>'<table><thead><tr>'+columns.map(([key,title])=>'<th scope="col">'+esc(title)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+columns.map(([key,title,format])=>'<td>'+esc(format?format(row[key]):row[key])+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
  const money=v=>'$'+Number(v).toFixed(2);
  let study,models,mapData;

  function setupTabs(selector,attribute,handler){
    const buttons=all(selector);
    function select(button){buttons.forEach(b=>{b.setAttribute('aria-selected',String(b===button));b.tabIndex=b===button?0:-1;});handler(button.dataset[attribute]);}
    buttons.forEach((button,i)=>{
      button.tabIndex=button.getAttribute('aria-selected')==='true'?0:-1;
      button.addEventListener('click',()=>select(button));
      button.addEventListener('keydown',event=>{let target;if(event.key==='ArrowRight')target=(i+1)%buttons.length;if(event.key==='ArrowLeft')target=(i-1+buttons.length)%buttons.length;if(event.key==='Home')target=0;if(event.key==='End')target=buttons.length-1;if(target!==undefined){event.preventDefault();buttons[target].focus();select(buttons[target]);}});
    });
  }
  function setupTarget(){
    const update=()=>{const fare=Number($('target-fare').value),tip=Number($('target-tip').value),ratio=tip/fare,generous=ratio>=.25;
      $('target-fare-value').textContent=money(fare);$('target-tip-value').textContent=money(tip);
      $('target-percent').textContent=pct(ratio,ratio*100%1===0?0:1);
      $('target-label').textContent=generous?'Generous tip':'Below our 25% target';$('target-label').style.color=generous?'#4ade80':'#fca5a5';
      $('target-equation').textContent=money(tip)+' ÷ '+money(fare)+(generous?' ≥ 25%':' < 25%');
      $('target-ring').style.background=`conic-gradient(${generous?'#facc15':'#38bdf8'} 0 ${Math.min(100,ratio*100)}%,#26364c 0)`;
    };
    ['target-fare','target-tip'].forEach(id=>$(id).addEventListener('input',update));
    all('[data-example]').forEach(button=>button.addEventListener('click',()=>{$('target-fare').value=20;$('target-tip').value=button.dataset.example;update();}));update();
    const stages=[
      'At pickup, the trip has just begun. Final distance, duration and rate code are not automatically available.',
      'During the journey, the meter measures distance and time. Our prediction is made later.',
      'Fare, distance, duration and zones are now known. The tip and total charge are still outside the model.',
      'Now the model estimates a 25%+ recorded card tip. The passenger has not entered the tip yet.'
    ];
    setupTabs('[data-stage]','stage',value=>{$('stage-caption').textContent=stages[Number(value)];});
    $('cash-tip').addEventListener('input',()=>{$('cash-value').textContent='$'+$('cash-tip').value;$('cash-note').textContent=$('cash-tip').value;});
    const menu=$('menu-toggle');menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?'Close chapter menu':'Open chapter menu');document.querySelector('.lab-nav').classList.toggle('menu-open',open);});
    all('.lab-nav a').forEach(a=>a.addEventListener('click',()=>{menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label','Open chapter menu');document.querySelector('.lab-nav').classList.remove('menu-open');}));
  }

  function renderData(){
    const names=[['train','May','TRAINING','Fit every learned step.'],['validation','June','VALIDATION','Choose features, model and threshold.'],['test','July','FINAL TEST','One frozen scoring pass.']];
    $('month-timeline').innerHTML=names.map(([split,name,role,note])=>{const rows=study.funnel[split],raw=rows[0].remaining,clean=rows.at(-1).remaining;return `<article class="month-card"><span class="month-role">${role}</span><h3>${name} <span aria-hidden="true">→</span></h3><strong>${fmt(raw)}</strong><small>recorded pickups</small><div class="month-clean">${fmt(clean)} eligible card trips · ${pct(clean/raw)} retained</div><p class="month-rule">${note}</p></article>`;}).join('');
    function funnel(){
      const rows=study.funnel[$('funnel-month').value],raw=rows[0].remaining;
      const stages=[['Raw records','Raw rows','All pickups in this calendar month.'],['Observable card payments','Observable card tips','Cash gratuities are unrecorded. Flex, disputed and voided trips are outside this target.'],['Positive, valid fare','Positive fare','A percentage target needs a finite fare greater than zero.'],['Valid amounts & journey','Plausible average speed','Valid tip and fees; fixed distance, duration and average-speed rules.'],['Eligible trips','Retain flagged cases','Keep unknown zones, missing passengers and nonstandard rates with flags.']];
      $('cleaning-funnel').innerHTML=stages.map(([label,step,explanation])=>{const row=rows.find(r=>r.step===step);return `<div class="funnel-stage" title="${esc(explanation)}"><div class="funnel-stage-header"><span>${label}</span><b>${fmt(row.remaining)}</b></div><div class="funnel-bar" style="width:${row.remaining/raw*100}%"></div><small>${pct(row.remaining/raw)} of raw trips retained · ${esc(explanation)}</small></div>`;}).join('');
      $('funnel-summary').textContent=fmt(rows.at(-1).remaining)+' trips remain. Each filter defines who the result applies to.';
      $('audit-table').innerHTML=table(rows,[['step','Decision step'],['remaining','Remaining',fmt],['removed','Removed',fmt],['card_positive_rate','Valid-card positive rate',pct],['decision','Policy']]);
    }$('funnel-month').addEventListener('change',funnel);funnel();
    const card=study.payments.find(r=>String(r.payment_type)==='1'),cash=study.payments.find(r=>String(r.payment_type)==='2');
    $('card-observed').textContent=fmt(card.valid_fare_trips)+' valid-fare May card trips; '+pct(card.recorded_25pct_rate)+' meet the target.';
    $('cash-observed').textContent=fmt(cash.valid_fare_trips)+' valid-fare May cash trips; '+pct(cash.recorded_nonzero_tip_rate,0)+' have a recorded nonzero tip.';
    const selected=study.metrics.July.find(r=>r.model==='selected'),base=study.metrics.July.find(r=>r.model==='majority');
    if($('brief-ap-model')){$('brief-ap-model').textContent=selected.average_precision.toFixed(3);$('brief-ap-baseline').textContent=base.average_precision.toFixed(3);$('brief-model-bar').style.width=100*selected.average_precision+'%';$('brief-baseline-bar').style.width=100*base.average_precision+'%';$('brief-precision').textContent=pct(selected.precision);$('brief-recall').textContent=pct(selected.recall);}
    const intervals=study.intervals.find(r=>r.metric==='average_precision'&&r.estimator==='model');
    $('results-strip').innerHTML=[['July AP',selected.average_precision.toFixed(3),`95% CI ${intervals.lower_95.toFixed(3)}–${intervals.upper_95.toFixed(3)}`],['Precision',pct(selected.precision),'Among predicted generous tips'],['Recall',pct(selected.recall),'Of actual generous tips found'],['Top-20% lift',selected.lift_at_20pct.toFixed(2)+'×',fmt(selected.n)+' eligible July trips']].map(([label,value,note])=>`<div class="result-stat"><strong>${value}</strong><span>${label}</span><small>${note}</small></div>`).join('');
    $('failure-examples').innerHTML=study.failures.map(row=>`<article class="failure-example"><span>REAL JULY EXAMPLE · ${row.kind.toUpperCase()}</span><strong>${pct(row.probability)} predicted probability</strong><p>${row.target?'The trip did reach the 25% target. The model missed it.':'The trip did not reach the 25% target. The model flagged it.'}</p><small>Fare $${esc(row.fare_band)} · ${esc(row.duration_band)} min · ${esc(row.distance_band)} miles. One saved example; not a representative average.</small></article>`).join('');
    const worst=study.slices.filter(r=>r.n>=200).sort((a,b)=>b.cost_per_trip-a.cost_per_trip).slice(0,8);
    $('failure-slices').innerHTML=table(worst,[['slice','Slice'],['value','Group'],['n','Trips',fmt],['precision','Precision',pct],['recall','Recall',pct],['cost_per_trip','Cost / trip',n=>n.toFixed(3)]]);
  }

  function setupMap(){
    const svg=$('zone-map'),ns='http://www.w3.org/2000/svg';svg.setAttribute('viewBox',mapData.viewBox);
    const paths=new Map();
    mapData.zones.forEach(zone=>{const path=document.createElementNS(ns,'path');path.setAttribute('d',zone.path);path.dataset.zone=zone.id;path.setAttribute('class',zone.airport?'airport':'');const title=document.createElementNS(ns,'title');title.textContent=`${zone.name} · ${zone.borough} · ${fmt(zone.n)} eligible May trips`;path.append(title);path.addEventListener('pointerenter',()=>showZone(zone));path.addEventListener('click',()=>{$('map-zone').value=zone.id;showZone(zone);});svg.append(path);paths.set(zone.id,path);});
    function showZone(zone){
      paths.forEach((path,id)=>path.classList.toggle('selected',id===zone.id));
      $('zone-detail').innerHTML=`<span class="mini-label">PICKUP ZONE ${zone.id} · ${esc(zone.borough)}</span><h3>${esc(zone.name)}</h3><div class="zone-stat-row"><div><strong>${fmt(zone.n)}</strong><span>eligible May trips</span></div><div><strong>${zone.n?pct(zone.rate):'—'}</strong><span>generous-tip rate</span></div></div>${zone.airport?'<span class="status-pill caution">'+esc(zone.airport)+'</span>':''}<p>${zone.n<200?'Small sample: fewer than 200 trips. Rate is not used for the map color.':'Descriptive association within this pickup zone; not a causal or individual claim.'}</p>`;
    }
    function draw(){
      const borough=$('map-borough').value,metric=$('map-metric').value;
      const visible=mapData.zones.filter(z=>borough==='all'||z.borough===borough);
      const values=visible.filter(z=>z.n>=200).map(z=>metric==='rate'?z.rate:Math.log1p(z.n));
      const min=metric==='rate'?0:0,max=metric==='rate'?1:Math.max(1,...values);
      mapData.zones.forEach(z=>{const path=paths.get(z.id),active=borough==='all'||z.borough===borough;path.classList.toggle('dimmed',!active);const score=metric==='rate'?z.rate:Math.log1p(z.n);const t=z.n>=200?Math.max(0,Math.min(1,(score-min)/(max-min))):0;path.style.fill=z.n<200?'#263348':`rgb(${Math.round(21+170*t)},${Math.round(64+176*t)},${Math.round(91+164*t)})`;});
      $('legend-low').textContent=metric==='rate'?'0%':'0 trips';$('legend-high').textContent=metric==='rate'?'100%':fmt(Math.round(Math.expm1(max)))+' · log scale';
      const selected=$('map-zone').value;
      $('map-zone').innerHTML='<option value="">Select a zone…</option>'+visible.sort((a,b)=>a.name.localeCompare(b.name)).map(z=>`<option value="${z.id}">${esc(z.name)} (${z.id})</option>`).join('');
      if(visible.some(z=>String(z.id)===selected))$('map-zone').value=selected;
      svg.setAttribute('viewBox',mapData.viewBox);
      if(borough!=='all'&&visible.length){const boxes=visible.map(z=>paths.get(z.id).getBBox());const x=Math.min(...boxes.map(b=>b.x)),y=Math.min(...boxes.map(b=>b.y)),x2=Math.max(...boxes.map(b=>b.x+b.width)),y2=Math.max(...boxes.map(b=>b.y+b.height));svg.setAttribute('viewBox',`${x-25} ${y-25} ${x2-x+50} ${y2-y+50}`);}
      const zone=visible.find(z=>String(z.id)===$('map-zone').value)||visible.find(z=>z.n>=200)||visible[0];if(zone)showZone(zone);
    }
    $('map-borough').addEventListener('change',draw);$('map-metric').addEventListener('change',draw);
    $('map-zone').addEventListener('change',()=>{const zone=mapData.zones.find(z=>String(z.id)===$('map-zone').value);if(zone)showZone(zone);});draw();
  }

  const humanNames={fare_amount:'Fare',airport_trip:'Airport trip',extra:'Extra charge',mta_tax:'MTA tax',tolls_amount:'Tolls',improvement_surcharge:'Improvement surcharge',congestion_surcharge:'Congestion surcharge',Airport_fee:'Airport fee',cbd_congestion_fee:'CBD fee',PULocationID:'Pickup zone',DOLocationID:'Drop-off zone',pickup_borough:'Pickup borough'};
  function splitLabel(model,node){
    const f=model.features[model.feature[node]],split=model.split[node];
    if(f.kind==='category')return `${humanNames[f.name]||f.name} = ${f.category}?`;
    const raw=split*f.scale+f.mean;
    return `${humanNames[f.name]||f.name} ≤ ${f.name==='airport_trip'?raw.toFixed(2):money(raw)}?`;
  }
  function defaults(model){const row={};model.features.forEach(f=>{if(f.kind==='numeric')row[f.name]=f.median;});row.PULocationID=161;row.DOLocationID=236;row.pickup_borough='Manhattan';return row;}

  function setupModels(){
    const names={fare:'Fare',journey:'Distance & duration',calendar:'Pickup time & day',geography:'Zones & airport',passengers:'Passenger count',rate:'Rate code',fees:'Pre-tip fees',quality:'Quality flags'};
    $('feature-ledger').innerHTML=study.features.map(row=>`<div class="feature-chip ${row.retained?'kept':''}" title="June AP change ${Number(row.delta_ap).toFixed(4)}"><span>${row.retained?'✓':'−'} ${names[row.addition]}</span><small>${row.retained?'KEPT':'NOT RETAINED'}</small></div>`).join('');
    $('feature-table').innerHTML=table(study.features,[['addition','Feature group'],['june_ap','June AP',v=>v.toFixed(4)],['delta_ap','AP change',v=>(v>=0?'+':'')+v.toFixed(4)],['retained','Retained',v=>v?'Yes':'No'],['reason','Decision']]);
    const stories={
      majority:['1 → 1 → 1','Majority baseline','May has more positive than negative labels. This baseline predicts a generous tip for every eligible card trip. Its score is the same May prevalence for every trip.'],
      rule:['fare ≤ $10?','A simple fare rule','A predeclared rule picks the May fare band with the highest positive rate: $0–10. That band gets a positive decision; other bands get a negative decision. The band was chosen from May, not July.'],
      tree:['◇ → ◇ → ●','A decision tree','A sequence of learned questions divides trips into groups. The predicted probability is the positive rate in the final May group. Below, follow the real two-level baseline.'],
      logistic:['inputs → σ → p','Logistic regression','Numeric features are scaled and categories encoded. Learned weights combine them into a score, then a logistic curve maps it to a probability between 0 and 1.']
    };
    function story(key){const [glyph,title,description]=stories[key];$('model-explainer').innerHTML=`<div class="model-glyph" aria-hidden="true">${esc(glyph)}</div><div><h3>${title}</h3><p>${description}</p></div>`;}
    setupTabs('[data-model-story]','modelStory',story);story('majority');
    $('pipeline-play').addEventListener('click',()=>{const track=document.querySelector('.pipeline-track');track.classList.remove('running');void track.offsetWidth;track.classList.add('running');$('pipeline-caption').textContent='Completed trip → May-fitted preprocessing → learned tree → estimated probability → compare with 0.32. Try the actual prediction below.';});
    function tree(){
      const model=models.depth2,row=defaults(model);row.fare_amount=Number($('tree-fare').value);row.congestion_surcharge=Number($('tree-congestion').value);row.extra=Number($('tree-extra').value);
      if(!Number.isFinite(row.fare_amount)||row.fare_amount<=0||row.congestion_surcharge<0||row.extra<0){$('tree-result').textContent='Use a positive fare and nonnegative charges.';return;}
      const prediction=TaxiModel.predict(model,row),activeNodes=new Set([...prediction.path.map(s=>s.node),prediction.leaf]);
      let edges='',nodes='';
      function visit(node,x,y,span){
        const leaf=model.left[node]===-1,label=leaf?pct(model.probability[node])+' positive rate':splitLabel(model,node);
        if(!leaf){[[model.left[node],x-span,'Yes'],[model.right[node],x+span,'No']].forEach(([child,cx,answer])=>{const cy=y+110;edges+=`<path class="edge ${activeNodes.has(node)&&activeNodes.has(child)?'active':''}" d="M${x},${y+27} V${y+55} H${cx} V${cy-27}"/><text class="edge-label" x="${(x+cx)/2}" y="${y+48}" text-anchor="middle">${answer}</text>`;visit(child,cx,cy,span/2);});}
        const words=label.length>25?label.split(' ≤ '):[label];
        nodes+=`<g><rect x="${x-95}" y="${y-27}" width="190" height="62" rx="7" class="node-rect ${activeNodes.has(node)?'on-path':''}"/><text x="${x}" y="${y-5}" text-anchor="middle">${esc(words[0])}</text>${words.length>1?`<text x="${x}" y="${y+10}" text-anchor="middle">≤ ${esc(words[1])}</text>`:''}<text x="${x}" y="${y+24}" text-anchor="middle" style="font-size:8px;fill:#92a8c3">${fmt(model.samples[node])} May trips${leaf?' · '+(model.probability[node]>=model.threshold?'predict positive':'predict negative'):''}</text></g>`;
      }visit(0,450,45,220);
      $('tree-diagram').innerHTML=`<svg viewBox="0 0 900 315" role="img" aria-label="Actual depth-two tree with selected path highlighted">${edges}${nodes}</svg>`;
      $('tree-result').textContent=`This trip reaches a leaf with ${pct(prediction.probability)} generous tips among ${fmt(prediction.samples)} May training trips. At the baseline’s 0.39 threshold: ${prediction.positive?'predict generous':'predict below target'}.`;
    }['tree-fare','tree-congestion','tree-extra'].forEach(id=>$(id).addEventListener('input',tree));tree();
  }

  function setupPredictor(){
    const options=models.zones.map(z=>`<option value="${z.LocationID}">${esc(z.Zone)} · ${esc(z.Borough)} (${z.LocationID})</option>`).join('');
    $('pickup-zone').innerHTML=options;$('dropoff-zone').innerHTML=options;$('pickup-zone').value='161';$('dropoff-zone').value='236';
    $('predict-form').querySelector('button[type=submit]').disabled=false;
    $('predict-form').addEventListener('submit',event=>{
      event.preventDefault();$('predict-error').textContent='';const form=$('predict-form');if(!form.reportValidity())return;
      const input=Object.fromEntries(new FormData(form).entries());
      const row={};models.selected.numeric_columns.forEach(name=>{if(name!=='airport_trip')row[name]=Number(input[name]);});
      const normalize=value=>{const n=Number(value);return Number.isInteger(n)&&n>=1&&n<=263?n:265;};
      row.PULocationID=normalize(input.PULocationID);row.DOLocationID=normalize(input.DOLocationID);
      row.pickup_borough=models.zones.find(z=>z.LocationID===row.PULocationID)?.Borough||'Unknown';
      row.airport_trip=Number([1,132,138].includes(row.PULocationID)||[1,132,138].includes(row.DOLocationID));
      const duration=Number(input.duration_minutes),distance=Number(input.trip_distance);
      if(!Number.isFinite(duration)||duration<0.5||duration>240||!Number.isFinite(distance)||distance<=0||distance>100){$('predict-error').textContent='Enter a duration of 0.5–240 minutes and a distance greater than 0 and at most 100 miles in Journey context.';return;}
      if(distance/duration*60>100){$('predict-error').textContent='This journey exceeds the study’s 100 mph average-speed limit. Adjust distance or duration.';return;}
      try{
        const result=TaxiModel.predict(models.selected,row);
        $('prediction-probability').textContent=pct(result.probability);
        $('probability-gauge').style.setProperty('--prob',pct(result.probability));
        $('prediction-class').textContent=result.positive?'Above the 0.32 decision threshold':'Below the 0.32 decision threshold';
        $('prediction-class').className='status-pill '+(result.positive?'positive':'caution');
        $('prediction-summary').textContent=`The selected leaf contains ${fmt(result.samples)} May trips. ${pct(result.probability)} met the target. This is a group-based estimate, not certainty about a passenger.`;
        const steps=result.path.map(step=>{const f=models.selected.features[step.feature];let label=splitLabel(models.selected,step.node);if(f.kind==='category')label+=step.left?' No.':' Yes.';else label+=step.left?' Yes.':' No.';return '<li>'+esc(label)+'</li>';}).join('');
        $('prediction-path').innerHTML=`<details class="prediction-path"><summary>Why this trip reached this estimate</summary><ol>${steps}</ol><small>This is the actual tree path, not a causal explanation or feature-importance estimate.</small></details>`;
      }catch(error){$('predict-error').textContent='Prediction could not be calculated: '+error.message;}
    });
    $('predict-form').addEventListener('input',()=>{if($('prediction-probability').textContent!=='—')$('prediction-class').textContent='Inputs changed · predict again to update';});
  }

  setupTarget();
  async function load(){
    const status=$('lab-status');status.hidden=false;status.classList.remove('error');status.textContent='Loading the study’s saved evidence…';
    try{
      const base=root.dataset.base==='.'?'./':root.dataset.base.replace(/\/$/,'')+'/';
      const fetchJSON=async name=>{const r=await fetch(base+'assets/lab/'+name);if(!r.ok)throw new Error('Missing '+name);return r.json();};
      [study,models,mapData]=await Promise.all(['study.json','model.json','zones.json'].map(fetchJSON));
      renderData();setupMap();setupModels();setupPredictor();
      if(!window.TaxiCharts)throw new Error('Chart module did not load');TaxiCharts.init(study);
      if(window.TaxiMotion)TaxiMotion.init();
      status.hidden=true;root.dataset.loaded='true';
    }catch(error){status.classList.add('error');status.textContent='The interactive evidence could not load. The full reports are still available through Docs. ';const retry=document.createElement('button');retry.textContent='Reload';retry.addEventListener('click',()=>location.reload());status.append(retry);console.error('Taxi lab:',error);}
  }load();
})();
