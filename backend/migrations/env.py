from alembic import context
from app.core.db import engine,Base
from app.models import entities
config=context.config
def offline():
    context.configure(url=str(engine.url),target_metadata=Base.metadata,literal_binds=True)
    with context.begin_transaction():context.run_migrations()
def online():
    with engine.connect() as connection:
        context.configure(connection=connection,target_metadata=Base.metadata,compare_type=True)
        with context.begin_transaction():context.run_migrations()
if context.is_offline_mode():offline()
else:online()
