# Test report

Verified on 8 October 2026. Build host: macOS ARM, Python 3.12.14 virtual environment, Node 25.3.0 for build/browser orchestration and Node 24.19.0 for the final frontend unit tests. Supported clean-install targets: Python 3.12 and Node 22.12+ or Node 24. Dependencies are locked. No unsupported Node branch is required by the project.

| Check | Result | Scope |
|---|---|---|
| Backend pytest | 24 passed | SQLite migration, real HTTP client, learned model, local evidence |
| Backend line coverage | 89.50% | Includes imported models and configuration, not field assurance |
| Frontend Vitest | 7 passed | Validation, badges, navigation guards |
| Playwright workflow | Passed | Citizen report/image, routing, office actions/image, feedback, admin analytics |
| Playwright mobile | Passed | 390px layout and registration validation |
| Production frontend build | Passed | TypeScript compilation and Vite bundle |
| npm dependency audit | Zero reported vulnerabilities after patching | Registry result at build time |
| Development Compose | Syntax validated | docker compose config --quiet |
| Production Compose overlay | Syntax validated | Merged production configuration |
| Live Docker services | Not run | Build host had no Docker engine |
| Live PostgreSQL/PostGIS | Not run | SQL/spatial implementation present, runtime acceptance needed |
| Redis/Celery/MinIO/Grafana | Not run | Integrated adapters/configuration, runtime acceptance needed |
| SMTP | Not sent | No delivery credentials configured |
| Remote deployment | Not performed | No hosting destination provided |

The backend tests exercise password policy, forced citizen registration, revoked sessions, token reuse, geographic inclusion/exclusion, foreign-reference errors, upload spoofing, evidence access, immutable audit triggers, scoped analytics, internal-note privacy, SLA idempotence, warnings, reopening, information replies, reassignment/corrections and eight concurrent public case IDs and configured multilevel escalation.

The browser test operates an isolated temporary database and synthetic accounts. It never contacts government systems. Its repair image is test-generated evidence. Functional tests passing do not establish official routing validity, model generalization, security certification or production reliability.

The build emits a size warning for MapLibre's approximately 1 MB JS module. The map is dynamically imported and its worker is separately bundled. Broader performance work needs measured user traffic and real map data.

Model evidence is in ml/evaluation/classification.json and auxiliary.json. Backend coverage summary is in testing/backend-coverage-summary.json. Full test commands are in README and SETUP documents.
