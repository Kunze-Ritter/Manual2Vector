--- HARDWARE STATUS ---
CPU:   0.0% | RAM:  44.0% (13.9GB)
2025-10-01 14:46:07,891 - optimized_text_processor - INFO - Memory usage at after_parallel_processing: 294.9 MB
INFO:krai.optimized_text_processor:Memory usage at after_parallel_processing: 294.9 MB
2025-10-01 14:46:08,114 - krai.database - ERROR - Failed to log audit event: {'message': "Could not find the 'action' column of 'audit_log' in the schema cache", 'code': 'PGRST204', 'hint': None, 'details': None}
ERROR:krai.database:Failed to log audit event: {'message': "Could not find the 'action' column of 'audit_log' in the schema cache", 'code': 'PGRST204', 'hint': None, 'details': None}
2025-10-01 14:46:08,115 - optimized_text_processor - INFO - Memory usage at final: 294.9 MB
INFO:krai.optimized_text_processor:Memory usage at final: 294.9 MB
  [1] Image Processing: A93E.pdf
2025-10-01 14:46:08,186 - image_processor - INFO - Extracting images from PDF...
INFO:krai.image_processor:Extracting images from PDF...
2025-10-01 14:46:08,198 - image_processor - INFO - Extracted 0 images from PDF
INFO:krai.image_processor:Extracted 0 images from PDF
2025-10-01 14:46:08,198 - image_processor - WARNING - No images found in document a4c76282-5c5e-4eba-aa02-ff8797f60d54
WARNING:krai.image_processor:No images found in document a4c76282-5c5e-4eba-aa02-ff8797f60d54
  [1] Classification: A93E.pdf
2025-10-01 14:46:08,242 - classification_processor - INFO - Classification processing for document a4c76282-5c5e-4eba-aa02-ff8797f60d54
INFO:krai.classification_processor:Classification processing for document a4c76282-5c5e-4eba-aa02-ff8797f60d54
2025-10-01 14:46:08,243 - classification_processor - INFO - File path: service_documents\A93E.pdf
INFO:krai.classification_processor:File path: service_documents\A93E.pdf
2025-10-01 14:46:08,244 - classification_processor - ERROR - PyMuPDF not available - cannot extract text from PDF
ERROR:krai.classification_processor:PyMuPDF not available - cannot extract text from PDF
2025-10-01 14:46:08,244 - classification_processor - INFO - PDF not available for a4c76282-5c5e-4eba-aa02-ff8797f60d54, using chunks for classification
INFO:krai.classification_processor:PDF not available for a4c76282-5c5e-4eba-aa02-ff8797f60d54, using chunks for classification
2025-10-01 14:46:10,299 - classification_processor - WARNING - No chunks found for document a4c76282-5c5e-4eba-aa02-ff8797f60d54
WARNING:krai.classification_processor:No chunks found for document a4c76282-5c5e-4eba-aa02-ff8797f60d54
2025-10-01 14:46:10,301 - optimized_text_processor - INFO - Memory usage at after_parallel_processing: 295.0 MB
INFO:krai.optimized_text_processor:Memory usage at after_parallel_processing: 295.0 MB
2025-10-01 14:46:10,413 - krai.database - ERROR - Failed to log audit event: {'message': "Could not find the 'action' column of 'audit_log' in the schema cache", 'code': 'PGRST204', 'hint': None, 'details': None}
ERROR:krai.database:Failed to log audit event: {'message': "Could not find the 'action' column of 'audit_log' in the schema cache", 'code': 'PGRST204', 'hint': None, 'details': None}
2025-10-01 14:46:10,413 - optimized_text_processor - INFO - Memory usage at final: 295.0 MB
INFO:krai.optimized_text_processor:Memory usage at final: 295.0 MB
  [2] Image Processing: A93E017.pdf
2025-10-01 14:46:10,477 - image_processor - INFO - Extracting images from PDF...
INFO:krai.image_processor:Extracting images from PDF...
2025-10-01 14:46:10,482 - image_processor - INFO - Extracted 0 images from PDF
INFO:krai.image_processor:Extracted 0 images from PDF
2025-10-01 14:46:10,482 - image_processor - WARNING - No images found in document 35622490-849a-4cdb-9ef2-65254fb710f9
WARNING:krai.image_processor:No images found in document 35622490-849a-4cdb-9ef2-65254fb710f9
  [2] Classification: A93E017.pdf
