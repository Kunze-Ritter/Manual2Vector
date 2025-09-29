"""
Data Models for KR-AI-Engine
Pydantic models for all data structures in the processing pipeline
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid

class DocumentType(str, Enum):
    """Document type enumeration"""
    SERVICE_MANUAL = "service_manual"
    PARTS_CATALOG = "parts_catalog"
    TECHNICAL_BULLETIN = "technical_bulletin"
    CPMD_DATABASE = "cpmd_database"
    USER_MANUAL = "user_manual"
    INSTALLATION_GUIDE = "installation_guide"
    TROUBLESHOOTING_GUIDE = "troubleshooting_guide"

class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ImageType(str, Enum):
    """Image type enumeration"""
    DIAGRAM = "diagram"
    SCREENSHOT = "screenshot"
    PHOTO = "photo"
    CHART = "chart"
    SCHEMATIC = "schematic"
    FLOWCHART = "flowchart"

class ChunkType(str, Enum):
    """Chunk type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    LIST = "list"
    CODE = "code"
    ERROR_CODE = "error_code"
    PROCEDURE = "procedure"

# Core Document Models
class DocumentModel(BaseModel):
    """Document model for krai_core.documents"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    file_size: int
    file_hash: str
    storage_path: Optional[str] = None  # Database only - no Object Storage
    storage_url: Optional[str] = None  # Database only - no Object Storage
    document_type: DocumentType
    language: str = "en"
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    manufacturer: Optional[str] = None
    series: Optional[str] = None
    models: List[str] = Field(default_factory=list)
    version: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class ManufacturerModel(BaseModel):
    """Manufacturer model for krai_core.manufacturers"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProductSeriesModel(BaseModel):
    """Product series model for krai_core.product_series"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    manufacturer_id: str
    series_name: str
    series_code: Optional[str] = None
    launch_date: Optional[datetime] = None
    end_of_life_date: Optional[datetime] = None
    target_market: Optional[str] = None
    price_range: Optional[str] = None
    key_features: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    series_description: Optional[str] = None
    marketing_name: Optional[str] = None
    successor_series_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProductModel(BaseModel):
    """Product model for krai_core.products"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    manufacturer_id: str
    series_id: str
    model_number: str
    model_name: str
    product_type: str
    launch_date: Optional[datetime] = None
    end_of_life_date: Optional[datetime] = None
    msrp_usd: Optional[float] = None
    weight_kg: Optional[float] = None
    dimensions_mm: Dict[str, float] = Field(default_factory=dict)  # JSONB
    color_options: List[str] = Field(default_factory=list)
    connectivity_options: List[str] = Field(default_factory=list)
    print_technology: Optional[str] = None
    max_print_speed_ppm: Optional[int] = None
    max_resolution_dpi: Optional[int] = None
    max_paper_size: Optional[str] = None
    duplex_capable: bool = False
    network_capable: bool = False
    mobile_print_support: bool = False
    supported_languages: List[str] = Field(default_factory=list)
    energy_star_certified: bool = False
    warranty_months: Optional[int] = None
    service_manual_url: Optional[str] = None
    parts_catalog_url: Optional[str] = None
    driver_download_url: Optional[str] = None
    firmware_version: Optional[str] = None
    option_dependencies: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    replacement_parts: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    common_issues: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Content Models
class ChunkModel(BaseModel):
    """Chunk model for krai_content.chunks"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    chunk_type: ChunkType
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    confidence_score: float = 0.0
    language: str = "en"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ImageModel(BaseModel):
    """Image model for krai_content.images"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    filename: str
    original_filename: str
    storage_path: str  # Object Storage path
    storage_url: str   # Object Storage URL
    file_size: int
    image_format: str
    width_px: int
    height_px: int
    page_number: int
    image_index: int
    image_type: ImageType
    ai_description: Optional[str] = None
    ai_confidence: float = 0.0
    contains_text: bool = False
    ocr_text: Optional[str] = None
    ocr_confidence: float = 0.0
    tags: List[str] = Field(default_factory=list)
    file_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Intelligence Models
class IntelligenceChunkModel(BaseModel):
    """Intelligence chunk model for krai_intelligence.chunks"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    text_chunk: str
    chunk_index: int
    page_start: int
    page_end: int
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    fingerprint: str
    metadata: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmbeddingModel(BaseModel):
    """Embedding model for krai_intelligence.embeddings"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    chunk_id: str
    embedding: List[float]  # 768-dimensional vector
    model_name: str
    model_version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ErrorCodeModel(BaseModel):
    """Error code model for krai_intelligence.error_codes"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    error_code: str
    error_description: str
    solution_text: str
    page_number: int
    confidence_score: float = 0.0
    extraction_method: str
    requires_technician: bool = False
    requires_parts: bool = False
    estimated_fix_time_minutes: Optional[int] = None
    severity_level: str = "low"
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SearchAnalyticsModel(BaseModel):
    """Search analytics model for krai_intelligence.search_analytics"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    results_count: int
    processing_time_ms: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# System Models
class ProcessingQueueModel(BaseModel):
    """Processing queue model for krai_system.processing_queue"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    processor_name: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLogModel(BaseModel):
    """Audit log model for krai_system.audit_log"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SystemMetricsModel(BaseModel):
    """System metrics model for krai_system.system_metrics"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str
    metric_value: float
    metric_unit: str
    tags: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Defect Detection Models
class PrintDefectModel(BaseModel):
    """Print defect model for krai_content.print_defects"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    image_id: str
    defect_type: str
    confidence: float
    suggested_solutions: List[str] = Field(default_factory=list)
    estimated_fix_time: Optional[str] = None
    required_parts: List[str] = Field(default_factory=list)
    difficulty_level: str = "easy"
    related_error_codes: List[str] = Field(default_factory=list)
    similar_cases: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# API Models
class DocumentUploadRequest(BaseModel):
    """Document upload request model"""
    filename: str
    file_content: bytes
    document_type: Optional[DocumentType] = None
    language: str = "en"

class DocumentUploadResponse(BaseModel):
    """Document upload response model"""
    document_id: str
    status: ProcessingStatus
    message: str
    processing_time: Optional[float] = None

class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    document_types: Optional[List[DocumentType]] = None
    manufacturers: Optional[List[str]] = None
    models: Optional[List[str]] = None
    limit: int = 10
    offset: int = 0

class SearchResponse(BaseModel):
    """Search response model"""
    results: List[Dict[str, Any]]
    total_count: int
    processing_time_ms: float
    query: str

class DefectDetectionRequest(BaseModel):
    """Defect detection request model"""
    image_content: bytes
    image_format: str = "png"
    description: Optional[str] = None

class DefectDetectionResponse(BaseModel):
    """Defect detection response model"""
    defect_type: str
    confidence: float
    suggested_solutions: List[str]
    estimated_fix_time: Optional[str] = None
    required_parts: List[str] = Field(default_factory=list)
    difficulty_level: str = "easy"
    related_error_codes: List[str] = Field(default_factory=list)
