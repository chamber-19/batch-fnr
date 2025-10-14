# AutoCAD Text Tools

A comprehensive, plugin-based application for advanced text processing in AutoCAD drawings. This unified application combines powerful find & replace functionality with intelligent text unification and scaling tools.

## Features

### 🔍 Find & Replace Plugin
- **Batch Processing**: Process entire directories or specific DWG files
- **Advanced Pattern Matching**: Support for regular expressions and case-sensitive searches
- **Title Block Management**: Automated revision tracking and field updates
- **Stamp Management**: Issue type management with layer control
- **Excel Reporting**: Detailed change logs and error reports
- **Preview Mode**: Safe testing without permanent changes

### 🎯 Text Unifier Plugin
- **Intelligent Clustering**: Automatic grouping of similar text entities
- **Column Detection**: Smart alignment and organization
- **Multiple Strategies**: Nudge, Mask, or Move unification approaches
- **Text Wrapping**: Advanced text formatting options
- **Visual Preview**: Real-time preview of unification results
- **Scaling Tools**: Comprehensive text height management

### 🏗️ Plugin Architecture
- **Modular Design**: Each tool is a standalone plugin
- **Easy Extension**: Simple framework for adding new tools
- **Shared Services**: Common AutoCAD interface and settings management
- **Dark Theme**: Professional, modern user interface

## Installation

### Prerequisites
- Windows 10/11
- AutoCAD 2016 or later
- Python 3.8 or later

### Quick Install
1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### Standalone Executable
For users without Python installed, a standalone executable can be built:
```bash
pip install PyInstaller
pyinstaller AutoCAD_Text_Tools.spec
```

## Usage

### Getting Started
1. Launch the application
2. Ensure AutoCAD is running with a drawing open
3. Click "Connect to AutoCAD" in the toolbar
4. Select the desired plugin tab
5. Configure settings and run operations

### Find & Replace Plugin
1. **Select Mode**: Choose between directory or specific files
2. **Add Rules**: Create find/replace rules with optional regex support
3. **Configure Title Block**: Set up revision management if needed
4. **Choose Stamp**: Select issue type for layer management
5. **Preview**: Test changes safely before applying
6. **Run**: Execute the batch operation

### Text Unifier Plugin
1. **Collect Text**: Gather text entities from the current drawing
2. **Review Groups**: Examine automatically created text groups
3. **Edit Groups**: Modify unified text as needed
4. **Select Strategy**: Choose Nudge, Mask, or Move approach
5. **Preview**: Visualize the unification results
6. **Apply**: Execute the unification operation

## Configuration

### Settings Management
The application uses YAML-based configuration with three levels:
- **Application Settings**: Global preferences and window layout
- **User Settings**: Personal preferences and defaults
- **Plugin Settings**: Tool-specific configurations

### AutoCAD Integration
- **Multi-Version Support**: Compatible with AutoCAD 2016-2024
- **Robust Connection**: Automatic retry and error handling
- **COM Threading**: Proper thread management for stability
- **Entity Support**: Text, MText, Dimensions, Leaders, and Attributes

## Advanced Features

### Scientific Computing Integration
When optional scientific libraries are installed:
- **ML Clustering**: DBSCAN and KMeans for advanced text grouping
- **Optimization**: SciPy algorithms for optimal text positioning
- **Vectorized Operations**: NumPy for high-performance geometry calculations

### Extensibility
The plugin system allows easy addition of new tools:
```python
from plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def setup_ui(self):
        # Create your UI here
        pass
    
    def get_plugin_info(self):
        return {
            "name": "My Plugin",
            "version": "1.0.0",
            "description": "Custom functionality"
        }
```

## Architecture

### Core Components
- **Application**: Main window and plugin management
- **AutoCAD Bridge**: Enhanced COM interface with caching
- **Plugin Manager**: Dynamic plugin discovery and loading
- **Settings Manager**: YAML-based configuration system
- **Geometry**: Advanced geometric operations and utilities

### Plugin Structure
```
plugins/
├── base_plugin.py          # Abstract base class
├── find_replace/           # Find & Replace plugin
│   ├── __init__.py
│   ├── find_replace_plugin.py
│   ├── replacement_rule.py
│   ├── title_block_manager.py
│   └── find_replace_worker.py
└── text_unifier/           # Text Unifier plugin
    ├── __init__.py
    ├── text_unifier_plugin.py
    ├── text_item.py
    ├── text_group.py
    ├── text_unifier_core.py
    └── scaling_tool.py
```

## Development

### Setting Up Development Environment
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-qt black flake8
   ```

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black .
flake8 .
```

### Creating New Plugins
1. Create a new directory in `plugins/`
2. Inherit from `BasePlugin`
3. Implement required methods
4. Add to plugin discovery path

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure code passes all tests and formatting checks
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the plugin development guide

## Roadmap

### Planned Features
- **Batch Drawing Processing**: Multi-file operations with progress tracking
- **Advanced ML Features**: Text similarity analysis and smart grouping
- **Cloud Integration**: Settings sync and backup
- **API Interface**: REST API for external tool integration
- **Additional Plugins**: Dimension tools, block management, layer utilities

### Version History
- **v2.0.0**: Unified plugin architecture with Find & Replace and Text Unifier
- **v1.x**: Original standalone tools

---

**AutoCAD Text Tools** - Streamlining text management in AutoCAD drawings through intelligent automation and user-friendly interfaces.
