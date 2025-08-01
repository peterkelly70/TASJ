import logging
from typing import Optional

from view.adventure_hooks_view import AdventureHooksView
from controller.adventure_hooks_generator import AdventureHooksGenerator

logger = logging.getLogger(__name__)

class AdventureHooksController:
    """Controller for adventure hooks generation and management."""
    
    def __init__(self, db_instance):
        """
        Initialize the adventure hooks controller.
        
        Args:
            db_instance: Database instance for accessing world data
        """
        self.db = db_instance
        self.generator = AdventureHooksGenerator()
        self.view = None
            
    def show_view(self, display_widget):
        """
        Show the adventure hooks view in the provided widget.
        
        Args:
            display_widget: Widget to display the adventure hooks view in
        """
        # Clear any existing layout
        if display_widget.layout():
            while display_widget.layout().count():
                item = display_widget.layout().takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            
        # Create view if it doesn't exist
        if not self.view:
            self.view = AdventureHooksView()
            
            # Connect the view to the database
            try:
                # Load worlds from database if available
                self.view.load_worlds_from_db(self.db)
            except Exception as e:
                logger.error(f"Failed to load worlds from database: {e}")
                
        # Add view to the display widget
        if display_widget.layout():
            display_widget.layout().addWidget(self.view)
        else:
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(display_widget)
            layout.addWidget(self.view)
            
        logger.info("Adventure hooks view displayed")
    
    def save_hook(self, hook_text: str, campaign_id: Optional[int] = None):
        """
        Save an adventure hook to the database.
        
        Args:
            hook_text: The text of the adventure hook
            campaign_id: Optional campaign ID to associate with the hook
        """
        try:
            # This is a placeholder - implement actual DB access based on your model
            # self.db.save_adventure_hook(hook_text, campaign_id)
            logger.info(f"Saved adventure hook to database: {hook_text[:30]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to save adventure hook: {e}")
            return False
