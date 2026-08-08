# Argus OSINT Tool

Argus is a comprehensive Open Source Intelligence (OSINT) gathering platform that combines multiple data sources to identify relationships between entities like people, emails, addresses, websites, and businesses.

## Features

- **Multi-source Intelligence Gathering**: Integrates data from LinkedIn, public records, WHOIS/RDAP, DNS, GitHub, PGP keyservers, and more
- **Relationship Mapping**: Automatically identifies and visualizes connections between entities using graph analysis
- **Multiple Interfaces**: 
  - CLI tool for terminal-based operations
  - Web API for integration with other tools
  - Desktop GUI with interactive graph visualization
- **Cross-platform**: Built with Python, Rust, and Vue.js/Tauri for maximum performance and compatibility

## Architecture

- **Python Core**: FastAPI backend, database management, and search orchestration
- **Rust Components**: High-performance network scanning and data extraction via PyO3 bindings
- **Vue.js Frontend**: Interactive web interface with Cytoscape.js graph visualization
- **Tauri Desktop**: Native desktop application wrapping the web interface

## Setup Instructions

### Prerequisites

- Python 3.10+
- Rust (latest stable)
- Node.js 18+
- SQLite3 (included with Python)

### Python Setup

1. Install Python dependencies:
```bash
cd src_python
pip install -r ../../pyproject.toml
```

Or use pip directly:
```bash
pip install fastapi uvicorn typer httpx beautifulsoup4 pydantic networkx dnspython rich
```

### Rust Setup

1. Install Rust if not already installed:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

2. Build the Rust components:
```bash
cd src_rust
cargo build --release
```

### Vue/Tauri Setup

1. Install Node.js dependencies:
```bash
cd src_ui
npm install
```

2. For development:
```bash
npm run dev
```

3. For production build:
```bash
npm run build
```

## Database Initialization

The SQLite database is automatically initialized on first run. The database file will be created at:
```
src_python/data/osint.db
```

The database includes tables for:
- `entities`: Stores discovered entities (names, emails, addresses, etc.)
- `relationships`: Stores connections between entities
- `profiles`: Stores user-created investigation profiles
- `profile_links`: Links entities to investigation profiles

## Usage Modes

### CLI Mode

Run the command-line interface:
```bash
cd src_python
python -m interfaces.cli --help
```

Available commands:
- `search`: Search for OSINT information on a target
- `show-graph`: Generate and display the relationship graph
- `create-profile`: Create a profile and link entities
- `list-profiles`: List all existing profiles
- `show-profile`: Show details of a specific profile

Example:
```bash
python -m interfaces.cli search name "John Doe"
python -m interfaces.cli show-graph
```

### Web API Mode

Start the FastAPI server:
```bash
cd src_python
python backend.py
```

The API will be available at `http://localhost:8000`

API endpoints:
- `POST /api/search`: Perform OSINT search
- `GET /api/graph`: Get graph data for visualization
- `POST /api/profiles`: Create a new profile
- `GET /api/profiles`: List all profiles
- `GET /api/profiles/{id}`: Get specific profile details
- `POST /api/profiles/{id}/entities`: Link entity to profile

### Desktop GUI Mode

Start the Tauri desktop application:
```bash
cd src_ui
npm run tauri dev
```

The desktop app includes:
- Interactive search interface
- Real-time graph visualization with Cytoscape.js
- Profile management panel
- Entity linking and annotation tools

## Development

### Running in Development Mode

1. Start the Python backend:
```bash
cd src_python
python backend.py
```

2. Start the Vue development server:
```bash
cd src_ui
npm run dev
```

3. Access the web interface at `http://localhost:5173`

### Building for Production

1. Build Rust components:
```bash
cd src_rust
cargo build --release
```

2. Build Vue frontend:
```bash
cd src_ui
npm run build
```

3. Build Tauri desktop app:
```bash
cd src_ui
npm run tauri build
```

## Project Structure

```
argus/
├── src_python/           # Python backend
│   ├── core/            # Core functionality
│   │   ├── database.py  # SQLite database operations
│   │   ├── orchestrator.py # Search orchestration
│   │   ├── graphing.py  # Graph generation
│   │   └── modules/     # Search modules (email, name, etc.)
│   ├── interfaces/      # API and CLI interfaces
│   │   ├── api.py       # FastAPI endpoints
│   │   └── cli.py       # Typer CLI commands
│   ├── data/            # SQLite database location
│   └── backend.py       # Backend server entry point
├── src_rust/            # Rust components
│   ├── src/
│   │   ├── main.rs      # Network scanning binary
│   │   └── lib.rs       # PyO3 bindings
│   └── Cargo.toml       # Rust dependencies
├── src_ui/              # Vue/Tauri frontend
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── App.vue      # Main application
│   │   ├── api.ts       # API client
│   │   └── main.ts      # Entry point
│   ├── src-tauri/       # Tauri configuration
│   └── package.json     # Node dependencies
└── pyproject.toml       # Python dependencies
```

## License

This project is provided as-is for educational and research purposes. Users are responsible for ensuring compliance with applicable laws and regulations when using OSINT tools.

## Contributing

Contributions are welcome! Please ensure all code follows the existing patterns and includes appropriate error handling and documentation.
