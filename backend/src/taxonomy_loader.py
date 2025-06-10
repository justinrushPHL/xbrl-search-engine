# backend/src/taxonomy_loader.py
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from arelle import Cntlr
from .config import US_GAAP_ENTRY_POINT

logger = logging.getLogger(__name__)

class TaxonomyLoader:
    """
    Enhanced taxonomy loader with comprehensive label matching capabilities.
    Loads US-GAAP taxonomy using Arelle and provides intelligent search functionality.
    """
    
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
        """Extract concepts from the loaded taxonomy with enhanced label extraction."""
        self.concepts = {}
        
        if not self.model_xbrl:
            return
        
        # Get all concepts from the DTS (Discoverable Taxonomy Set)
        for concept in self.model_xbrl.qnameConcepts.values():
            if concept is not None:
                try:
                    # Extract multiple label types
                    labels = self._extract_all_labels(concept)
                    
                    concept_info = {
                        'name': concept.name,
                        'qname': str(concept.qname),
                        'label': labels.get('standard', concept.name),
                        'terse_label': labels.get('terse'),
                        'verbose_label': labels.get('verbose'),
                        'total_label': labels.get('total'),
                        'documentation': self._get_concept_documentation(concept),
                        'data_type': self._get_data_type(concept),
                        'period_type': getattr(concept, 'periodType', None),
                        'balance_type': getattr(concept, 'balance', None),
                        'is_deprecated': self._is_deprecated(concept),
                        'is_abstract': getattr(concept, 'isAbstract', False),
                        'substitution_group': self._get_substitution_group(concept),
                        'all_labels': labels  # Store all extracted labels
                    }
                    
                    self.concepts[concept.name] = concept_info
                except Exception as e:
                    logger.warning(f"Error processing concept {getattr(concept, 'name', 'unknown')}: {e}")
                    continue
    
    def _extract_all_labels(self, concept) -> Dict[str, str]:
        """Extract all available label types for a concept."""
        labels = {}
        
        try:
            # Try to get standard label
            if hasattr(concept, 'genLabel'):
                try:
                    standard_label = concept.genLabel()
                    if isinstance(standard_label, str) and standard_label.strip():
                        labels['standard'] = standard_label.strip()
                except:
                    pass
            
            # Try to get labels from label linkbase
            if hasattr(concept, 'modelXbrl') and concept.modelXbrl:
                # Look for different label roles
                label_roles = [
                    'http://www.xbrl.org/2003/role/label',  # Standard
                    'http://www.xbrl.org/2003/role/terseLabel',  # Terse
                    'http://www.xbrl.org/2003/role/verboseLabel',  # Verbose
                    'http://www.xbrl.org/2003/role/totalLabel',  # Total
                    'http://www.xbrl.org/2003/role/documentation'  # Documentation
                ]
                
                for role in label_roles:
                    try:
                        label = concept.genLabel(role=role)
                        if isinstance(label, str) and label.strip():
                            role_name = role.split('/')[-1].lower()
                            if role_name.endswith('label'):
                                role_name = role_name[:-5]  # Remove 'label' suffix
                            labels[role_name] = label.strip()
                    except:
                        continue
            
            # Fallback to concept name if no labels found
            if not labels:
                labels['standard'] = concept.name
                
        except Exception as e:
            logger.debug(f"Error extracting labels for {concept.name}: {e}")
            labels['standard'] = concept.name
        
        return labels
    
    def _build_label_index(self):
        """Build an enhanced index for faster label-based searching."""
        self.concept_labels = {}
        
        for concept_name, concept_info in self.concepts.items():
            # Index by name (lowercase for case-insensitive search)
            name_key = concept_name.lower()
            if name_key not in self.concept_labels:
                self.concept_labels[name_key] = []
            self.concept_labels[name_key].append(concept_name)
            
            # Index by all available labels
            all_labels = concept_info.get('all_labels', {})
            for label_type, label in all_labels.items():
                if label and isinstance(label, str) and label != concept_name:
                    label_key = label.lower()
                    if label_key not in self.concept_labels:
                        self.concept_labels[label_key] = []
                    self.concept_labels[label_key].append(concept_name)
                    
                    # Also index individual words from labels
                    words = label.lower().split()
                    for word in words:
                        if len(word) > 2:  # Skip very short words
                            if word not in self.concept_labels:
                                self.concept_labels[word] = []
                            if concept_name not in self.concept_labels[word]:
                                self.concept_labels[word].append(concept_name)
    
    def _get_concept_documentation(self, concept) -> Optional[str]:
        """Extract documentation/definition for a concept."""
        try:
            # Try to get documentation from various sources
            if hasattr(concept, 'documentation') and concept.documentation:
                doc = concept.documentation
                if callable(doc):
                    return None  # Skip callable objects
                return str(doc)
            
            # Try to get documentation label
            if hasattr(concept, 'genLabel'):
                try:
                    doc_label = concept.genLabel(role='http://www.xbrl.org/2003/role/documentation')
                    if isinstance(doc_label, str) and doc_label.strip():
                        return doc_label.strip()
                except:
                    pass
            
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
            if 'deprecated' in name or 'obsolete' in name:
                return True
                
            # Check in documentation
            doc = self._get_concept_documentation(concept)
            if doc and ('deprecated' in doc.lower() or 'obsolete' in doc.lower()):
                return True
                
            return False
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
        Search for concepts by name or label with improved word-based matching.
        
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
        # Split query into individual words for better matching
        query_words = [word.strip() for word in query_lower.split() if word.strip()]
        
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
            
            # Get searchable text (name and all labels)
            searchable_texts = [
                concept_name.lower(),
                concept_info.get('label', '').lower(),
                concept_info.get('terse_label', '').lower(),
                concept_info.get('verbose_label', '').lower(),
                concept_info.get('total_label', '').lower(),
                concept_info.get('documentation', '').lower()
            ]
            
            # Calculate match score across all searchable texts
            match_score = self._calculate_comprehensive_match_score(query_lower, query_words, searchable_texts)
            
            if match_score > 0:
                results.append({
                    'name': concept_info['name'],
                    'label': concept_info.get('label') or concept_info['name'],
                    'documentation': concept_info.get('documentation'),
                    'data_type': concept_info.get('data_type'),
                    'period_type': concept_info.get('period_type'),
                    'balance_type': concept_info.get('balance_type'),
                    'is_deprecated': concept_info.get('is_deprecated', False),
                    'match_score': match_score
                })
                seen_concepts.add(concept_name)
        
        # Sort results by match score (highest first)
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Remove match_score from final results
        for result in results:
            del result['match_score']
        
        return results[:limit]
    
    def find_concepts_by_labels(self, query: str, include_deprecated: bool = False) -> List[Dict[str, Any]]:
        """
        Find concepts by searching across all label types (standard, terse, verbose, total).
        
        Args:
            query: Search term to find in labels
            include_deprecated: Whether to include deprecated concepts
            
        Returns:
            List of matching concepts with their XBRL tag names
        """
        if not self.is_loaded:
            raise Exception("Taxonomy not loaded. Call load_taxonomy() first.")
        
        query_lower = query.strip().lower()
        query_words = [word.strip() for word in query_lower.split() if word.strip()]
        
        matches = []
        seen_concepts = set()
        
        for concept_name, concept_info in self.concepts.items():
            if concept_name in seen_concepts:
                continue
                
            if not include_deprecated and concept_info.get('is_deprecated', False):
                continue
            
            # Check all available labels
            labels_to_check = [
                ('standard', concept_info.get('label', '')),
                ('terse', concept_info.get('terse_label', '')),
                ('verbose', concept_info.get('verbose_label', '')),
                ('total', concept_info.get('total_label', '')),
                ('documentation', concept_info.get('documentation', '')),
                ('concept_name', concept_name)
            ]
            
            best_match_score = 0
            best_label_type = 'standard'
            matching_label = ''
            
            for label_type, label in labels_to_check:
                if not label:
                    continue
                    
                label_lower = label.lower()
                match_score = self._calculate_match_score(query_lower, query_words, concept_name.lower(), label_lower)
                
                if match_score > best_match_score:
                    best_match_score = match_score
                    matching_label = label
                    best_label_type = label_type
            
            if best_match_score > 0:
                matches.append({
                    'concept_name': concept_name,
                    'xbrl_tag': f"us-gaap:{concept_name}",
                    'matching_label': matching_label,
                    'label_type': best_label_type,
                    'match_score': best_match_score,
                    'standard_label': concept_info.get('label', concept_name),
                    'data_type': concept_info.get('data_type'),
                    'period_type': concept_info.get('period_type'),
                    'balance_type': concept_info.get('balance_type'),
                    'is_deprecated': concept_info.get('is_deprecated', False)
                })
                seen_concepts.add(concept_name)
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Remove match_score from final results  
        for match in matches:
            del match['match_score']
            
        return matches
    
    def _calculate_match_score(self, query_full: str, query_words: List[str], name: str, label: str) -> float:
        """
        Calculate a match score for a concept based on query.
        Higher score = better match.
        """
        score = 0.0
        
        # Exact full query matches get highest score
        if query_full == name or query_full == label:
            return 100.0
        
        # Exact word matches in name or label
        for word in query_words:
            if word in name:
                score += 10.0
            if word in label:
                score += 8.0
        
        # Partial word matches (for words like "cash" matching "CashAndCash...")
        for word in query_words:
            # Check if the word appears as part of a larger word
            if word in name and word not in name.split():
                score += 5.0
            if word in label and word not in label.split():
                score += 4.0
        
        # Bonus for concepts that start with query words
        for word in query_words:
            if name.startswith(word):
                score += 3.0
            if label.startswith(word):
                score += 2.0
        
        # Bonus if all query words are found
        if len(query_words) > 1:
            name_words_found = sum(1 for word in query_words if word in name)
            label_words_found = sum(1 for word in query_words if word in label)
            
            if name_words_found == len(query_words):
                score += 15.0
            elif label_words_found == len(query_words):
                score += 12.0
            elif name_words_found + label_words_found >= len(query_words):
                score += 8.0
        
        return score
    
    def _calculate_comprehensive_match_score(self, query_full: str, query_words: List[str], searchable_texts: List[str]) -> float:
        """
        Calculate match score across multiple text sources.
        """
        max_score = 0.0
        
        for text in searchable_texts:
            if not text:
                continue
            score = self._calculate_match_score(query_full, query_words, text, text)
            max_score = max(max_score, score)
        
        return max_score
    
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
            'terse_label': concept_info.get('terse_label'),
            'verbose_label': concept_info.get('verbose_label'),
            'total_label': concept_info.get('total_label'),
            'documentation': concept_info.get('documentation'),
            'data_type': concept_info.get('data_type'),
            'period_type': concept_info.get('period_type'),
            'balance_type': concept_info.get('balance_type'),
            'is_deprecated': concept_info.get('is_deprecated', False),
            'is_abstract': concept_info.get('is_abstract', False),
            'substitution_group': concept_info.get('substitution_group'),
            'xbrl_tag': f"us-gaap:{concept_info['name']}"
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
        
        # Count concepts with different label types
        label_coverage = {
            'standard_labels': sum(1 for c in self.concepts.values() if c.get('label')),
            'terse_labels': sum(1 for c in self.concepts.values() if c.get('terse_label')),
            'verbose_labels': sum(1 for c in self.concepts.values() if c.get('verbose_label')),
            'total_labels': sum(1 for c in self.concepts.values() if c.get('total_label')),
            'documentation': sum(1 for c in self.concepts.values() if c.get('documentation'))
        }
        
        return {
            'loaded': True,
            'total_concepts': total_concepts,
            'deprecated_concepts': deprecated_count,
            'abstract_concepts': abstract_count,
            'active_concepts': total_concepts - deprecated_count,
            'data_types': data_types,
            'period_types': period_types,
            'label_coverage': label_coverage,
            'taxonomy_file': str(US_GAAP_ENTRY_POINT),
            'search_index_size': len(self.concept_labels)
        }

# Global instance
taxonomy_loader = TaxonomyLoader()