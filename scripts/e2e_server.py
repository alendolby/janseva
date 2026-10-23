import os,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.chdir(root/"backend");sys.path.insert(0,str(root/"backend"))
os.environ.update({"DATABASE_URL":"sqlite:///"+str(Path(tempfile.mkdtemp())/"e2e.db"),
 "JWT_SECRET":"e2e-only-"+"b"*64,"DEMO_MODE":"true","DEMO_PASSWORD":"BrowserDemo2026Safe",
 "STORAGE_MODE":"local","UPLOAD_DIR":tempfile.mkdtemp(),"RATE_LIMIT_BACKEND":"memory"})
from alembic import command
from alembic.config import Config
command.upgrade(Config("alembic.ini"),"head")
from app.seed import seed
seed()
import uvicorn
uvicorn.run("app.main:app",host="127.0.0.1",port=8000)
