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

def execute_migration_file(db, migration_file, worker=None):
    """
    Execute a migration file.
    
    Reads and executes a single migration file.
    For ALTER TABLE commands, it processes them individually.
    
    Args:
        db: Database connection
        migration_file: Path to the migration file
        worker: Optional worker thread for progress updates and cancellation
        
    Returns:
        bool: True if migration was successful, False otherwise
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

def run_migrations(db_type, worker=None, existing_db=None):
    """
    Runs all migration files from the migrations directory for the given db_type.
    Uses a migration tracking table to ensure each migration is applied only once.
    
    Args:
        db_type: Type of database (e.g., 'sqlite', 'mysql')
        worker: Optional worker thread for progress updates and cancellation
        existing_db: Optional existing database connection to use instead of creating a new one
    """
    migration_dir = f'migrations/{db_type}'
    if not os.path.exists(migration_dir):
        if worker:
            worker.progress.emit(f"Migration directory not found: {migration_dir}")
        raise FileNotFoundError(f"Migration directory not found: {migration_dir}")
    
    migration_files = sorted(glob.glob(f'{migration_dir}/*.sql'))
    if not migration_files:
        if worker:
            worker.progress.emit(f"No migration files found in {migration_dir}")
        print(f"No migration files found in {migration_dir}")
        return
    
    # Use existing database connection if provided, otherwise create a new one
    db = existing_db if existing_db else TravellerDatabase(db_type)
    should_close_db = existing_db is None  # Only close if we created a new connection
    
    try:
        ensure_migrations_table(db)
        total_files = len(migration_files)
        
        for idx, migration_file in enumerate(migration_files, 1):
            if worker and hasattr(worker, '_is_cancelled') and worker._is_cancelled:
                if worker:
                    worker.progress.emit("Migration cancelled by user")
                print("Migration cancelled by user")
                return False
                
            migration_name = os.path.basename(migration_file)
            
            if worker:
                progress = f"[{idx}/{total_files}] {migration_name}"
                worker.progress.emit(progress)
                
            if migration_already_applied(db, migration_name):
                msg = f"Skipping already applied migration: {migration_name}"
                if worker:
                    worker.progress.emit(msg)
                print(msg)
                continue
            
            print(f"Running migration: {migration_name}")
            try:
                success = execute_migration_file(db, migration_file, worker)
                if success:
                    record_migration(db, migration_name)
                    msg = f"Migration {migration_name} applied successfully."
                    if worker:
                        worker.progress.emit(msg)
                    print(msg)
                else:
                    msg = f"Migration {migration_name} failed."
                    if worker:
                        worker.progress.emit(msg)
                    print(msg)
                    return False
            except Exception as e:
                error_msg = f"Error applying migration {migration_name}: {str(e)}"
                if worker:
                    worker.progress.emit(error_msg)
                print(error_msg)
                raise
                
        return True
    finally:
        # Only close the database if we created a new connection
        if should_close_db:
            try:
                db.close()
            except Exception as e:
                if worker:
                    worker.progress.emit(f"Error closing database: {str(e)}")
                print(f"Error closing database: {str(e)}")

if __name__ == "__main__":
    # For example, use "sqlite" (or "mysql" as needed)
    db_type = "sqlite"
    run_migrations(db_type)
