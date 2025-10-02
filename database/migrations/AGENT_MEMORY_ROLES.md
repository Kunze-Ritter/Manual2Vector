# Agent Memory - Role Types Documentation

## 📋 Overview

The `krai_agent.memory` table supports flexible role types for different use cases:
- Standard AI/LLM communication
- n8n AI Agent integration
- Custom business roles (technicians, engineers, etc.)

## 🎭 Supported Roles

### Standard AI/LLM Roles

| Role | Description | Use Case |
|------|-------------|----------|
| `user` | Human user input | Standard chat messages from users |
| `assistant` | AI model response | Responses from AI/LLM models |
| `system` | System prompts | System instructions and context |
| `function` | Function results | Results from function calls |
| `tool` | Tool results | Results from tool executions |

**Example:**
```sql
INSERT INTO krai_agent.memory (session_id, role, content, metadata) VALUES
('session-123', 'user', 'What is error code E001?', '{"source": "web_ui"}'),
('session-123', 'assistant', 'Error E001 indicates a paper jam.', '{"confidence": 0.95}');
```

---

### n8n AI Agent Roles

| Role | Description | Equivalent Standard Role |
|------|-------------|-------------------------|
| `ai` | n8n AI Agent response | `assistant` |
| `human` | n8n Human/User message | `user` |
| `chatbot` | Alternative AI naming | `assistant` |

**Example:**
```sql
INSERT INTO krai_agent.memory (session_id, role, content) VALUES
('n8n-session', 'human', 'How do I fix printer jam?', '{}'),
('n8n-session', 'ai', 'Check paper tray and remove stuck paper.', '{}');
```

---

### Custom Business Roles (KRAI Specific)

| Role | German | Description | Use Case |
|------|--------|-------------|----------|
| `technician` | Techniker | Service technician | Field service queries and responses |
| `engineer` | Ingenieur | Technical engineer | Technical specifications and design |
| `manager` | Manager | Manager/Supervisor | Management decisions and oversight |
| `supervisor` | Teamleiter | Team lead | Team coordination and assignment |
| `customer` | Kunde | End customer | Customer inquiries and feedback |
| `support` | Support | Support team | Customer support interactions |
| `expert` | Experte | Subject expert | Expert knowledge and consultation |

**Example:**
```sql
-- Technician asking for error code help
INSERT INTO krai_agent.memory (session_id, role, content, metadata) VALUES
('tech-session-001', 'technician', 'Error code E023 on HP LaserJet?', '{"technician_id": "TECH-001"}'),
('tech-session-001', 'assistant', 'E023: Replace toner cartridge.', '{"source": "knowledge_base"}');

-- Manager reviewing service cases
INSERT INTO krai_agent.memory (session_id, role, content) VALUES
('mgr-session-005', 'manager', 'Show all open service tickets', '{}'),
('mgr-session-005', 'assistant', 'Found 15 open tickets. Priority: 3 high, 8 medium, 4 low.', '{}');
```

---

## 🔧 Configuration

### Current Constraint

The role constraint is defined in **Migration 11**:

```sql
CHECK (role IN (
    'user', 'assistant', 'system', 'function', 'tool',  -- Standard
    'ai', 'human', 'chatbot',                            -- n8n
    'technician', 'engineer', 'manager', 'supervisor',   -- Business
    'customer', 'support', 'expert'
))
```

### Adding New Roles

To add a new role, update the constraint:

```sql
-- Drop existing constraint
ALTER TABLE krai_agent.memory DROP CONSTRAINT memory_role_check;

-- Add new constraint with additional role
ALTER TABLE krai_agent.memory
ADD CONSTRAINT memory_role_check 
CHECK (role IN (
    -- ... existing roles ...
    'your_new_role'  -- Your new role
));
```

### Removing Constraint (Maximum Flexibility)

For complete flexibility (any role value allowed):

```sql
ALTER TABLE krai_agent.memory DROP CONSTRAINT memory_role_check;
```

⚠️ **Warning**: Removing the constraint allows any string value, which may lead to inconsistent data.

---

## 🎯 Best Practices

### 1. **Use Standard Roles for AI Communication**
```sql
-- ✅ Good
INSERT INTO krai_agent.memory (session_id, role, content) VALUES
('session-1', 'user', 'Query...', '{}');

-- ❌ Avoid custom roles for standard AI chat
INSERT INTO krai_agent.memory (session_id, role, content) VALUES
('session-1', 'random_role', 'Query...', '{}');
```

### 2. **Use Business Roles for Context**
```sql
-- ✅ Good - Clear who is asking
INSERT INTO krai_agent.memory (session_id, role, content, metadata) VALUES
('service-call', 'technician', 'Error E045?', '{"tech_id": "TECH-123"}');

-- ✅ Also good - Standard role with metadata
INSERT INTO krai_agent.memory (session_id, role, content, metadata) VALUES
('service-call', 'user', 'Error E045?', '{"role": "technician", "tech_id": "TECH-123"}');
```

### 3. **Use Metadata for Additional Context**
```sql
INSERT INTO krai_agent.memory (session_id, role, content, metadata) VALUES
('session-1', 'technician', 'Printer jam issue', jsonb_build_object(
    'technician_id', 'TECH-001',
    'location', 'Munich Office',
    'device_serial', 'HP-12345',
    'urgency', 'high'
));
```

---

## 📊 Querying by Role

### Get all technician queries
```sql
SELECT * FROM krai_agent.memory 
WHERE role = 'technician' 
ORDER BY created_at DESC;
```

### Count messages by role
```sql
SELECT role, COUNT(*) as message_count 
FROM krai_agent.memory 
GROUP BY role 
ORDER BY message_count DESC;
```

### Get conversation with role context
```sql
SELECT 
    created_at,
    role,
    content,
    metadata->>'technician_id' as tech_id
FROM krai_agent.memory 
WHERE session_id = 'service-session-001'
ORDER BY created_at ASC;
```

---

## 🔗 Related Documentation

- **Migration 07**: `07_agent_memory_table.sql` - Initial table creation
- **Migration 10**: `10_agent_memory_content_to_message.sql` - View with message alias (deprecated)
- **Migration 11**: `11_expand_memory_role_constraint.sql` - Expanded role constraint
- **Migration 12**: `12_add_message_column_with_sync.sql` - Added message column with auto-sync
- **n8n Setup**: `../docs/n8n/N8N_POSTGRES_MEMORY_INTEGRATION.md`

---

## 📝 Changelog

| Date | Change | Migration |
|------|--------|-----------|
| 2025-10-02 | Initial roles: user, assistant, system, function, tool | 07 |
| 2025-10-02 | View alias: content AS message | 10 |
| 2025-10-02 | Added n8n roles: ai, human, chatbot | 11 |
| 2025-10-02 | Added business roles: technician, engineer, manager, etc. | 11 |
| 2025-10-02 | Added message column with auto-sync trigger | 12 |

---

**Need a new role?** Update Migration 11 or drop the constraint for full flexibility!
