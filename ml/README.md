# Baseline ML subsystem

Training/inference implementation is in backend/app/ml. The top-level datasets/training/evaluation/models folders retain reproducible inputs, commands, metrics and versioned trusted artifacts. Train from root with your Python 3.12 environment: `python ml/training/train.py`. Auxiliary evaluation imports the database-backed duplicate subsystem, so run `python ../ml/evaluation/evaluate_auxiliary.py` from backend with its .env configured.

Corpus: authored synthetic English examples, 84 train and 24 held-out, six categories. No personal information or scraped complaints. Read docs/AI_GIS_METHODOLOGY.md before interpreting metrics. Never load an untrusted joblib model; deserialization can execute code. The included artifact is produced by the supplied training script and should be used with requirements.lock. Source distribution includes the artifact for convenience; Git ignores generated joblib files by default.
