"""
Main FastAPI application for XBRL Search.
Provides endpoints for searching and analyzing XBRL documents.
"""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime

# from .config import settings  # Temporarily commented out
from .taxonomy_loader import TaxonomyLoader
from .sec_client import SECClient
from .classifier import FinancialStatementClassifier, StatementInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="XBRL Search API",
    description="Search and analyze XBRL financial documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Global instances
taxonomy_loader = None
sec_client = None
classifier = None


# Pydantic models for API
class SearchQuery(BaseModel):
    """Model for concept search queries."""
    query: str = Field(..., description="Search term or concept name")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    include_deprecated: bool = Field(default=False, description="Include deprecated concepts")


class CompanySearchQuery(BaseModel):
    """Model for company search queries."""
    company_name: str = Field(..., description="Company name or ticker symbol")
    filing_type: str = Field(default="10-K", description="SEC filing type")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum filings to return")


class ConceptInfo(BaseModel):
    """Model for concept information."""
    name: str
    label: str
    documentation: Optional[str] = None
    data_type: Optional[str] = None
    period_type: Optional[str] = None
    balance_type: Optional[str] = None
    is_deprecated: bool = False


class FilingInfo(BaseModel):
    """Model for SEC filing information."""
    cik: str
    company_name: str
    form_type: str
    filing_date: str
    accession_number: str
    primary_document: str


class StatementInfoResponse(BaseModel):
    """Model for statement classification response."""
    statement_type: str
    confidence: float
    primary_concepts: List[str]
    role_uri: Optional[str] = None


# Dependency to ensure services are initialized
async def get_taxonomy_loader():
    """Get taxonomy loader instance."""
    global taxonomy_loader
    if taxonomy_loader is None:
        taxonomy_loader = TaxonomyLoader()
        await asyncio.to_thread(taxonomy_loader.load_taxonomy)
    return taxonomy_loader


async def get_sec_client():
    """Get SEC client instance."""
    global sec_client
    if sec_client is None:
        sec_client = SECClient()
    return sec_client


async def get_classifier():
    """Get classifier instance."""
    global classifier
    if classifier is None:
        classifier = FinancialStatementClassifier()
    return classifier


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting XBRL Search API...")
    try:
        # Initialize taxonomy loader
        await get_taxonomy_loader()
        logger.info("Taxonomy loaded successfully")
        
        # Initialize other services
        await get_sec_client()
        await get_classifier()
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "XBRL Search API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global taxonomy_loader, sec_client, classifier
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "taxonomy_loader": taxonomy_loader is not None,
            "sec_client": sec_client is not None,
            "classifier": classifier is not None
        }
    }
    
    if not all(health_status["services"].values()):
        health_status["status"] = "degraded"
    
    return health_status


@app.post("/search/concepts", response_model=List[ConceptInfo])
async def search_concepts(
    query: SearchQuery,
    loader: TaxonomyLoader = Depends(get_taxonomy_loader)
):
    """
    Search for XBRL concepts in the taxonomy.
    
    Returns matching concepts with their metadata.
    """
    try:
        results = await asyncio.to_thread(
            loader.search_concepts,
            query.query,
            limit=query.limit,
            include_deprecated=query.include_deprecated
        )
        
        # Convert results to ConceptInfo models
        concept_infos = []
        for concept in results:
            concept_info = ConceptInfo(
                name=concept.get('name', ''),
                label=concept.get('label', ''),
                documentation=concept.get('documentation'),
                data_type=concept.get('data_type'),
                period_type=concept.get('period_type'),
                balance_type=concept.get('balance_type'),
                is_deprecated=concept.get('is_deprecated', False)
            )
            concept_infos.append(concept_info)
        
        return concept_infos
        
    except Exception as e:
        logger.error(f"Error searching concepts: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/search/companies", response_model=List[FilingInfo])
async def search_companies(
    query: CompanySearchQuery,
    client: SECClient = Depends(get_sec_client)
):
    """
    Search for company filings from SEC EDGAR database.
    
    Returns recent filings for the specified company.
    """
    try:
        filings = await asyncio.to_thread(
            client.search_company_filings,
            query.company_name,
            form_type=query.filing_type,
            limit=query.limit
        )
        
        # Convert to FilingInfo models
        filing_infos = []
        for filing in filings:
            filing_info = FilingInfo(
                cik=filing.get('cik', ''),
                company_name=filing.get('company_name', ''),
                form_type=filing.get('form_type', ''),
                filing_date=filing.get('filing_date', ''),
                accession_number=filing.get('accession_number', ''),
                primary_document=filing.get('primary_document', '')
            )
            filing_infos.append(filing_info)
        
        return filing_infos
        
    except Exception as e:
        logger.error(f"Error searching companies: {e}")
        raise HTTPException(status_code=500, detail=f"Company search failed: {str(e)}")


@app.get("/filing/{cik}/{accession_number}/analyze")
async def analyze_filing(
    cik: str,
    accession_number: str,
    client: SECClient = Depends(get_sec_client),
    classifier_service: FinancialStatementClassifier = Depends(get_classifier)
):
    """
    Analyze a specific SEC filing and classify its financial statements.
    
    Returns detailed analysis including statement classification and key concepts.
    """
    try:
        # Get filing data
        filing_data = await asyncio.to_thread(
            client.get_filing_data,
            cik,
            accession_number
        )
        
        if not filing_data:
            raise HTTPException(status_code=404, detail="Filing not found")
        
        # Extract facts and roles
        facts = filing_data.get('facts', {})
        roles = filing_data.get('roles', {})
        
        # Classify statements
        classification_results = await asyncio.to_thread(
            classifier_service.classify_statements,
            facts,
            roles
        )
        
        # Convert to response models
        statements = {}
        for stmt_type, info in classification_results.items():
            statements[stmt_type] = StatementInfoResponse(
                statement_type=info.statement_type,
                confidence=info.confidence,
                primary_concepts=info.primary_concepts,
                role_uri=info.role_uri
            )
        
        # Generate summary
        summary = classifier_service.get_statement_summary(classification_results)
        
        return {
            "cik": cik,
            "accession_number": accession_number,
            "company_name": filing_data.get('company_name'),
            "filing_date": filing_data.get('filing_date'),
            "form_type": filing_data.get('form_type'),
            "statements": statements,
            "summary": summary,
            "total_concepts": len(facts),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing filing: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/concepts/{concept_name}")
async def get_concept_details(
    concept_name: str,
    loader: TaxonomyLoader = Depends(get_taxonomy_loader)
):
    """
    Get detailed information about a specific concept.
    
    Returns comprehensive concept metadata and relationships.
    """
    try:
        concept_details = await asyncio.to_thread(
            loader.get_concept_details,
            concept_name
        )
        
        if not concept_details:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        return concept_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting concept details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get concept details: {str(e)}")


@app.get("/taxonomy/stats")
async def get_taxonomy_stats(
    loader: TaxonomyLoader = Depends(get_taxonomy_loader)
):
    """
    Get statistics about the loaded taxonomy.
    
    Returns counts and metadata about available concepts.
    """
    try:
        stats = await asyncio.to_thread(loader.get_taxonomy_statistics)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting taxonomy stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get taxonomy statistics: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )