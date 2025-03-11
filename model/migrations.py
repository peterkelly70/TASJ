import glob
from model.traveller_database import TravellerDatabase

def run_migrations():
    migration_dir = f'migrations/{db_type}'
    migration_files = sorted(glob.glob(f'{migration_dir}/*.sql'))

    db = TravellerDatabase(db_type)

    for migration_file in migration_files:
        with open(migration_file, 'r') as file:
            migration_sql = file.read()

            db.execute_script(migration_sql)
            print(f"Executed migration {migration_file}")

    db.close()
