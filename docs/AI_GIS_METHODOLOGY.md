# AI and GIS methodology

## Classification

The real baseline uses scikit-learn TF-IDF word unigrams/bigrams with sublinear term frequency and logistic regression (C=5, random seed 42). `complaints.csv` contains 108 authored English complaints across Pothole, Garbage, Streetlight, Waterlogging, Drainage and Road Damage. 84 examples train the model and 24 independently written examples form the held-out synthetic test set. Every category has 14 training and 4 test items. No downloaded citizen data is used.

Training uses only training rows. Evaluation reports accuracy, per-category precision/recall/F1, macro averages, confusion matrix, inference time and low-confidence rate. Artifact version is `tfidf-logreg-demo-v1` with dataset `synthetic-v1`. The database stores model version, prediction, confidence and timestamp for every case. A probability below 0.4 triggers manual routing review unless a citizen explicitly selects a valid category through the API. Predictions are suggestions, and probabilities are not calibrated on field data.

Observed held-out accuracy: 23/24 = 95.83%. Macro precision 96.67%, recall 95.83%, F1 95.77%. One pothole example became Road Damage. Five of 24 examples had confidence below 0.4. A tiny synthetic corpus can substantially overstate real-world performance. Test wording and training domains overlap. External district-level data, independent annotators, multilingual evaluation, drift monitoring and calibration are prerequisites for operational use.

## Severity

Text heuristics contribute up to 30 points for reported damage, 25 for safety terms, 15 for sensitive locations, 15 for related reports and 10 for traffic. Historical incidents currently contribute 0. The configured prototype bands are Low 0–25, Moderate 26–50, High 51–75 and Critical 76–100. Explanations are stored with the case. The implementation does not infer visual damage or historical safety incidents from uploaded photos. A four-example policy consistency check produced MAE 2.5 points against hand-entered expected scores. This is a policy test, not a validated severity predictor.

## Related incidents

Candidates share category, lie within 150 metres, and were reported in the previous 30 days. PostGIS mode uses ST_DWithin on geography to select nearby candidates. Portable tests use Haversine distance. The score is 0.8 × TF-IDF cosine similarity + 0.2 × normalized geographic proximity. A threshold of 0.45 links reports to a cluster. Candidate comparisons are capped at 500 recent reports for bounded work.

All citizen cases remain individually stored. Matching does not delete or suppress any complaint. The score is a heuristic similarity, not a same-incident probability. Evaluation on eight synthetic pairs produced positive precision 1.0, recall 0.4 and F1 0.5714. Low recall is a known limitation. This test is too small for a field claim. Image similarity, multilingual embeddings and human-reviewed cluster merging are future work.

## Human corrections

Authorized office/admin users can store a corrected category and reason. The original prediction remains available. The case enters routing review after correction. The admin must review office assignment and SLA consistency. Corrections do not automatically retrain or replace the model. Retraining is an explicit offline step with held-out evaluation and versioned deployment.

## GIS and routing

GIS answers where a case lies. PostGIS stores WGS84/SRID 4326 case Points and ward MultiPolygons. ST_Covers includes points on boundaries. Overlapping boundary matches fail safely into review. Invalid polygons and coordinates are rejected. A source record and verified flag accompany imported geometry. Portable mode uses Shapely covers with the same geographic coordinates.

The bundled rectangle is synthetic and has no official ward meaning. It spans longitude 76.25–76.35 and latitude 9.90–10.03. These are fixture coordinates only. Production mode excludes unverified polygons and rules. Obtain reliable authorized boundaries, then create district/local-body/ward relationships through admin configuration.

Routing independently queries category + ward + active verified configuration. No ML output determines legal responsibility. Unknown jurisdiction, absent trusted rules and low-confidence classification lead to ROUTING_REVIEW_REQUIRED. The seed rule maps six categories in the synthetic ward to DEMO Civic Office A. This is explicitly prototype data.

## SLA and escalation

Prototype policies use 24/72/168/336 hours for Critical/High/Moderate/Low. Each assignment snapshots start/deadline/warning time into an instance. The Celery job checks every 60 seconds. It notifies at warning and records an escalation at breach. Duplicate checks do not repeat an active escalation. The initial configured escalation authority is the policy's escalation office. Continued breaches advance through configured parent offices after another policy-duration interval. The chain ends safely when no parent is configured. No case is automatically escalated to the Chief Minister's Office.
