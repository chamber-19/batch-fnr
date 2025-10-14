#!/usr/bin/env python3
"""
AutoCAD Text Tools - Unified Application
Main entry point for the combined AutoCAD text processing tools.

This application provides a plugin-based architecture for various AutoCAD text operations:
- Batch Find & Replace with title block management
- Text Unification and scaling
- Advanced geometry operations
- Extensible plugin system

Author: Root3Power LLC
Version: 2.0.0
"""

import sys
import os
import logging
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(app_dir / 'logs' / 'autocad_tools.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    try:
        # Ensure logs directory exists
        (app_dir / 'logs').mkdir(exist_ok=True)
        
        # Import PySide6 components
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QIcon
        
        # Import our application
        from core.application import AutoCADTextToolsApp
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("AutoCAD Text Tools")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("Root3Power LLC")
        
        # Set application icon
        icon_path = app_dir / 'resources' / 'root3_logo.png'
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Create and show main application
        main_app = AutoCADTextToolsApp()
        main_app.show()
        
        logger.info("AutoCAD Text Tools application started successfully")
        
        # Run the application
        return app.exec()
        
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Please install required packages:")
        print("pip install PySide6 pywin32 pyyaml pandas openpyxl pillow")
        return 1
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        print(f"Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
