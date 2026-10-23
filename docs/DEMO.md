# Complete demonstration

Start the application and use the generated synthetic credentials in `DEMO_ACCOUNTS.txt`.

1. Sign in as `citizen@example.com`. Open Report an issue.
2. Title: Large pothole near school. Description: There is a large pothole near the school entrance and vehicles are swerving to avoid it.
3. Select demo coordinates 9.965, 76.30. Enter a landmark and upload a JPG or PNG.
4. Submit. Record the generated JNS-KL-year-sequence case ID. Open the detail page and inspect the actual baseline confidence, score breakdown, office, SLA and timeline. Do not substitute an invented confidence.
5. Sign out. Sign in as `office@example.com` and open Case inbox. Choose the case, acknowledge it, then start work.
6. Add a status note if needed. Upload a repair image using Add resolution evidence. Enter a completion note and choose Resolve.
7. Sign out. Sign in as the citizen and open My complaints. Choose the case, inspect repair evidence, give a rating/comment and confirm resolution. Status becomes CLOSED.
8. Open Notifications to see the updates. Before closure, a citizen may instead request reopening with a reason.
9. Sign out. Sign in as `admin@example.com`. Open All complaints, Analytics, AI baseline and Audit logs. The case contributes to live workload and resolution metrics.

## Review and escalation demonstrations

- A report outside the synthetic rectangle enters ROUTING with ROUTING_REVIEW_REQUIRED. Admin reviews its location/category and assigns an office with a reason.
- Request information from an acknowledged or active case, then sign in as its citizen and provide a reply.
- Use Escalate with a reason for manual escalation. The configured supervisory authority receives oversight notifications.
- The Celery schedule evaluates warnings and overdue cases every 60 seconds. The admin SLA screen also provides a manual check for local development. To test overdue behavior reproducibly, run `pytest tests/test_workflow.py -k sla` from backend. Tests set clocks in isolated test data rather than mutating demo records.
- Sign in as `citizen2@example.com` or `office2@example.com` to verify unrelated cases are absent.

## User guide

Citizen: report, track, upload report evidence, read notifications, answer information requests, confirm resolution or request reopening. Feedback is available for RESOLVED cases.

Office: view permitted inbox/map/statistics, acknowledge, start, request information, record internal notes, assign an officer in the same office, upload repair evidence, resolve/reject with a reason, or escalate. Higher offices have read-only escalation oversight unless an admin reassigns the case.

Admin: manage accounts/roles/activation, departments, offices, categories, district/local-body/ward configuration, boundary provenance, routing rules and SLA policies. Inspect model metrics, correction counts, analytics and immutable audit records. Runtime deployment settings are read-only in the portal and configured through environment files.

Screenshots in `screenshots/` are from the real application using synthetic test data. UI labels and figures represent the state of those test cases, not real civic activity.
