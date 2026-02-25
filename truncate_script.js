const fs = require('fs');
const path = 'C:\\Users\\haast\\Docker\\KRAI-minimal\\backend\\api\\agent_api.py';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split('\n');
const newContent = lines.slice(0, 441).join('\n') + '\n';
fs.writeFileSync(path, newContent, 'utf8');
console.log('Done. New line count:', newContent.split('\n').length);
