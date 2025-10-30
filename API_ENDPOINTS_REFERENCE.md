# API Endpoints Reference

Complete reference of all API endpoints with authentication requirements and access levels.

## Authentication

- **Public**: No authentication required
- **Auth**: Requires valid JWT token (both FULL and CONTROL)
- **FULL Only**: Requires JWT token with FULL role

## Chat Endpoints (`src/api/routes/enhanced_chat.py`)

### GET /api/chat/personas
**Access**: Public  
**Description**: List all available personas for enhanced chat  
**Returns**: Array of persona objects with id, name, description

### POST /api/chat/start
**Access**: Auth (FULL + CONTROL)  
**Description**: Start a new enhanced conversation with a persona  
**Body**:
```json
{
  "persona_id": "string"
}
```
**Returns**: conversation_id, session_id, persona_name, initial_greeting

### POST /api/chat/send
**Access**: Auth (FULL + CONTROL)  
**Description**: Send a message in an enhanced conversation  
**Body**:
```json
{
  "message": "string",
  "persona_id": "string",
  "session_id": "string",
  "conversation_id": "string (optional)",
  "conversation_history": "array (optional)",
  "persona_llm": "string (optional, default: gpt-4o-mini)"
}
```
**Returns**: Enhanced response with trust level, interaction quality, empathy metrics

### GET /api/chat/conversations/{conversation_id}
**Access**: Auth (FULL + CONTROL)  
**Description**: Get full conversation history with interaction context  
**Returns**: Conversation metadata, messages, memories

### GET /api/chat/debug/interaction-analysis/{conversation_id}
**Access**: Auth (FULL + CONTROL)  
**Description**: Debug endpoint showing natural empathy assessment analysis  
**Returns**: Interaction analysis with turn-by-turn breakdown

### GET /api/chat/debug/trust-progression/{conversation_id}
**Access**: Auth (FULL + CONTROL)  
**Description**: Show trust progression throughout conversation  
**Returns**: Trust indicators and memory-based progression

### GET /api/chat/debug/character-knowledge/{persona_id}
**Access**: Auth (FULL + CONTROL)  
**Description**: Show knowledge tiers for a character  
**Returns**: All knowledge tiers with trust thresholds

### GET /api/chat/debug/short-term-memory
**Access**: Auth (FULL + CONTROL)  
**Description**: Get short-term memory usage statistics  
**Returns**: Memory usage, active sessions, session details

### GET /api/chat/analytics/dashboard
**Access**: Auth (FULL + CONTROL)  
**Description**: Analytics dashboard with overall statistics  
**Returns**: Overall stats, daily stats, trust analysis

### GET /api/chat/analytics/session/{session_id}
**Access**: Auth (FULL + CONTROL)  
**Description**: Detailed analytics for specific session  
**Returns**: Session analytics and memory stats

### GET /api/chat/analytics/persona/{persona_id}
**Access**: Auth (FULL + CONTROL)  
**Description**: Analytics for specific persona  
**Query Params**: `days` (optional, default: 7)  
**Returns**: Trust analysis and persona-specific metrics

---

## Analysis Endpoints (`src/api/routes/analysis.py`)

### POST /api/v1/analysis/submit
**Access**: FULL Only  
**Description**: Submit transcript for person-centred analysis  
**Body**:
```json
{
  "transcript": "string",
  "context": "object (optional)",
  "speaker_hints": "object (optional)"
}
```
**Returns**: job_id, status

### POST /api/v1/analysis/text
**Access**: FULL Only  
**Description**: Submit transcript text for MAPS analysis (frontend compatible)  
**Body**: Same as /submit  
**Returns**: job_id, status

### POST /api/v1/analysis/enhanced/{conversation_id}
**Access**: FULL Only  
**Description**: Analyze enhanced chat conversation by conversation_id  
**Returns**: job_id, status

### POST /api/v1/analysis/maps
**Access**: FULL Only  
**Description**: Submit transcript for MAPS person-centred analysis  
**Body**: Same as /submit  
**Returns**: job_id, status, analysis_type

### GET /api/v1/analysis/status/{job_id}
**Access**: Public  
**Description**: Get analysis job status  
**Returns**: job_id, status, progress, stage, result (if complete)

### GET /api/v1/analysis/result/{job_id}
**Access**: Public  
**Description**: Get completed analysis results  
**Returns**: job_id, status, result, completed_at

### GET /api/v1/analysis/result/{job_id}/export
**Access**: Public  
**Description**: Export analysis results in various formats  
**Query Params**: `format` (json|html|txt)  
**Returns**: File download

### DELETE /api/v1/analysis/cache
**Access**: Public  
**Description**: Clear analysis cache for fresh analysis  
**Returns**: Cleared count and status

---

## MAPS Analysis Endpoints (`src/api/routes/maps_analysis.py`)

### POST /api/v1/maps/analyze/transcript
**Access**: FULL Only  
**Description**: Analyze raw transcript using MAPS framework (standalone)  
**Body**:
```json
{
  "transcript": "string",
  "context": "object (optional)",
  "manager_name": "string (default: Manager)",
  "persona_name": "string (default: Employee)"
}
```
**Returns**: job_id, status, analysis_type

