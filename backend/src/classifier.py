"""
Financial Statement Classifier for XBRL documents.
Classifies financial statements based on their primary statement type.
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class StatementInfo:
    """Information about a financial statement."""
    statement_type: str
    confidence: float
    primary_concepts: List[str]
    role_uri: Optional[str] = None


class FinancialStatementClassifier:
    """
    Classifies financial statements from XBRL data based on the concepts present.
    """
    
    def __init__(self):
        """Initialize the classifier with statement patterns."""
        self.statement_patterns = {
            'balance_sheet': {
                'required_concepts': [
                    'Assets', 'AssetsCurrent', 'Liabilities', 'LiabilitiesCurrent',
                    'StockholdersEquity', 'LiabilitiesAndStockholdersEquity'
                ],
                'identifying_concepts': [
                    'Cash', 'CashAndCashEquivalents', 'AccountsReceivable',
                    'Inventory', 'AccountsPayable', 'RetainedEarnings'
                ],
                'keywords': ['balance', 'sheet', 'position', 'financial position']
            },
            'income_statement': {
                'required_concepts': [
                    'Revenues', 'Revenue', 'NetIncomeLoss', 'OperatingIncomeLoss',
                    'CostOfRevenue', 'CostOfGoodsAndServicesSold'
                ],
                'identifying_concepts': [
                    'SalesRevenueNet', 'GrossProfit', 'OperatingExpenses',
                    'InterestExpense', 'IncomeTaxExpense', 'EarningsPerShare'
                ],
                'keywords': ['income', 'operations', 'earnings', 'profit', 'loss']
            },
            'cash_flow': {
                'required_concepts': [
                    'NetCashProvidedByUsedInOperatingActivities',
                    'NetCashProvidedByUsedInInvestingActivities',
                    'NetCashProvidedByUsedInFinancingActivities',
                    'CashAndCashEquivalentsPeriodIncreaseDecrease'
                ],
                'identifying_concepts': [
                    'DepreciationDepletionAndAmortization',
                    'CapitalExpenditures', 'DividendsPaid',
                    'ProceedsFromIssuanceOfDebt'
                ],
                'keywords': ['cash', 'flow', 'flows']
            },
            'equity_statement': {
                'required_concepts': [
                    'StockholdersEquity', 'RetainedEarnings',
                    'CommonStockSharesOutstanding', 'AdditionalPaidInCapital'
                ],
                'identifying_concepts': [
                    'CommonStockDividendsPerShareDeclared',
                    'StockIssuedDuringPeriodValue',
                    'StockRepurchasedDuringPeriodValue'
                ],
                'keywords': ['equity', 'stockholders', 'shareholders', 'changes']
            }
        }
    
    def classify_statements(self, facts: Dict, roles: Optional[Dict] = None) -> Dict[str, StatementInfo]:
        """
        Classify financial statements from XBRL facts.
        
        Args:
            facts: Dictionary of XBRL facts by concept name
            roles: Optional dictionary of role information
            
        Returns:
            Dictionary mapping statement types to StatementInfo objects
        """
        results = {}
        concept_names = set(facts.keys())
        
        for stmt_type, patterns in self.statement_patterns.items():
            confidence = self._calculate_confidence(concept_names, patterns)
            
            if confidence > 0.3:  # Minimum threshold
                primary_concepts = self._find_primary_concepts(concept_names, patterns)
                role_uri = self._find_matching_role(stmt_type, roles) if roles else None
                
                results[stmt_type] = StatementInfo(
                    statement_type=stmt_type,
                    confidence=confidence,
                    primary_concepts=primary_concepts,
                    role_uri=role_uri
                )
        
        return results
    
    def _calculate_confidence(self, concept_names: set, patterns: Dict) -> float:
        """Calculate confidence score for a statement type."""
        required_matches = sum(
            1 for concept in patterns['required_concepts']
            if any(concept.lower() in name.lower() for name in concept_names)
        )
        
        identifying_matches = sum(
            1 for concept in patterns['identifying_concepts']
            if any(concept.lower() in name.lower() for name in concept_names)
        )
        
        # Weight required concepts more heavily
        required_weight = 0.7
        identifying_weight = 0.3
        
        required_score = (required_matches / len(patterns['required_concepts'])) * required_weight
        identifying_score = (identifying_matches / len(patterns['identifying_concepts'])) * identifying_weight
        
        return min(required_score + identifying_score, 1.0)
    
    def _find_primary_concepts(self, concept_names: set, patterns: Dict) -> List[str]:
        """Find primary concepts present for this statement type."""
        primary_concepts = []
        
        for concept in patterns['required_concepts'] + patterns['identifying_concepts']:
            matching_names = [
                name for name in concept_names
                if concept.lower() in name.lower()
            ]
            primary_concepts.extend(matching_names[:3])  # Limit to top 3 matches
        
        return list(set(primary_concepts))  # Remove duplicates
    
    def _find_matching_role(self, stmt_type: str, roles: Dict) -> Optional[str]:
        """Find the role URI that best matches the statement type."""
        if not roles:
            return None
        
        keywords = self.statement_patterns[stmt_type]['keywords']
        
        for role_uri, role_info in roles.items():
            role_definition = role_info.get('definition', '').lower()
            
            if any(keyword in role_definition for keyword in keywords):
                return role_uri
        
        return None
    
    def get_statement_summary(self, classification_results: Dict[str, StatementInfo]) -> str:
        """Generate a human-readable summary of classified statements."""
        if not classification_results:
            return "No financial statements could be classified."
        
        summary_parts = []
        for stmt_type, info in sorted(classification_results.items(), 
                                    key=lambda x: x[1].confidence, reverse=True):
            
            stmt_name = stmt_type.replace('_', ' ').title()
            confidence_pct = int(info.confidence * 100)
            concept_count = len(info.primary_concepts)
            
            summary_parts.append(
                f"• {stmt_name}: {confidence_pct}% confidence ({concept_count} key concepts)"
            )
        
        return "Identified Financial Statements:\n" + "\n".join(summary_parts)


def classify_xbrl_statements(facts: Dict, roles: Optional[Dict] = None) -> Dict[str, StatementInfo]:
    """
    Convenience function to classify XBRL statements.
    
    Args:
        facts: Dictionary of XBRL facts
        roles: Optional role information
        
    Returns:
        Classification results
    """
    classifier = FinancialStatementClassifier()
    return classifier.classify_statements(facts, roles)