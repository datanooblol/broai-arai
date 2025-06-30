# from sqlmodel import SQLModel
# from .engine import engine
# from sqlmodel import text

# def get_extensions():
#     with engine.connect() as conn:
#         conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
#         conn.commit()

# def create_db_tables():
#     with engine.begin() as conn:
#         SQLModel.metadata.create_all(conn)

# def initialize_memories():
#     get_extensions()
#     create_db_tables()

from sqlmodel import SQLModel
from .engine import engine
from sqlmodel import text
from sqlalchemy.exc import ProgrammingError, DBAPIError

def get_extensions():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

def create_db_tables():
    with engine.begin() as conn:
        SQLModel.metadata.create_all(conn)

def create_jargon_search_trigger_and_index():
    with engine.connect() as conn:
        # Run outside transaction block to allow isolated errors
        trans = conn.begin()
        try:
            conn.execute(text("""
                CREATE TRIGGER jargon_search_vector_update
                BEFORE INSERT OR UPDATE ON jargon
                FOR EACH ROW EXECUTE FUNCTION
                tsvector_update_trigger(search_vector, 'pg_catalog.english', jargon);
            """))
        except DBAPIError as e:
            if "already exists" in str(e):
                print("🔁 Trigger already exists, skipping.")
                trans.rollback()
            else:
                print("❌ Trigger creation failed.")
                trans.rollback()
                raise
        else:
            trans.commit()

        # Separate block for index creation
        trans = conn.begin()
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_jargon_search_vector
                ON jargon USING GIN (search_vector);
            """))
        except DBAPIError as e:
            print("❌ Index creation failed.")
            trans.rollback()
            raise
        else:
            trans.commit()

def initialize_memories():
    get_extensions()
    create_db_tables()
    create_jargon_search_trigger_and_index()