### POST /api/v1/maps/analyze/conversation
**Access**: FULL Only  
**Description**: Analyze conversation from Supabase by conversation_id  
**Body**:
```json
{
  "conversation_id": "string",
  "context": "object (optional)"
}
```
**Returns**: job_id, status, analysis_type, conversation_id

### GET /api/v1/maps/status/{job_id}
**Access**: Public  
**Description**: Get MAPS analysis job status  
**Returns**: Same as analysis status endpoint

### GET /api/v1/maps/result/{job_id}
**Access**: Public  
**Description**: Get MAPS analysis results  
**Returns**: Detailed MAPS analysis with all four framework sections

---

## Reflection Endpoints (`src/api/routes/reflection.py`)

### GET /api/reflection/health
**Access**: Public  
**Description**: Health check for reflection service  
**Returns**: status, service

### POST /api/reflection/generate-summary
**Access**: FULL Only  
**Description**: Generate cohesive summary from reflection responses  
**Body**:
```json
{
  "question1_response": "string (what went well)",
  "question2_response": "string (struggles)",
  "question3_response": "string (future improvements)",
  "session_id": "string (optional)",
  "persona_practiced": "string (optional)"
}
```
**Returns**: summary, generated_at

### POST /api/reflection/send-email
**Access**: FULL Only  
**Description**: Send reflection results via email  
**Body**:
```json
{
  "email": "string",
  "question1": "string",
  "question2": "string",
  "question3": "string",
  "summary": "string",
  "session_id": "string (optional)",
  "persona_practiced": "string (optional)"
}
```
**Returns**: success, message, email_configured

---

## Feedback Endpoints (`src/api/routes/feedback.py`)

### POST /api/feedback/submit
**Access**: FULL Only  
**Description**: Submit user feedback after practice session  
**Body**:
```json
{
  "session_id": "string",
  "conversation_id": "string (optional)",
  "persona_practiced": "string (optional)",
  "helpfulness_score": "integer (0-10)",
  "what_was_helpful": "string (optional)",
  "improvement_suggestions": "string (optional)",
  "user_email": "string (optional)"
}
```
**Returns**: success, feedback_id, message

### GET /api/feedback/stats
**Access**: Public  
**Description**: Get aggregate feedback statistics  
**Returns**: total_feedback, average_score, score_distribution

---

## Metrics Endpoints (`src/api/routes/metrics.py`)

### GET /api/metrics
**Access**: Public  
**Description**: Get system metrics  
**Returns**: System performance metrics

---

## Web API Endpoints (`src/api/routes/web_api.py`)

### GET /api/web/personas
**Access**: Public  
**Description**: List all personas in web-friendly format  
**Returns**: Array of personas with id, name, description, difficulty

### POST /api/web/personas/{persona_id}/chat
**Access**: Public  
**Description**: Simplified chat endpoint for web interface  
**Body**:
```json
{
  "message": "string",
  "session_id": "string",
  "context": "object (optional)"
}
```
**Returns**: response, timestamp

### GET /api/web/v1/dialogue/scenarios
**Access**: Public  
**Description**: Get available dialogue scenarios  
**Returns**: Array of scenarios

### GET /api/web/v1/dialogue/scenarios/{scenario_id}
**Access**: Public  
**Description**: Get specific dialogue scenario data  
**Returns**: Scenario details

### POST /api/web/v1/dialogue/scenarios/{scenario_id}/next
**Access**: Public  
**Description**: Handle dialogue progression  
**Returns**: success, message

### POST /api/web/export/pdf
**Access**: Public  
**Description**: Export conversation as PDF/HTML  
**Body**:
```json
{
  "messages": "array",
  "metadata": "object"
}
```
**Returns**: HTML file for printing/PDF conversion

---

## Access Control Summary

### Public Endpoints (No Auth Required)
- GET /api/chat/personas
- GET /api/reflection/health
- GET /api/feedback/stats
- GET /api/metrics
- All /api/web/* endpoints
- Analysis status/result endpoints

### Auth Endpoints (FULL + CONTROL)
- POST /api/chat/start
- POST /api/chat/send
- GET /api/chat/conversations/*
- All /api/chat/debug/* endpoints
- All /api/chat/analytics/* endpoints

### FULL Only Endpoints
- All /api/v1/analysis/* endpoints
- All /api/v1/maps/* endpoints
- POST /api/reflection/generate-summary
- POST /api/reflection/send-email
- POST /api/feedback/submit

---

## Authentication Header Format

All authenticated endpoints require:
```
Authorization: Bearer {JWT_TOKEN}
```

## Error Responses

- **401 Unauthorized**: Missing or invalid token
- **403 Forbidden**: Valid token but insufficient permissions (CONTROL accessing FULL-only)
- **404 Not Found**: Resource or endpoint doesn't exist
- **500 Internal Server Error**: Server error (check logs)

## Rate Limiting

Not currently implemented. Consider adding for production deployment.

## CORS

CORS is configured in the main FastAPI app. Update origins in production settings.
