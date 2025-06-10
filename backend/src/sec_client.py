# backend/src/sec_client.py
import requests
import time
import logging
from typing import Optional, Tuple, Dict, List
from .config import SEC_USER_AGENT, SEC_BASE_URL, SEC_ARCHIVES_URL, SEC_API_DELAY

logger = logging.getLogger(__name__)

class SECClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": SEC_USER_AGENT})
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Ensure we don't exceed SEC rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < SEC_API_DELAY:
            time.sleep(SEC_API_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def get_cik_by_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK for a stock ticker"""
        try:
            self._rate_limit()
            
            response = self.session.get(f"{SEC_BASE_URL}/files/company_tickers.json")
            response.raise_for_status()
            data = response.json()
            
            for entry in data.values():
                if entry["ticker"].upper() == ticker.upper():
                    return str(entry["cik_str"]).zfill(10)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting CIK for {ticker}: {e}")
            return None
    
    def get_latest_filing(self, cik: str, form_type: str = "10-K") -> Optional[Tuple[str, str]]:
        """Get latest filing for a CIK"""
        try:
            self._rate_limit()
            
            response = self.session.get(f"{SEC_BASE_URL}/submissions/CIK{cik}.json")
            response.raise_for_status()
            data = response.json()
            
            recent_filings = data["filings"]["recent"]
            forms = recent_filings["form"]
            accession_numbers = recent_filings["accessionNumber"]
            primary_documents = recent_filings["primaryDocument"]
            
            for i, form in enumerate(forms):
                if form == form_type:
                    accession = accession_numbers[i].replace("-", "")
                    document = primary_documents[i]
                    return accession, document
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest filing for CIK {cik}: {e}")
            return None
    
    def search_company_filings(self, company_name: str, form_type: str = "10-K", limit: int = 5) -> List[Dict]:
        """Search for company filings (placeholder implementation)"""
        # This is a simplified implementation
        # In a real app, you'd implement proper company search
        try:
            # For now, try to get CIK if company_name looks like a ticker
            if len(company_name) <= 5 and company_name.isalpha():
                cik = self.get_cik_by_ticker(company_name)
                if cik:
                    filing_info = self.get_latest_filing(cik, form_type)
                    if filing_info:
                        return [{
                            'cik': cik,
                            'company_name': company_name.upper(),
                            'form_type': form_type,
                            'filing_date': 'Unknown',
                            'accession_number': filing_info[0],
                            'primary_document': filing_info[1]
                        }]
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching company filings: {e}")
            return []
    
    def get_filing_data(self, cik: str, accession_number: str) -> Optional[Dict]:
        """Get filing data (placeholder implementation)"""
        # This would parse XBRL data from the filing
        # For now, return a placeholder structure
        return {
            'cik': cik,
            'accession_number': accession_number,
            'company_name': 'Unknown',
            'filing_date': 'Unknown',
            'form_type': 'Unknown',
            'facts': {},  # Would contain XBRL facts
            'roles': {}   # Would contain role information
        }
    
    def get_filing_url(self, cik: str, accession: str, document: str) -> str:
        """Construct filing URL"""
        cik_no_leading_zeros = cik.lstrip('0')
        return f"{SEC_ARCHIVES_URL}/{cik_no_leading_zeros}/{accession}/{document}"

# Global instance
sec_client = SECClient()