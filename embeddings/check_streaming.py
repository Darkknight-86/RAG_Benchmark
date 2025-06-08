import os
import sys
sys.path.append('src')

from Adapters.ClickHouseAdapter import ClickHouseAdapter
import logging

logging.basicConfig(level=logging.INFO)

print('🔍 Checking ClickHouse for streaming data...')
adapter = ClickHouseAdapter()

# Check total records
total = adapter.client.command('SELECT count() FROM rag_chunks_v2')
print(f'📊 Total records: {total}')

# Check recent streaming data (not test data)
recent = adapter.client.query('''
    SELECT timestamp, security, price, change_percent, volume, source
    FROM rag_chunks_v2
    WHERE source != 'test_streaming'
    ORDER BY timestamp DESC
    LIMIT 10
''')

if recent.result_rows:
    print('📈 Recent streaming data:')
    for row in recent.result_rows:
        print(f'  {row[0]} | {row[1]} | ${row[2]} | {row[3]}% | Vol: {row[4]} | Source: {row[5]}')
else:
    print('❌ No streaming data found (only test data)')

# Check by source
sources = adapter.client.query('''
    SELECT source, count() as count, max(timestamp) as latest
    FROM rag_chunks_v2
    GROUP BY source
    ORDER BY count DESC
''')

print('📋 Data by source:')
for row in sources.result_rows:
    print(f'  {row[0]}: {row[1]} records, latest: {row[2]}')