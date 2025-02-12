# company-intelligence-agent
 An AI-powered intelligent agent that monitors and analyzes company-related news, categorizes content into meaningful groups, and enables users to query information through a simple interface.

## Overview
The Company Intelligence Agent is an AI-powered system designed to monitor and analyze company-related news and content. It collects data from RSS feeds and web scraping, processes and categorizes it, and allows users to query the information through a simple interface.

## Features
- **Automated Content Collection**: Gathers data from configurable RSS feeds and web sources.
- **Intelligent Categorization**: Uses an LLM to classify content into meaningful categories.
- **Search & Query Support**: Enables users to query collected data via a user-friendly interface.

## Project Structure
```
company-intelligence-agent/
│── src/                     # Main source code
│   │── backend/             # Backend (FastAPI, data pipeline, LLM integration)
│   │── frontend/            # Frontend (React)
│   │── orchestrator/        # Manages content ingestion and updates
│   │── utils/               # Helper functions, utilities
│
│── configs/                 # Config files (e.g., env variables, settings)
│── tests/                   # Unit and integration tests
│── docs/                    # Documentation (API specs, setup guide)
│── .gitignore               # Ignore unnecessary files
│── README.md                # Project overview and instructions
│── requirements.txt         # Python dependencies
│── LICENSE                  # License file
```

## Setup Instructions
### Prerequisites
- Python 3.10+
- React (for frontend development)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/p-breslin/company-intelligence-agent.git
   cd company-intelligence-agent
   ```
2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. TO-DO


## Usage
- The system will collect and process data automatically.
- Use the web interface to browse content and run queries.
- Adjust settings via the configuration panel.


## License
TO-DO
