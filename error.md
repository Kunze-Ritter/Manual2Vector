C:\Manual2Vector>python backend/tests/krai_master_pipeline.py
Hardware Detection:
   RAM: 31.7 GB
   CPU: 20 cores, 28 threads
   GPU: Not Available
   Recommended Tier: balanced
   GPU Acceleration: Disabled
   Selected Models: llama3.2:13b, embeddinggemma:2b, llava:13b
KR-AI-ENGINE MASTER PIPELINE
==================================================
Ein einziges Script für alle Pipeline-Funktionen!
==================================================
Initializing KR Master Pipeline Services...
2025-10-01 14:25:34,495 - krai.database - ERROR - Failed to connect to database: supabase_url is required
ERROR:krai.database:Failed to connect to database: supabase_url is required
Traceback (most recent call last):
  File "C:\Manual2Vector\backend\services\database_service_production.py", line 60, in connect
    self.client = create_client(self.supabase_url, self.supabase_key)
                  ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Demo\AppData\Roaming\Python\Python313\site-packages\supabase\_sync\client.py", line 369, in create_client
    return SyncClient.create(
           ~~~~~~~~~~~~~~~~~^
        supabase_url=supabase_url, supabase_key=supabase_key, options=options
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\Users\Demo\AppData\Roaming\Python\Python313\site-packages\supabase\_sync\client.py", line 101, in create
    client = cls(supabase_url, supabase_key, options)
  File "C:\Users\Demo\AppData\Roaming\Python\Python313\site-packages\supabase\_sync\client.py", line 53, in __init__
    raise SupabaseException("supabase_url is required")
supabase._sync.client.SupabaseException: supabase_url is required

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Manual2Vector\backend\tests\krai_master_pipeline.py", line 714, in <module>
    asyncio.run(main())
    ~~~~~~~~~~~^^^^^^^^
  File "C:\Program Files\Python313\Lib\asyncio\runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "C:\Program Files\Python313\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Program Files\Python313\Lib\asyncio\base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "C:\Manual2Vector\backend\tests\krai_master_pipeline.py", line 516, in main
    await pipeline.initialize_services()
  File "C:\Manual2Vector\backend\tests\krai_master_pipeline.py", line 81, in initialize_services
    await self.database_service.connect()
  File "C:\Manual2Vector\backend\services\database_service_production.py", line 68, in connect
    raise RuntimeError(f"Cannot connect to Supabase database: {e}")
RuntimeError: Cannot connect to Supabase database: supabase_url is required
