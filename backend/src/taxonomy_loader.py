# backend/src/taxonomy_loader.py
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from arelle import Cntlr
from .config import US_GAAP_ENTRY_POINT

logger = logging.getLogger(__name__)

class TaxonomyLoader:
    def __init__(self):
        self.controller = None
        self.model_xbrl = None
        self.concepts = {}
        self.concept_labels = {}
        self.is_loaded = False
    
    def load_taxonomy(self):
        """Load the US-GAAP taxonomy using Arelle."""
        if self.is_loaded:
            logger.info("Taxonomy already loaded")
            return
        
        try:
            logger.info("Loading US-GAAP taxonomy...")
            
            # Initialize Arelle controller
            self.controller = Cntlr.Cntlr()
            
            # Load the taxonomy
            self.model_xbrl = self.controller.modelManager.load(str(US_GAAP_ENTRY_POINT))
            
            if self.model_xbrl is None:
                raise Exception("Failed to load taxonomy")
            
            # Extract concepts and build search index
            self._extract_concepts()
            self._build_label_index()
            
            self.is_loaded = True
            logger.info(f"Loaded {len(self.concepts)} concepts")
            logger.info(f"Built index with {len(self.concept_labels)} labels")
            
        except Exception as e:
            logger.error(f"Failed to load taxonomy: {e}")
            raise
    
    def _extract_concepts(self):
        """Extract concepts from the loaded taxonomy."""
        self.concepts = {}
        
        if not self.model_xbrl:
            return
        
        # Get all concepts from the DTS (Discoverable Taxonomy Set)
        for concept in self.model_xbrl.qnameConcepts.values():
            if concept is not None:
                try:
                    # Safely get the label
                    label = concept.name  # Default to name
                    if hasattr(concept, 'genLabel'):
                        try:
                            gen_label = concept.genLabel()
                            if isinstance(gen_label, str) and gen_label.strip():
                                label = gen_label
                        except:
                            pass
                    
                    concept_info = {
                        'name': concept.name,
                        'qname': str(concept.qname),
                        'label': label,
                        'documentation': self._get_concept_documentation(concept),
                        'data_type': self._get_data_type(concept),
                        'period_type': getattr(concept, 'periodType', None),
                        'balance_type': getattr(concept, 'balance', None),
                        'is_deprecated': self._is_deprecated(concept),
                        'is_abstract': getattr(concept, 'isAbstract', False),
                        'substitution_group': self._get_substitution_group(concept)
                    }
                    
                    self.concepts[concept.name] = concept_info
                except Exception as e:
                    logger.warning(f"Error processing concept {getattr(concept, 'name', 'unknown')}: {e}")
                    continue
    
    def _build_label_index(self):
        """Build an index for faster label-based searching."""
        self.concept_labels = {}
        
        for concept_name, concept_info in self.concepts.items():
            # Index by name (lowercase for case-insensitive search)
            name_key = concept_name.lower()
            if name_key not in self.concept_labels:
                self.concept_labels[name_key] = []
            self.concept_labels[name_key].append(concept_name)
            
            # Index by label if available
            label = concept_info.get('label', '')
            if label and isinstance(label, str) and label != concept_name:
                label_key = label.lower()
                if label_key not in self.concept_labels:
                    self.concept_labels[label_key] = []
                self.concept_labels[label_key].append(concept_name)
    
    def _get_concept_documentation(self, concept) -> Optional[str]:
        """Extract documentation/definition for a concept."""
        try:
            # Try to get documentation from various sources
            if hasattr(concept, 'documentation') and concept.documentation:
                doc = concept.documentation
                if callable(doc):
                    return None  # Skip callable objects
                return str(doc)
            
            if hasattr(concept, 'genLabel') and concept.genLabel:
                label = concept.genLabel()
                if isinstance(label, str):
                    return label
            
            return None
        except Exception:
            return None
    
    def _get_data_type(self, concept) -> Optional[str]:
        """Get the data type of a concept."""
        try:
            if hasattr(concept, 'typeQname') and concept.typeQname:
                return str(concept.typeQname)
            return None
        except:
            return None
    
    def _is_deprecated(self, concept) -> bool:
        """Check if a concept is deprecated."""
        try:
            # Check for deprecation indicators
            if hasattr(concept, 'isDeprecated'):
                return concept.isDeprecated
            
            # Check labels for deprecation indicators
            name = concept.name.lower()
            return 'deprecated' in name or 'obsolete' in name
        except:
            return False
    
    def _get_substitution_group(self, concept) -> Optional[str]:
        """Get the substitution group of a concept."""
        try:
            if hasattr(concept, 'substitutionGroupQname') and concept.substitutionGroupQname:
                return str(concept.substitutionGroupQname)
            return None
        except:
            return None
    
    def search_concepts(self, query: str, limit: int = 10, include_deprecated: bool = False) -> List[Dict[str, Any]]:
        """
        Search for concepts by name or label.
        
        Args:
            query: Search term
            limit: Maximum number of results to return
            include_deprecated: Whether to include deprecated concepts
            
        Returns:
            List of matching concepts
        """
        if not self.is_loaded:
            raise Exception("Taxonomy not loaded. Call load_taxonomy() first.")
        
        if not query or not query.strip():
            return []
        
        query_lower = query.strip().lower()
        results = []
        seen_concepts = set()
        
        # Search through all concepts
        for concept_name, concept_info in self.concepts.items():
            if len(results) >= limit:
                break
            
            if concept_name in seen_concepts:
                continue
            
            # Skip deprecated concepts if not requested
            if not include_deprecated and concept_info.get('is_deprecated', False):
                continue
            
            # Check if query matches concept name or label
            name_match = query_lower in concept_name.lower()
            label_match = query_lower in (concept_info.get('label', '') or '').lower()
            
            if name_match or label_match:
                results.append({
                    'name': concept_info['name'],
                    'label': concept_info.get('label') or concept_info['name'],
                    'documentation': concept_info.get('documentation'),
                    'data_type': concept_info.get('data_type'),
                    'period_type': concept_info.get('period_type'),
                    'balance_type': concept_info.get('balance_type'),
                    'is_deprecated': concept_info.get('is_deprecated', False)
                })
                seen_concepts.add(concept_name)
        
        # Sort results by relevance (exact matches first, then partial matches)
        def sort_key(concept):
            name = concept['name'].lower()
            label = (concept['label'] or '').lower()
            
            # Exact matches get highest priority
            if name == query_lower or label == query_lower:
                return 0
            # Starts with query gets second priority
            elif name.startswith(query_lower) or label.startswith(query_lower):
                return 1
            # Contains query gets lowest priority
            else:
                return 2
        
        results.sort(key=sort_key)
        return results[:limit]
    
    def get_concept_details(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific concept.
        
        Args:
            concept_name: Name of the concept
            
        Returns:
            Detailed concept information or None if not found
        """
        if not self.is_loaded:
            raise Exception("Taxonomy not loaded. Call load_taxonomy() first.")
        
        concept_info = self.concepts.get(concept_name)
        if not concept_info:
            return None
        
        return {
            'name': concept_info['name'],
            'qname': concept_info.get('qname'),
            'label': concept_info.get('label'),
            'documentation': concept_info.get('documentation'),
            'data_type': concept_info.get('data_type'),
            'period_type': concept_info.get('period_type'),
            'balance_type': concept_info.get('balance_type'),
            'is_deprecated': concept_info.get('is_deprecated', False),
            'is_abstract': concept_info.get('is_abstract', False),
            'substitution_group': concept_info.get('substitution_group')
        }
    
    def get_taxonomy_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded taxonomy.
        
        Returns:
            Dictionary with taxonomy statistics
        """
        if not self.is_loaded:
            return {
                'loaded': False,
                'error': 'Taxonomy not loaded'
            }
        
        total_concepts = len(self.concepts)
        deprecated_count = sum(1 for c in self.concepts.values() if c.get('is_deprecated', False))
        abstract_count = sum(1 for c in self.concepts.values() if c.get('is_abstract', False))
        
        # Count by data type
        data_types = {}
        for concept in self.concepts.values():
            data_type = concept.get('data_type', 'Unknown')
            data_types[data_type] = data_types.get(data_type, 0) + 1
        
        # Count by period type
        period_types = {}
        for concept in self.concepts.values():
            period_type = concept.get('period_type', 'Unknown')
            period_types[period_type] = period_types.get(period_type, 0) + 1
        
        return {
            'loaded': True,
            'total_concepts': total_concepts,
            'deprecated_concepts': deprecated_count,
            'abstract_concepts': abstract_count,
            'active_concepts': total_concepts - deprecated_count,
            'data_types': data_types,
            'period_types': period_types,
            'taxonomy_file': str(US_GAAP_ENTRY_POINT)
        }

# Global instance
taxonomy_loader = TaxonomyLoader()