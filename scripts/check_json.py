import json

try:
    with open('n8n/workflows/TOOL_Video_Enrichment.json', encoding='utf-8') as f:
        data = json.load(f)
    print('✅ JSON is valid!')
    print(f'Nodes: {len(data["nodes"])}')
    print(f'Format node code length: {len(data["nodes"][3]["parameters"]["jsCode"])}')
except Exception as e:
    print(f'❌ JSON ERROR: {e}')
