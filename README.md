# XBRL Search Engine

A powerful financial concept search engine built with FastAPI and Arelle, providing intelligent search capabilities across the US-GAAP XBRL taxonomy.

![XBRL Search Demo](https://img.shields.io/badge/Concepts-20%2C970-brightgreen) ![Python](https://img.shields.io/badge/python-3.9+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg) ![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🚀 Features

- **🔍 Intelligent Search**: Search through 20,970+ US-GAAP financial concepts
- **📊 Rich Metadata**: Get detailed information including data types, period types, and balance types
- **🎯 Quick Access**: Pre-defined quick searches for common financial terms
- **📱 Responsive UI**: Modern, mobile-friendly interface
- **🔧 RESTful API**: Well-documented API endpoints with OpenAPI/Swagger
- **⚡ Fast Performance**: Optimized search with indexed concept labels
- **🎨 Professional Interface**: Clean, intuitive design with color-coded results

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **XBRL Processing**: Arelle
- **Frontend**: HTML5, CSS3, JavaScript
- **Data**: US-GAAP 2025 Taxonomy
- **API Documentation**: OpenAPI/Swagger

## 📋 Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/xbrl-search-engine.git
cd xbrl-search-engine
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install fastapi "uvicorn[standard]"
pip install requests python-multipart python-dotenv
pip install git+https://github.com/Arelle/Arelle.git
```

### 4. Download US-GAAP Taxonomy

1. Visit [FASB US-GAAP](https://www.fasb.org/us-gaap)
2. Download the latest taxonomy ZIP file
3. Extract to `taxonomies/us-gaap-2025/` directory
4. Ensure the entry point file exists at: `taxonomies/us-gaap-2025/entire/us-gaap-entryPoint-all-2025.xsd`

### 5. Run the Application

```bash
python -m uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the Application

- **Web Interface**: http://localhost:8000/static/index.html
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Concept Search
```http
POST /search/concepts
Content-Type: application/json

{
  "query": "revenue",
  "limit": 10,
  "include_deprecated": false
}
```

### Get Concept Details
```http
GET /concepts/{concept_name}
```

### Taxonomy Statistics
```http
GET /taxonomy/stats
```

### Health Check
```http
GET /health
```

## 🔍 Usage Examples

### Search for Revenue Concepts
```bash
curl -X POST "http://localhost:8000/search/concepts" \
  -H "Content-Type: application/json" \
  -d '{"query": "revenue", "limit": 5, "include_deprecated": false}'
```

### Get Taxonomy Statistics
```bash
curl http://localhost:8000/taxonomy/stats
```

## 📁 Project Structure

```
xbrl-search-engine/
├── backend/
│   └── src/
│       ├── main.py                 # FastAPI application
│       ├── taxonomy_loader.py      # XBRL taxonomy processing
│       ├── sec_client.py          # SEC EDGAR API client
│       ├── classifier.py          # Financial statement classifier
│       └── config.py              # Configuration settings
├── frontend/
│   └── index.html                 # Web interface
├── taxonomies/
│   └── us-gaap-2025/             # US-GAAP taxonomy files
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

## 🎯 Search Features

### Quick Searches
The interface provides quick access buttons for common financial concepts:
- Revenue
- Assets
- Cash
- Income
- Equity
- Debt
- Expense
- Inventory

### Advanced Filtering
- **Result Limits**: 5, 10, 20, or 50 results
- **Deprecated Concepts**: Include/exclude deprecated items
- **Intelligent Ranking**: Results ranked by relevance

### Concept Metadata
Each search result includes:
- **Concept Name**: Official XBRL identifier
- **Human Label**: Readable description
- **Data Type**: Monetary, string, decimal, etc.
- **Period Type**: Instant or duration
- **Balance Type**: Debit or credit
- **Deprecation Status**: Active or deprecated

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Arelle](https://arelle.org/) - XBRL processing library
- [FASB](https://www.fasb.org/) - US-GAAP taxonomy provider
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SEC EDGAR](https://www.sec.gov/edgar) - Financial filing database

## 📞 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/YOUR-USERNAME/xbrl-search-engine/issues) on GitHub.

## 🔮 Future Enhancements

- [ ] Enhanced SEC filing integration
- [ ] Financial statement classification
- [ ] Company-specific XBRL analysis
- [ ] Export functionality (CSV, JSON)
- [ ] Advanced concept relationships
- [ ] Multi-year taxonomy support
- [ ] Real-time filing notifications

---

**Built with ❤️ for the financial technology community**