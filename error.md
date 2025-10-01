INFO:krai.database:Audit event (disabled): images_processed on document mock_doc_c19c8bce-d3aa-4b5f-9ae3-4aad2cb5b111
  [2] Classification: A93E017.pdf
2025-10-01 13:47:57,085 - classification_processor - INFO - Classification processing for document mock_doc_c19c8bce-d3aa-4b5f-9ae3-4aad2cb5b111
INFO:krai.classification_processor:Classification processing for document mock_doc_c19c8bce-d3aa-4b5f-9ae3-4aad2cb5b111
2025-10-01 13:47:57,085 - classification_processor - INFO - File path: service_documents\A93E017.pdf
INFO:krai.classification_processor:File path: service_documents\A93E017.pdf
2025-10-01 13:47:57,086 - classification_processor - ERROR - PyMuPDF not available - cannot extract text from PDF
ERROR:krai.classification_processor:PyMuPDF not available - cannot extract text from PDF
2025-10-01 13:47:57,086 - classification_processor - INFO - PDF not available for mock_doc_c19c8bce-d3aa-4b5f-9ae3-4aad2cb5b111, using chunks for classification
INFO:krai.classification_processor:PDF not available for mock_doc_c19c8bce-d3aa-4b5f-9ae3-4aad2cb5b111, using chunks for classification
2025-10-01 13:47:57,086 - Database - ERROR - Failed to get chunks by document ID: 'NoneType' object has no attribute 'table'
ERROR:krai.database:Failed to get chunks by document ID: 'NoneType' object has no attribute 'table'
2025-10-01 13:47:57,086 - classification_processor - WARNING - No chunks found for document mock_doc_c19c8bce-d3aa-4b5f-9ae3-4aad2cb5b111
WARNING:krai.classification_processor:No chunks found for document mock_doc_c19c8bce-d3aa-4b5f-9ae3-4aad2cb5b111

--- HARDWARE STATUS ---
CPU:   9.1% | RAM:  46.7% (14.8GB)
2025-10-01 13:47:58,985 - AI - INFO - Document classified: service_manual (Unknown)
INFO:krai.ai:Document classified: service_manual (Unknown)
2025-10-01 13:47:58,985 - Database - INFO - Created manufacturer mock_manufacturer_24ec9611-3087-4dba-b2eb-221202720ad7 (mock)
INFO:krai.database:Created manufacturer mock_manufacturer_24ec9611-3087-4dba-b2eb-221202720ad7 (mock)
2025-10-01 13:47:58,986 - classification_processor - INFO - Created new manufacturer: Unknown
INFO:krai.classification_processor:Created new manufacturer: Unknown
2025-10-01 13:47:58,986 - Database - INFO - Created product series mock_series_db1aaedb-70cf-4a7c-91d7-0c80d86a5c1c (mock)
INFO:krai.database:Created product series mock_series_db1aaedb-70cf-4a7c-91d7-0c80d86a5c1c (mock)
2025-10-01 13:47:58,986 - classification_processor - INFO - Created product series: Unknown
INFO:krai.classification_processor:Created product series: Unknown
2025-10-01 13:47:58,986 - classification_processor - INFO - Creating products for 0 models: []
INFO:krai.classification_processor:Creating products for 0 models: []
2025-10-01 13:47:58,986 - classification_processor - INFO - Total products created/found: 0
INFO:krai.classification_processor:Total products created/found: 0
2025-10-01 13:48:00,791 - AI - INFO - Document classified: service_manual (Unknown)
INFO:krai.ai:Document classified: service_manual (Unknown)
