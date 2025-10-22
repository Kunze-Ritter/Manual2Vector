"""
Configuration Validator - Validates product configurations
Checks for conflicts, missing requirements, and suggests alternatives
"""
import logging
from typing import List, Dict, Optional, Set
from uuid import UUID
from dataclasses import dataclass
from supabase import Client


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'recommendations': self.recommendations
        }


class ConfigurationValidator:
    """Validates product configurations against option dependencies"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.logger = logging.getLogger(__name__)
    
    def validate_configuration(
        self,
        product_id: UUID,
        accessory_ids: List[UUID]
    ) -> ValidationResult:
        """
        Validate a product configuration
        
        Args:
            product_id: Base product UUID
            accessory_ids: List of accessory/option UUIDs to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        errors = []
        warnings = []
        recommendations = []
        
        try:
            # Get all dependencies for the accessories
            dependencies = self._get_dependencies(accessory_ids)
            
            # Check 'requires' dependencies
            required_errors = self._check_required_dependencies(
                accessory_ids, dependencies
            )
            errors.extend(required_errors)
            
            # Check 'excludes' dependencies (conflicts)
            conflict_errors = self._check_conflicts(
                accessory_ids, dependencies
            )
            errors.extend(conflict_errors)
            
            # Check 'alternative' dependencies (warnings)
            alternative_warnings = self._check_alternatives(
                accessory_ids, dependencies
            )
            warnings.extend(alternative_warnings)
            
            # Get recommendations
            recommendations = self._get_recommendations(
                product_id, accessory_ids, dependencies
            )
            
            # Configuration is valid if no errors
            valid = len(errors) == 0
            
            return ValidationResult(
                valid=valid,
                errors=errors,
                warnings=warnings,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
            return ValidationResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                recommendations=[]
            )
    
    def _get_dependencies(self, accessory_ids: List[UUID]) -> List[Dict]:
        """Get all dependencies for given accessories"""
        try:
            if not accessory_ids:
                return []
            
            # Convert UUIDs to strings
            accessory_id_strs = [str(aid) for aid in accessory_ids]
            
            # Query dependencies
            response = self.supabase.schema('krai_core').table('option_dependencies').select(
                'id, option_id, depends_on_option_id, dependency_type, notes'
            ).in_('option_id', accessory_id_strs).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting dependencies: {e}")
            return []
    
    def _check_required_dependencies(
        self,
        accessory_ids: List[UUID],
        dependencies: List[Dict]
    ) -> List[str]:
        """Check if all required dependencies are satisfied"""
        errors = []
        accessory_id_set = set(str(aid) for aid in accessory_ids)
        
        # Get product details for better error messages
        product_names = self._get_product_names(accessory_ids)
        
        for dep in dependencies:
            if dep['dependency_type'] == 'requires':
                option_id = dep['option_id']
                required_id = dep['depends_on_option_id']
                
                # Check if required option is in configuration
                if required_id not in accessory_id_set:
                    option_name = product_names.get(option_id, option_id)
                    required_name = self._get_product_name(required_id)
                    
                    error_msg = (
                        f"❌ {option_name} requires {required_name} "
                        f"(missing from configuration)"
                    )
                    if dep.get('notes'):
                        error_msg += f" - {dep['notes']}"
                    
                    errors.append(error_msg)
        
        return errors
    
    def _check_conflicts(
        self,
        accessory_ids: List[UUID],
        dependencies: List[Dict]
    ) -> List[str]:
        """Check for conflicting options (excludes)"""
        errors = []
        accessory_id_set = set(str(aid) for aid in accessory_ids)
        
        # Get product details for better error messages
        product_names = self._get_product_names(accessory_ids)
        
        for dep in dependencies:
            if dep['dependency_type'] == 'excludes':
                option_id = dep['option_id']
                excluded_id = dep['depends_on_option_id']
                
                # Check if excluded option is in configuration
                if excluded_id in accessory_id_set:
                    option_name = product_names.get(option_id, option_id)
                    excluded_name = product_names.get(excluded_id, excluded_id)
                    
                    error_msg = (
                        f"⚠️ {option_name} conflicts with {excluded_name} "
                        f"(cannot use both)"
                    )
                    if dep.get('notes'):
                        error_msg += f" - {dep['notes']}"
                    
                    errors.append(error_msg)
        
        return errors
    
    def _check_alternatives(
        self,
        accessory_ids: List[UUID],
        dependencies: List[Dict]
    ) -> List[str]:
        """Check for alternative options (warnings)"""
        warnings = []
        accessory_id_set = set(str(aid) for aid in accessory_ids)
        
        # Get product details for better messages
        product_names = self._get_product_names(accessory_ids)
        
        for dep in dependencies:
            if dep['dependency_type'] == 'alternative':
                option_id = dep['option_id']
                alternative_id = dep['depends_on_option_id']
                
                # Check if both alternatives are in configuration
                if alternative_id in accessory_id_set:
                    option_name = product_names.get(option_id, option_id)
                    alternative_name = product_names.get(alternative_id, alternative_id)
                    
                    warning_msg = (
                        f"ℹ️ {option_name} and {alternative_name} are alternatives "
                        f"(typically choose one)"
                    )
                    if dep.get('notes'):
                        warning_msg += f" - {dep['notes']}"
                    
                    warnings.append(warning_msg)
        
        return warnings
    
    def _get_recommendations(
        self,
        product_id: UUID,
        accessory_ids: List[UUID],
        dependencies: List[Dict]
    ) -> List[str]:
        """Get recommendations for the configuration"""
        recommendations = []
        
        # Check if there are standard accessories not included
        try:
            response = self.supabase.schema('krai_core').table('product_accessories').select(
                'accessory_id, is_standard'
            ).eq('product_id', str(product_id)).eq('is_standard', True).execute()
            
            if response.data:
                accessory_id_set = set(str(aid) for aid in accessory_ids)
                
                for row in response.data:
                    accessory_id = row['accessory_id']
                    if accessory_id not in accessory_id_set:
                        accessory_name = self._get_product_name(accessory_id)
                        recommendations.append(
                            f"💡 Consider adding {accessory_name} (standard accessory)"
                        )
        
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
        
        return recommendations
    
    def _get_product_names(self, product_ids: List[UUID]) -> Dict[str, str]:
        """Get product names for multiple products"""
        try:
            if not product_ids:
                return {}
            
            product_id_strs = [str(pid) for pid in product_ids]
            
            response = self.supabase.schema('krai_core').table('products').select(
                'id, model_number'
            ).in_('id', product_id_strs).execute()
            
            if response.data:
                return {row['id']: row['model_number'] for row in response.data}
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting product names: {e}")
            return {}
    
    def _get_product_name(self, product_id: str) -> str:
        """Get product name for a single product"""
        try:
            response = self.supabase.schema('krai_core').table('products').select(
                'model_number'
            ).eq('id', product_id).single().execute()
            
            if response.data:
                return response.data['model_number']
            
            return product_id
            
        except Exception as e:
            self.logger.error(f"Error getting product name: {e}")
            return product_id
    
    def get_compatible_accessories(self, product_id: UUID) -> List[Dict]:
        """
        Get all compatible accessories for a product
        
        Returns list with compatibility info and dependency warnings
        """
        try:
            # Get all accessories for this product
            response = self.supabase.schema('krai_core').table('product_accessories').select(
                'accessory_id, is_standard, compatibility_notes'
            ).eq('product_id', str(product_id)).execute()
            
            if not response.data:
                return []
            
            accessory_ids = [row['accessory_id'] for row in response.data]
            
            # Get accessory details
            accessories_response = self.supabase.schema('krai_core').table('products').select(
                'id, model_number, product_type'
            ).in_('id', accessory_ids).execute()
            
            if not accessories_response.data:
                return []
            
            # Get dependencies for these accessories
            dependencies = self._get_dependencies([UUID(aid) for aid in accessory_ids])
            
            # Build result with dependency info
            result = []
            for accessory in accessories_response.data:
                accessory_id = accessory['id']
                
                # Find original compatibility info
                compat_info = next(
                    (r for r in response.data if r['accessory_id'] == accessory_id),
                    {}
                )
                
                # Find dependencies
                requires = [
                    d for d in dependencies 
                    if d['option_id'] == accessory_id and d['dependency_type'] == 'requires'
                ]
                excludes = [
                    d for d in dependencies 
                    if d['option_id'] == accessory_id and d['dependency_type'] == 'excludes'
                ]
                
                result.append({
                    'id': accessory_id,
                    'model_number': accessory['model_number'],
                    'product_type': accessory['product_type'],
                    'is_standard': compat_info.get('is_standard', False),
                    'compatibility_notes': compat_info.get('compatibility_notes'),
                    'requires': [d['depends_on_option_id'] for d in requires],
                    'excludes': [d['depends_on_option_id'] for d in excludes]
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting compatible accessories: {e}")
            return []
