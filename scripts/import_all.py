#!/usr/bin/env python3
"""Import all samples from CSV chunks."""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from axon.ingest.adapters.nih import NIHAdapter
from axon.ingest.importer import SampleImporter

async def main():
    engine = create_async_engine('postgresql+asyncpg://axon:axon@localhost:5433/axon')
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    # Get all chunk files
    chunks_dir = Path('data/chunks')
    chunk_files = sorted(chunks_dir.glob('chunk_*.csv'))
    print(f"Found {len(chunk_files)} chunk files")
    
    adapter = NIHAdapter()
    total_created = 0
    total_updated = 0
    total_errors = 0
    
    for i, chunk_file in enumerate(chunk_files):
        print(f"\n[{i+1}/{len(chunk_files)}] Processing {chunk_file.name}...", flush=True)
        
        # Parse chunk
        samples = list(adapter.process_csv(str(chunk_file)))
        print(f"  Parsed {len(samples)} samples", flush=True)
        
        # Import
        async with session_factory() as session:
            importer = SampleImporter(session, auto_create_sources=True)
            result = await importer.import_batch(samples, batch_size=100)
            await session.commit()
            
            total_created += result.created
            total_updated += result.updated
            total_errors += result.errors
            print(f"  Imported: {result.created} created, {result.updated} updated, {result.errors} errors", flush=True)
    
    print(f"\n{'='*50}")
    print(f"TOTAL: {total_created} created, {total_updated} updated, {total_errors} errors")
    
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())

