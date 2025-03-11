import glob
import os
import re
from model.traveller_database import TravellerDatabase

def ensure_migrations_table(db):
    """
    Creates a migrations table to track applied migrations if it doesn't already exist.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS migrations (
        migration_name TEXT PRIMARY KEY,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    db.execute_script(sql)

def migration_already_applied(db, migration_name):
    """
    Checks if a migration (by its filename) has already been applied.
    """
    result = db.read_records("migrations", {"migration_name": migration_name})
    return len(result) > 0

def record_migration(db, migration_name):
    """
    Records the successful application of a migration.
    """
    db.create_record("migrations", {"migration_name": migration_name})

def execute_alter_commands(db, migration_sql):
    """
    Processes ALTER TABLE ADD COLUMN commands from the migration SQL.
    It uses a regex to extract the table, column, and definition.
    """
    # Regex to capture: ALTER TABLE <table> ADD COLUMN <column> <definition>;
    pattern = re.compile(r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+COLUMN\s+(\w+)\s+([^;]+);', re.IGNORECASE)
    for match in pattern.finditer(migration_sql):
        table, column, definition = match.groups()
        if db.column_exists(table, column):
            print(f"Skipping: Column '{column}' already exists in table '{table}'.")
        else:
            command = f"ALTER TABLE {table} ADD COLUMN {column} {definition};"
            result = db.execute_script(command)
            if result == 1:
                print(f"Executed: {command}")
            else:
                print(f"Failed to execute: {command}")

def execute_migration_file(db, migration_file):
    """
    Reads and executes a single migration file.
    For ALTER TABLE commands, it processes them individually.
    Otherwise, it executes the script as a whole.
    """
    with open(migration_file, 'r') as file:
        migration_sql = file.read()
    if "ALTER TABLE" in migration_sql.upper():
        execute_alter_commands(db, migration_sql)
    else:
        result = db.execute_script(migration_sql)
        if result != 1:
            print(f"Failed migration: {migration_file}")
            return False
    return True

def run_migrations(db_type):
    """
    Runs all migration files from the migrations directory for the given db_type.
    Uses a migration tracking table to ensure each migration is applied only once.
    """
    migration_dir = f'migrations/{db_type}'
    migration_files = sorted(glob.glob(f'{migration_dir}/*.sql'))
    
    db = TravellerDatabase(db_type)
    ensure_migrations_table(db)
    
    for migration_file in migration_files:
        migration_name = os.path.basename(migration_file)
        if migration_already_applied(db, migration_name):
            print(f"Skipping already applied migration: {migration_name}")
            continue
        
        print(f"Running migration: {migration_name}")
        success = execute_migration_file(db, migration_file)
        if success:
            record_migration(db, migration_name)
            print(f"Migration {migration_name} applied successfully.")
        else:
            print(f"Migration {migration_name} failed.")
    
    db.close()

if __name__ == "__main__":
    # For example, use "sqlite" (or "mysql" as needed)
    db_type = "sqlite"
    run_migrations(db_type)
