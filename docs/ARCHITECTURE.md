# MAPS Architecture Documentation

This document provides comprehensive architecture diagrams and explanations of the MAPS system.

## Table of Contents

1. [System Overview](#system-overview)
2. [Service Architecture](#service-architecture)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [Authentication Flow](#authentication-flow)
5. [Scenario Pipeline](#scenario-pipeline)
6. [Circuit Breaker Pattern](#circuit-breaker-pattern)

---

## System Overview

```mermaid
graph TB
    subgraph Client["Client Layer"]
        WEB[Web Browser]
        JS[JavaScript Client]
    end
    
    subgraph APILayer["API Layer"]
        FAST[FastAPI Application]
        AUTH[Auth Middleware]
        RATE[Rate Limit Middleware]
        CORS[CORS Middleware]
    end
    
    subgraph Services["Service Layer"]
        LLM[LLM Service]
        CB[Circuit Breaker]
        MPS[Model Provider Service]
        PRE[Persona Response Engine]
        IAS[Interaction Analyzer]
        MAPS[MAPS Analysis Service]
        MS[Metrics Service]
    end
    
    subgraph External["External Services"]
        OPENAI[OpenAI API]
        ANTHRO[Anthropic API]
        GEMINI[Google Gemini API]
        DEEP[Deepgram Voice]
    end
    
    subgraph Data["Data Layer"]
        SUPA[(Supabase PostgreSQL)]
        VEC[Vector Store]
    end
    
    WEB --> JS
    JS --> FAST
    FAST --> AUTH
    AUTH --> RATE
    RATE --> CORS
    CORS --> LLM
    CORS --> PRE
    CORS --> MAPS
    
    LLM --> CB
    CB --> MPS
    MPS --> OPENAI
    MPS --> ANTHRO
    MPS --> GEMINI
    
    PRE --> LLM
    IAS --> LLM
    MAPS --> LLM
    MAPS --> SUPA
    
    MS --> SUPA
    
    FAST --> DEEP
    
    PRE --> SUPA
    IAS --> SUPA
```

### Component Descriptions

| Component | Purpose | Technology |
|-----------|---------|------------|
| **FastAPI** | Web framework and API endpoints | FastAPI |
| **Auth Middleware** | JWT validation and route protection | Custom + PyJWT |
| **Rate Limit Middleware** | Request throttling and abuse prevention | Custom |
| **Circuit Breaker** | LLM provider resilience | Custom implementation |
| **LLM Service** | Unified interface for all LLM providers | OpenAI, Anthropic, Gemini SDKs |
| **Model Provider Service** | Multi-provider failover | Custom |
| **Persona Response Engine** | Generates authentic persona responses | LLM-based |
| **MAPS Analysis Service** | Person-centered coaching analysis | LLM + Pydantic |
| **Metrics Service** | System metrics collection | Supabase |

---

## Service Architecture

### LLM Provider Chain with Circuit Breaker

```mermaid
flowchart TD
    A[Request] --> B{Circuit Breaker}
    B -->|CLOSED| C[Attempt Primary Provider]
    B -->|OPEN| D[Fast Fail]
    B -->|HALF_OPEN| E[Test Provider]
    
    C --> F{Success?}
    F -->|Yes| G[Return Response]
    F -->|No| H[Record Failure]
    
    H --> I{Failure Count >= Threshold?}
    I -->|Yes| J[Open Circuit]
    I -->|No| C
    
    E --> K{Test Success?}
    K -->|Yes| L[Close Circuit]
    K -->|No| J
    
    J --> M[Try Failover Chain]
    M --> N[Secondary Provider]
    N --> O{Tertiary Provider}
    
    G --> P[Record Success]
    L --> P
    
    D --> Q[Return Error]
```

### Provider Failover Chain

```mermaid
graph LR
    subgraph "Failover Priority"
        A1[Primary] --> B1[Secondary]
        B1 --> C1[Tertiary]
    end
    
    subgraph "Persona Response"
        A2[gemini-2.5-flash-lite] --> B2[gemini-2.5-flash]
        B2 --> C2[claude-3-sonnet]
    end
    
    subgraph "MI Analysis"
        A3[gpt-4.1-nano] --> B3[claude-3-haiku]
        B3 --> C3[gemini-2.5-flash]
    end
    
    subgraph "Memory Formation"
        A4[gpt-4.1-nano] --> B4[claude-3-haiku]
        B4 --> C4[gemini-2.5-flash]
    end
```

---

## Data Flow Diagrams

### Scenario Training Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as API Layer
    participant SP as Scenario Pipeline
    participant PRE as Persona Engine
    participant IAS as Interaction Analyzer
    participant FG as Feedback Generator
    participant LLM as LLM Service
    participant DB as Supabase

    U->>API: POST /api/scenarios/{id}/interact
    API->>SP: process_turn(scenario, attempt, input)
    
    SP->>DB: Get conversation history
    DB-->>SP: Return history
    
    SP->>PRE: generate_response(config, input, history, state)
    PRE->>LLM: generate_response(prompt)
    LLM-->>PRE: persona_response
    PRE-->>SP: PersonaResponse(message, updated_state)
    
    SP->>IAS: analyze_turn(manager_msg, persona_response, state_change)
    IAS->>LLM: structured_completion(analysis_prompt)
    LLM-->>IAS: analysis_data
    IAS-->>SP: InteractionAnalysis
    
    SP->>FG: generate_realtime_tip(analysis)
    FG-->>SP: FeedbackResult
    
    SP->>DB: Save turn to transcript
    
    SP-->>API: TurnResult
    API-->>U: {persona_message, feedback, analysis}
```

### MAPS Analysis Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as API Layer
    participant MAPS as MAPS Analysis Service
    participant LLM as LLM Service
    participant DB as Supabase

    U->>API: POST /api/analysis/{conversation_id}
    API->>MAPS: analyze_conversation_by_id(conversation_id)
    
    MAPS->>DB: Fetch conversation
    DB-->>MAPS: Conversation messages
    
    MAPS->>DB: Get persona config
    DB-->>MAPS: Persona details
    
    MAPS->>LLM: Analyze patterns
    LLM-->>MAPS: PatternsObserved
    
    MAPS->>LLM: Assess coaching effectiveness
    LLM-->>MAPS: CoreCoachingEffectiveness
    
    MAPS->>LLM: Generate strengths & suggestions
    LLM-->>MAPS: StrengthsAndSuggestions
    
    MAPS->>MAPS: Compile MAPSAnalysisResult
    
    MAPS-->>API: AnalysisResult
    API-->>U: Complete analysis report
```

### Authentication Flow

```mermaid
flowchart TD
    A[Client Request] --> B{Route Type?}
    
    B -->|Public| C[Allow Access]
    B -->|API| D{Auth Header?}
    B -->|Protected Page| E{Cookie/Token?}
    
    D -->|Yes| F[Validate JWT]
    D -->|No| G{Auth Indicator?}
    
    E -->|Yes| F
    E -->|No| G
    
    F -->|Valid| C
    F -->|Invalid| H[Return 401]
    
    G -->|Yes| I[Allow - Client-side Check]
    G -->|No| J[Redirect to /auth]
    
    C --> K[Process Request]
    H --> L[Return Error]
    I --> K
    J --> M[Auth Page]
```

---

## Scenario Pipeline

### State Management

```mermaid
stateDiagram-v2
    [*] --> Initializing: User starts scenario
    
    Initializing --> AwaitingUser: Display persona intro
    
    AwaitingUser --> Processing: User sends message
    
    Processing --> GeneratingResponse: Validate input
    
    GeneratingResponse --> Analyzing: Get LLM response
    
    Analyzing --> ProvidingFeedback: Analyze interaction
    
    ProvidingFeedback --> CheckingCompletion: Generate tip
    
    CheckingCompletion --> AwaitingUser: Continue
    CheckingCompletion --> Complete: Objective met
    CheckingCompletion --> Failed: Max turns exceeded
    
    Complete --> [*]: Return final feedback
    Failed --> [*]: Return partial feedback
```

### Trust Level Evolution

```mermaid
graph LR
    subgraph "Trust Trajectory"
        R[Resistance] --> N[Neutral]
        N --> C[Cooperation]
        C --> T[Trust]
    
        R -->|MI Adherent| N
        N -->|MI Adherent| C
        C -->|MI Adherent| T
        
        T -->|MI Non-Adherent| C
        C -->|MI Non-Adherent| N
        N -->|MI Non-Adherent| R
    end
```

---

## Circuit Breaker Pattern

### State Machine

```mermaid
stateDiagram-v2
    [*] --> Closed: Initialize
    
    Closed --> Closed: Success
    Closed --> Open: Failure Count >= Threshold
    
    Open --> HalfOpen: Timeout Elapsed
    Open --> Open: Request Blocked
    
    HalfOpen --> Closed: Success Count >= Threshold
    HalfOpen --> Open: Any Failure
    
    Closed --> [*]: Shutdown
    Open --> [*]: Shutdown
    HalfOpen --> [*]: Shutdown
```

### Configuration per Provider

```mermaid
graph TB
    subgraph "OpenAI Circuit"
        A1[Failure Threshold: 5]
        B1[Recovery Timeout: 60s]
        C1[Half-Open Max: 3]
        D1[Success Threshold: 2]
    end
    
    subgraph "Anthropic Circuit"
        A2[Failure Threshold: 5]
        B2[Recovery Timeout: 60s]
        C2[Half-Open Max: 3]
        D2[Success Threshold: 2]
    end
    
    subgraph "Gemini Circuit"
        A3[Failure Threshold: 5]
        B3[Recovery Timeout: 60s]
        C3[Half-Open Max: 3]
        D3[Success Threshold: 2]
    end
```

---

## Rate Limiting Strategy

### Request Flow

```mermaid
flowchart TD
    A[Incoming Request] --> B{Exempt Path?}
    B -->|Yes| C[Allow]
    B -->|No| D{Rate Limit Exceeded?}
    
    D -->|No| E{ Burst Limit?}
    D -->|Yes| F[Block - 429]
    
    E -->|OK| G[Process]
    E -->|Exceeded| F
    
    G --> H[Add Headers]
    C --> H
    
    H --> I[X-RateLimit-Limit]
    H --> J[X-RateLimit-Remaining]
    H --> K[X-RateLimit-Reset]
```

### Limits by Endpoint Type

```mermaid
graph LR
    subgraph "Rate Limits"
        A[Default: 60/min] 
        B[Chat: 30/min]
        C[Voice: 20/min]
        D[Analysis: 10/min]
        E[Auth: 10/min]
    end
    
    subgraph "Burst Allowance"
        A1[Default: 10]
        B1[Chat: 5]
        C1[Voice: 3]
        D1[Analysis: 2]
        E1[Auth: 5]
    end
```

---

## Database Schema (Simplified)

```mermaid
erDiagram
    USERS ||--o{ CONVERSATIONS : has
    USERS ||--o{ ATTEMPTS : makes
    USERS {
        uuid id
        string email
        string role
        timestamp created_at
    }
    
    CONVERSATIONS ||--o{ MESSAGES : contains
    CONVERSATIONS {
        uuid id
        uuid user_id
        uuid persona_id
        string status
        jsonb metadata
    }
    
    MESSAGES {
        uuid id
        uuid conversation_id
        string role
        text content
        timestamp created_at
    }
    
    PERSONAS ||--o{ CONVERSATIONS : participates
    PERSONAS {
        uuid id
        string name
        jsonb config
        int difficulty_level
    }
    
    SCENARIOS ||--o{ ATTEMPTS : generates
    SCENARIOS {
        uuid id
        string code
        jsonb dialogue_structure
        jsonb maps_rubric
    }
    
    ATTEMPTS {
        uuid id
        uuid user_id
        uuid scenario_id
        jsonb transcript
        string status
        timestamp completed_at
    }
    
    METRICS {
        uuid id
        int llm_calls_total
        int errors_total
        jsonb calls_by_provider
        jsonb latency_by_model
        timestamp created_at
    }
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Client"
        BROWSER[Web Browser]
    end
    
    subgraph "CDN/Edge"
        STATIC[Static Assets]
    end
    
    subgraph "Railway/App Platform"
        APP[FastAPI App]
        WORKER[Background Workers]
    end
    
    subgraph "Supabase"
        PG[(PostgreSQL)]
        AUTH[Authentication]
        STORAGE[File Storage]
        REALTIME[Realtime]
    end
    
    subgraph "External APIs"
        OAI[OpenAI]
        ANTH[Anthropic]
        GEM[Google Gemini]
        DG[Deepgram]
    end
    
    BROWSER --> STATIC
    BROWSER --> APP
    APP --> PG
    APP --> AUTH
    APP --> OAI
    APP --> ANTH
    APP --> GEM
    APP --> DG
    WORKER --> PG
```

---

*Last Updated: 2026-02-02*
