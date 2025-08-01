import logging
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from controller.adventure_hooks_generator import AdventureHooksGenerator

logger = logging.getLogger(__name__)

class AdventureHooksView(QWidget):
    """View for generating and displaying adventure hooks."""
    
    # Signal to notify when hooks are generated
    hooks_generated = pyqtSignal(list)
    
    def __init__(self, parent=None):
        """Initialize the adventure hooks view."""
        super().__init__(parent)
        self.generator = AdventureHooksGenerator()
        self.hooks = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Adventure Hook Generator")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Controls section
        controls_group = QGroupBox("Generation Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Options layout
        options_layout = QHBoxLayout()
        
        # Number of hooks
        count_layout = QVBoxLayout()
        count_label = QLabel("Number of Hooks:")
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(1, 10)
        self.count_spinbox.setValue(3)
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_spinbox)
        options_layout.addLayout(count_layout)
        
        # World selection
        world_layout = QVBoxLayout()
        world_label = QLabel("World:")
        self.world_combo = QComboBox()
        self.world_combo.addItem("Random")
        for world in self.generator.worlds:
            self.world_combo.addItem(world["name"])
        world_layout.addWidget(world_label)
        world_layout.addWidget(self.world_combo)
        options_layout.addLayout(world_layout)
        
        # AI enhancement option
        ai_layout = QVBoxLayout()
        ai_label = QLabel("Generation Method:")
        self.ai_checkbox = QCheckBox("Use AI Enhancement")
        self.ai_checkbox.setChecked(self.generator.gpt_available)
        self.ai_checkbox.setEnabled(self.generator.gpt_available)
        if not self.generator.gpt_available:
            self.ai_checkbox.setToolTip("AI enhancement unavailable - API key not found")
        ai_layout.addWidget(ai_label)
        ai_layout.addWidget(self.ai_checkbox)
        options_layout.addLayout(ai_layout)
        
        controls_layout.addLayout(options_layout)
        
        # Generate button
        self.generate_button = QPushButton("Generate Adventure Hooks")
        self.generate_button.clicked.connect(self.generate_hooks)
        controls_layout.addWidget(self.generate_button)
        
        main_layout.addWidget(controls_group)
        
        # Results section
        results_group = QGroupBox("Generated Hooks")
        results_layout = QVBoxLayout(results_group)
        
        # Scrollable area for hooks
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.hooks_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        results_layout.addWidget(scroll_area)
        
        main_layout.addWidget(results_group)
        
        # Set the main layout
        main_layout.setStretch(0, 0)  # Title
        main_layout.setStretch(1, 0)  # Controls
        main_layout.setStretch(2, 1)  # Results (should stretch)
    
    def generate_hooks(self):
        """Generate adventure hooks based on current settings."""
        try:
            # Clear existing hooks
            self._clear_hooks()
            
            # Get parameters
            count = self.count_spinbox.value()
            use_gpt = self.ai_checkbox.isChecked()
            world_idx = self.world_combo.currentIndex()
            
            # Generate hooks
            if world_idx == 0:  # Random world
                self.hooks = self.generator.generate_multiple_hooks(count, use_gpt)
            else:
                # Generate hooks for specific world
                world_data = self.generator.worlds[world_idx - 1]  # -1 because first item is "Random"
                self.hooks = []
                for _ in range(count):
                    if use_gpt:
                        hook = self.generator.generate_gpt_hook(world_data)
                        if hook:
                            self.hooks.append(hook)
                        else:
                            # Fall back to template if GPT fails
                            self.hooks.append(self.generator.generate_template_hook())
                    else:
                        # Force the template generator to use the selected world
                        saved_worlds = self.generator.worlds.copy()
                        self.generator.worlds = [world_data]
                        self.hooks.append(self.generator.generate_template_hook())
                        self.generator.worlds = saved_worlds
            
            # Display hooks
            self._display_hooks()
            
            # Emit signal
            self.hooks_generated.emit(self.hooks)
            
        except Exception as e:
            logger.error(f"Error generating hooks: {e}")
            # Display error in the UI
            error_text = QTextEdit()
            error_text.setReadOnly(True)
            error_text.setText(f"Error generating hooks: {e}")
            self.hooks_layout.addWidget(error_text)
    
    def _clear_hooks(self):
        """Clear all displayed hooks."""
        # Remove all widgets from the hooks layout
        while self.hooks_layout.count():
            item = self.hooks_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.hooks = []
    
    def _display_hooks(self):
        """Display the generated hooks in the UI."""
        for i, hook in enumerate(self.hooks, 1):
            # Create a frame for each hook
            hook_frame = QFrame()
            hook_frame.setFrameShape(QFrame.Shape.StyledPanel)
            hook_frame.setFrameShadow(QFrame.Shadow.Raised)
            hook_layout = QVBoxLayout(hook_frame)
            
            # Hook number
            number_label = QLabel(f"Hook #{i}")
            number_label.setStyleSheet("font-weight: bold;")
            hook_layout.addWidget(number_label)
            
            # Hook text
            hook_text = QTextEdit()
            hook_text.setReadOnly(True)
            hook_text.setText(hook)
            hook_text.setMinimumHeight(100)
            hook_layout.addWidget(hook_text)
            
            # Add to main layout
            self.hooks_layout.addWidget(hook_frame)
    
    def load_worlds_from_db(self, db_controller):
        """
        Load worlds from the database.
        
        Args:
            db_controller: Database controller with access to planet data
        """
        self.generator.load_worlds_from_db(db_controller)
        
        # Update the world combo box
        self.world_combo.clear()
        self.world_combo.addItem("Random")
        for world in self.generator.worlds:
            self.world_combo.addItem(world["name"])
