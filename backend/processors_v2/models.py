"""
Data models for processor V2

Pydantic models for type safety and validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID, uuid4


class ExtractedProduct(BaseModel):
    """Product extracted from document"""
    model_number: str = Field(..., min_length=3, max_length=100)
    product_series: Optional[str] = Field(None, description="Product series/family (e.g., LaserJet, AccurioPress)")
    product_type: str = Field(
        ..., 
        pattern="^(printer|scanner|multifunction|copier|plotter|finisher|feeder|tray|cabinet|accessory|consumable)$",
        description="Product type: printer, scanner, multifunction, copier, plotter, finisher, feeder, tray, cabinet, accessory, consumable"
    )
    manufacturer_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_page: Optional[int] = None
    extraction_method: str = Field(default="regex")
    
    # Specifications (JSONB - flexible storage)
    specifications: Dict[str, Any] = Field(
        default_factory=dict, 
        description="All specifications in flexible JSONB format"
    )
    
    # Computed property for display name
    @property
    def display_name(self) -> str:
        """Generate display name from series + model_number"""
        if self.product_series:
            return f"{self.product_series} {self.model_number}"
        return self.model_number
    
    # Helper properties for common specs (backward compatibility)
    @property
    def max_print_speed_ppm(self) -> Optional[int]:
        return self.specifications.get('max_print_speed_ppm')
    
    @property
    def max_resolution_dpi(self) -> Optional[int]:
        return self.specifications.get('max_resolution_dpi')
    
    @property
    def duplex_capable(self) -> Optional[bool]:
        return self.specifications.get('duplex_capable')
    
    @validator('model_number')
    def validate_model_number(cls, v):
        """Ensure model number is not a filename"""
        if '.' in v or '_' in v or '/' in v or '\\' in v:
            raise ValueError("Model number appears to be a filename")
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Model number must contain both letters and numbers")
        return v


class ExtractedErrorCode(BaseModel):
    """Error code extracted from document"""
    error_code: str = Field(..., pattern=r"^\d{2}\.\d{2}(\.\d{2})?$")
    error_description: str = Field(..., min_length=20)
    solution_text: Optional[str] = None
    context_text: str = Field(..., min_length=100)
    confidence: float = Field(..., ge=0.0, le=1.0)
    page_number: int
    extraction_method: str = Field(default="regex_pattern")
    requires_technician: bool = False
    requires_parts: bool = False
    severity_level: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    
    @validator('error_description')
    def validate_description(cls, v):
        """Ensure description is not generic"""
        generic_phrases = [
            'error code',
            'refer to manual',
            'see documentation',
            'contact support'
        ]
        # If description is short and contains generic phrase, reject
        if len(v) < 30:
            for phrase in generic_phrases:
                if phrase in v.lower():
                    raise ValueError(f"Description too generic: contains '{phrase}'")
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Minimum confidence threshold"""
        if v < 0.6:
            raise ValueError("Confidence below minimum threshold (0.6)")
        return v


class TextChunk(BaseModel):
    """Text chunk for embedding"""
    chunk_id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    text: str = Field(..., min_length=50)
    chunk_index: int
    page_start: int
    page_end: int
    chunk_type: str = Field(default="text")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    fingerprint: Optional[str] = None
    
    @validator('text')
    def validate_text(cls, v):
        """Ensure text is meaningful"""
        if len(v.strip()) < 50:
            raise ValueError("Chunk text too short after stripping")
        return v.strip()


class DocumentMetadata(BaseModel):
    """Document metadata"""
    document_id: UUID
    title: Optional[str] = None
    author: Optional[str] = None
    creation_date: Optional[datetime] = None
    page_count: int = Field(..., gt=0)
    file_size_bytes: int = Field(..., gt=0)
    mime_type: str = Field(default="application/pdf")
    language: str = Field(default="en")
    document_type: str = Field(..., pattern="^(service_manual|parts_catalog|user_guide|troubleshooting)$")


class ProcessingResult(BaseModel):
    """Result of document processing"""
    document_id: UUID
    success: bool
    metadata: DocumentMetadata
    chunks: List[TextChunk] = Field(default_factory=list)
    products: List[ExtractedProduct] = Field(default_factory=list)
    error_codes: List[ExtractedErrorCode] = Field(default_factory=list)
    versions: List['ExtractedVersion'] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    processing_time_seconds: float
    statistics: Dict[str, Any] = Field(default_factory=dict)
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary for logging"""
        return {
            "document_id": str(self.document_id),
            "success": self.success,
            "chunks_created": len(self.chunks),
            "products_extracted": len(self.products),
            "error_codes_extracted": len(self.error_codes),
            "versions_extracted": len(self.versions),
            "validation_errors": len(self.validation_errors),
            "avg_product_confidence": sum(p.confidence for p in self.products) / len(self.products) if self.products else 0,
            "avg_error_code_confidence": sum(e.confidence for e in self.error_codes) / len(self.error_codes) if self.error_codes else 0,
            "avg_version_confidence": sum(v.confidence for v in self.versions) / len(self.versions) if self.versions else 0,
            "processing_time": f"{self.processing_time_seconds:.2f}s"
        }


class ExtractedVersion(BaseModel):
    """Version extracted from document"""
    version_string: str = Field(..., min_length=1, max_length=50)
    version_type: str = Field(
        ...,
        pattern="^(edition|date|firmware|version|revision)$",
        description="Type of version: edition, date, firmware, version, revision"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    extraction_method: str = Field(default="pattern_matching")
    page_number: Optional[int] = None
    context: Optional[str] = Field(None, max_length=200, description="Surrounding context")
    
    @validator('version_string')
    def validate_version_string(cls, v):
        """Ensure version string is reasonable"""
        if len(v.strip()) < 1:
            raise ValueError("Version string cannot be empty")
        # Remove excessive whitespace
        return ' '.join(v.split())


class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    value: Any
    error_message: str
    severity: str = Field(default="error", pattern="^(warning|error|critical)$")
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: {self.error_message} (value: {self.value})"
