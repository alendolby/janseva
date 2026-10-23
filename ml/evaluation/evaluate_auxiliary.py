import sys,json
from pathlib import Path
from sklearn.metrics import classification_report,mean_absolute_error
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"backend"))
from app.ml.duplicates import similarity
from app.ml.severity import severity
# Independent, hand-authored toy pairs. Illustrative thresholds, not operational validation.
pairs=[
("large pothole near school","deep pothole outside school",20,1),
("garbage near market","rubbish bags dumped at market",15,1),
("broken streetlight at bus stop","streetlight outside hospital is off",140,0),
("blocked sewage drain","drain clogged with sewage",10,1),
("pothole on road","loose asphalt on damaged pavement",40,0),
("rainwater flooding lane","standing rainwater floods lane",30,1),
("garbage at park","food waste near hospital",120,0),
("street lamps off at night","road is dark because lamps failed",10,1)]
y=[r[3] for r in pairs];pred=[int(similarity(a,b,d)>=0.45) for a,b,d,_ in pairs]
# Expected scores are manually specified against prototype policy.
cases=[("small pothole",10),("large pothole near school vehicles swerving",80),("broken lamp unsafe",55),("large garbage near hospital",55)]
report={"duplicates":classification_report(y,pred,output_dict=True,zero_division=0),
 "severity_mae":mean_absolute_error([y for t,y in cases],[severity(t)["score"] for t,y in cases]),
 "limitations":"8 synthetic text pairs and 4 manually specified severity checks. No real-world accuracy claim."}
(Path(__file__).parent/"auxiliary.json").write_text(json.dumps(report,indent=2));print(report)