2025-10-01 14:46:10,540 - classification_processor - INFO - Classification processing for document 35622490-849a-4cdb-9ef2-65254fb710f9
INFO:krai.classification_processor:Classification processing for document 35622490-849a-4cdb-9ef2-65254fb710f9
2025-10-01 14:46:10,541 - classification_processor - INFO - File path: service_documents\A93E017.pdf
INFO:krai.classification_processor:File path: service_documents\A93E017.pdf
2025-10-01 14:46:10,542 - classification_processor - ERROR - PyMuPDF not available - cannot extract text from PDF
ERROR:krai.classification_processor:PyMuPDF not available - cannot extract text from PDF
2025-10-01 14:46:10,542 - classification_processor - INFO - PDF not available for 35622490-849a-4cdb-9ef2-65254fb710f9, using chunks for classification
INFO:krai.classification_processor:PDF not available for 35622490-849a-4cdb-9ef2-65254fb710f9, using chunks for classification
2025-10-01 14:46:10,598 - classification_processor - WARNING - No chunks found for document 35622490-849a-4cdb-9ef2-65254fb710f9
WARNING:krai.classification_processor:No chunks found for document 35622490-849a-4cdb-9ef2-65254fb710f9
2025-10-01 14:46:10,909 - optimized_text_processor - INFO - Memory usage at after_parallel_processing: 295.0 MB
INFO:krai.optimized_text_processor:Memory usage at after_parallel_processing: 295.0 MB
2025-10-01 14:46:11,015 - krai.database - ERROR - Failed to log audit event: {'message': "Could not find the 'action' column of 'audit_log' in the schema cache", 'code': 'PGRST204', 'hint': None, 'details': None}
ERROR:krai.database:Failed to log audit event: {'message': "Could not find the 'action' column of 'audit_log' in the schema cache", 'code': 'PGRST204', 'hint': None, 'details': None}
2025-10-01 14:46:11,015 - optimized_text_processor - INFO - Memory usage at final: 295.0 MB
INFO:krai.optimized_text_processor:Memory usage at final: 295.0 MB
  [4] Image Processing: AAJN007.pdf
2025-10-01 14:46:11,078 - image_processor - INFO - Extracting images from PDF...
INFO:krai.image_processor:Extracting images from PDF...
2025-10-01 14:46:11,082 - image_processor - INFO - Extracted 0 images from PDF
INFO:krai.image_processor:Extracted 0 images from PDF
2025-10-01 14:46:11,082 - image_processor - WARNING - No images found in document 5aec0c77-514e-4f23-b07a-8d797e3d3fd6
WARNING:krai.image_processor:No images found in document 5aec0c77-514e-4f23-b07a-8d797e3d3fd6
  [4] Classification: AAJN007.pdf
2025-10-01 14:46:11,124 - classification_processor - INFO - Classification processing for document 5aec0c77-514e-4f23-b07a-8d797e3d3fd6
INFO:krai.classification_processor:Classification processing for document 5aec0c77-514e-4f23-b07a-8d797e3d3fd6
2025-10-01 14:46:11,125 - classification_processor - INFO - File path: service_documents\AAJN007.pdf
INFO:krai.classification_processor:File path: service_documents\AAJN007.pdf
2025-10-01 14:46:11,125 - classification_processor - ERROR - PyMuPDF not available - cannot extract text from PDF
ERROR:krai.classification_processor:PyMuPDF not available - cannot extract text from PDF
2025-10-01 14:46:11,125 - classification_processor - INFO - PDF not available for 5aec0c77-514e-4f23-b07a-8d797e3d3fd6, using chunks for classification
INFO:krai.classification_processor:PDF not available for 5aec0c77-514e-4f23-b07a-8d797e3d3fd6, using chunks for classification
2025-10-01 14:46:11,186 - classification_processor - WARNING - No chunks found for document 5aec0c77-514e-4f23-b07a-8d797e3d3fd6
WARNING:krai.classification_processor:No chunks found for document 5aec0c77-514e-4f23-b07a-8d797e3d3fd6
