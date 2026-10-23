from functools import lru_cache
from pathlib import Path
import csv, json, time,logging
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "ml/datasets/complaints.csv"
MODEL = ROOT / "ml/models/baseline.joblib"
VERSION = "tfidf-logreg-demo-v1"

def train():
    with DATA.open() as f: rows = list(csv.DictReader(f))
    train_rows = [r for r in rows if r["split"] == "train"]
    test_rows = [r for r in rows if r["split"] == "test"]
    model = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)),
        ("classifier", LogisticRegression(C=5, max_iter=1000, random_state=42))])
    model.fit([r["text"] for r in train_rows], [r["category"] for r in train_rows])
    started=time.perf_counter(); predicted=model.predict([r["text"] for r in test_rows])
    elapsed=(time.perf_counter()-started)*1000/len(test_rows)
    report=classification_report([r["category"] for r in test_rows], predicted, output_dict=True, zero_division=0)
    report.update({"confusion_matrix":confusion_matrix([r["category"] for r in test_rows], predicted, labels=model.classes_).tolist(),
        "labels":model.classes_.tolist(), "inference_ms_per_sample":elapsed,
        "low_confidence_rate":float((model.predict_proba([r["text"] for r in test_rows]).max(axis=1)<0.4).mean()),
        "train_samples":len(train_rows), "test_samples":len(test_rows),
        "limitation":"Authored synthetic English corpus. Test data is small and domain-specific, not external validation."})
    MODEL.parent.mkdir(parents=True,exist_ok=True);joblib.dump(model,MODEL)
    path=ROOT/"ml/evaluation/classification.json";path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2))
    return model,report

@lru_cache
def load_model():
    if not MODEL.exists(): return train()[0]
    return joblib.load(MODEL)  # Only locally trained, trusted artifacts.

def classify(text):
    model=load_model(); p=model.predict_proba([text])[0]; idx=int(p.argmax())
    logging.getLogger("janaseva").info(json.dumps({"event":"ai_inference","model":VERSION,"confidence":round(float(p[idx]),3)}))
    return {"category":str(model.classes_[idx]), "confidence":float(p[idx]),
        "model_version":VERSION, "review_required":bool(p[idx]<0.4), "baseline":True}
