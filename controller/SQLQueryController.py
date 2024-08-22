from model.traveller_database import TravellerDatabase
from view.sql_query_view import SQLQueryView

class SQLQueryController:
    def __init__(self, db_instance):
        self.db = TravellerDatabase(db_instance)
        self.view = SQLQueryView(self)

    def get_table_names(self):
        return self.db.get_table_names()

    def run_query(self, query):
        try:
            results = self.db.run_custom_query(query)
            return results
        except Exception as e:
            return f"Error: {e}"

    def show_view(self):
        self.view.show()