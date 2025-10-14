# Hyphae Batch Find & Replace Unifier

A comprehensive AutoCAD text processing suite with both desktop and web interfaces.

## 📁 Project Structure

```
BatchFindAndReplace/
├── BatchFindAndReplaceV1/  # Original version (archived)
├── V1.5/                   # Current development version
│   ├── main.py            # Desktop application entry point
│   ├── core/              # Core application logic
│   ├── plugins/           # Plugin system (find-replace, text-unifier)
│   └── config/            # Configuration files
├── web-panel/             # React web interface
│   ├── src/
│   ├── package.json
│   └── ...
├── Dockerfile.frontend    # Web panel container
├── Dockerfile.backend     # API wrapper container
├── api_wrapper.py         # FastAPI backend
└── nginx.conf            # Web server config
```

## 🚀 Usage Options

### 1. **Desktop Application (V1.5)**
Full-featured PySide6 GUI with plugin architecture:
```bash
cd V1.5
python main.py
```

### 2. **Web Panel**
Modern React interface for quick operations:
- **URL**: http://batch-fnr-unifier.localhost
- **API**: http://batch-fnr-unifier-api.localhost

### 3. **Standalone Web Development**
```bash
cd web-panel
npm install
npm run dev
```

## 🔧 Features

### **Batch Find & Replace**
- Search and replace text across multiple AutoCAD drawings
- Regex pattern support
- Title block management
- Case-sensitive options
- Preview before execution

### **Text Unifier & Scaling**
- Standardize text heights and styles
- Multiple scaling modes (uniform, proportional, selective)
- Geometry operations (align, distribute, normalize)
- Layer cleanup tools

### **Plugin Architecture**
- Extensible system for custom operations
- Modular design for easy maintenance
- Configuration-driven workflows

## 🐳 Docker Integration

Part of the Hyphae Engineering ecosystem:
- **Frontend**: React panel with Tailwind CSS
- **Backend**: FastAPI wrapper for V1.5 functionality
- **Volumes**: Persistent storage for processed files
- **Networks**: Integrated with Traefik routing

## 📋 API Endpoints

- `GET /api/status` - System status
- `POST /api/find-replace/preview` - Preview find/replace
- `POST /api/find-replace/execute` - Execute find/replace
- `POST /api/text-unifier/analyze` - Analyze text objects
- `POST /api/text-unifier/execute` - Execute unification
- `POST /api/launch-desktop` - Launch desktop app

## 🔄 Development Workflow

1. **Desktop changes**: Work in `V1.5/` directory
2. **Web changes**: Work in `web-panel/` directory
3. **API changes**: Modify `api_wrapper.py`
4. **Deploy**: Use main Hyphae Engineering deployment

## 📝 Version History

- **V1**: Original batch find & replace tool
- **V1.5**: Unified application with text unifier and plugin system
- **Web Panel**: Modern web interface for integration with Hyphae ecosystem

## 🏢 License

© 2024 Root3Power LLC • Hyphae Engineering
