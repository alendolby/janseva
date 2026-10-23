from alembic import op
from migrations.schema_v1 import Base
revision="0001"
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    if bind.dialect.name=="postgresql":op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    Base.metadata.create_all(bind)
    if bind.dialect.name=="postgresql":
        op.execute("""CREATE FUNCTION prevent_audit_mutation() RETURNS trigger AS $$
        BEGIN RAISE EXCEPTION 'Audit records are immutable'; END; $$ LANGUAGE plpgsql""")
        for table in ["audit_logs","case_events"]:
            op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation()")
    else:
        for table in ["audit_logs","case_events"]:
            for action in ["UPDATE","DELETE"]:
                op.execute(f"CREATE TRIGGER immutable_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'Audit records are immutable'); END")

def downgrade():
    bind=op.get_bind()
    if bind.dialect.name=="postgresql":
        for table in ["audit_logs","case_events"]:op.execute(f"DROP TRIGGER immutable_{table} ON {table}")
        op.execute("DROP FUNCTION prevent_audit_mutation()")
    Base.metadata.drop_all(bind)
