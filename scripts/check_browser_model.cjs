/* Cross-language parity check against cached sklearn predictions on May. */
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const runtime=require(path.join(root,'docs/javascripts/model-runtime.js'));
const model=JSON.parse(fs.readFileSync(path.join(root,'docs/assets/lab/model.json'))).selected;
const fixtures=JSON.parse(fs.readFileSync(path.join(root,'artifacts/browser_fixtures.json')));
let maximumError=0;
fixtures.rows.forEach((row,i)=>{
  const prediction=runtime.predict(model,row);
  maximumError=Math.max(maximumError,Math.abs(prediction.probability-fixtures.probabilities[i]));
  if(prediction.positive!==(fixtures.probabilities[i]>=model.threshold))throw new Error('Class mismatch at '+i);
});
if(maximumError>1e-12)throw new Error('Probability mismatch: '+maximumError);
const altered={...fixtures.rows[0],tip_amount:99999,total_amount:-99999,pickup_hour:23,trip_distance:99,duration_minutes:120,passenger_count:6};
if(runtime.predict(model,altered).probability!==runtime.predict(model,fixtures.rows[0]).probability)throw new Error('Unused fields affected prediction');
console.log(`Browser model matches sklearn on ${fixtures.rows.length} May rows; max error ${maximumError}. Forbidden/unused fields do not change scores.`);
