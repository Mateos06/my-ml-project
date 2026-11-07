/* Interactive views of exported aggregate evidence. No fitting or scoring here. */
(function (root) {
  'use strict';
  const COLORS = { yellow: '#facc15', blue: '#38bdf8', green: '#22c55e', red: '#ef4444', muted: '#8ea6c3', grid: '#ffffff10', text: '#dce8f6' };
  const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const fmt = n => Number(n).toLocaleString('en-US');
  const pct = (n, digits = 1) => Number.isFinite(Number(n)) ? (100 * Number(n)).toFixed(digits) + '%' : 'Unavailable';
  const dec = (n, digits = 3) => Number.isFinite(Number(n)) ? Number(n).toFixed(digits) : 'Unavailable';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const el = id => document.getElementById(id);
  const setText = (id, value) => { if (el(id)) el(id).textContent = value; };

  function table(headers, rows, caption) {
    return '<table><caption style="text-align:left;padding:8px 0;color:#a9b7cc">' + esc(caption) + '</caption><thead><tr>' + headers.map(h => '<th scope="col">' + esc(h) + '</th>').join('') + '</tr></thead><tbody>' + rows.map(row => '<tr>' + row.map(v => '<td>' + esc(v) + '</td>').join('') + '</tr>').join('') + '</tbody></table>';
  }

  function init(study) {
    if (!root.echarts) throw new Error('The local chart library did not load. Reload the page to retry.');
    if (root.TaxiCharts.instance) root.TaxiCharts.instance.dispose();
    const charts = new Map(), cleanups = [];
    const motion = root.matchMedia('(prefers-reduced-motion: reduce)');
    const bind = (target, type, listener) => { if (target) { target.addEventListener(type, listener); cleanups.push(() => target.removeEventListener(type, listener)); } };
    const chartObserver = new ResizeObserver(entries => entries.forEach(entry => {
      const chart = charts.get(entry.target.id);
      if (chart && entry.contentRect.width > 0) chart.resize();
    }));
    const base = () => ({
      backgroundColor: 'transparent', animation: !motion.matches, animationDuration: 700, animationDurationUpdate: 450,
      animationEasing: 'cubicOut', textStyle: { fontFamily: 'Segoe UI, Arial, sans-serif', color: COLORS.text },
      color: [COLORS.blue, COLORS.yellow, COLORS.green], aria: { enabled: true, decal: { show: false } },
      grid: { left: 60, right: 25, top: 34, bottom: 65, containLabel: false },
      tooltip: { confine: true, backgroundColor: '#0a1525f7', borderColor: '#3a506d', textStyle: { color: '#e2edf9', fontSize: 12 }, padding: 14 },
      xAxis: { axisLine: { lineStyle: { color: '#40516a' } }, axisTick: { show: false }, axisLabel: { color: COLORS.muted, fontSize: 10 }, nameTextStyle: { color: '#a9bdd5', fontSize: 10 }, nameLocation: 'middle', nameGap: 36 },
      yAxis: { axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: COLORS.muted, fontSize: 10 }, splitLine: { lineStyle: { color: COLORS.grid } }, nameTextStyle: { color: '#a9bdd5', fontSize: 10 }, nameGap: 18 }
    });
    function draw(id, option, description) {
      const element = el(id);
      if (!element) return null;
      let chart = charts.get(id);
      if (!chart) {
        chart = root.echarts.init(element, null, { renderer: 'svg' });
        charts.set(id, chart); chartObserver.observe(element);
      }
      const defaults = base();
      const merged = { ...defaults, ...option, aria: { ...defaults.aria, description },
        tooltip: { ...defaults.tooltip, ...option.tooltip },
        xAxis: { ...defaults.xAxis, ...option.xAxis }, yAxis: { ...defaults.yAxis, ...option.yAxis } };
      chart.setOption(merged, { notMerge: true });
      element.setAttribute('aria-label', description);
      return chart;
    }
    function tabs(selector, attribute, callback) {
      const buttons = [...document.querySelectorAll(selector)];
      function activate(button) {
        buttons.forEach(other => { const active = other === button; other.setAttribute('aria-selected', String(active)); other.tabIndex = active ? 0 : -1; });
        callback(button.getAttribute(attribute));
      }
      buttons.forEach(button => {
        button.tabIndex = button.getAttribute('aria-selected') === 'true' ? 0 : -1;
        bind(button, 'click', () => activate(button));
        bind(button, 'keydown', event => {
          if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
          event.preventDefault();
          const index = buttons.indexOf(button);
          const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length;
          activate(buttons[next]); buttons[next].focus();
        });
      });
    }
    function accessibleDetail(chartId, id, caption) {
      let target = el(id);
      if (target) return target;
      const details = document.createElement('details'); details.className = 'technical';
      const summary = document.createElement('summary'); summary.textContent = caption;
      target = document.createElement('div'); target.id = id; target.className = 'table-scroll';
      details.append(summary, target); el(chartId)?.parentElement.append(details);
      return target;
    }
    function intervalSeries(rows) {
      return { name: '95% Wilson interval', type: 'custom', silent: true, z: 6,
        data: rows.map((row, i) => [i, row.lower_95 * 100, row.upper_95 * 100]),
        renderItem: (params, api) => {
          const low = api.coord([api.value(0), api.value(1)]), high = api.coord([api.value(0), api.value(2)]);
          const style = { stroke: '#e0edfa', lineWidth: 1.25, opacity: .85 };
          return { type: 'group', children: [
            { type: 'line', shape: { x1: low[0], y1: low[1], x2: high[0], y2: high[1] }, style },
            { type: 'line', shape: { x1: low[0] - 4, y1: low[1], x2: low[0] + 4, y2: low[1] }, style },
            { type: 'line', shape: { x1: high[0] - 4, y1: high[1], x2: high[0] + 4, y2: high[1] }, style }
          ] };
        }
      };
    }

    const groupMeta = {
      fare_band: { title: 'The fare changes the tipping pattern', axis: 'Meter fare ($)', label: row => '$' + row.fare_band, interpretation: 'Bars show the share of eligible card trips with a tip of at least 25% of fare. Whiskers are 95% Wilson intervals. Fare bands use (lower, upper] boundaries; this is an association, not evidence that changing a fare causes a different tip.' },
      pickup_hour: { title: 'Twenty-four hours of recorded tipping', axis: 'Hour of pickup · local recorded clock', label: row => String(row.pickup_hour).padStart(2, '0') + ':00', interpretation: 'Each tile is an hour of the pickup clock. Color represents the generous-tip rate on a fixed 0–100% scale. The tooltip gives the count and uncertainty interval. The trip record does not measure the reason for the difference.' },
      day_of_week: { title: 'Does the day of the week matter?', axis: 'Pickup weekday', label: row => DAYS[row.day_of_week], interpretation: 'Select weekdays to compare. The vertical scale stays at 0–100% so a small difference cannot look enormous. Whiskers show 95% Wilson intervals; these comparisons are descriptive and not adjusted for multiple testing.' },
      airport_trip: { title: 'Airport trips have a different profile', axis: 'Pickup or drop-off at an airport', label: row => row.airport_trip === 1 ? 'Airport trip' : 'Non-airport', interpretation: 'An airport trip starts or ends in zone 1 (Newark/EWR), 132 (JFK), or 138 (LaGuardia/LGA). This chart pools those three airports. It does not provide airport-specific rates or establish that the airport itself causes the difference.' },
      distance_band: { title: 'Short trips and long trips look different', axis: 'Meter distance (miles)', label: row => row.distance_band + ' mi', interpretation: 'Distance is known at payment. Bars compare completed-trip distance bands, with 95% Wilson intervals. The target is a percentage of fare, so its relationship with distance is not a causal estimate.' },
      duration_band: { title: 'The journey clock tells part of the story', axis: 'Trip duration (minutes)', label: row => row.duration_band + ' min', interpretation: 'Duration is derived from the pickup and drop-off timestamps. Rates describe the fixed cleaned population; trips under 30 seconds or over four hours were excluded. Whiskers are 95% Wilson intervals.' },
      passenger_count: { title: 'More passengers, less certainty', axis: 'Recorded passenger count', label: row => row.passenger_count == null ? 'Unknown' : String(row.passenger_count), interpretation: 'Missing, zero and invalid passenger counts become Unknown. Counts of five or six have much smaller samples; the six-passenger bar has fewer than 200 trips. The model did not retain this feature group after June comparison.' }
    };
    let edaKey = 'distribution', fareFocus = 'all';
    const selectedDays = new Set([0, 1, 2, 3, 4, 5, 6]);
    function sortedRows(key) {
      return [...study.rates[key]].sort((a, b) => {
        if (a[key] == null) return 1; if (b[key] == null) return -1;
        return parseFloat(a[key]) - parseFloat(b[key]);
      });
    }
    function rangeSummary(rows, key) {
      const meta = groupMeta[key], high = rows.reduce((a, b) => a.rate > b.rate ? a : b), low = rows.reduce((a, b) => a.rate < b.rate ? a : b);
      if (rows.length === 1) return `${meta.label(rows[0])}: ${pct(rows[0].rate)} generous tips across ${fmt(rows[0].n)} eligible trips.`;
      return `${meta.label(high)}: ${pct(high.rate)}; ${meta.label(low)}: ${pct(low.rate)}. A ${((high.rate - low.rate) * 100).toFixed(1)} percentage-point difference in May.`;
    }
    function setEdaControl(key) {
      const control = el('eda-control'); if (!control) return;
      control.replaceChildren();
      if (key === 'fare_band') {
        const label = document.createElement('label'); label.textContent = 'Highlight a fare range'; label.htmlFor = 'fare-range';
        const select = document.createElement('select'); select.id = 'fare-range';
        select.innerHTML = '<option value="all">Compare all fares</option>' + sortedRows(key).map(row => '<option value="' + esc(row.fare_band) + '">$' + esc(row.fare_band) + ' · n=' + fmt(row.n) + '</option>').join('');
        select.value = fareFocus; bind(select, 'change', () => { fareFocus = select.value; renderEDA(false); });
        label.append(select); control.append(label);
      } else if (key === 'day_of_week') {
        const group = document.createElement('div'); group.className = 'day-pills'; group.setAttribute('role', 'group'); group.setAttribute('aria-label', 'Weekdays to compare');
        DAYS.forEach((day, i) => {
          const button = document.createElement('button'); button.type = 'button'; button.textContent = day.slice(0, 3); button.setAttribute('aria-label', 'Include ' + day); button.setAttribute('aria-pressed', String(selectedDays.has(i)));
          bind(button, 'click', () => {
            if (selectedDays.has(i)) { if (selectedDays.size === 1) return; selectedDays.delete(i); } else selectedDays.add(i);
            button.setAttribute('aria-pressed', String(selectedDays.has(i))); renderEDA(false);
          }); group.append(button);
        }); control.append(group);
      }
    }
    function renderEDA(rebuildControls = true) {
      if (rebuildControls) setEdaControl(edaKey);
      if (edaKey === 'distribution') {
        const histogram = study.histogram;
        const peaks = [...histogram].filter(row => row.percentage > 0 && row.percentage < 100).sort((a, b) => b.count - a.count).slice(0, 3);
        const peakSet = new Set(peaks.map(row => row.percentage));
        setText('eda-title', 'A cluster around the generous-tip threshold');
        setText('eda-subtitle', `May · ${fmt(study.may_n)} eligible card trips · one-percentage-point bins`);
        setText('eda-takeaway', `The largest nonzero bin is ${peaks[0].percentage}–${peaks[0].percentage + 1}% of fare. Tip-screen suggestions may contribute, but the records cannot prove why people chose these amounts.`);
        setText('eda-interpretation', 'Each bar counts recorded tip percentages in [lower, upper) bins. The last bin pools all percentages at or above 100%; those trips stayed in the analysis. Yellow bars highlight the three largest nonzero bins, and the vertical line marks the 25% target. Zooming changes the view, not the sample.');
        if (el('eda-table')) el('eda-table').innerHTML = table(['Tip / fare bin', 'Trips', 'Share of May population'], histogram.map(row => [row.percentage === 100 ? '100% or more' : row.percentage + '–' + (row.percentage + 1) + '%', fmt(row.count), pct(row.share, 2)]), 'Histogram bins from the cleaned May population');
        draw('eda-chart', {
          grid: { left: 65, right: 20, top: 32, bottom: 85 },
          xAxis: { type: 'category', data: histogram.map(row => String(row.percentage)), name: 'Recorded tip / meter fare (%)', axisLabel: { color: COLORS.muted, fontSize: 10, interval: 9, formatter: value => value === '100' ? '100+' : value } },
          yAxis: { type: 'value', name: 'Card trips', axisLabel: { color: COLORS.muted, fontSize: 10, formatter: value => value >= 1000 ? (value / 1000).toFixed(0) + 'k' : value } },
          tooltip: { trigger: 'item', formatter: params => { const row = histogram[params.dataIndex]; return '<b>' + (row.percentage === 100 ? '100% or more' : row.percentage + '–' + (row.percentage + 1) + '% of fare') + '</b><br>' + fmt(row.count) + ' trips<br>' + pct(row.share, 2) + ' of the May population'; } },
          dataZoom: [{ type: 'inside', startValue: 0, endValue: 100 }, { type: 'slider', height: 13, bottom: 11, borderColor: 'transparent', backgroundColor: '#1b2a41', fillerColor: '#38bdf825', handleStyle: { color: COLORS.blue }, textStyle: { color: COLORS.muted, fontSize: 9 }, dataBackground: { lineStyle: { color: '#395c7e' }, areaStyle: { color: '#253f5b' } } }],
          series: [{ name: 'Card trips', type: 'bar', barCategoryGap: '12%', data: histogram.map(row => ({ value: row.count, itemStyle: { color: peakSet.has(row.percentage) ? COLORS.yellow : COLORS.blue, opacity: row.percentage >= 25 ? 1 : .55, borderRadius: [2, 2, 0, 0] } })),
            markLine: { symbol: 'none', label: { formatter: '25% target', color: COLORS.yellow, fontSize: 10 }, lineStyle: { color: COLORS.yellow, type: 'dashed' }, data: [{ xAxis: '25' }] } }]
        }, `Histogram of recorded tip percentages for ${fmt(study.may_n)} May card trips. Largest nonzero bin: ${peaks[0].percentage} to ${peaks[0].percentage + 1} percent. Data table follows.`);
        return;
      }
      const meta = groupMeta[edaKey]; let rows = sortedRows(edaKey);
      if (edaKey === 'day_of_week') rows = rows.filter(row => selectedDays.has(row.day_of_week));
      const sample = rows.reduce((sum, row) => sum + row.n, 0);
      setText('eda-title', meta.title); setText('eda-subtitle', `May · ${fmt(sample)} eligible card trips${edaKey === 'day_of_week' && rows.length < 7 ? ' in selected weekdays' : ''}`);
      let takeaway = rangeSummary(rows, edaKey);
      if (edaKey === 'fare_band' && fareFocus !== 'all') takeaway = rangeSummary(rows.filter(row => row.fare_band === fareFocus), edaKey) + ' Other ranges stay visible for context.';
      if (edaKey === 'passenger_count') takeaway = `Single-passenger trips dominate the sample (${fmt(rows.find(row => row.passenger_count === 1).n)}). Rates for five or six passengers rely on far fewer observations.`;
      if (edaKey === 'airport_trip') takeaway = `Airport trips: ${pct(rows.find(row => row.airport_trip === 1).rate)} generous tips; non-airport trips: ${pct(rows.find(row => row.airport_trip === 0).rate)}. Airport trips also differ in fare and route.`;
      setText('eda-takeaway', takeaway); setText('eda-interpretation', meta.interpretation);
      if (el('eda-table')) el('eda-table').innerHTML = table([meta.axis, 'Trips', 'Generous tips', 'Rate', '95% Wilson interval', 'Difference from overall'], rows.map(row => [meta.label(row), fmt(row.n), fmt(row.positives), pct(row.rate), pct(row.lower_95) + '–' + pct(row.upper_95), (row.difference_pp >= 0 ? '+' : '') + row.difference_pp.toFixed(1) + ' pp']), 'Rates and sample sizes from the cleaned May population');
      const tooltip = row => '<b>' + esc(meta.label(row)) + '</b><br>' + pct(row.rate) + ' generous tips<br>n = ' + fmt(row.n) + '<br>95% interval: ' + pct(row.lower_95) + '–' + pct(row.upper_95) + (row.n < 200 ? '<br><span style="color:#facc15">Small sample · n &lt; 200</span>' : '');
      if (edaKey === 'pickup_hour') {
        draw('eda-chart', {
          grid: { left: 65, right: 20, top: 20, bottom: 92 },
          xAxis: { type: 'category', data: ['+0h', '+1h', '+2h', '+3h', '+4h', '+5h'], name: 'Hour within each six-hour block', splitArea: { show: false }, axisLine: { show: false } },
          yAxis: { type: 'category', data: ['00–05', '06–11', '12–17', '18–23'], inverse: true, name: 'Local time', splitLine: { show: false }, axisLine: { show: false } },
          tooltip: { trigger: 'item', formatter: params => tooltip(rows[params.dataIndex]) },
          visualMap: { min: 0, max: 100, orient: 'horizontal', left: 'center', bottom: 0, itemWidth: 12, itemHeight: 160, calculable: false, text: ['100%', '0%'], textStyle: { color: COLORS.muted, fontSize: 9 }, inRange: { color: ['#152a41', '#176491', '#38bdf8', '#c3f4ff'] } },
          series: [{ type: 'heatmap', name: 'Generous-tip rate', data: rows.map(row => [row.pickup_hour % 6, Math.floor(row.pickup_hour / 6), row.rate * 100]), itemStyle: { borderColor: '#111d30', borderWidth: 5, borderRadius: 6 }, label: { show: true, fontSize: 10, color: '#f8fafc', formatter: params => { const row = rows[params.dataIndex]; return meta.label(row) + '\n' + pct(row.rate, 0); } }, emphasis: { itemStyle: { borderColor: COLORS.yellow } } }]
        }, `${meta.title}. Twenty-four hour tiles with a fixed zero to 100 percent color scale. ${takeaway}`);
      } else {
        draw('eda-chart', {
          grid: { left: 60, right: 25, top: 35, bottom: 65 },
          xAxis: { type: 'category', data: rows.map(meta.label), name: meta.axis, axisLabel: { color: COLORS.muted, fontSize: 10, interval: 0, formatter: value => edaKey === 'day_of_week' ? value.slice(0, 3) : value } },
          yAxis: { type: 'value', name: 'Generous-tip rate', min: 0, max: 100, axisLabel: { color: COLORS.muted, fontSize: 10, formatter: '{value}%' } },
          tooltip: { trigger: 'item', formatter: params => tooltip(rows[params.dataIndex]) },
          series: [{ name: 'Generous-tip rate', type: 'bar', barMaxWidth: 90, data: rows.map(row => ({ value: row.rate * 100, itemStyle: { color: row.n < 200 ? '#8293a9' : edaKey === 'fare_band' && fareFocus === row.fare_band ? COLORS.yellow : COLORS.blue, opacity: edaKey === 'fare_band' && fareFocus !== 'all' && fareFocus !== row.fare_band ? .25 : 1, borderRadius: [4, 4, 0, 0] } })), label: { show: true, position: 'top', distance: 12, color: '#e2edf9', fontSize: 11, formatter: params => params.value.toFixed(1) + '%' }, markLine: { symbol: 'none', lineStyle: { color: COLORS.yellow, type: 'dashed', opacity: .5 }, label: { show: false }, data: [{ yAxis: study.selection.training_prevalence * 100 }] } }, intervalSeries(rows)]
        }, `${meta.title}. Rates use a zero to 100 percent scale. ${takeaway} Whiskers show 95 percent Wilson intervals; accessible table follows.`);
      }
    }
    tabs('[data-eda]', 'data-eda', key => { edaKey = key; renderEDA(); });
    renderEDA();

    const modelLabels = { majority: 'Majority baseline', fare_rule: 'Simple fare rule', tree_depth_2: 'Depth-2 tree', logistic: 'Logistic regression', tree_depth_8: 'Selected depth-8 tree', selected: 'Selected depth-8 tree', tree_depth_4: 'Depth-4 tree', tree_depth_6: 'Depth-6 tree', tree_depth_6_leaf_1000: 'Depth-6 · leaf 1,000' };
    const metricMeta = {
      average_precision: { name: 'Average precision / PR AUC', max: 1, direction: 'Higher is better', explain: 'AP summarizes precision across recall levels. July: 0.747 for the selected tree versus 0.585 for constant scores.' },
      precision: { name: 'Precision', max: 1, direction: 'Higher is better', explain: 'Of the trips flagged as generous, how many really were? In July, about 71 of every 100 flagged trips had a 25%+ recorded tip.' },
      recall: { name: 'Recall', max: 1, direction: 'Higher is better', explain: 'Of all genuinely generous recorded tips, how many were found? In July, the selected tree found about 95 of every 100.' },
      lift_at_20pct: { name: 'Lift in the top 20%', max: null, direction: 'Higher is better; 1× = population rate', explain: 'Lift compares the generous-tip rate in the highest-scored fifth of trips with the overall rate. July lift was 1.33×.' },
      brier: { name: 'Brier score', max: 1, direction: 'Lower is better', explain: 'Brier score averages squared probability errors. It reflects both calibration and discrimination; it is not a pure calibration measure.' },
      cost_per_trip: { name: 'Decision cost per trip', max: null, direction: 'Lower is better', explain: 'Cost uses the stated assumption FP = 1 and FN = 2 units. It is an illustrative trade-off, not measured dollars.' }
    };
    function metricValue(metric, value) {
      return metric === 'precision' || metric === 'recall' ? pct(value) : metric === 'lift_at_20pct' ? dec(value, 2) + '×' : dec(value);
    }
    function getSelected(month) { return study.metrics[month].find(row => row.model === (month === 'July' ? 'selected' : study.selection.selected_model)); }
    function renderComparison() {
      const month = el('compare-month')?.value || 'June', metric = el('compare-metric')?.value || 'average_precision', meta = metricMeta[metric];
      const wanted = ['majority', 'fare_rule', 'tree_depth_2', 'logistic', month === 'July' ? 'selected' : study.selection.selected_model];
      const rows = wanted.map(name => study.metrics[month].find(row => row.model === name) || { model: name, missing: true });
      setText('comparison-subtitle', month === 'June' ? `June · ${fmt(study.selection.n_validation)} eligible trips · used for model selection` : `July · ${fmt(study.final.n_test)} eligible trips · logistic regression was not scored in the final test`);
      const selected = getSelected(month), baseline = study.metrics[month].find(row => row.model === 'majority');
      let explain = meta.explain;
      if (metric === 'average_precision') explain = `${month}: selected-tree AP ${dec(selected.average_precision)} versus baseline ${dec(baseline.average_precision)}. AP summarizes precision across recall levels; it is not accuracy.`;
      setText('metric-definition', explain + ' ' + meta.direction + '.');
      const all = study.metrics[month];
      const headers = ['Model', 'Trips', 'AP', 'Precision', 'Recall', 'Top-20% lift', 'Brier', 'Cost / trip', 'Threshold'];
      if (el('comparison-table')) {
        let html = table(headers, all.map(row => [modelLabels[row.model] || row.model, fmt(row.n), dec(row.average_precision, 4), pct(row.precision), pct(row.recall), dec(row.lift_at_20pct, 3) + '×', dec(row.brier, 4), dec(row.cost_per_trip, 4), dec(row.threshold, 2)]), month + ' complete saved model results');
        if (month === 'July') html += table(['Metric', 'Estimator', 'Estimate', '95% lower', '95% upper'], study.intervals.map(row => [row.metric, row.estimator, dec(row.estimate, 4), dec(row.lower_95, 4), dec(row.upper_95, 4)]), '500 paired trip-level bootstrap resamples; fixed predictions');
        else html += '<p style="font-size:11px;margin-top:12px">June was reused for feature, model and threshold choices. Its winning score is a development result, not an unbiased estimate of future performance.</p>';
        el('comparison-table').innerHTML = html;
      }
      const narrow = el('comparison-chart')?.clientWidth < 500;
      const axisMax = meta.max || Math.max(1, ...rows.filter(row => !row.missing).map(row => row[metric])) * 1.18;
      const colors = rows.map(row => row.model === study.selection.selected_model || row.model === 'selected' ? COLORS.yellow : row.model === 'majority' ? '#526b8a' : COLORS.blue);
      const chart = draw('comparison-chart', {
        grid: { left: narrow ? 112 : 165, right: 62, top: 17, bottom: 51 },
        xAxis: { type: 'value', min: 0, max: axisMax, name: meta.name, nameGap: 32, splitLine: { lineStyle: { color: COLORS.grid } }, axisLabel: { color: COLORS.muted, fontSize: 9, formatter: value => metric === 'precision' || metric === 'recall' ? pct(value, 0) : metric === 'lift_at_20pct' ? value.toFixed(1) + '×' : value.toFixed(1) } },
        yAxis: { type: 'category', inverse: true, data: rows.map(row => modelLabels[row.model]), splitLine: { show: false }, axisLabel: { color: COLORS.text, fontSize: narrow ? 9 : 11, width: narrow ? 100 : 150, overflow: 'break' } },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => { const row = rows[params[0].dataIndex]; return '<b>' + esc(modelLabels[row.model]) + '</b><br>' + (row.missing ? 'Not scored on July. No result is invented.' : esc(meta.name) + ': <b>' + metricValue(metric, row[metric]) + '</b><br>n = ' + fmt(row.n) + '<br>Decision threshold: ' + dec(row.threshold, 2)); } },
        series: [{ type: 'bar', name: meta.name, barWidth: 22, showBackground: true, backgroundStyle: { color: '#ffffff04', borderRadius: 4 }, data: rows.map((row, index) => ({ value: row.missing ? null : row[metric], itemStyle: { color: colors[index], borderRadius: [0, 4, 4, 0] } })), label: { show: true, position: 'right', color: '#dce8f6', fontSize: 11, formatter: params => metricValue(metric, params.value) } }],
        graphic: month === 'July' ? [{ type: 'text', left: narrow ? 122 : 175, top: '61%', silent: true, style: { text: 'Not scored on July', fill: '#8299b5', font: '10px Segoe UI' } }] : []
      }, `${month} model comparison for ${meta.name}. ${meta.direction}. Selected tree: ${metricValue(metric, selected[metric])}; majority: ${metricValue(metric, baseline[metric])}. ${month === 'July' ? 'Logistic regression has no July result.' : ''} Complete data table follows.`);
      if (chart) chart.resize();
    }
    bind(el('compare-month'), 'change', renderComparison); bind(el('compare-metric'), 'change', renderComparison);
    renderComparison();

    const prTable = accessibleDetail('pr-chart', 'pr-data-table', 'Curve thresholds · accessible data');
    const calibrationTable = accessibleDetail('calibration-chart', 'calibration-data-table', 'Probability bins · sample sizes & data');
    function renderCurves() {
      const month = el('curve-month')?.value || 'June', rows = study.curves[month], selected = getSelected(month), calibration = study.reliability[month];
      const description = `${month} selected-tree precision recall curve, ${fmt(selected.n)} trips, average precision ${dec(selected.average_precision)}.`;
      draw('pr-chart', {
        grid: { left: 57, right: 18, top: 32, bottom: 55 },
        xAxis: { type: 'value', name: 'Recall · share of generous tips found', min: 0, max: 1, axisLabel: { color: COLORS.muted, fontSize: 9, formatter: value => pct(value, 0) } },
        yAxis: { type: 'value', name: 'Precision', min: 0, max: 1, axisLabel: { color: COLORS.muted, fontSize: 9, formatter: value => pct(value, 0) } },
        tooltip: { trigger: 'item', formatter: params => {
          if (params.seriesName !== 'Selected tree') return 'Constant-score reference: ' + pct(selected.positive_rate) + '<br>n = ' + fmt(selected.n);
          const row = rows[params.dataIndex]; return '<b>' + month + ' · saved predictions</b><br>Threshold: ' + (row.threshold == null ? 'No positive predictions (endpoint)' : dec(row.threshold, 4)) + '<br>Precision: ' + pct(row.precision) + '<br>Recall: ' + pct(row.recall) + '<br>n = ' + fmt(selected.n);
        } },
        series: [{ name: 'Selected tree', type: 'line', data: rows.map(row => [row.recall, row.precision]), symbol: 'circle', symbolSize: 5, showSymbol: true, smooth: false, lineStyle: { width: 2.5, color: COLORS.blue }, itemStyle: { color: COLORS.blue }, areaStyle: { color: '#38bdf80b' } },
          { name: 'Prevalence reference', type: 'line', data: [[0, selected.positive_rate], [1, selected.positive_rate]], showSymbol: false, lineStyle: { color: COLORS.yellow, type: 'dashed', width: 1.2 } }]
      }, description + ' Hover points for thresholds; the full threshold table is available below.');
      if (prTable) prTable.innerHTML = table(['Threshold', 'Precision', 'Recall', 'Sample size'], rows.map(row => [row.threshold == null ? 'No-positive endpoint' : dec(row.threshold, 6), pct(row.precision), pct(row.recall), fmt(selected.n)]), description);
      const reliabilityElement = el('calibration-chart');
      const subtitle = reliabilityElement?.parentElement.querySelector('.chart-heading p'); if (subtitle) subtitle.textContent = `${month} · ${fmt(selected.n)} trips · 0.1-wide probability bins`;
      draw('calibration-chart', {
        grid: { left: 57, right: 18, top: 32, bottom: 55 },
        xAxis: { type: 'value', name: 'Mean predicted probability', min: 0, max: 1, axisLabel: { color: COLORS.muted, fontSize: 9, formatter: value => pct(value, 0) } },
        yAxis: { type: 'value', name: 'Observed rate', min: 0, max: 1, axisLabel: { color: COLORS.muted, fontSize: 9, formatter: value => pct(value, 0) } },
        tooltip: { trigger: 'item', formatter: params => {
          if (params.seriesName === 'Perfect calibration') return 'Perfect calibration: predicted and observed rates match.';
          const row = calibration[params.dataIndex]; return '<b>' + esc(row.bin) + ' probability bin</b><br>Mean prediction: ' + pct(row.predicted) + '<br>Observed positives: ' + pct(row.observed) + '<br>n = ' + fmt(row.n) + (row.n < 200 ? '<br>Small sample: interpret cautiously.' : '');
        } },
        series: [{ name: 'Perfect calibration', type: 'line', data: [[0, 0], [1, 1]], showSymbol: false, lineStyle: { color: COLORS.yellow, type: 'dashed', width: 1.2 } },
          { name: 'Observed reliability', type: 'line', data: calibration.map(row => [row.predicted, row.observed]), symbol: 'circle', symbolSize: (value, params) => Math.min(16, 5 + Math.sqrt(calibration[params.dataIndex].n) / 30), lineStyle: { color: COLORS.blue, width: 2 }, itemStyle: { color: COLORS.blue }, smooth: false }]
      }, `${month} probability reliability on ${fmt(selected.n)} trips. Predicted versus observed positive rates in fixed bins. Bubble size reflects the bin sample size; table follows. Brier score ${dec(selected.brier)}.`);
      if (calibrationTable) calibrationTable.innerHTML = table(['Probability bin', 'Trips', 'Mean prediction', 'Observed rate'], calibration.map(row => [row.bin, fmt(row.n), pct(row.predicted), pct(row.observed)]), `${month} reliability. Empty bins omitted; no post-hoc calibration was fitted.`);
    }
    bind(el('curve-month'), 'change', renderCurves); renderCurves();

    const explanations = {
      tp: 'True positive: the model predicted a generous tip and the recorded tip was at least 25% of fare.',
      fp: 'False positive: the model predicted a generous tip, but the recorded tip was below 25% of fare. Cost: 1 assumed unit.',
      fn: 'False negative: the model predicted below the threshold, but the recorded tip was generous. Cost: 2 assumed units.',
      tn: 'True negative: the model predicted below the threshold and the recorded tip was below 25% of fare.'
    };
    let selectedCell = null;
    function renderDecision() {
      const month = el('decision-month')?.value || 'June', slider = el('decision-threshold');
      if (!slider) return;
      const frozen = month === 'July'; slider.disabled = frozen;
      if (frozen) slider.value = String(Math.round(study.selection.threshold * 100));
      const threshold = frozen ? study.selection.threshold : Number(slider.value) / 100;
      const row = frozen ? getSelected('July') : study.thresholds.find(item => Math.abs(item.threshold - threshold) < .000001);
      if (!row) throw new Error('The selected threshold has no saved June result.');
      const n = row.tp + row.fp + row.fn + row.tn;
      setText('decision-value', threshold.toFixed(2));
      slider.setAttribute('aria-valuetext', threshold.toFixed(2) + ' probability threshold');
      setText('decision-note', frozen ? 'July is locked at the June-chosen 0.32 threshold. These counts come from the single saved scoring pass.' : `June only · ${fmt(n)} trips. Exploration changes this display, not the frozen model or July result.`);
      setText('decision-cost', dec(row.cost_per_trip, 3) + ' assumed cost units / trip');
      const axis = el('confusion-matrix')?.parentElement.querySelector('.matrix-axis'); if (axis) axis.textContent = 'Rows: prediction + / − · columns: actual + / −';
      if (el('confusion-matrix')) {
        const cells = [['tp', 'Correct positive', 'Predicted + · Actual +'], ['fp', 'False positive', 'Predicted + · Actual −'], ['fn', 'Missed positive', 'Predicted − · Actual +'], ['tn', 'Correct negative', 'Predicted − · Actual −']];
        el('confusion-matrix').innerHTML = cells.map(([key, label, small]) => '<button type="button" class="matrix-cell ' + (key === 'fp' || key === 'fn' ? 'error' : '') + '" data-matrix="' + key + '" aria-pressed="' + String(selectedCell === key) + '" aria-label="' + esc(label + ', ' + fmt(row[key]) + ' trips. ' + explanations[key]) + '"><small>' + small + '</small><strong>' + fmt(row[key]) + '</strong><span>' + label + '</span><small>' + pct(row[key] / n) + ' of ' + month + ' trips</small></button>').join('');
        // Delegated click handler is attached once below, not once per slider event.
      }
      setText('matrix-explanation', selectedCell ? explanations[selectedCell] : `${month}: precision ${pct(row.precision)}, recall ${pct(row.recall)}. Select a cell to explain an outcome.`);
    }
    bind(el('confusion-matrix'), 'click', event => { const button = event.target.closest('[data-matrix]'); if (button) { selectedCell = button.dataset.matrix; renderDecision(); } });
    bind(el('decision-threshold'), 'input', renderDecision); bind(el('decision-month'), 'change', renderDecision); renderDecision();

    bind(motion, 'change', () => { renderEDA(false); renderComparison(); renderCurves(); });
    const instance = { dispose() { chartObserver.disconnect(); cleanups.forEach(fn => fn()); charts.forEach(chart => chart.dispose()); charts.clear(); }, resize() { charts.forEach(chart => chart.resize()); } };
    root.TaxiCharts.instance = instance;
    return instance;
  }

  root.TaxiCharts = { init };
})(window);
