/* Exact interpreter of the exported sklearn preprocessing and decision tree. */
(function(root){
  'use strict';
  function vector(model, row) {
    return model.features.map(f=>{
      if(f.kind==='category') return String(row[f.name]??'Unknown')===f.category?1:0;
      let value=row[f.name];
      if(value===null||value===undefined||value==='') value=f.median;
      value=Number(value);
      if(!Number.isFinite(value)) throw new Error('Enter a finite value for '+f.name);
      return Math.fround((value-f.mean)/f.scale);
    });
  }
  function predict(model,row){
    const x=vector(model,row),path=[];let node=0;
    while(model.left[node]!==-1){
      const feature=model.feature[node],left=x[feature]<=model.split[node];
      path.push({node,feature,split:model.split[node],value:x[feature],left});
      node=left?model.left[node]:model.right[node];
    }
    return {probability:model.probability[node],positive:model.probability[node]>=model.threshold,path,leaf:node,samples:model.samples[node]};
  }
  root.TaxiModel={vector,predict};
  if(typeof module!=='undefined')module.exports=root.TaxiModel;
})(typeof window!=='undefined'?window:globalThis);
