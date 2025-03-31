class VehicleController:
    def __init__(self, db_instance):
        self.db = db_instance
    
    def show_view(self, display_widget):
        display_widget.setText("Vehicle button has been pushed")
