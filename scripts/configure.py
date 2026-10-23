"""Run from the repository root. Generates local-only secrets, never part of source control."""
from pathlib import Path
import secrets
root=Path(__file__).resolve().parents[1]
if (root/".env").exists():raise SystemExit(".env exists. Preserve your existing settings or explicitly remove it to regenerate.")
password=secrets.token_urlsafe(24);jwt=secrets.token_urlsafe(48)
demo="Demo"+secrets.token_urlsafe(16)+"2026a"
access="jns"+secrets.token_hex(8);storage=secrets.token_urlsafe(36)
values={"DEMO_MODE":"true","DEMO_PASSWORD":demo,"POSTGRES_DB":"janaseva","POSTGRES_USER":"janaseva",
 "POSTGRES_PASSWORD":password,"DATABASE_URL":f"postgresql+psycopg://janaseva:{password}@postgres:5432/janaseva",
 "JWT_SECRET":jwt,"REDIS_URL":"redis://redis:6379/0","RATE_LIMIT_BACKEND":"redis","STORAGE_MODE":"s3",
 "STORAGE_ENDPOINT":"http://minio:9000","STORAGE_ACCESS_KEY":access,"STORAGE_SECRET_KEY":storage,
 "STORAGE_BUCKET":"janaseva","CORS_ORIGINS":"http://localhost:8080,http://localhost:5173"}
(root/".env").write_text("\n".join(f"{k}={v}" for k,v in values.items())+"\n")
values.update({"DATABASE_URL":"sqlite:///./janaseva.db","STORAGE_MODE":"local","RATE_LIMIT_BACKEND":"memory","UPLOAD_DIR":"./uploads","REDIS_URL":"redis://localhost:6379/0"})
(root/"backend/.env").write_text("\n".join(f"{k}={v}" for k,v in values.items())+"\n")
accounts="Synthetic demo accounts\nPassword for all demo accounts: "+demo+"\n"+"\n".join(["citizen@example.com","citizen2@example.com","office@example.com","office2@example.com","supervisor@example.com","admin@example.com"])+"\n"
(root/"DEMO_ACCOUNTS.txt").write_text(accounts)
for path in [root/".env",root/"backend/.env",root/"DEMO_ACCOUNTS.txt"]:
    try:path.chmod(0o600)
    except OSError:pass
print("Generated .env, backend/.env and DEMO_ACCOUNTS.txt. These are local files excluded from Git.")
