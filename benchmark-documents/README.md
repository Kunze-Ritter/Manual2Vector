# Benchmark Documents Directory

## Purpose

This directory stores representative test documents for performance benchmarking of the KRAI processing pipeline in the staging environment.

## Expected Content

The directory should contain **10 representative documents** ranging from **1MB to 100MB** in size. These documents are used to:

- Measure processing performance across different document sizes
- Establish performance baselines for regression testing
- Validate pipeline throughput and resource utilization
- Test concurrent processing capabilities

## File Naming Convention

Documents should follow this naming pattern:

```
benchmark_doc_01.pdf
benchmark_doc_02.pdf
benchmark_doc_03.pdf
...
benchmark_doc_10.pdf
```

## Document Selection Criteria

When populating this directory, select documents that:

1. **Represent real-world workloads** - Use actual service manuals, technical documentation, or similar content
2. **Vary in size** - Include small (1-5MB), medium (5-20MB), and large (20-100MB) documents
3. **Vary in complexity** - Mix text-heavy, image-heavy, and mixed-content documents
4. **Include diverse content types** - Error codes, parts catalogs, diagrams, tables, etc.
5. **Are production-safe** - No sensitive or confidential information

## Size Distribution Recommendation

| Document | Size Range | Content Type |
|----------|------------|--------------|
| benchmark_doc_01.pdf | 1-2 MB | Text-heavy manual |
| benchmark_doc_02.pdf | 2-5 MB | Mixed text and images |
| benchmark_doc_03.pdf | 5-10 MB | Image-heavy catalog |
| benchmark_doc_04.pdf | 10-15 MB | Technical diagrams |
| benchmark_doc_05.pdf | 15-20 MB | Parts catalog |
| benchmark_doc_06.pdf | 20-30 MB | Service manual |
| benchmark_doc_07.pdf | 30-40 MB | Combined documentation |
| benchmark_doc_08.pdf | 40-60 MB | Large service manual |
| benchmark_doc_09.pdf | 60-80 MB | Comprehensive guide |
| benchmark_doc_10.pdf | 80-100 MB | Complete documentation set |

## Data Population

Documents will be populated by data snapshot scripts created in subsequent implementation phases. These scripts will:

- Copy representative documents from production data
- Anonymize sensitive information if necessary
- Verify document integrity and readability
- Generate metadata for benchmark tracking

## Usage in Staging Environment

The staging environment (`docker-compose.staging.yml`) mounts this directory to `/app/benchmark-documents` inside the backend container. Benchmark scripts can access these documents for:

- Automated performance testing
- Regression detection
- Capacity planning
- Optimization validation

## Git Tracking

- **Tracked**: This README.md and .gitkeep files
- **Ignored**: All PDF files (see `.gitignore`)
- **Reason**: Large binary files should not be committed to version control

## Notes

- Actual documents are **not included in the repository**
- Documents must be populated manually or via snapshot scripts
- Total directory size when populated: ~500MB-1GB
- Ensure sufficient disk space before populating
