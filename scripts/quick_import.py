#!/usr/bin/env python3
"""Quick import script for testing."""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

# Add src to path
sys.path.insert(0, 'src')

from axon.ingest.adapters.nih import NIHAdapter

async def main():
    print("Starting...", flush=True)
    engine = create_async_engine('postgresql+asyncpg://axon:axon@localhost:5433/axon')
    
    # Parse just 5 samples
    print("Parsing CSV...", flush=True)
    adapter = NIHAdapter()
    samples = list(adapter.process_csv('data/chunks/chunk_aa.csv'))[:5]
    print(f'Got {len(samples)} samples', flush=True)
    
    async with engine.begin() as conn:
        for i, s in enumerate(samples):
            print(f'Inserting {i+1}...', flush=True)
            sql = text("""INSERT INTO samples (id, source_bank, external_id, raw_data, imported_at, updated_at) 
                         VALUES (:id, :source_bank, :external_id, :raw_data, NOW(), NOW())
                         ON CONFLICT (source_bank, external_id) DO NOTHING""")
            await conn.execute(sql, {
                'id': f'quick_{i}',
                'source_bank': s['source_bank'],
                'external_id': s['external_id'],
                'raw_data': json.dumps(s.get('raw_data', {}))
            })
    
    print('Done!', flush=True)
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())

