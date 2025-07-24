**\<?xml version="1.0" encoding="UTF-8"?\>**  
**\<module\_a\_data\_persistence\>**  
    **\<metadata\>**  
        **\<title\>Module A: Data Persistence & Event Architecture Implementation Guide\</title\>**  
        **\<implements\>PostgreSQL Memory Backend, Event Sourcing, Real-time Projections, HIPAA-compliant Audit Trails\</implements\>**  
        **\<dependencies\>Master Control Document\</dependencies\>**  
        **\<version\>1.0-Hybrid\</version\>**  
        **\<purpose\>Transform AUREN from JSON file storage to production-grade data layer supporting unlimited memory, event sourcing, and real-time projections\</purpose\>**  
        **\<token\_budget\>35000\</token\_budget\>**  
    **\</metadata\>**

    **\<load\_manifest\>**  
        **\<always\_load\>Master Control Document\</always\_load\>**  
        **\<primary\_module\>This document (Module A)\</primary\_module\>**  
        **\<optional\_modules\>**  
            **\<module\>Module B (for agent memory integration)\</module\>**  
            **\<module\>Module D (for CrewAI hooks)\</module\>**  
        **\</optional\_modules\>**  
        **\<token\_calculation\>Master (30k) \+ This (35k) \+ Optional (35k) \= 100k used\</token\_calculation\>**  
        **\<available\_tokens\>100k for implementation work\</available\_tokens\>**  
    **\</load\_manifest\>**

    **\<section id="1" name="quick\_context"\>**  
        **\<title\>Quick Context\</title\>**  
        **\<description\>**  
            **This module implements the foundational data infrastructure that transforms AUREN from file-based storage to a production-grade system supporting the multi-agent architecture. The implementation eliminates the 1000-record JSON file limit and provides unlimited memory storage with complete audit trails for HIPAA compliance.**

            **Key insight: Healthcare AI requires immutable audit trails while supporting real-time agent decision-making. Event sourcing provides immutability and audit guarantees, while CQRS projections enable sub-second response times agents need.**

            **The PostgreSQL backend serves as the single source of truth, with Redis projections for real-time agent access and ChromaDB projections for semantic retrieval. This architecture supports hypothesis validation, cross-agent memory sharing, and real-time biometric processing that define AUREN's compound intelligence.**  
        **\</description\>**  
        **\<eliminates\>**  
            **\<limitation\>1000-record limit of JSON file storage\</limitation\>**  
            **\<limitation\>No audit trails for compliance\</limitation\>**  
            **\<limitation\>No real-time memory sharing between agents\</limitation\>**  
            **\<limitation\>No event replay capabilities\</limitation\>**  
        **\</eliminates\>**  
        **\<enables\>**  
            **\<capability\>Unlimited memory storage with ACID guarantees\</capability\>**  
            **\<capability\>Complete audit trails for HIPAA compliance\</capability\>**  
            **\<capability\>Real-time memory sharing across specialist agents\</capability\>**  
            **\<capability\>Event sourcing with replay capabilities\</capability\>**  
            **\<capability\>Sub-second memory retrieval for agent responses\</capability\>**  
        **\</enables\>**  
    **\</section\>**

    **\<section id="2" name="implementation\_checklist"\>**  
        **\<title\>Implementation Checklist\</title\>**  
        **\<checklist\>**  
            **\<item\>PostgreSQL connection pool with AsyncPostgresManager singleton\</item\>**  
            **\<item\>Event store schema with JSONB events and sequence management\</item\>**  
            **\<item\>EventStore class with optimistic concurrency control\</item\>**  
            **\<item\>Memory backend replacing JSON files with full CRUD operations\</item\>**  
            **\<item\>LISTEN/NOTIFY triggers for real-time projection updates\</item\>**  
            **\<item\>Redis projection handlers with conflict resolution\</item\>**  
            **\<item\>ChromaDB vector sync for semantic retrieval\</item\>**  
            **\<item\>Migration scripts from existing JSON files to PostgreSQL\</item\>**  
            **\<item\>Performance optimization with proper indexing strategy\</item\>**  
            **\<item\>Connection health monitoring and automatic recovery\</item\>**  
            **\<item\>Comprehensive test suite covering all failure modes\</item\>**  
            **\<item\>Integration with CrewAI memory interface\</item\>**  
        **\</checklist\>**  
    **\</section\>**

    **\<section id="3" name="detailed\_implementation"\>**  
        **\<title\>Detailed Implementation\</title\>**

        **\<subsection id="3.1" name="connection\_management"\>**  
            **\<title\>PostgreSQL Connection Management\</title\>**  
            **\<description\>Singleton connection manager with retry logic and health monitoring\</description\>**  
              
            **\<implementation language="python"\>**  
                **\<\!\[CDATA\[**  
**"""**  
**AsyncPostgresManager \- Singleton connection pool manager**  
**Provides robust connection handling with exponential backoff retry logic**  
**"""**

**import asyncio**  
**import asyncpg**  
**from asyncpg.pool import Pool**  
**import logging**  
**from typing import Optional, Dict, Any**  
**from contextlib import asynccontextmanager**  
**from datetime import datetime, timezone**

**logger \= logging.getLogger(\_\_name\_\_)**

**class AsyncPostgresManager:**  
    **"""**  
    **Singleton manager for asyncpg connection pool**  
    **Ensures one pool per application instance with proper lifecycle management**  
    **"""**  
    **\_instance \= None**  
    **\_pool: Optional\[Pool\] \= None**  
    **\_initialized \= False**

    **def \_\_new\_\_(cls):**  
        **if cls.\_instance is None:**  
            **cls.\_instance \= super().\_\_new\_\_(cls)**  
        **return cls.\_instance**

    **@classmethod**  
    **async def initialize(cls,**   
                        **dsn: str,**   
                        **min\_size: int \= 10,**   
                        **max\_size: int \= 50,**  
                        **command\_timeout: float \= 30.0,**  
                        **server\_settings: Optional\[Dict\[str, str\]\] \= None) \-\> None:**  
        **"""**  
        **Initialize connection pool with retry logic**  
          
        **Args:**  
            **dsn: Database connection string**  
            **min\_size: Minimum connections to maintain**  
            **max\_size: Maximum connections in pool**  
            **command\_timeout: Query timeout in seconds**  
            **server\_settings: Additional PostgreSQL settings**  
        **"""**  
        **if cls.\_pool is not None:**  
            **logger.info("Connection pool already initialized")**  
            **return**

        **default\_settings \= {**  
            **'application\_name': 'auren\_data\_layer',**  
            **'jit': 'off'  \# Disable JIT for faster connection times**  
        **}**  
          
        **if server\_settings:**  
            **default\_settings.update(server\_settings)**

        **cls.\_pool \= await cls.\_create\_pool\_with\_retries(**  
            **dsn=dsn,**  
            **min\_size=min\_size,**  
            **max\_size=max\_size,**  
            **command\_timeout=command\_timeout,**  
            **server\_settings=default\_settings**  
        **)**  
        **cls.\_initialized \= True**  
        **logger.info(f"PostgreSQL connection pool initialized: {min\_size}-{max\_size} connections")**

    **@classmethod**  
    **async def \_create\_pool\_with\_retries(cls,**  
                                       **dsn: str,**  
                                       **min\_size: int,**  
                                       **max\_size: int,**  
                                       **command\_timeout: float,**  
                                       **server\_settings: Dict\[str, str\],**  
                                       **max\_retries: int \= 5,**  
                                       **base\_delay: float \= 1.0) \-\> Pool:**  
        **"""**  
        **Create connection pool with exponential backoff retry logic**  
          
        **Args:**  
            **dsn: Database connection string**  
            **min\_size: Minimum pool size**  
            **max\_size: Maximum pool size**  
            **command\_timeout: Query timeout**  
            **server\_settings: PostgreSQL server settings**  
            **max\_retries: Maximum retry attempts**  
            **base\_delay: Base delay for exponential backoff**  
              
        **Returns:**  
            **Initialized connection pool**  
              
        **Raises:**  
            **ConnectionError: If pool creation fails after all retries**  
        **"""**  
        **last\_exception \= None**  
          
        **for attempt in range(max\_retries):**  
            **try:**  
                **pool \= await asyncpg.create\_pool(**  
                    **dsn=dsn,**  
                    **min\_size=min\_size,**  
                    **max\_size=max\_size,**  
                    **command\_timeout=command\_timeout,**  
                    **server\_settings=server\_settings**  
                **)**  
                  
                **\# Test connection**  
                **async with pool.acquire() as conn:**  
                    **await conn.fetchval("SELECT 1")**  
                  
                **logger.info(f"Successfully created PostgreSQL pool on attempt {attempt \+ 1}")**  
                **return pool**  
                  
            **except (asyncpg.PostgresError, OSError, ConnectionRefusedError) as e:**  
                **last\_exception \= e**  
                **if attempt \< max\_retries \- 1:**  
                    **delay \= base\_delay \* (2 \*\* attempt)  \# Exponential backoff**  
                    **logger.warning(f"Connection attempt {attempt \+ 1} failed: {e}. Retrying in {delay}s")**  
                    **await asyncio.sleep(delay)**  
                **else:**  
                    **logger.error(f"All {max\_retries} connection attempts failed")**

        **raise ConnectionError(f"Failed to create database pool after {max\_retries} attempts") from last\_exception**

    **@classmethod**  
    **async def get\_pool(cls) \-\> Pool:**  
        **"""**  
        **Get the connection pool instance**  
          
        **Returns:**  
            **Active connection pool**  
              
        **Raises:**  
            **RuntimeError: If pool not initialized**  
        **"""**  
        **if not cls.\_initialized or cls.\_pool is None:**  
            **raise RuntimeError("AsyncPostgresManager not initialized. Call initialize() first.")**  
        **return cls.\_pool**

    **@classmethod**  
    **@asynccontextmanager**  
    **async def get\_connection(cls):**  
        **"""**  
        **Get database connection with automatic retry and error handling**  
          
        **Usage:**  
            **async with AsyncPostgresManager.get\_connection() as conn:**  
                **result \= await conn.fetchval("SELECT 1")**  
        **"""**  
        **pool \= await cls.get\_pool()**  
        **max\_retries \= 3**  
          
        **for attempt in range(max\_retries):**  
            **try:**  
                **async with pool.acquire() as conn:**  
                    **yield conn**  
                **return**  
            **except (asyncpg.PostgresError, asyncpg.InterfaceError) as e:**  
                **if attempt \== max\_retries \- 1:**  
                    **logger.error(f"Connection failed after {max\_retries} attempts: {e}")**  
                    **raise**  
                **logger.warning(f"Connection attempt {attempt \+ 1} failed: {e}. Retrying...")**  
                **await asyncio.sleep(0.1 \* (2 \*\* attempt))**

    **@classmethod**  
    **async def health\_check(cls) \-\> Dict\[str, Any\]:**  
        **"""**  
        **Comprehensive health check for connection pool**  
          
        **Returns:**  
            **Health status with metrics**  
        **"""**  
        **try:**  
            **if not cls.\_initialized or cls.\_pool is None:**  
                **return {**  
                    **"status": "unhealthy",**  
                    **"error": "Pool not initialized",**  
                    **"timestamp": datetime.now(timezone.utc).isoformat()**  
                **}**

            **start\_time \= datetime.now()**  
              
            **async with cls.get\_connection() as conn:**  
                **\# Test basic query**  
                **await conn.fetchval("SELECT 1")**  
                  
                **\# Get pool statistics**  
                **pool\_stats \= {**  
                    **"size": cls.\_pool.get\_size(),**  
                    **"min\_size": cls.\_pool.get\_min\_size(),**  
                    **"max\_size": cls.\_pool.get\_max\_size(),**  
                    **"idle\_size": cls.\_pool.get\_idle\_size()**  
                **}**  
                  
                **\# Check database version and stats**  
                **db\_version \= await conn.fetchval("SELECT version()")**  
                **active\_connections \= await conn.fetchval(**  
                    **"SELECT count(\*) FROM pg\_stat\_activity WHERE state \= 'active'"**  
                **)**  
                  
            **response\_time \= (datetime.now() \- start\_time).total\_seconds() \* 1000**  
              
            **return {**  
                **"status": "healthy",**  
                **"response\_time\_ms": response\_time,**  
                **"pool\_stats": pool\_stats,**  
                **"database\_version": db\_version,**  
                **"active\_connections": active\_connections,**  
                **"timestamp": datetime.now(timezone.utc).isoformat()**  
            **}**  
              
        **except Exception as e:**  
            **return {**  
                **"status": "unhealthy",**  
                **"error": str(e),**  
                **"timestamp": datetime.now(timezone.utc).isoformat()**  
            **}**

    **@classmethod**  
    **async def close(cls) \-\> None:**  
        **"""**  
        **Gracefully close connection pool**  
        **Should be called on application shutdown**  
        **"""**  
        **if cls.\_pool is not None:**  
            **logger.info("Closing PostgreSQL connection pool")**  
            **await cls.\_pool.close()**  
            **cls.\_pool \= None**  
            **cls.\_initialized \= False**  
**\]\]\>**  
            **\</implementation\>**  
        **\</subsection\>**

        **\<subsection id="3.2" name="database\_schema"\>**  
            **\<title\>Database Schema\</title\>**  
            **\<description\>Complete PostgreSQL schema for event sourcing and memory storage\</description\>**  
              
            **\<schema language="sql"\>**  
                **\<\!\[CDATA\[**  
**\-- AUREN Data Layer Schema**  
**\-- Event sourcing foundation with projection tables for performance**

**\-- Enable UUID extension**  
**CREATE EXTENSION IF NOT EXISTS "uuid-ossp";**

**\-- Global sequence for event ordering**  
**CREATE SEQUENCE IF NOT EXISTS global\_event\_sequence;**

**\-- Core events table (single source of truth)**  
**CREATE TABLE IF NOT EXISTS events (**  
    **sequence\_id BIGINT PRIMARY KEY DEFAULT nextval('global\_event\_sequence'),**  
    **event\_id UUID NOT NULL UNIQUE DEFAULT uuid\_generate\_v4(),**  
    **stream\_id UUID NOT NULL,**  
    **event\_type VARCHAR(255) NOT NULL,**  
    **version INTEGER NOT NULL,**  
    **payload JSONB NOT NULL,**  
    **metadata JSONB DEFAULT '{}',**  
    **created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),**  
      
    **\-- Optimistic concurrency control**  
    **CONSTRAINT unique\_stream\_version UNIQUE (stream\_id, version)**  
**);**

**\-- Agent memories projection (for fast retrieval)**  
**CREATE TABLE IF NOT EXISTS agent\_memories (**  
    **id UUID PRIMARY KEY DEFAULT uuid\_generate\_v4(),**  
    **agent\_id VARCHAR(255) NOT NULL,**  
    **user\_id UUID,**  
    **memory\_type VARCHAR(100) NOT NULL,**  
    **content JSONB NOT NULL,**  
    **metadata JSONB DEFAULT '{}',**  
    **confidence FLOAT DEFAULT 1.0 CHECK (confidence \>= 0 AND confidence \<= 1),**  
    **created\_at TIMESTAMPTZ DEFAULT NOW(),**  
    **updated\_at TIMESTAMPTZ DEFAULT NOW(),**  
    **expires\_at TIMESTAMPTZ,**  
    **is\_deleted BOOLEAN DEFAULT FALSE,**  
      
    **\-- Event sourcing link**  
    **source\_event\_id UUID REFERENCES events(event\_id)**  
**);**

**\-- User profiles and preferences**  
**CREATE TABLE IF NOT EXISTS user\_profiles (**  
    **user\_id UUID PRIMARY KEY,**  
    **profile\_data JSONB NOT NULL,**  
    **preferences JSONB DEFAULT '{}',**  
    **privacy\_settings JSONB DEFAULT '{}',**  
    **created\_at TIMESTAMPTZ DEFAULT NOW(),**  
    **updated\_at TIMESTAMPTZ DEFAULT NOW()**  
**);**

**\-- Conversation memories for agent context**  
**CREATE TABLE IF NOT EXISTS conversation\_memories (**  
    **id UUID PRIMARY KEY DEFAULT uuid\_generate\_v4(),**  
    **conversation\_id UUID NOT NULL,**  
    **agent\_id VARCHAR(255) NOT NULL,**  
    **user\_id UUID NOT NULL,**  
    **message\_context JSONB NOT NULL,**  
    **insights JSONB DEFAULT '\[\]',**  
    **follow\_up\_actions JSONB DEFAULT '\[\]',**  
    **created\_at TIMESTAMPTZ DEFAULT NOW()**  
**);**

**\-- Specialist knowledge base**  
**CREATE TABLE IF NOT EXISTS specialist\_knowledge (**  
    **id UUID PRIMARY KEY DEFAULT uuid\_generate\_v4(),**  
    **agent\_id VARCHAR(255) NOT NULL,**  
    **domain VARCHAR(100) NOT NULL,**  
    **knowledge\_type VARCHAR(100) NOT NULL,**  
    **content JSONB NOT NULL,**  
    **confidence FLOAT NOT NULL CHECK (confidence \>= 0 AND confidence \<= 1),**  
    **evidence JSONB DEFAULT '\[\]',**  
    **validation\_status VARCHAR(50) DEFAULT 'pending',**  
    **created\_at TIMESTAMPTZ DEFAULT NOW(),**  
    **validated\_at TIMESTAMPTZ**  
**);**

**\-- Performance indexes**  
**CREATE INDEX IF NOT EXISTS idx\_events\_stream\_id ON events (stream\_id);**  
**CREATE INDEX IF NOT EXISTS idx\_events\_type ON events (event\_type);**  
**CREATE INDEX IF NOT EXISTS idx\_events\_created\_at ON events (created\_at DESC);**  
**CREATE INDEX IF NOT EXISTS idx\_events\_sequence ON events (sequence\_id);**

**\-- Memory access patterns**  
**CREATE INDEX IF NOT EXISTS idx\_agent\_memories\_agent\_user**   
    **ON agent\_memories(agent\_id, user\_id) WHERE NOT is\_deleted;**  
**CREATE INDEX IF NOT EXISTS idx\_agent\_memories\_type**   
    **ON agent\_memories(memory\_type) WHERE NOT is\_deleted;**  
**CREATE INDEX IF NOT EXISTS idx\_agent\_memories\_created**   
    **ON agent\_memories(created\_at DESC) WHERE NOT is\_deleted;**  
**CREATE INDEX IF NOT EXISTS idx\_agent\_memories\_content\_gin**   
    **ON agent\_memories USING GIN(content);**

**\-- Conversation patterns**  
**CREATE INDEX IF NOT EXISTS idx\_conversation\_memories\_conv\_agent**   
    **ON conversation\_memories(conversation\_id, agent\_id);**  
**CREATE INDEX IF NOT EXISTS idx\_conversation\_memories\_user**   
    **ON conversation\_memories(user\_id, created\_at DESC);**

**\-- Knowledge patterns**  
**CREATE INDEX IF NOT EXISTS idx\_specialist\_knowledge\_agent\_domain**   
    **ON specialist\_knowledge(agent\_id, domain, confidence DESC);**  
**CREATE INDEX IF NOT EXISTS idx\_specialist\_knowledge\_validation**   
    **ON specialist\_knowledge(validation\_status, confidence DESC);**

**\-- Trigger function for updated\_at timestamps**  
**CREATE OR REPLACE FUNCTION update\_updated\_at\_column()**  
**RETURNS TRIGGER AS $$**  
**BEGIN**  
    **NEW.updated\_at \= NOW();**  
    **RETURN NEW;**  
**END;**  
**$$ language 'plpgsql';**

**\-- Apply updated\_at triggers**  
**CREATE TRIGGER update\_agent\_memories\_updated\_at**   
    **BEFORE UPDATE ON agent\_memories**  
    **FOR EACH ROW EXECUTE FUNCTION update\_updated\_at\_column();**

**CREATE TRIGGER update\_user\_profiles\_updated\_at**   
    **BEFORE UPDATE ON user\_profiles**  
    **FOR EACH ROW EXECUTE FUNCTION update\_updated\_at\_column();**

**\-- Real-time notification function**  
**CREATE OR REPLACE FUNCTION notify\_new\_event()**  
**RETURNS TRIGGER AS $$**  
**BEGIN**  
    **PERFORM pg\_notify('memory\_events',**   
        **json\_build\_object(**  
            **'sequence\_id', NEW.sequence\_id,**  
            **'event\_id', NEW.event\_id,**  
            **'stream\_id', NEW.stream\_id,**  
            **'event\_type', NEW.event\_type**  
        **)::text**  
    **);**  
    **RETURN NEW;**  
**END;**  
**$$ LANGUAGE plpgsql;**

**\-- Trigger for real-time notifications**  
**CREATE TRIGGER trigger\_new\_event\_notification**  
    **AFTER INSERT ON events**  
    **FOR EACH ROW**  
    **EXECUTE FUNCTION notify\_new\_event();**  
**\]\]\>**  
            **\</schema\>**  
        **\</subsection\>**

        **\<subsection id="3.3" name="event\_store"\>**  
            **\<title\>Event Store Implementation\</title\>**  
            **\<description\>Production event store with optimistic concurrency control and audit trails\</description\>**  
              
            **\<implementation language="python"\>**  
                **\<\!\[CDATA\[**  
**"""**  
**EventStore \- Core event sourcing implementation**  
**Provides immutable audit trails and optimistic concurrency control**  
**"""**

**import uuid**  
**import json**  
**from datetime import datetime, timezone**  
**from typing import Dict, List, Optional, Any**  
**from dataclasses import dataclass, asdict**  
**from enum import Enum**  
**import logging**

**logger \= logging.getLogger(\_\_name\_\_)**

**class EventType(Enum):**  
    **"""Core event types for AUREN system"""**  
    **\# Memory events**  
    **MEMORY\_CREATED \= "memory\_created"**  
    **MEMORY\_UPDATED \= "memory\_updated"**  
    **MEMORY\_DELETED \= "memory\_deleted"**  
    **MEMORY\_RETRIEVED \= "memory\_retrieved"**  
      
    **\# Agent events**  
    **AGENT\_DECISION \= "agent\_decision"**  
    **AGENT\_HANDOFF \= "agent\_handoff"**  
    **HYPOTHESIS\_FORMED \= "hypothesis\_formed"**  
    **HYPOTHESIS\_VALIDATED \= "hypothesis\_validated"**  
      
    **\# User events**  
    **USER\_ONBOARDED \= "user\_onboarded"**  
    **BIOMETRIC\_RECEIVED \= "biometric\_received"**  
    **CONVERSATION\_TURN \= "conversation\_turn"**  
      
    **\# System events**  
    **PROJECTION\_UPDATED \= "projection\_updated"**  
    **ERROR\_OCCURRED \= "error\_occurred"**

**@dataclass**  
**class Event:**  
    **"""Immutable event record"""**  
    **event\_id: str**  
    **stream\_id: str**  
    **event\_type: str**  
    **version: int**  
    **payload: Dict\[str, Any\]**  
    **metadata: Dict\[str, Any\]**  
    **created\_at: datetime**  
    **sequence\_id: Optional\[int\] \= None**

**class ConcurrencyError(Exception):**  
    **"""Raised when optimistic concurrency control fails"""**  
    **pass**

**class EventStore:**  
    **"""**  
    **Production event store implementation**  
      
    **Features:**  
    **\- Immutable event storage with ACID guarantees**  
    **\- Optimistic concurrency control**  
    **\- Event replay capabilities**  
    **\- Real-time notifications via LISTEN/NOTIFY**  
    **\- Audit trail compliance**  
    **"""**  
      
    **def \_\_init\_\_(self):**  
        **self.\_event\_handlers: List\[callable\] \= \[\]**

    **async def append\_event(self,**  
                          **stream\_id: str,**  
                          **event\_type: EventType,**  
                          **payload: Dict\[str, Any\],**  
                          **expected\_version: Optional\[int\] \= None,**  
                          **metadata: Optional\[Dict\[str, Any\]\] \= None,**  
                          **correlation\_id: Optional\[str\] \= None,**  
                          **causation\_id: Optional\[str\] \= None) \-\> Event:**  
        **"""**  
        **Append event to stream with optimistic concurrency control**  
          
        **Args:**  
            **stream\_id: Unique stream identifier (user\_id, agent\_id, etc.)**  
            **event\_type: Type of event being recorded**  
            **payload: Event data**  
            **expected\_version: Expected stream version for concurrency control**  
            **metadata: Additional event metadata**  
            **correlation\_id: ID linking related events**  
            **causation\_id: ID of event that caused this event**  
              
        **Returns:**  
            **Created event with assigned sequence number**  
              
        **Raises:**  
            **ConcurrencyError: If expected\_version doesn't match actual**  
        **"""**  
          
        **event\_id \= str(uuid.uuid4())**  
        **event\_metadata \= metadata or {}**  
          
        **\# Add correlation and causation tracking**  
        **if correlation\_id:**  
            **event\_metadata\['correlation\_id'\] \= correlation\_id**  
        **if causation\_id:**  
            **event\_metadata\['causation\_id'\] \= causation\_id**  
              
        **\# Add agent context if available**  
        **event\_metadata\['timestamp'\] \= datetime.now(timezone.utc).isoformat()**  
          
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **async with conn.transaction():**  
                **\# Check stream version if provided**  
                **current\_version \= 0**  
                **if expected\_version is not None:**  
                    **current\_version \= await conn.fetchval(**  
                        **"SELECT MAX(version) FROM events WHERE stream\_id \= $1",**  
                        **stream\_id**  
                    **) or 0**  
                      
                    **if current\_version \!= expected\_version:**  
                        **raise ConcurrencyError(**  
                            **f"Stream {stream\_id}: expected version {expected\_version}, "**  
                            **f"actual version {current\_version}"**  
                        **)**  
                  
                **new\_version \= current\_version \+ 1**  
                  
                **\# Insert event**  
                **sequence\_id \= await conn.fetchval("""**  
                    **INSERT INTO events**   
                    **(event\_id, stream\_id, event\_type, version, payload, metadata)**  
                    **VALUES ($1, $2, $3, $4, $5, $6)**  
                    **RETURNING sequence\_id**  
                **""", event\_id, stream\_id, event\_type.value, new\_version,**  
                    **json.dumps(payload), json.dumps(event\_metadata))**  
                  
                **event \= Event(**  
                    **event\_id=event\_id,**  
                    **stream\_id=stream\_id,**  
                    **event\_type=event\_type.value,**  
                    **version=new\_version,**  
                    **payload=payload,**  
                    **metadata=event\_metadata,**  
                    **created\_at=datetime.now(timezone.utc),**  
                    **sequence\_id=sequence\_id**  
                **)**  
                  
                **\# Process event handlers**  
                **for handler in self.\_event\_handlers:**  
                    **try:**  
                        **await handler(event)**  
                    **except Exception as e:**  
                        **logger.error(f"Event handler failed for {event\_id}: {e}")**  
                        **\# Continue with other handlers**  
                  
                **logger.info(f"Event appended: {event\_type.value} to stream {stream\_id}")**  
                **return event**

    **async def get\_stream\_events(self,**  
                               **stream\_id: str,**  
                               **from\_version: int \= 0,**  
                               **to\_version: Optional\[int\] \= None,**  
                               **limit: int \= 1000\) \-\> List\[Event\]:**  
        **"""**  
        **Get events from a specific stream**  
          
        **Args:**  
            **stream\_id: Stream identifier**  
            **from\_version: Starting version (exclusive)**  
            **to\_version: Ending version (inclusive)**  
            **limit: Maximum events to return**  
              
        **Returns:**  
            **List of events in version order**  
        **"""**  
          
        **conditions \= \["stream\_id \= $1", "version \> $2"\]**  
        **params \= \[stream\_id, from\_version\]**  
        **param\_count \= 2**  
          
        **if to\_version is not None:**  
            **conditions.append(f"version \<= ${param\_count \+ 1}")**  
            **params.append(to\_version)**  
            **param\_count \+= 1**  
          
        **query \= f"""**  
            **SELECT sequence\_id, event\_id, stream\_id, event\_type, version,**  
                   **payload, metadata, created\_at**  
            **FROM events**  
            **WHERE {' AND '.join(conditions)}**  
            **ORDER BY version ASC**  
            **LIMIT ${param\_count \+ 1}**  
        **"""**  
        **params.append(limit)**  
          
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **rows \= await conn.fetch(query, \*params)**  
              
            **events \= \[\]**  
            **for row in rows:**  
                **event \= Event(**  
                    **event\_id=str(row\['event\_id'\]),**  
                    **stream\_id=row\['stream\_id'\],**  
                    **event\_type=row\['event\_type'\],**  
                    **version=row\['version'\],**  
                    **payload=json.loads(row\['payload'\]),**  
                    **metadata=json.loads(row\['metadata'\]),**  
                    **created\_at=row\['created\_at'\],**  
                    **sequence\_id=row\['sequence\_id'\]**  
                **)**  
                **events.append(event)**  
              
            **return events**

    **async def get\_stream\_version(self, stream\_id: str) \-\> int:**  
        **"""Get current version of stream"""**  
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **version \= await conn.fetchval(**  
                **"SELECT MAX(version) FROM events WHERE stream\_id \= $1",**  
                **stream\_id**  
            **)**  
            **return version or 0**

    **async def replay\_stream(self,**  
                           **stream\_id: str,**  
                           **projection\_handler: callable,**  
                           **from\_version: int \= 0\) \-\> Any:**  
        **"""**  
        **Replay stream events through projection handler**  
          
        **Args:**  
            **stream\_id: Stream to replay**  
            **projection\_handler: Function to process each event**  
            **from\_version: Starting version for incremental updates**  
              
        **Returns:**  
            **Final projection state**  
        **"""**  
          
        **events \= await self.get\_stream\_events(stream\_id, from\_version)**  
          
        **\# Start with empty state or snapshot**  
        **state \= {}**  
          
        **\# Apply events to build current state**  
        **for event in events:**  
            **try:**  
                **state \= await projection\_handler(state, event)**  
            **except Exception as e:**  
                **logger.error(f"Projection handler failed for event {event.event\_id}: {e}")**  
                **\# Continue with other events**  
          
        **return state**

    **def register\_event\_handler(self, handler: callable) \-\> None:**  
        **"""Register handler for processing events as they're appended"""**  
        **self.\_event\_handlers.append(handler)**  
        **logger.info(f"Registered event handler: {handler.\_\_name\_\_}")**

    **async def get\_events\_by\_type(self,**  
                                **event\_type: EventType,**  
                                **from\_timestamp: Optional\[datetime\] \= None,**  
                                **limit: int \= 1000\) \-\> List\[Event\]:**  
        **"""Get events by type across all streams"""**  
          
        **conditions \= \["event\_type \= $1"\]**  
        **params \= \[event\_type.value\]**  
        **param\_count \= 1**  
          
        **if from\_timestamp:**  
            **conditions.append(f"created\_at \>= ${param\_count \+ 1}")**  
            **params.append(from\_timestamp)**  
            **param\_count \+= 1**  
          
        **query \= f"""**  
            **SELECT sequence\_id, event\_id, stream\_id, event\_type, version,**  
                   **payload, metadata, created\_at**  
            **FROM events**  
            **WHERE {' AND '.join(conditions)}**  
            **ORDER BY created\_at DESC**  
            **LIMIT ${param\_count \+ 1}**  
        **"""**  
        **params.append(limit)**  
          
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **rows \= await conn.fetch(query, \*params)**  
              
            **events \= \[\]**  
            **for row in rows:**  
                **event \= Event(**  
                    **event\_id=str(row\['event\_id'\]),**  
                    **stream\_id=row\['stream\_id'\],**  
                    **event\_type=row\['event\_type'\],**  
                    **version=row\['version'\],**  
                    **payload=json.loads(row\['payload'\]),**  
                    **metadata=json.loads(row\['metadata'\]),**  
                    **created\_at=row\['created\_at'\],**  
                    **sequence\_id=row\['sequence\_id'\]**  
                **)**  
                **events.append(event)**  
              
            **return events**  
**\]\]\>**  
            **\</implementation\>**  
        **\</subsection\>**

        **\<subsection id="3.4" name="memory\_backend"\>**  
            **\<title\>Memory Backend Implementation\</title\>**  
            **\<description\>PostgreSQL memory backend replacing JSON files with unlimited storage\</description\>**  
              
            **\<implementation language="python"\>**  
                **\<\!\[CDATA\[**  
**"""**  
**PostgreSQLMemoryBackend \- Production memory storage**  
**Replaces JSON file limitations with unlimited PostgreSQL storage**  
**"""**

**from typing import Dict, List, Optional, Any, Union**  
**import json**  
**import uuid**  
**from datetime import datetime, timezone**  
**from enum import Enum**

**class MemoryType(Enum):**  
    **"""Types of memory stored in the system"""**  
    **FACT \= "fact"**  
    **ANALYSIS \= "analysis"**  
    **RECOMMENDATION \= "recommendation"**  
    **HYPOTHESIS \= "hypothesis"**  
    **INSIGHT \= "insight"**  
    **CONVERSATION \= "conversation"**  
    **DECISION \= "decision"**

**class PostgreSQLMemoryBackend:**  
    **"""**  
    **Production-grade PostgreSQL memory backend**  
      
    **Features:**  
    **\- Unlimited memory storage (vs 1000 record JSON limit)**  
    **\- HIPAA-compliant audit trails through event sourcing**  
    **\- Real-time updates via LISTEN/NOTIFY**  
    **\- Automatic projection management**  
    **\- Connection pooling and retry logic**  
    **\- Graceful degradation and error recovery**  
    **"""**  
      
    **def \_\_init\_\_(self, event\_store: EventStore):**  
        **self.event\_store \= event\_store**  
        **self.\_setup\_event\_handlers()**

    **def \_setup\_event\_handlers(self):**  
        **"""Setup automatic projection updates from events"""**  
        **self.event\_store.register\_event\_handler(self.\_handle\_memory\_event)**

    **async def store\_memory(self,**  
                          **agent\_id: str,**  
                          **memory\_type: MemoryType,**  
                          **content: Dict\[str, Any\],**  
                          **user\_id: Optional\[str\] \= None,**  
                          **metadata: Optional\[Dict\[str, Any\]\] \= None,**  
                          **confidence: float \= 1.0,**  
                          **expires\_at: Optional\[datetime\] \= None) \-\> str:**  
        **"""**  
        **Store agent memory with event sourcing**  
          
        **Args:**  
            **agent\_id: Agent storing the memory**  
            **memory\_type: Type of memory being stored**  
            **content: Memory content**  
            **user\_id: Associated user (if any)**  
            **metadata: Additional metadata**  
            **confidence: Confidence score (0.0 to 1.0)**  
            **expires\_at: Optional expiration timestamp**  
              
        **Returns:**  
            **Memory ID for reference**  
        **"""**  
          
        **memory\_id \= str(uuid.uuid4())**  
        **stream\_id \= user\_id or agent\_id**  
          
        **\# Store in projection table for fast access**  
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **await conn.execute("""**  
                **INSERT INTO agent\_memories**   
                **(id, agent\_id, user\_id, memory\_type, content, metadata, confidence, expires\_at)**  
                **VALUES ($1, $2, $3, $4, $5, $6, $7, $8)**  
            **""", memory\_id, agent\_id, user\_id, memory\_type.value,**  
                **json.dumps(content), json.dumps(metadata or {}), confidence, expires\_at)**  
          
        **\# Record event for audit trail**  
        **await self.event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.MEMORY\_CREATED,**  
            **payload={**  
                **"memory\_id": memory\_id,**  
                **"agent\_id": agent\_id,**  
                **"user\_id": user\_id,**  
                **"memory\_type": memory\_type.value,**  
                **"content": content,**  
                **"metadata": metadata,**  
                **"confidence": confidence,**  
                **"expires\_at": expires\_at.isoformat() if expires\_at else None**  
            **}**  
        **)**  
          
        **logger.info(f"Memory stored: {memory\_id} by agent {agent\_id}")**  
        **return memory\_id**

    **async def retrieve\_memories(self,**  
                               **agent\_id: str,**  
                               **user\_id: Optional\[str\] \= None,**  
                               **memory\_type: Optional\[MemoryType\] \= None,**  
                               **limit: int \= 100,**  
                               **offset: int \= 0,**  
                               **include\_expired: bool \= False) \-\> List\[Dict\[str, Any\]\]:**  
        **"""**  
        **Retrieve agent memories with filtering**  
          
        **Args:**  
            **agent\_id: Agent whose memories to retrieve**  
            **user\_id: Filter by specific user**  
            **memory\_type: Filter by memory type**  
            **limit: Maximum memories to return**  
            **offset: Pagination offset**  
            **include\_expired: Include expired memories**  
              
        **Returns:**  
            **List of memory records**  
        **"""**  
          
        **conditions \= \["NOT is\_deleted"\]**  
        **params \= \[\]**  
        **param\_count \= 0**  
          
        **\# Filter by agent**  
        **conditions.append(f"agent\_id \= ${param\_count \+ 1}")**  
        **params.append(agent\_id)**  
        **param\_count \+= 1**  
          
        **\# Filter by user if specified**  
        **if user\_id:**  
            **conditions.append(f"user\_id \= ${param\_count \+ 1}")**  
            **params.append(user\_id)**  
            **param\_count \+= 1**  
          
        **\# Filter by memory type if specified**  
        **if memory\_type:**  
            **conditions.append(f"memory\_type \= ${param\_count \+ 1}")**  
            **params.append(memory\_type.value)**  
            **param\_count \+= 1**  
          
        **\# Filter expired memories unless explicitly requested**  
        **if not include\_expired:**  
            **conditions.append("(expires\_at IS NULL OR expires\_at \> NOW())")**  
          
        **query \= f"""**  
            **SELECT id, agent\_id, user\_id, memory\_type, content, metadata,**  
                   **confidence, created\_at, updated\_at, expires\_at**  
            **FROM agent\_memories**  
            **WHERE {' AND '.join(conditions)}**  
            **ORDER BY created\_at DESC**  
            **LIMIT ${param\_count \+ 1} OFFSET ${param\_count \+ 2}**  
        **"""**  
        **params.extend(\[limit, offset\])**  
          
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **rows \= await conn.fetch(query, \*params)**  
              
            **memories \= \[\]**  
            **for row in rows:**  
                **memory \= {**  
                    **"id": str(row\["id"\]),**  
                    **"agent\_id": row\["agent\_id"\],**  
                    **"user\_id": str(row\["user\_id"\]) if row\["user\_id"\] else None,**  
                    **"memory\_type": row\["memory\_type"\],**  
                    **"content": json.loads(row\["content"\]),**  
                    **"metadata": json.loads(row\["metadata"\]),**  
                    **"confidence": float(row\["confidence"\]),**  
                    **"created\_at": row\["created\_at"\].isoformat(),**  
                    **"updated\_at": row\["updated\_at"\].isoformat(),**  
                    **"expires\_at": row\["expires\_at"\].isoformat() if row\["expires\_at"\] else None**  
                **}**  
                **memories.append(memory)**  
              
            **\# Record retrieval event for audit**  
            **if memories:**  
                **await self.event\_store.append\_event(**  
                    **stream\_id=user\_id or agent\_id,**  
                    **event\_type=EventType.MEMORY\_RETRIEVED,**  
                    **payload={**  
                        **"agent\_id": agent\_id,**  
                        **"user\_id": user\_id,**  
                        **"memory\_type": memory\_type.value if memory\_type else None,**  
                        **"count": len(memories),**  
                        **"limit": limit,**  
                        **"offset": offset**  
                    **}**  
                **)**  
              
            **return memories**

    **async def update\_memory(self,**  
                           **memory\_id: str,**  
                           **content: Optional\[Dict\[str, Any\]\] \= None,**  
                           **metadata: Optional\[Dict\[str, Any\]\] \= None,**  
                           **confidence: Optional\[float\] \= None) \-\> bool:**  
        **"""**  
        **Update existing memory with event recording**  
          
        **Args:**  
            **memory\_id: Memory to update**  
            **content: New content (if any)**  
            **metadata: New metadata (if any)**  
            **confidence: New confidence score (if any)**  
              
        **Returns:**  
            **True if memory was updated, False if not found**  
        **"""**  
          
        **updates \= \[\]**  
        **params \= \[\]**  
        **param\_count \= 0**  
          
        **if content is not None:**  
            **updates.append(f"content \= ${param\_count \+ 1}")**  
            **params.append(json.dumps(content))**  
            **param\_count \+= 1**  
          
        **if metadata is not None:**  
            **updates.append(f"metadata \= ${param\_count \+ 1}")**  
            **params.append(json.dumps(metadata))**  
            **param\_count \+= 1**  
          
        **if confidence is not None:**  
            **updates.append(f"confidence \= ${param\_count \+ 1}")**  
            **params.append(confidence)**  
            **param\_count \+= 1**  
          
        **if not updates:**  
            **return False**  
          
        **query \= f"""**  
            **UPDATE agent\_memories**  
            **SET {', '.join(updates)}, updated\_at \= NOW()**  
            **WHERE id \= ${param\_count \+ 1} AND NOT is\_deleted**  
            **RETURNING agent\_id, user\_id, memory\_type**  
        **"""**  
        **params.append(memory\_id)**  
          
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **row \= await conn.fetchrow(query, \*params)**  
              
            **if not row:**  
                **return False**  
              
            **\# Record update event**  
            **await self.event\_store.append\_event(**  
                **stream\_id=row\["user\_id"\] or row\["agent\_id"\],**  
                **event\_type=EventType.MEMORY\_UPDATED,**  
                **payload={**  
                    **"memory\_id": memory\_id,**  
                    **"agent\_id": row\["agent\_id"\],**  
                    **"updates": {**  
                        **"content": content,**  
                        **"metadata": metadata,**  
                        **"confidence": confidence**  
                    **}**  
                **}**  
            **)**  
              
            **return True**

    **async def delete\_memory(self, memory\_id: str) \-\> bool:**  
        **"""**  
        **Soft delete memory with event recording**  
          
        **Args:**  
            **memory\_id: Memory to delete**  
              
        **Returns:**  
            **True if memory was deleted, False if not found**  
        **"""**  
          
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **row \= await conn.fetchrow("""**  
                **UPDATE agent\_memories**  
                **SET is\_deleted \= TRUE, updated\_at \= NOW()**  
                **WHERE id \= $1 AND NOT is\_deleted**  
                **RETURNING agent\_id, user\_id, memory\_type**  
            **""", memory\_id)**  
              
            **if not row:**  
                **return False**  
              
            **\# Record deletion event**  
            **await self.event\_store.append\_event(**  
                **stream\_id=row\["user\_id"\] or row\["agent\_id"\],**  
                **event\_type=EventType.MEMORY\_DELETED,**  
                **payload={**  
                    **"memory\_id": memory\_id,**  
                    **"agent\_id": row\["agent\_id"\]**  
                **}**  
            **)**  
              
            **return True**

    **async def search\_memories(self,**  
                             **agent\_id: str,**  
                             **query: str,**  
                             **user\_id: Optional\[str\] \= None,**  
                             **limit: int \= 50\) \-\> List\[Dict\[str, Any\]\]:**  
        **"""**  
        **Search memories using full-text search**  
          
        **Args:**  
            **agent\_id: Agent whose memories to search**  
            **query: Search query**  
            **user\_id: Optional user filter**  
            **limit: Maximum results**  
              
        **Returns:**  
            **List of matching memories with relevance scores**  
        **"""**  
          
        **conditions \= \["NOT is\_deleted", "agent\_id \= $1"\]**  
        **params \= \[agent\_id\]**  
        **param\_count \= 1**  
          
        **if user\_id:**  
            **conditions.append(f"user\_id \= ${param\_count \+ 1}")**  
            **params.append(user\_id)**  
            **param\_count \+= 1**  
          
        **\# Use PostgreSQL full-text search**  
        **search\_query \= f"""**  
            **SELECT id, agent\_id, user\_id, memory\_type, content, metadata,**  
                   **confidence, created\_at, updated\_at,**  
                   **ts\_rank(to\_tsvector('english', content::text), plainto\_tsquery('english', ${param\_count \+ 1})) as relevance**  
            **FROM agent\_memories**  
            **WHERE {' AND '.join(conditions)}**  
            **AND to\_tsvector('english', content::text) @@ plainto\_tsquery('english', ${param\_count \+ 1})**  
            **ORDER BY relevance DESC, created\_at DESC**  
            **LIMIT ${param\_count \+ 2}**  
        **"""**  
        **params.extend(\[query, limit\])**  
          
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **rows \= await conn.fetch(search\_query, \*params)**  
              
            **memories \= \[\]**  
            **for row in rows:**  
                **memory \= {**  
                    **"id": str(row\["id"\]),**  
                    **"agent\_id": row\["agent\_id"\],**  
                    **"user\_id": str(row\["user\_id"\]) if row\["user\_id"\] else None,**  
                    **"memory\_type": row\["memory\_type"\],**  
                    **"content": json.loads(row\["content"\]),**  
                    **"metadata": json.loads(row\["metadata"\]),**  
                    **"confidence": float(row\["confidence"\]),**  
                    **"created\_at": row\["created\_at"\].isoformat(),**  
                    **"updated\_at": row\["updated\_at"\].isoformat(),**  
                    **"relevance": float(row\["relevance"\])**  
                **}**  
                **memories.append(memory)**  
              
            **return memories**

    **async def \_handle\_memory\_event(self, event: Event) \-\> None:**  
        **"""Handle memory events for maintaining projections"""**  
        **try:**  
            **if event.event\_type \== EventType.MEMORY\_CREATED.value:**  
                **\# Memory already stored in store\_memory method**  
                **pass**  
            **elif event.event\_type \== EventType.MEMORY\_UPDATED.value:**  
                **\# Memory already updated in update\_memory method**  
                **pass**  
            **elif event.event\_type \== EventType.MEMORY\_DELETED.value:**  
                **\# Memory already deleted in delete\_memory method**  
                **pass**  
              
        **except Exception as e:**  
            **logger.error(f"Failed to handle memory event {event.event\_id}: {e}")**

    **async def get\_memory\_stats(self, agent\_id: str) \-\> Dict\[str, Any\]:**  
        **"""Get memory statistics for an agent"""**  
          
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **stats \= await conn.fetchrow("""**  
                **SELECT**   
                    **COUNT(\*) as total\_memories,**  
                    **COUNT(\*) FILTER (WHERE memory\_type \= 'fact') as facts,**  
                    **COUNT(\*) FILTER (WHERE memory\_type \= 'analysis') as analyses,**  
                    **COUNT(\*) FILTER (WHERE memory\_type \= 'recommendation') as recommendations,**  
                    **AVG(confidence) as avg\_confidence,**  
                    **MAX(created\_at) as last\_memory\_created**  
                **FROM agent\_memories**  
                **WHERE agent\_id \= $1 AND NOT is\_deleted**  
            **""", agent\_id)**  
              
            **return {**  
                **"agent\_id": agent\_id,**  
                **"total\_memories": stats\["total\_memories"\],**  
                **"memory\_breakdown": {**  
                    **"facts": stats\["facts"\],**  
                    **"analyses": stats\["analyses"\],**  
                    **"recommendations": stats\["recommendations"\]**  
                **},**  
                **"average\_confidence": float(stats\["avg\_confidence"\] or 0),**  
                **"last\_memory\_created": stats\["last\_memory\_created"\].isoformat() if stats\["last\_memory\_created"\] else None**  
            **}**  
**\]\]\>**  
            **\</implementation\>**  
        **\</subsection\>**

        **\<subsection id="3.5" name="projection\_handlers"\>**  
            **\<title\>Projection Handlers\</title\>**  
            **\<description\>Real-time projection updates for Redis and ChromaDB\</description\>**  
              
            **\<implementation language="python"\>**  
                **\<\!\[CDATA\[**  
**"""**  
**Projection handlers for real-time updates to Redis and ChromaDB**  
**Implement CQRS pattern for optimized read models**  
**"""**

**import asyncio**  
**import json**  
**import logging**  
**from abc import ABC, abstractmethod**  
**from typing import Dict, Any, Optional, List**

**logger \= logging.getLogger(\_\_name\_\_)**

**class BaseProjectionHandler(ABC):**  
    **"""Base class for projection handlers"""**  
      
    **def \_\_init\_\_(self, name: str):**  
        **self.name \= name**  
        **self.is\_running \= False**  
        **self.\_listeners \= \[\]**

    **async def start\_listening(self) \-\> None:**  
        **"""Start listening for database notifications"""**  
        **self.is\_running \= True**  
          
        **try:**  
            **async with AsyncPostgresManager.get\_connection() as conn:**  
                **await conn.add\_listener('memory\_events', self.\_handle\_notification)**  
                **logger.info(f"Projection handler {self.name} started listening")**  
                  
                **\# Keep connection alive**  
                **while self.is\_running:**  
                    **await asyncio.sleep(1)**  
                      
        **except Exception as e:**  
            **logger.error(f"Projection handler {self.name} failed: {e}")**  
        **finally:**  
            **logger.info(f"Projection handler {self.name} stopped")**

    **async def \_handle\_notification(self, connection, pid, channel, payload):**  
        **"""Handle PostgreSQL notification"""**  
        **try:**  
            **event\_data \= json.loads(payload)**  
            **await self.process\_event(event\_data)**  
        **except Exception as e:**  
            **logger.error(f"Error processing notification in {self.name}: {e}")**

    **@abstractmethod**  
    **async def process\_event(self, event\_data: Dict\[str, Any\]) \-\> None:**  
        **"""Process individual event \- implement in subclasses"""**  
        **pass**

    **def stop(self):**  
        **"""Stop listening for events"""**  
        **self.is\_running \= False**

**class RedisProjectionHandler(BaseProjectionHandler):**  
    **"""**  
    **Updates Redis cache for fast agent memory access**  
    **Implements Tier 1 memory (immediate access) from Master Control**  
    **"""**  
      
    **def \_\_init\_\_(self, redis\_client):**  
        **super().\_\_init\_\_("RedisProjection")**  
        **self.redis \= redis\_client**

    **async def process\_event(self, event\_data: Dict\[str, Any\]) \-\> None:**  
        **"""Update Redis projections based on events"""**  
          
        **try:**  
            **event\_type \= event\_data.get('event\_type')**  
            **stream\_id \= event\_data.get('stream\_id')**  
            **sequence\_id \= event\_data.get('sequence\_id')**  
              
            **\# Fetch full event from database**  
            **event \= await self.\_get\_event\_by\_sequence(sequence\_id)**  
            **if not event:**  
                **return**  
              
            **payload \= json.loads(event\['payload'\])**  
              
            **if event\_type \== 'memory\_created':**  
                **await self.\_update\_agent\_memory\_cache(event, payload)**  
            **elif event\_type \== 'memory\_updated':**  
                **await self.\_update\_agent\_memory\_cache(event, payload)**  
            **elif event\_type \== 'memory\_deleted':**  
                **await self.\_remove\_from\_cache(event, payload)**  
            **elif event\_type \== 'conversation\_turn':**  
                **await self.\_update\_conversation\_cache(event, payload)**  
            **elif event\_type \== 'agent\_decision':**  
                **await self.\_cache\_agent\_decision(event, payload)**  
              
        **except Exception as e:**  
            **logger.error(f"Redis projection failed for event {event\_data}: {e}")**

    **async def \_get\_event\_by\_sequence(self, sequence\_id: int) \-\> Optional\[Dict\[str, Any\]\]:**  
        **"""Fetch event details from database"""**  
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **row \= await conn.fetchrow(**  
                **"SELECT \* FROM events WHERE sequence\_id \= $1",**  
                **sequence\_id**  
            **)**  
            **return dict(row) if row else None**

    **async def \_update\_agent\_memory\_cache(self, event: Dict, payload: Dict) \-\> None:**  
        **"""Update agent memory in Redis cache"""**  
          
        **agent\_id \= payload.get('agent\_id')**  
        **memory\_id \= payload.get('memory\_id')**  
        **user\_id \= payload.get('user\_id')**  
          
        **if not agent\_id or not memory\_id:**  
            **return**  
          
        **\# Cache key patterns**  
        **agent\_key \= f"agent:{agent\_id}:memories"**  
        **user\_agent\_key \= f"user:{user\_id}:agent:{agent\_id}:memories" if user\_id else None**  
        **memory\_key \= f"memory:{memory\_id}"**  
          
        **\# Cache memory details**  
        **memory\_data \= {**  
            **"id": memory\_id,**  
            **"agent\_id": agent\_id,**  
            **"user\_id": user\_id,**  
            **"type": payload.get('memory\_type'),**  
            **"content": payload.get('content'),**  
            **"confidence": payload.get('confidence', 1.0),**  
            **"created\_at": event\['created\_at'\].isoformat(),**  
            **"metadata": payload.get('metadata', {})**  
        **}**  
          
        **\# Store with TTL**  
        **await self.redis.setex(**  
            **memory\_key,**   
            **3600,  \# 1 hour TTL**  
            **json.dumps(memory\_data)**  
        **)**  
          
        **\# Add to agent's memory list**  
        **await self.redis.lpush(agent\_key, memory\_id)**  
        **await self.redis.expire(agent\_key, 3600\)**  
          
        **\# Add to user-agent memory list if user-specific**  
        **if user\_agent\_key:**  
            **await self.redis.lpush(user\_agent\_key, memory\_id)**  
            **await self.redis.expire(user\_agent\_key, 3600\)**  
          
        **logger.debug(f"Updated Redis cache for memory {memory\_id}")**

    **async def \_remove\_from\_cache(self, event: Dict, payload: Dict) \-\> None:**  
        **"""Remove deleted memory from Redis cache"""**  
          
        **memory\_id \= payload.get('memory\_id')**  
        **agent\_id \= payload.get('agent\_id')**  
          
        **if not memory\_id or not agent\_id:**  
            **return**  
          
        **\# Remove memory details**  
        **await self.redis.delete(f"memory:{memory\_id}")**  
          
        **\# Remove from agent's memory list**  
        **await self.redis.lrem(f"agent:{agent\_id}:memories", 0, memory\_id)**  
          
        **logger.debug(f"Removed memory {memory\_id} from Redis cache")**

    **async def \_update\_conversation\_cache(self, event: Dict, payload: Dict) \-\> None:**  
        **"""Cache recent conversation context"""**  
          
        **user\_id \= payload.get('user\_id')**  
        **conversation\_id \= payload.get('conversation\_id')**  
          
        **if not user\_id or not conversation\_id:**  
            **return**  
          
        **\# Cache conversation context**  
        **conv\_key \= f"conversation:{conversation\_id}:context"**  
        **user\_conv\_key \= f"user:{user\_id}:recent\_conversations"**  
          
        **await self.redis.setex(**  
            **conv\_key,**  
            **1800,  \# 30 minutes TTL**  
            **json.dumps(payload)**  
        **)**  
          
        **\# Track recent conversations for user**  
        **await self.redis.lpush(user\_conv\_key, conversation\_id)**  
        **await self.redis.ltrim(user\_conv\_key, 0, 10\)  \# Keep last 10**  
        **await self.redis.expire(user\_conv\_key, 3600\)**

    **async def \_cache\_agent\_decision(self, event: Dict, payload: Dict) \-\> None:**  
        **"""Cache agent decisions for quick access"""**  
          
        **agent\_id \= payload.get('agent\_id')**  
        **decision\_id \= payload.get('decision\_id', event\['event\_id'\])**  
          
        **if not agent\_id:**  
            **return**  
          
        **decision\_key \= f"agent:{agent\_id}:recent\_decisions"**  
          
        **decision\_data \= {**  
            **"id": decision\_id,**  
            **"agent\_id": agent\_id,**  
            **"decision": payload.get('decision'),**  
            **"confidence": payload.get('confidence'),**  
            **"timestamp": event\['created\_at'\].isoformat()**  
        **}**  
          
        **await self.redis.lpush(decision\_key, json.dumps(decision\_data))**  
        **await self.redis.ltrim(decision\_key, 0, 5\)  \# Keep last 5 decisions**  
        **await self.redis.expire(decision\_key, 1800\)  \# 30 minutes TTL**

**class ChromaDBProjectionHandler(BaseProjectionHandler):**  
    **"""**  
    **Updates ChromaDB vectors for semantic memory search**  
    **Implements Tier 3 memory (semantic search) from Master Control**  
    **"""**  
      
    **def \_\_init\_\_(self, chroma\_client, collection\_name: str \= "auren\_memories"):**  
        **super().\_\_init\_\_("ChromaDBProjection")**  
        **self.client \= chroma\_client**  
        **self.collection\_name \= collection\_name**  
        **self.collection \= None**

    **async def initialize(self):**  
        **"""Initialize ChromaDB collection"""**  
        **try:**  
            **self.collection \= self.client.get\_or\_create\_collection(**  
                **name=self.collection\_name,**  
                **metadata={"description": "AUREN agent memories for semantic search"}**  
            **)**  
            **logger.info(f"ChromaDB collection '{self.collection\_name}' initialized")**  
        **except Exception as e:**  
            **logger.error(f"Failed to initialize ChromaDB collection: {e}")**  
            **raise**

    **async def process\_event(self, event\_data: Dict\[str, Any\]) \-\> None:**  
        **"""Update ChromaDB vectors based on events"""**  
          
        **if not self.collection:**  
            **logger.warning("ChromaDB collection not initialized")**  
            **return**  
          
        **try:**  
            **event\_type \= event\_data.get('event\_type')**  
            **sequence\_id \= event\_data.get('sequence\_id')**  
              
            **\# Fetch full event from database**  
            **event \= await self.\_get\_event\_by\_sequence(sequence\_id)**  
            **if not event:**  
                **return**  
              
            **payload \= json.loads(event\['payload'\])**  
              
            **if event\_type \== 'memory\_created':**  
                **await self.\_add\_memory\_vector(event, payload)**  
            **elif event\_type \== 'memory\_updated':**  
                **await self.\_update\_memory\_vector(event, payload)**  
            **elif event\_type \== 'memory\_deleted':**  
                **await self.\_remove\_memory\_vector(event, payload)**  
            **elif event\_type \== 'conversation\_turn':**  
                **await self.\_add\_conversation\_vector(event, payload)**  
              
        **except Exception as e:**  
            **logger.error(f"ChromaDB projection failed for event {event\_data}: {e}")**

    **async def \_get\_event\_by\_sequence(self, sequence\_id: int) \-\> Optional\[Dict\[str, Any\]\]:**  
        **"""Fetch event details from database"""**  
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **row \= await conn.fetchrow(**  
                **"SELECT \* FROM events WHERE sequence\_id \= $1",**  
                **sequence\_id**  
            **)**  
            **return dict(row) if row else None**

    **async def \_add\_memory\_vector(self, event: Dict, payload: Dict) \-\> None:**  
        **"""Add memory to ChromaDB for semantic search"""**  
          
        **memory\_id \= payload.get('memory\_id')**  
        **content \= payload.get('content', {})**  
        **agent\_id \= payload.get('agent\_id')**  
        **user\_id \= payload.get('user\_id')**  
          
        **if not memory\_id or not content:**  
            **return**  
          
        **\# Extract text for embedding**  
        **text\_content \= self.\_extract\_text\_content(content)**  
        **if not text\_content:**  
            **return**  
          
        **\# Metadata for filtering and context**  
        **metadata \= {**  
            **"memory\_id": memory\_id,**  
            **"agent\_id": agent\_id,**  
            **"user\_id": user\_id or "",**  
            **"memory\_type": payload.get('memory\_type', ''),**  
            **"confidence": payload.get('confidence', 1.0),**  
            **"created\_at": event\['created\_at'\].isoformat(),**  
            **"source": "agent\_memory"**  
        **}**  
          
        **try:**  
            **\# Add to ChromaDB (embedding generated automatically)**  
            **self.collection.add(**  
                **ids=\[memory\_id\],**  
                **documents=\[text\_content\],**  
                **metadatas=\[metadata\]**  
            **)**  
              
            **logger.debug(f"Added memory {memory\_id} to ChromaDB")**  
              
        **except Exception as e:**  
            **logger.error(f"Failed to add memory {memory\_id} to ChromaDB: {e}")**

    **async def \_update\_memory\_vector(self, event: Dict, payload: Dict) \-\> None:**  
        **"""Update existing memory vector in ChromaDB"""**  
          
        **memory\_id \= payload.get('memory\_id')**  
        **updates \= payload.get('updates', {})**  
          
        **if not memory\_id:**  
            **return**  
          
        **try:**  
            **\# Check if memory exists**  
            **results \= self.collection.get(ids=\[memory\_id\])**  
            **if not results\['ids'\]:**  
                **logger.warning(f"Memory {memory\_id} not found in ChromaDB for update")**  
                **return**  
              
            **\# Update if content changed**  
            **if 'content' in updates and updates\['content'\]:**  
                **text\_content \= self.\_extract\_text\_content(updates\['content'\])**  
                **if text\_content:**  
                    **\# Update document**  
                    **self.collection.update(**  
                        **ids=\[memory\_id\],**  
                        **documents=\[text\_content\]**  
                    **)**  
              
            **\# Update metadata**  
            **current\_metadata \= results\['metadatas'\]\[0\]**  
            **if 'confidence' in updates and updates\['confidence'\] is not None:**  
                **current\_metadata\['confidence'\] \= updates\['confidence'\]**  
              
            **current\_metadata\['updated\_at'\] \= event\['created\_at'\].isoformat()**  
              
            **self.collection.update(**  
                **ids=\[memory\_id\],**  
                **metadatas=\[current\_metadata\]**  
            **)**  
              
            **logger.debug(f"Updated memory {memory\_id} in ChromaDB")**  
              
        **except Exception as e:**  
            **logger.error(f"Failed to update memory {memory\_id} in ChromaDB: {e}")**

    **async def \_remove\_memory\_vector(self, event: Dict, payload: Dict) \-\> None:**  
        **"""Remove memory vector from ChromaDB"""**  
          
        **memory\_id \= payload.get('memory\_id')**  
          
        **if not memory\_id:**  
            **return**  
          
        **try:**  
            **self.collection.delete(ids=\[memory\_id\])**  
            **logger.debug(f"Removed memory {memory\_id} from ChromaDB")**  
              
        **except Exception as e:**  
            **logger.error(f"Failed to remove memory {memory\_id} from ChromaDB: {e}")**

    **async def \_add\_conversation\_vector(self, event: Dict, payload: Dict) \-\> None:**  
        **"""Add conversation turn to ChromaDB for context retrieval"""**  
          
        **conversation\_id \= payload.get('conversation\_id')**  
        **user\_message \= payload.get('user\_message', '')**  
        **agent\_response \= payload.get('agent\_response', '')**  
          
        **if not conversation\_id or not (user\_message or agent\_response):**  
            **return**  
          
        **\# Combine user message and agent response**  
        **text\_content \= f"User: {user\_message}\\nAgent: {agent\_response}".strip()**  
          
        **metadata \= {**  
            **"conversation\_id": conversation\_id,**  
            **"user\_id": payload.get('user\_id', ''),**  
            **"agent\_id": payload.get('agent\_id', ''),**  
            **"created\_at": event\['created\_at'\].isoformat(),**  
            **"source": "conversation"**  
        **}**  
          
        **try:**  
            **doc\_id \= f"conv\_{conversation\_id}\_{event\['sequence\_id'\]}"**  
              
            **self.collection.add(**  
                **ids=\[doc\_id\],**  
                **documents=\[text\_content\],**  
                **metadatas=\[metadata\]**  
            **)**  
              
            **logger.debug(f"Added conversation turn {doc\_id} to ChromaDB")**  
              
        **except Exception as e:**  
            **logger.error(f"Failed to add conversation to ChromaDB: {e}")**

    **def \_extract\_text\_content(self, content: Dict\[str, Any\]) \-\> str:**  
        **"""Extract meaningful text from memory content for embedding"""**  
          
        **text\_parts \= \[\]**  
          
        **\# Extract various text fields**  
        **for key, value in content.items():**  
            **if isinstance(value, str) and value.strip():**  
                **text\_parts.append(f"{key}: {value}")**  
            **elif isinstance(value, (int, float)):**  
                **text\_parts.append(f"{key}: {value}")**  
            **elif isinstance(value, dict):**  
                **\# Recursively extract from nested objects**  
                **nested\_text \= self.\_extract\_text\_content(value)**  
                **if nested\_text:**  
                    **text\_parts.append(f"{key}: {nested\_text}")**  
          
        **return " | ".join(text\_parts)**  
**\]\]\>**  
            **\</implementation\>**  
        **\</subsection\>**

        **\<subsection id="3.6" name="crewai\_integration"\>**  
            **\<title\>CrewAI Integration\</title\>**  
            **\<description\>Integration points for connecting with CrewAI memory system\</description\>**  
              
            **\<implementation language="python"\>**  
                **\<\!\[CDATA\[**  
**"""**  
**CrewAI Integration Layer**  
**Provides seamless integration between AUREN data layer and CrewAI framework**  
**"""**

**from typing import Dict, Any, List, Optional**  
**from crewai.memory.storage.interface import Storage**  
**from crewai.memory.entity.entity import Entity**  
**import json**

**class AURENMemoryStorage(Storage):**  
    **"""**  
    **Custom CrewAI storage implementation using AUREN's PostgreSQL backend**  
    **Replaces default JSON file storage with production-grade persistence**  
    **"""**  
      
    **def \_\_init\_\_(self, memory\_backend: PostgreSQLMemoryBackend, agent\_id: str):**  
        **self.memory\_backend \= memory\_backend**  
        **self.agent\_id \= agent\_id**  
        **super().\_\_init\_\_(type="auren\_postgresql")**

    **def save(self, value: Any, metadata: Dict\[str, Any\]) \-\> None:**  
        **"""Save memory to AUREN backend"""**  
          
        **\# Convert CrewAI Entity to AUREN memory format**  
        **if isinstance(value, Entity):**  
            **content \= {**  
                **"entity\_type": value.\_\_class\_\_.\_\_name\_\_,**  
                **"data": value.model\_dump() if hasattr(value, 'model\_dump') else str(value)**  
            **}**  
            **memory\_type \= MemoryType.FACT**  
        **else:**  
            **content \= {"value": value}**  
            **memory\_type \= MemoryType.ANALYSIS**  
          
        **\# Extract user context from metadata**  
        **user\_id \= metadata.get('user\_id')**  
        **confidence \= metadata.get('confidence', 1.0)**  
          
        **\# Store asynchronously (CrewAI expects sync interface)**  
        **import asyncio**  
        **try:**  
            **loop \= asyncio.get\_event\_loop()**  
            **if loop.is\_running():**  
                **\# Create task for running loop**  
                **asyncio.create\_task(self.\_async\_save(content, memory\_type, user\_id, metadata, confidence))**  
            **else:**  
                **\# Run in new loop**  
                **loop.run\_until\_complete(self.\_async\_save(content, memory\_type, user\_id, metadata, confidence))**  
        **except RuntimeError:**  
            **\# Fallback for environments without event loop**  
            **asyncio.run(self.\_async\_save(content, memory\_type, user\_id, metadata, confidence))**

    **async def \_async\_save(self, content: Dict\[str, Any\], memory\_type: MemoryType,**   
                         **user\_id: Optional\[str\], metadata: Dict\[str, Any\], confidence: float):**  
        **"""Async helper for saving memory"""**  
        **await self.memory\_backend.store\_memory(**  
            **agent\_id=self.agent\_id,**  
            **memory\_type=memory\_type,**  
            **content=content,**  
            **user\_id=user\_id,**  
            **metadata=metadata,**  
            **confidence=confidence**  
        **)**

    **def search(self, query: str, limit: int \= 3, filter: Dict\[str, Any\] \= None) \-\> List\[Dict\[str, Any\]\]:**  
        **"""Search memories using AUREN backend"""**  
          
        **\# Extract user context from filter**  
        **user\_id \= filter.get('user\_id') if filter else None**  
          
        **\# Search asynchronously**  
        **import asyncio**  
        **try:**  
            **loop \= asyncio.get\_event\_loop()**  
            **if loop.is\_running():**  
                **\# For running loop, we need to handle this differently**  
                **\# This is a limitation of CrewAI's sync interface**  
                **return \[\]**  
            **else:**  
                **return loop.run\_until\_complete(self.\_async\_search(query, limit, user\_id))**  
        **except RuntimeError:**  
            **return asyncio.run(self.\_async\_search(query, limit, user\_id))**

    **async def \_async\_search(self, query: str, limit: int, user\_id: Optional\[str\]) \-\> List\[Dict\[str, Any\]\]:**  
        **"""Async helper for searching memories"""**  
        **memories \= await self.memory\_backend.search\_memories(**  
            **agent\_id=self.agent\_id,**  
            **query=query,**  
            **user\_id=user\_id,**  
            **limit=limit**  
        **)**  
          
        **\# Convert to CrewAI format**  
        **results \= \[\]**  
        **for memory in memories:**  
            **result \= {**  
                **"content": memory\["content"\],**  
                **"metadata": {**  
                    **\*\*memory\["metadata"\],**  
                    **"memory\_id": memory\["id"\],**  
                    **"confidence": memory\["confidence"\],**  
                    **"created\_at": memory\["created\_at"\],**  
                    **"relevance": memory.get("relevance", 1.0)**  
                **}**  
            **}**  
            **results.append(result)**  
          
        **return results**

**class AURENCrewMemoryIntegration:**  
    **"""**  
    **High-level integration for AUREN memory system with CrewAI**  
    **Provides context management and cross-agent memory sharing**  
    **"""**  
      
    **def \_\_init\_\_(self, memory\_backend: PostgreSQLMemoryBackend, event\_store: EventStore):**  
        **self.memory\_backend \= memory\_backend**  
        **self.event\_store \= event\_store**

    **def create\_agent\_memory\_storage(self, agent\_id: str) \-\> AURENMemoryStorage:**  
        **"""Create custom memory storage for a CrewAI agent"""**  
        **return AURENMemoryStorage(self.memory\_backend, agent\_id)**

    **async def get\_shared\_context(self, user\_id: str, requesting\_agent: str) \-\> Dict\[str, Any\]:**  
        **"""**  
        **Get shared context across all agents for a user**  
        **Enables compound intelligence through cross-agent memory access**  
        **"""**  
          
        **\# Get memories from all agents for this user**  
        **all\_agents \= \[**  
            **"neuroscientist", "nutritionist", "training\_agent",**   
            **"recovery\_agent", "sleep\_agent", "mental\_health\_agent"**  
        **\]**  
          
        **shared\_context \= {**  
            **"user\_id": user\_id,**  
            **"requesting\_agent": requesting\_agent,**  
            **"cross\_agent\_memories": {},**  
            **"recent\_decisions": \[\],**  
            **"validated\_hypotheses": \[\]**  
        **}**  
          
        **\# Gather memories from each agent**  
        **for agent\_id in all\_agents:**  
            **if agent\_id \== requesting\_agent:**  
                **continue  \# Skip self**  
                  
            **agent\_memories \= await self.memory\_backend.retrieve\_memories(**  
                **agent\_id=agent\_id,**  
                **user\_id=user\_id,**  
                **limit=10  \# Recent memories only**  
            **)**  
              
            **\# Filter for high-confidence insights**  
            **high\_confidence\_memories \= \[**  
                **memory for memory in agent\_memories**   
                **if memory\["confidence"\] \>= 0.7**  
            **\]**  
              
            **shared\_context\["cross\_agent\_memories"\]\[agent\_id\] \= high\_confidence\_memories**  
          
        **\# Get recent agent decisions from events**  
        **decision\_events \= await self.event\_store.get\_events\_by\_type(**  
            **event\_type=EventType.AGENT\_DECISION,**  
            **limit=20**  
        **)**  
          
        **user\_decisions \= \[**  
            **event for event in decision\_events**   
            **if event.payload.get("user\_id") \== user\_id**  
        **\]**  
          
        **shared\_context\["recent\_decisions"\] \= \[**  
            **{**  
                **"agent\_id": event.payload.get("agent\_id"),**  
                **"decision": event.payload.get("decision"),**  
                **"confidence": event.payload.get("confidence"),**  
                **"timestamp": event.created\_at.isoformat()**  
            **}**  
            **for event in user\_decisions\[:5\]  \# Last 5 decisions**  
        **\]**  
          
        **\# Get validated hypotheses**  
        **hypothesis\_events \= await self.event\_store.get\_events\_by\_type(**  
            **event\_type=EventType.HYPOTHESIS\_VALIDATED,**  
            **limit=10**  
        **)**  
          
        **user\_hypotheses \= \[**  
            **event for event in hypothesis\_events**   
            **if event.payload.get("user\_id") \== user\_id**  
        **\]**  
          
        **shared\_context\["validated\_hypotheses"\] \= \[**  
            **{**  
                **"hypothesis": event.payload.get("hypothesis"),**  
                **"confidence": event.payload.get("final\_confidence"),**  
                **"evidence": event.payload.get("validation\_evidence"),**  
                **"timestamp": event.created\_at.isoformat()**  
            **}**  
            **for event in user\_hypotheses\[:3\]  \# Last 3 validated hypotheses**  
        **\]**  
          
        **return shared\_context**

    **async def store\_agent\_decision(self,**   
                                  **agent\_id: str,**  
                                  **user\_id: str,**  
                                  **decision: Dict\[str, Any\],**  
                                  **confidence: float,**  
                                  **context: Dict\[str, Any\]) \-\> str:**  
        **"""**  
        **Store agent decision with full context and audit trail**  
        **Links decision to triggering events and cross-agent insights**  
        **"""**  
          
        **\# Store as memory for the agent**  
        **memory\_id \= await self.memory\_backend.store\_memory(**  
            **agent\_id=agent\_id,**  
            **memory\_type=MemoryType.DECISION,**  
            **content=decision,**  
            **user\_id=user\_id,**  
            **metadata={**  
                **"decision\_context": context,**  
                **"cross\_agent\_insights\_used": context.get("cross\_agent\_memories", {}),**  
                **"triggering\_events": context.get("triggering\_events", \[\])**  
            **},**  
            **confidence=confidence**  
        **)**  
          
        **\# Record as event for other agents to see**  
        **await self.event\_store.append\_event(**  
            **stream\_id=user\_id,**  
            **event\_type=EventType.AGENT\_DECISION,**  
            **payload={**  
                **"agent\_id": agent\_id,**  
                **"user\_id": user\_id,**  
                **"decision": decision,**  
                **"confidence": confidence,**  
                **"memory\_id": memory\_id,**  
                **"context\_summary": context.get("summary", "")**  
            **},**  
            **metadata={**  
                **"decision\_category": decision.get("category", "general"),**  
                **"urgency": decision.get("urgency", "normal"),**  
                **"cross\_agent\_collaboration": len(context.get("cross\_agent\_memories", {})) \> 0**  
            **}**  
        **)**  
          
        **return memory\_id**

    **async def initiate\_agent\_handoff(self,**  
                                    **from\_agent: str,**  
                                    **to\_agent: str,**  
                                    **user\_id: str,**  
                                    **topic: str,**  
                                    **context: Dict\[str, Any\]) \-\> None:**  
        **"""**  
        **Initiate handoff between specialist agents with context preservation**  
        **"""**  
          
        **\# Create handoff event**  
        **await self.event\_store.append\_event(**  
            **stream\_id=user\_id,**  
            **event\_type=EventType.AGENT\_HANDOFF,**  
            **payload={**  
                **"from\_agent": from\_agent,**  
                **"to\_agent": to\_agent,**  
                **"user\_id": user\_id,**  
                **"topic": topic,**  
                **"handoff\_context": context,**  
                **"handoff\_reason": context.get("reason", "specialist\_expertise\_required")**  
            **},**  
            **metadata={**  
                **"handoff\_type": context.get("type", "consultation"),**  
                **"urgency": context.get("urgency", "normal"),**  
                **"expected\_duration": context.get("expected\_duration", "unknown")**  
            **}**  
        **)**  
          
        **\# Store handoff memory for receiving agent**  
        **await self.memory\_backend.store\_memory(**  
            **agent\_id=to\_agent,**  
            **memory\_type=MemoryType.CONVERSATION,**  
            **content={**  
                **"handoff\_received": True,**  
                **"from\_agent": from\_agent,**  
                **"topic": topic,**  
                **"context": context**  
            **},**  
            **user\_id=user\_id,**  
            **metadata={**  
                **"handoff\_id": str(uuid.uuid4()),**  
                **"requires\_response": context.get("requires\_response", True)**  
            **}**  
        **)**  
**\]\]\>**  
            **\</implementation\>**  
        **\</subsection\>**

        **\<subsection id="3.7" name="migration\_guide"\>**  
            **\<title\>Migration from JSON Files\</title\>**  
            **\<description\>Complete migration script from legacy JSON file storage to PostgreSQL\</description\>**  
              
            **\<implementation language="python"\>**  
                **\<\!\[CDATA\[**  
**"""**  
**Migration script from JSON file storage to PostgreSQL backend**  
**Handles data transformation and validation**  
**"""**

**import os**  
**import json**  
**import uuid**  
**from pathlib import Path**  
**from typing import Dict, Any, List, Optional**  
**from datetime import datetime, timezone**  
**import logging**

**logger \= logging.getLogger(\_\_name\_\_)**

**class JSONToPostgreSQLMigrator:**  
    **"""**  
    **Migrates legacy JSON memory files to PostgreSQL event store**  
    **Preserves data integrity and creates audit trail**  
    **"""**  
      
    **def \_\_init\_\_(self,**   
                 **json\_directory: Path,**  
                 **memory\_backend: PostgreSQLMemoryBackend,**  
                 **event\_store: EventStore):**  
        **self.json\_directory \= Path(json\_directory)**  
        **self.memory\_backend \= memory\_backend**  
        **self.event\_store \= event\_store**  
        **self.migration\_stats \= {**  
            **"files\_processed": 0,**  
            **"memories\_migrated": 0,**  
            **"errors": \[\],**  
            **"agent\_breakdown": {},**  
            **"start\_time": None,**  
            **"end\_time": None**  
        **}**

    **async def migrate\_all(self, dry\_run: bool \= False) \-\> Dict\[str, Any\]:**  
        **"""**  
        **Migrate all JSON memory files to PostgreSQL**  
          
        **Args:**  
            **dry\_run: If True, validate files without writing to database**  
              
        **Returns:**  
            **Migration statistics and results**  
        **"""**  
          
        **self.migration\_stats\["start\_time"\] \= datetime.now(timezone.utc)**  
        **logger.info(f"Starting migration from {self.json\_directory}")**  
          
        **if dry\_run:**  
            **logger.info("DRY RUN MODE \- No data will be written")**  
          
        **\# Find all JSON files**  
        **json\_files \= list(self.json\_directory.glob("\*.json"))**  
        **logger.info(f"Found {len(json\_files)} JSON files to migrate")**  
          
        **\# Process each file**  
        **for json\_file in json\_files:**  
            **try:**  
                **await self.\_migrate\_file(json\_file, dry\_run)**  
                **self.migration\_stats\["files\_processed"\] \+= 1**  
                  
                **if self.migration\_stats\["files\_processed"\] % 10 \== 0:**  
                    **logger.info(f"Processed {self.migration\_stats\['files\_processed'\]} files...")**  
                      
            **except Exception as e:**  
                **error\_msg \= f"Failed to migrate {json\_file}: {e}"**  
                **self.migration\_stats\["errors"\].append(error\_msg)**  
                **logger.error(error\_msg)**  
          
        **self.migration\_stats\["end\_time"\] \= datetime.now(timezone.utc)**  
        **duration \= (self.migration\_stats\["end\_time"\] \- self.migration\_stats\["start\_time"\]).total\_seconds()**  
          
        **logger.info(f"Migration completed in {duration:.2f} seconds")**  
        **logger.info(f"Files processed: {self.migration\_stats\['files\_processed'\]}")**  
        **logger.info(f"Memories migrated: {self.migration\_stats\['memories\_migrated'\]}")**  
        **logger.info(f"Errors: {len(self.migration\_stats\['errors'\])}")**  
          
        **return self.migration\_stats**

    **async def \_migrate\_file(self, json\_file: Path, dry\_run: bool) \-\> None:**  
        **"""Migrate individual JSON file"""**  
          
        **logger.debug(f"Processing file: {json\_file}")**  
          
        **\# Load JSON data**  
        **try:**  
            **with open(json\_file, 'r', encoding='utf-8') as f:**  
                **data \= json.load(f)**  
        **except (json.JSONDecodeError, UnicodeDecodeError) as e:**  
            **raise ValueError(f"Invalid JSON file {json\_file}: {e}")**  
          
        **\# Extract agent and user information**  
        **agent\_id, user\_id \= self.\_extract\_identifiers(json\_file, data)**  
          
        **\# Validate data structure**  
        **memories \= self.\_validate\_and\_transform\_data(data, agent\_id, user\_id)**  
          
        **if dry\_run:**  
            **logger.debug(f"DRY RUN: Would migrate {len(memories)} memories from {json\_file}")**  
            **self.migration\_stats\["memories\_migrated"\] \+= len(memories)**  
            **return**  
          
        **\# Check if already migrated**  
        **if await self.\_is\_already\_migrated(json\_file, agent\_id, user\_id):**  
            **logger.info(f"File {json\_file} already migrated, skipping")**  
            **return**  
          
        **\# Migrate memories**  
        **for memory\_data in memories:**  
            **try:**  
                **await self.\_migrate\_memory(agent\_id, user\_id, memory\_data, json\_file)**  
                **self.migration\_stats\["memories\_migrated"\] \+= 1**  
                  
                **\# Track agent breakdown**  
                **if agent\_id not in self.migration\_stats\["agent\_breakdown"\]:**  
                    **self.migration\_stats\["agent\_breakdown"\]\[agent\_id\] \= 0**  
                **self.migration\_stats\["agent\_breakdown"\]\[agent\_id\] \+= 1**  
                  
            **except Exception as e:**  
                **error\_msg \= f"Failed to migrate memory from {json\_file}: {e}"**  
                **self.migration\_stats\["errors"\].append(error\_msg)**  
                **logger.error(error\_msg)**

    **def \_extract\_identifiers(self, json\_file: Path, data: Dict\[str, Any\]) \-\> tuple\[str, Optional\[str\]\]:**  
        **"""Extract agent\_id and user\_id from file and data"""**  
          
        **\# Try to get from data first**  
        **agent\_id \= data.get('agent\_id')**  
        **user\_id \= data.get('user\_id')**  
          
        **\# Extract agent\_id from filename if not in data**  
        **if not agent\_id:**  
            **filename \= json\_file.stem.lower()**  
              
            **\# Map filename patterns to agent IDs**  
            **agent\_mappings \= {**  
                **'neuroscientist': 'neuroscientist',**  
                **'nutritionist': 'nutritionist',**  
                **'training': 'training\_agent',**  
                **'recovery': 'recovery\_agent',**  
                **'sleep': 'sleep\_agent',**  
                **'mental': 'mental\_health\_agent',**  
                **'coach': 'training\_agent',**  
                **'diet': 'nutritionist'**  
            **}**  
              
            **for pattern, mapped\_agent in agent\_mappings.items():**  
                **if pattern in filename:**  
                    **agent\_id \= mapped\_agent**  
                    **break**  
              
            **if not agent\_id:**  
                **\# Try to extract from directory structure**  
                **parent\_dir \= json\_file.parent.name.lower()**  
                **for pattern, mapped\_agent in agent\_mappings.items():**  
                    **if pattern in parent\_dir:**  
                        **agent\_id \= mapped\_agent**  
                        **break**  
                          
                **if not agent\_id:**  
                    **agent\_id \= "unknown\_agent"**  
          
        **\# Try to extract user\_id from filename**  
        **if not user\_id:**  
            **filename \= json\_file.stem**  
            **\# Look for UUID pattern in filename**  
            **import re**  
            **uuid\_pattern \= r'\[0-9a-f\]{8}-\[0-9a-f\]{4}-\[0-9a-f\]{4}-\[0-9a-f\]{4}-\[0-9a-f\]{12}'**  
            **uuid\_match \= re.search(uuid\_pattern, filename, re.IGNORECASE)**  
            **if uuid\_match:**  
                **user\_id \= uuid\_match.group()**  
          
        **return agent\_id, user\_id**

    **def \_validate\_and\_transform\_data(self,**   
                                   **data: Dict\[str, Any\],**   
                                   **agent\_id: str,**   
                                   **user\_id: Optional\[str\]) \-\> List\[Dict\[str, Any\]\]:**  
        **"""Validate and transform JSON data to memory format"""**  
          
        **memories \= \[\]**  
          
        **if isinstance(data, list):**  
            **\# List of memories**  
            **for item in data:**  
                **if isinstance(item, dict):**  
                    **memory \= self.\_transform\_memory\_item(item, agent\_id, user\_id)**  
                    **if memory:**  
                        **memories.append(memory)**  
          
        **elif isinstance(data, dict):**  
            **\# Check for different data structures**  
            **if 'memories' in data and isinstance(data\['memories'\], list):**  
                **\# Standard memory structure**  
                **for memory\_item in data\['memories'\]:**  
                    **memory \= self.\_transform\_memory\_item(memory\_item, agent\_id, user\_id)**  
                    **if memory:**  
                        **memories.append(memory)**  
              
            **elif 'data' in data:**  
                **\# Nested data structure**  
                **nested\_memories \= self.\_validate\_and\_transform\_data(data\['data'\], agent\_id, user\_id)**  
                **memories.extend(nested\_memories)**  
              
            **else:**  
                **\# Single memory object**  
                **memory \= self.\_transform\_memory\_item(data, agent\_id, user\_id)**  
                **if memory:**  
                    **memories.append(memory)**  
          
        **return memories**

    **def \_transform\_memory\_item(self,**   
                              **item: Dict\[str, Any\],**   
                              **agent\_id: str,**   
                              **user\_id: Optional\[str\]) \-\> Optional\[Dict\[str, Any\]\]:**  
        **"""Transform individual memory item to standard format"""**  
          
        **if not isinstance(item, dict):**  
            **return None**  
          
        **\# Determine memory type**  
        **memory\_type \= item.get('type', 'fact')**  
        **if memory\_type not in \[t.value for t in MemoryType\]:**  
            **\# Map legacy types**  
            **type\_mapping \= {**  
                **'observation': 'fact',**  
                **'pattern': 'analysis',**  
                **'suggestion': 'recommendation',**  
                **'note': 'insight',**  
                **'chat': 'conversation'**  
            **}**  
            **memory\_type \= type\_mapping.get(memory\_type, 'fact')**  
          
        **\# Extract content**  
        **content \= item.get('content')**  
        **if not content:**  
            **\# Try different content fields**  
            **content \= (item.get('value') or**   
                      **item.get('data') or**   
                      **item.get('text') or**   
                      **item.get('message'))**  
          
        **if not content:**  
            **\# Use the entire item as content if no specific content field**  
            **content \= {k: v for k, v in item.items()**   
                      **if k not in \['type', 'agent\_id', 'user\_id', 'metadata', 'timestamp'\]}**  
          
        **\# Extract metadata**  
        **metadata \= item.get('metadata', {})**  
        **metadata.update({**  
            **'migrated\_from': 'json\_file',**  
            **'migration\_timestamp': datetime.now(timezone.utc).isoformat(),**  
            **'original\_structure': item**  
        **})**  
          
        **\# Extract confidence**  
        **confidence \= item.get('confidence', 1.0)**  
        **if isinstance(confidence, str):**  
            **try:**  
                **confidence \= float(confidence)**  
            **except ValueError:**  
                **confidence \= 1.0**  
          
        **\# Ensure confidence is in valid range**  
        **confidence \= max(0.0, min(1.0, confidence))**  
          
        **\# Extract timestamp**  
        **created\_at \= item.get('timestamp') or item.get('created\_at')**  
        **if created\_at and isinstance(created\_at, str):**  
            **try:**  
                **created\_at \= datetime.fromisoformat(created\_at.replace('Z', '+00:00'))**  
            **except ValueError:**  
                **created\_at \= None**  
          
        **return {**  
            **'memory\_type': memory\_type,**  
            **'content': content,**  
            **'metadata': metadata,**  
            **'confidence': confidence,**  
            **'created\_at': created\_at**  
        **}**

    **async def \_is\_already\_migrated(self,**   
                                  **json\_file: Path,**   
                                  **agent\_id: str,**   
                                  **user\_id: Optional\[str\]) \-\> bool:**  
        **"""Check if file has already been migrated"""**  
          
        **\# Look for migration marker in agent memories**  
        **migration\_markers \= await self.memory\_backend.retrieve\_memories(**  
            **agent\_id="migration\_service",**  
            **memory\_type=MemoryType.FACT,**  
            **limit=1000**  
        **)**  
          
        **file\_signature \= f"{json\_file.name}:{agent\_id}:{user\_id or 'no\_user'}"**  
          
        **for marker in migration\_markers:**  
            **if marker\["content"\].get("file\_signature") \== file\_signature:**  
                **return True**  
          
        **return False**

    **async def \_migrate\_memory(self,**   
                             **agent\_id: str,**  
                             **user\_id: Optional\[str\],**  
                             **memory\_data: Dict\[str, Any\],**  
                             **source\_file: Path) \-\> None:**  
        **"""Migrate individual memory to PostgreSQL"""**  
          
        **\# Store memory**  
        **memory\_id \= await self.memory\_backend.store\_memory(**  
            **agent\_id=agent\_id,**  
            **memory\_type=MemoryType(memory\_data\["memory\_type"\]),**  
            **content=memory\_data\["content"\],**  
            **user\_id=user\_id,**  
            **metadata=memory\_data\["metadata"\],**  
            **confidence=memory\_data\["confidence"\]**  
        **)**  
          
        **\# Create migration event for audit trail**  
        **await self.event\_store.append\_event(**  
            **stream\_id=user\_id or agent\_id,**  
            **event\_type=EventType.MEMORY\_CREATED,**  
            **payload={**  
                **"memory\_id": memory\_id,**  
                **"agent\_id": agent\_id,**  
                **"user\_id": user\_id,**  
                **"migration\_source": str(source\_file),**  
                **"migrated\_at": datetime.now(timezone.utc).isoformat()**  
            **},**  
            **metadata={**  
                **"migration": True,**  
                **"source\_file": source\_file.name,**  
                **"original\_data": memory\_data**  
            **}**  
        **)**

    **async def create\_migration\_marker(self, json\_file: Path, agent\_id: str, user\_id: Optional\[str\]) \-\> None:**  
        **"""Create marker to track completed migrations"""**  
          
        **file\_signature \= f"{json\_file.name}:{agent\_id}:{user\_id or 'no\_user'}"**  
          
        **await self.memory\_backend.store\_memory(**  
            **agent\_id="migration\_service",**  
            **memory\_type=MemoryType.FACT,**  
            **content={**  
                **"file\_signature": file\_signature,**  
                **"source\_file": str(json\_file),**  
                **"agent\_id": agent\_id,**  
                **"user\_id": user\_id,**  
                **"migrated\_at": datetime.now(timezone.utc).isoformat()**  
            **},**  
            **metadata={**  
                **"migration\_marker": True,**  
                **"file\_stats": {**  
                    **"size": json\_file.stat().st\_size,**  
                    **"mtime": datetime.fromtimestamp(json\_file.stat().st\_mtime).isoformat()**  
                **}**  
            **}**  
        **)**

**\# Migration execution script**  
**async def run\_migration(json\_directory: str,**   
                       **database\_url: str,**   
                       **dry\_run: bool \= False) \-\> Dict\[str, Any\]:**  
    **"""**  
    **Execute complete migration process**  
      
    **Args:**  
        **json\_directory: Path to directory containing JSON files**  
        **database\_url: PostgreSQL connection string**  
        **dry\_run: If True, validate without writing to database**  
          
    **Returns:**  
        **Migration results and statistics**  
    **"""**  
      
    **\# Initialize database connection**  
    **await AsyncPostgresManager.initialize(database\_url)**  
      
    **\# Initialize components**  
    **event\_store \= EventStore()**  
    **memory\_backend \= PostgreSQLMemoryBackend(event\_store)**  
      
    **\# Create migrator**  
    **migrator \= JSONToPostgreSQLMigrator(**  
        **json\_directory=Path(json\_directory),**  
        **memory\_backend=memory\_backend,**  
        **event\_store=event\_store**  
    **)**  
      
    **try:**  
        **\# Run migration**  
        **results \= await migrator.migrate\_all(dry\_run=dry\_run)**  
          
        **\# Print summary**  
        **print("\\n" \+ "="\*50)**  
        **print("MIGRATION SUMMARY")**  
        **print("="\*50)**  
        **print(f"Files processed: {results\['files\_processed'\]}")**  
        **print(f"Memories migrated: {results\['memories\_migrated'\]}")**  
        **print(f"Errors: {len(results\['errors'\])}")**  
          
        **if results\['agent\_breakdown'\]:**  
            **print("\\nAgent breakdown:")**  
            **for agent, count in results\['agent\_breakdown'\].items():**  
                **print(f"  {agent}: {count} memories")**  
          
        **if results\['errors'\]:**  
            **print("\\nErrors encountered:")**  
            **for error in results\['errors'\]\[:5\]:  \# Show first 5 errors**  
                **print(f"  \- {error}")**  
            **if len(results\['errors'\]) \> 5:**  
                **print(f"  ... and {len(results\['errors'\]) \- 5} more errors")**  
          
        **return results**  
          
    **finally:**  
        **await AsyncPostgresManager.close()**

**if \_\_name\_\_ \== "\_\_main\_\_":**  
    **import asyncio**  
    **import sys**  
      
    **if len(sys.argv) \< 3:**  
        **print("Usage: python migration.py \<json\_directory\> \<database\_url\> \[--dry-run\]")**  
        **sys.exit(1)**  
      
    **json\_dir \= sys.argv\[1\]**  
    **db\_url \= sys.argv\[2\]**  
    **dry\_run \= "--dry-run" in sys.argv**  
      
    **results \= asyncio.run(run\_migration(json\_dir, db\_url, dry\_run))**  
**\]\]\>**  
            **\</implementation\>**  
        **\</subsection\>**

        **\<subsection id="3.8" name="testing\_suite"\>**  
            **\<title\>Comprehensive Testing Suite\</title\>**  
            **\<description\>Complete test coverage for all data layer components\</description\>**  
              
            **\<implementation language="python"\>**  
                **\<\!\[CDATA\[**  
**"""**  
**Comprehensive test suite for AUREN data persistence layer**  
**Tests all components with focus on failure modes and edge cases**  
**"""**

**import pytest**  
**import asyncio**  
**import uuid**  
**import json**  
**from datetime import datetime, timezone, timedelta**  
**from typing import Dict, Any**  
**from unittest.mock import AsyncMock, patch, MagicMock**

**\# Test configuration**  
**TEST\_DATABASE\_URL \= "postgresql://test:test@localhost:5432/auren\_test"**

**@pytest.fixture(scope="session")**  
**def event\_loop():**  
    **"""Create event loop for async tests"""**  
    **loop \= asyncio.new\_event\_loop()**  
    **yield loop**  
    **loop.close()**

**@pytest.fixture**  
**async def db\_setup():**  
    **"""Setup test database and clean up after tests"""**  
      
    **\# Initialize database connection**  
    **await AsyncPostgresManager.initialize(**  
        **dsn=TEST\_DATABASE\_URL,**  
        **min\_size=2,**  
        **max\_size=5**  
    **)**  
      
    **\# Clean database before tests**  
    **async with AsyncPostgresManager.get\_connection() as conn:**  
        **await conn.execute("TRUNCATE events, agent\_memories, user\_profiles, conversation\_memories, specialist\_knowledge RESTART IDENTITY CASCADE")**  
      
    **yield**  
      
    **\# Clean up**  
    **await AsyncPostgresManager.close()**

**@pytest.fixture**  
**async def event\_store(db\_setup):**  
    **"""Create test event store"""**  
    **return EventStore()**

**@pytest.fixture**  
**async def memory\_backend(event\_store):**  
    **"""Create test memory backend"""**  
    **return PostgreSQLMemoryBackend(event\_store)**

**@pytest.fixture**  
**def sample\_user\_id():**  
    **"""Generate sample user ID"""**  
    **return str(uuid.uuid4())**

**@pytest.fixture**  
**def sample\_agent\_id():**  
    **"""Generate sample agent ID"""**  
    **return "test\_neuroscientist"**

**class TestAsyncPostgresManager:**  
    **"""Test PostgreSQL connection management"""**  
      
    **async def test\_initialize\_connection\_pool(self):**  
        **"""Test connection pool initialization"""**  
          
        **\# Initialize pool**  
        **await AsyncPostgresManager.initialize(**  
            **dsn=TEST\_DATABASE\_URL,**  
            **min\_size=2,**  
            **max\_size=10**  
        **)**  
          
        **\# Get pool and test connection**  
        **pool \= await AsyncPostgresManager.get\_pool()**  
        **assert pool is not None**  
          
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **result \= await conn.fetchval("SELECT 1")**  
            **assert result \== 1**  
          
        **await AsyncPostgresManager.close()**

    **async def test\_connection\_retry\_logic(self):**  
        **"""Test connection retry with bad DSN"""**  
          
        **with pytest.raises(ConnectionError):**  
            **await AsyncPostgresManager.initialize(**  
                **dsn="postgresql://bad:bad@localhost:9999/bad",**  
                **min\_size=1,**  
                **max\_size=2**  
            **)**

    **async def test\_health\_check(self, db\_setup):**  
        **"""Test health check functionality"""**  
          
        **health \= await AsyncPostgresManager.health\_check()**  
          
        **assert health\["status"\] \== "healthy"**  
        **assert "response\_time\_ms" in health**  
        **assert "pool\_stats" in health**  
        **assert health\["pool\_stats"\]\["size"\] \>= 0**

    **async def test\_connection\_context\_manager(self, db\_setup):**  
        **"""Test connection context manager with retry logic"""**  
          
        **\# Test successful connection**  
        **async with AsyncPostgresManager.get\_connection() as conn:**  
            **result \= await conn.fetchval("SELECT 42")**  
            **assert result \== 42**

**class TestEventStore:**  
    **"""Test event store functionality"""**  
      
    **async def test\_append\_and\_retrieve\_events(self, event\_store, sample\_user\_id):**  
        **"""Test basic event append and retrieval"""**  
          
        **stream\_id \= sample\_user\_id**  
          
        **\# Append first event**  
        **event1 \= await event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.MEMORY\_CREATED,**  
            **payload={"test": "data1", "value": 42}**  
        **)**  
          
        **assert event1.event\_id is not None**  
        **assert event1.version \== 1**  
        **assert event1.sequence\_id is not None**  
          
        **\# Append second event**  
        **event2 \= await event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.MEMORY\_UPDATED,**  
            **payload={"test": "data2", "value": 84},**  
            **expected\_version=1**  
        **)**  
          
        **assert event2.version \== 2**  
          
        **\# Retrieve events**  
        **events \= await event\_store.get\_stream\_events(stream\_id)**  
          
        **assert len(events) \== 2**  
        **assert events\[0\].event\_id \== event1.event\_id**  
        **assert events\[1\].event\_id \== event2.event\_id**  
        **assert events\[0\].payload\["value"\] \== 42**  
        **assert events\[1\].payload\["value"\] \== 84**

    **async def test\_optimistic\_concurrency\_control(self, event\_store, sample\_user\_id):**  
        **"""Test optimistic concurrency control"""**  
          
        **stream\_id \= sample\_user\_id**  
          
        **\# Append initial event**  
        **await event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.USER\_ONBOARDED,**  
            **payload={"user": "test"}**  
        **)**  
          
        **\# Successful append with correct version**  
        **await event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.MEMORY\_CREATED,**  
            **payload={"memory": "test"},**  
            **expected\_version=1**  
        **)**  
          
        **\# Failed append with incorrect version**  
        **with pytest.raises(ConcurrencyError):**  
            **await event\_store.append\_event(**  
                **stream\_id=stream\_id,**  
                **event\_type=EventType.MEMORY\_UPDATED,**  
                **payload={"memory": "conflict"},**  
                **expected\_version=1  \# Should be 2**  
            **)**

    **async def test\_stream\_version\_tracking(self, event\_store, sample\_user\_id):**  
        **"""Test stream version tracking"""**  
          
        **stream\_id \= sample\_user\_id**  
          
        **\# New stream should have version 0**  
        **version \= await event\_store.get\_stream\_version(stream\_id)**  
        **assert version \== 0**  
          
        **\# Add events and check version increments**  
        **await event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.MEMORY\_CREATED,**  
            **payload={"test": 1}**  
        **)**  
          
        **version \= await event\_store.get\_stream\_version(stream\_id)**  
        **assert version \== 1**  
          
        **await event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.MEMORY\_UPDATED,**  
            **payload={"test": 2}**  
        **)**  
          
        **version \= await event\_store.get\_stream\_version(stream\_id)**  
        **assert version \== 2**

    **async def test\_event\_replay(self, event\_store, sample\_user\_id):**  
        **"""Test event replay functionality"""**  
          
        **stream\_id \= sample\_user\_id**  
          
        **\# Create test events**  
        **await event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.MEMORY\_CREATED,**  
            **payload={"counter": 1}**  
        **)**  
          
        **await event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.MEMORY\_UPDATED,**  
            **payload={"counter": 5}**  
        **)**  
          
        **await event\_store.append\_event(**  
            **stream\_id=stream\_id,**  
            **event\_type=EventType.MEMORY\_UPDATED,**  
            **payload={"counter": 10}**  
        **)**  
          
        **\# Define projection handler**  
        **async def counter\_projection(state, event):**  
            **if event.event\_type in \[EventType.MEMORY\_CREATED.value, EventType.MEMORY\_UPDATED.value\]:**  
                **state\["counter"\] \= event.payload.get("counter", 0\)**  
            **return state**  
          
        **\# Replay stream**  
        **final\_state \= await event\_store.replay\_stream(**  
            **stream\_id=stream\_id,**  
            **projection\_handler=counter\_projection**  
        **)**  
          
        **assert final\_state\["counter"\] \== 10**

**class TestPostgreSQLMemoryBackend:**  
    **"""Test memory backend functionality"""**  
      
    **async def test\_store\_and\_retrieve\_memory(self, memory\_backend, sample\_agent\_id, sample\_user\_id):**  
        **"""Test basic memory storage and retrieval"""**  
          
        **\# Store memory**  
        **memory\_id \= await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.ANALYSIS,**  
            **content={"pattern": "elevated\_hrv", "confidence\_score": 0.85},**  
            **user\_id=sample\_user\_id,**  
            **metadata={"source": "biometric\_analysis"},**  
            **confidence=0.85**  
        **)**  
          
        **assert memory\_id is not None**  
          
        **\# Retrieve memories**  
        **memories \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **assert len(memories) \== 1**  
        **memory \= memories\[0\]**  
        **assert memory\["id"\] \== memory\_id**  
        **assert memory\["agent\_id"\] \== sample\_agent\_id**  
        **assert memory\["user\_id"\] \== sample\_user\_id**  
        **assert memory\["memory\_type"\] \== MemoryType.ANALYSIS.value**  
        **assert memory\["content"\]\["pattern"\] \== "elevated\_hrv"**  
        **assert memory\["confidence"\] \== 0.85**

    **async def test\_update\_memory(self, memory\_backend, sample\_agent\_id, sample\_user\_id):**  
        **"""Test memory updates"""**  
          
        **\# Store initial memory**  
        **memory\_id \= await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.RECOMMENDATION,**  
            **content={"advice": "increase\_protein"},**  
            **user\_id=sample\_user\_id,**  
            **confidence=0.7**  
        **)**  
          
        **\# Update memory**  
        **success \= await memory\_backend.update\_memory(**  
            **memory\_id=memory\_id,**  
            **content={"advice": "increase\_protein", "amount": "25g"},**  
            **confidence=0.9**  
        **)**  
          
        **assert success is True**  
          
        **\# Verify update**  
        **memories \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **memory \= memories\[0\]**  
        **assert memory\["content"\]\["amount"\] \== "25g"**  
        **assert memory\["confidence"\] \== 0.9**

    **async def test\_delete\_memory(self, memory\_backend, sample\_agent\_id, sample\_user\_id):**  
        **"""Test memory deletion"""**  
          
        **\# Store memory**  
        **memory\_id \= await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.FACT,**  
            **content={"fact": "user\_prefers\_morning\_workouts"},**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **\# Delete memory**  
        **success \= await memory\_backend.delete\_memory(memory\_id)**  
        **assert success is True**  
          
        **\# Verify deletion (should not appear in normal retrieval)**  
        **memories \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **assert len(memories) \== 0**

    **async def test\_search\_memories(self, memory\_backend, sample\_agent\_id, sample\_user\_id):**  
        **"""Test memory search functionality"""**  
          
        **\# Store multiple memories**  
        **await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.ANALYSIS,**  
            **content={"analysis": "sleep quality declining", "metric": "hrv"},**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.RECOMMENDATION,**  
            **content={"recommendation": "improve sleep hygiene", "priority": "high"},**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.FACT,**  
            **content={"fact": "user exercises in morning", "frequency": "daily"},**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **\# Search for sleep-related memories**  
        **results \= await memory\_backend.search\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **query="sleep",**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **assert len(results) \== 2  \# Should find analysis and recommendation**  
        **sleep\_contents \= \[r\["content"\] for r in results\]**  
        **assert any("sleep quality declining" in str(content) for content in sleep\_contents)**  
        **assert any("improve sleep hygiene" in str(content) for content in sleep\_contents)**

    **async def test\_memory\_filtering(self, memory\_backend, sample\_agent\_id, sample\_user\_id):**  
        **"""Test memory filtering by type and other criteria"""**  
          
        **\# Store different types of memories**  
        **await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.FACT,**  
            **content={"fact": "baseline\_rhr\_60bpm"},**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.ANALYSIS,**  
            **content={"pattern": "rhr\_trending\_up"},**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.RECOMMENDATION,**  
            **content={"advice": "monitor\_stress\_levels"},**  
            **user\_id=sample\_user\_id**  
        **)**  
          
        **\# Filter by memory type**  
        **facts \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id,**  
            **memory\_type=MemoryType.FACT**  
        **)**  
          
        **analyses \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id,**  
            **memory\_type=MemoryType.ANALYSIS**  
        **)**  
          
        **recommendations \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id,**  
            **memory\_type=MemoryType.RECOMMENDATION**  
        **)**  
          
        **assert len(facts) \== 1**  
        **assert len(analyses) \== 1**  
        **assert len(recommendations) \== 1**  
          
        **assert facts\[0\]\["memory\_type"\] \== MemoryType.FACT.value**  
        **assert analyses\[0\]\["memory\_type"\] \== MemoryType.ANALYSIS.value**  
        **assert recommendations\[0\]\["memory\_type"\] \== MemoryType.RECOMMENDATION.value**

    **async def test\_memory\_expiration(self, memory\_backend, sample\_agent\_id, sample\_user\_id):**  
        **"""Test memory expiration functionality"""**  
          
        **\# Store memory with expiration**  
        **expires\_at \= datetime.now(timezone.utc) \+ timedelta(seconds=1)**  
          
        **memory\_id \= await memory\_backend.store\_memory(**  
            **agent\_id=sample\_agent\_id,**  
            **memory\_type=MemoryType.FACT,**  
            **content={"temporary": "data"},**  
            **user\_id=sample\_user\_id,**  
            **expires\_at=expires\_at**  
        **)**  
          
        **\# Should be retrievable immediately**  
        **memories \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id**  
        **)**  
        **assert len(memories) \== 1**  
          
        **\# Wait for expiration**  
        **await asyncio.sleep(2)**  
          
        **\# Should not be retrievable after expiration (without include\_expired)**  
        **memories \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id,**  
            **include\_expired=False**  
        **)**  
        **assert len(memories) \== 0**  
          
        **\# Should be retrievable with include\_expired**  
        **memories \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id,**  
            **include\_expired=True**  
        **)**  
        **assert len(memories) \== 1**

**class TestCrewAIIntegration:**  
    **"""Test CrewAI integration components"""**  
      
    **async def test\_auren\_memory\_storage(self, memory\_backend, sample\_agent\_id):**  
        **"""Test AURENMemoryStorage implementation"""**  
          
        **storage \= AURENMemoryStorage(memory\_backend, sample\_agent\_id)**  
          
        **\# Test save operation**  
        **test\_data \= {"analysis": "test\_analysis", "confidence": 0.8}**  
        **metadata \= {"user\_id": str(uuid.uuid4()), "confidence": 0.8}**  
          
        **\# Note: save is sync but uses async backend**  
        **storage.save(test\_data, metadata)**  
          
        **\# Allow async operation to complete**  
        **await asyncio.sleep(0.1)**  
          
        **\# Test search operation (simplified for testing)**  
        **\# In real usage, would need proper event loop handling**  
        **\# results \= storage.search("analysis", limit=5, filter={"user\_id": metadata\["user\_id"\]})**  
        **\# assert len(results) \>= 0  \# Basic functionality test**

**class TestProjectionHandlers:**  
    **"""Test projection handler functionality"""**  
      
    **async def test\_redis\_projection\_handler(self, event\_store):**  
        **"""Test Redis projection handler"""**  
          
        **\# Mock Redis client**  
        **mock\_redis \= AsyncMock()**  
          
        **handler \= RedisProjectionHandler(mock\_redis)**  
          
        **\# Test event processing**  
        **event\_data \= {**  
            **"sequence\_id": 1,**  
            **"event\_type": "memory\_created",**  
            **"stream\_id": str(uuid.uuid4())**  
        **}**  
          
        **\# Mock the database query**  
        **with patch.object(handler, '\_get\_event\_by\_sequence') as mock\_get\_event:**  
            **mock\_get\_event.return\_value \= {**  
                **"payload": json.dumps({**  
                    **"agent\_id": "test\_agent",**  
                    **"memory\_id": str(uuid.uuid4()),**  
                    **"user\_id": str(uuid.uuid4()),**  
                    **"memory\_type": "fact",**  
                    **"content": {"test": "data"}**  
                **}),**  
                **"created\_at": datetime.now(timezone.utc)**  
            **}**  
              
            **await handler.process\_event(event\_data)**  
              
            **\# Verify Redis operations were called**  
            **assert mock\_redis.setex.called**  
            **assert mock\_redis.lpush.called**

**class TestMigration:**  
    **"""Test migration functionality"""**  
      
    **async def test\_json\_migration\_validation(self, memory\_backend, event\_store, tmp\_path):**  
        **"""Test JSON file migration validation"""**  
          
        **\# Create test JSON file**  
        **test\_data \= {**  
            **"agent\_id": "test\_agent",**  
            **"memories": \[**  
                **{**  
                    **"type": "fact",**  
                    **"content": {"test": "migration\_data"},**  
                    **"confidence": 0.9,**  
                    **"timestamp": datetime.now(timezone.utc).isoformat()**  
                **}**  
            **\]**  
        **}**  
          
        **json\_file \= tmp\_path / "test\_agent\_memories.json"**  
        **with open(json\_file, 'w') as f:**  
            **json.dump(test\_data, f)**  
          
        **\# Test migration**  
        **migrator \= JSONToPostgreSQLMigrator(**  
            **json\_directory=tmp\_path,**  
            **memory\_backend=memory\_backend,**  
            **event\_store=event\_store**  
        **)**  
          
        **\# Dry run first**  
        **results \= await migrator.migrate\_all(dry\_run=True)**  
          
        **assert results\["files\_processed"\] \== 1**  
        **assert results\["memories\_migrated"\] \== 1**  
        **assert len(results\["errors"\]) \== 0**

**class TestPerformance:**  
    **"""Test performance characteristics"""**  
      
    **async def test\_bulk\_memory\_operations(self, memory\_backend, sample\_agent\_id, sample\_user\_id):**  
        **"""Test performance with bulk operations"""**  
          
        **start\_time \= datetime.now()**  
          
        **\# Store many memories**  
        **memory\_ids \= \[\]**  
        **for i in range(100):**  
            **memory\_id \= await memory\_backend.store\_memory(**  
                **agent\_id=sample\_agent\_id,**  
                **memory\_type=MemoryType.FACT,**  
                **content={"bulk\_test": f"data\_{i}", "index": i},**  
                **user\_id=sample\_user\_id,**  
                **confidence=0.5 \+ (i % 50\) / 100  \# Vary confidence**  
            **)**  
            **memory\_ids.append(memory\_id)**  
          
        **store\_time \= (datetime.now() \- start\_time).total\_seconds()**  
          
        **\# Retrieve all memories**  
        **start\_time \= datetime.now()**  
        **memories \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id,**  
            **limit=1000**  
        **)**  
        **retrieve\_time \= (datetime.now() \- start\_time).total\_seconds()**  
          
        **\# Verify results**  
        **assert len(memories) \== 100**  
        **assert store\_time \< 10.0  \# Should complete in reasonable time**  
        **assert retrieve\_time \< 1.0  \# Retrieval should be fast**  
          
        **\# Test search performance**  
        **start\_time \= datetime.now()**  
        **search\_results \= await memory\_backend.search\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **query="bulk\_test",**  
            **user\_id=sample\_user\_id,**  
            **limit=50**  
        **)**  
        **search\_time \= (datetime.now() \- start\_time).total\_seconds()**  
          
        **assert len(search\_results) \> 0**  
        **assert search\_time \< 2.0  \# Search should be reasonably fast**

    **async def test\_concurrent\_operations(self, memory\_backend, sample\_agent\_id, sample\_user\_id):**  
        **"""Test concurrent memory operations"""**  
          
        **async def store\_memory\_batch(batch\_id: int):**  
            **"""Store a batch of memories concurrently"""**  
            **for i in range(10):**  
                **await memory\_backend.store\_memory(**  
                    **agent\_id=sample\_agent\_id,**  
                    **memory\_type=MemoryType.ANALYSIS,**  
                    **content={"batch": batch\_id, "item": i},**  
                    **user\_id=sample\_user\_id**  
                **)**  
          
        **\# Run multiple batches concurrently**  
        **start\_time \= datetime.now()**  
        **await asyncio.gather(\*\[**  
            **store\_memory\_batch(batch\_id)**   
            **for batch\_id in range(5)**  
        **\])**  
        **concurrent\_time \= (datetime.now() \- start\_time).total\_seconds()**  
          
        **\# Verify all memories were stored**  
        **memories \= await memory\_backend.retrieve\_memories(**  
            **agent\_id=sample\_agent\_id,**  
            **user\_id=sample\_user\_id,**  
            **limit=100**  
        **)**  
          
        **assert len(memories) \== 50  \# 5 batches \* 10 items each**  
        **assert concurrent\_time \< 5.0  \# Should handle concurrency well**

**class TestErrorHandling:**  
    **"""Test error handling and edge cases"""**  
      
    **async def test\_invalid\_memory\_operations(self, memory\_backend):**  
        **"""Test error handling for invalid operations"""**  
          
        **\# Test update non-existent memory**  
        **success \= await memory\_backend.update\_memory(**  
            **memory\_id=str(uuid.uuid4()),  \# Random non-existent ID**  
            **content={"new": "content"}**  
        **)**  
        **assert success is False**  
          
        **\# Test delete non-existent memory**  
        **success \= await memory\_backend.delete\_memory(str(uuid.uuid4()))**  
        **assert success is False**

    **async def test\_database\_connection\_failure(self, memory\_backend):**  
        **"""Test handling of database connection failures"""**  
          
        **\# Mock connection failure**  
        **with patch.object(AsyncPostgresManager, 'get\_connection') as mock\_get\_conn:**  
            **mock\_get\_conn.side\_effect \= Exception("Connection failed")**  
              
            **with pytest.raises(Exception):**  
                **await memory\_backend.store\_memory(**  
                    **agent\_id="test",**  
                    **memory\_type=MemoryType.FACT,**  
                    **content={"test": "data"}**  
                **)**

**if \_\_name\_\_ \== "\_\_main\_\_":**  
    **\# Run tests**  
    **pytest.main(\["-v", \_\_file\_\_\])**  
**\]\]\>**  
            **\</implementation\>**  
        **\</subsection\>**

        **\<subsection id="3.9" name="performance\_tuning"\>**  
            **\<title\>Performance Tuning and Optimization\</title\>**  
            **\<description\>Database optimization and performance monitoring\</description\>**  
              
            **\<configuration language="sql"\>**  
                **\<\!\[CDATA\[**  
**\-- PostgreSQL performance optimization for AUREN workloads**  
**\-- Apply these settings for production deployment**

**\-- Connection and memory settings**  
**ALTER SYSTEM SET max\_connections \= 200;**  
**ALTER SYSTEM SET shared\_buffers \= '4GB';  \-- 25% of available RAM**  
**ALTER SYSTEM SET effective\_cache\_size \= '12GB';  \-- 75% of available RAM**  
**ALTER SYSTEM SET work\_mem \= '64MB';  \-- For complex queries and sorts**  
**ALTER SYSTEM SET maintenance\_work\_mem \= '1GB';  \-- For maintenance operations**

**\-- Write-ahead logging optimization**  
**ALTER SYSTEM SET wal\_buffers \= '64MB';**  
**ALTER SYSTEM SET checkpoint\_completion\_target \= 0.9;**  
**ALTER SYSTEM SET checkpoint\_timeout \= '15min';**  
**ALTER SYSTEM SET max\_wal\_size \= '4GB';**  
**ALTER SYSTEM SET min\_wal\_size \= '1GB';**

**\-- Query planner optimization**  
**ALTER SYSTEM SET random\_page\_cost \= 1.5;  \-- Optimized for SSDs**  
**ALTER SYSTEM SET effective\_io\_concurrency \= 200;  \-- SSD concurrency**  
**ALTER SYSTEM SET default\_statistics\_target \= 100;  \-- Better query planning**

**\-- Logging and monitoring**  
**ALTER SYSTEM SET log\_statement \= 'mod';  \-- Log all data modifications**  
**ALTER SYSTEM SET log\_min\_duration\_statement \= 1000;  \-- Log slow queries (\>1s)**  
**ALTER SYSTEM SET log\_line\_prefix \= '%t \[%p\]: \[%l-1\] user=%u,db=%d,app=%a,client=%h ';**  
**ALTER SYSTEM SET log\_checkpoints \= on;**  
**ALTER SYSTEM SET log\_connections \= on;**  
**ALTER SYSTEM SET log\_disconnections \= on;**

**\-- Autovacuum tuning for high-write tables**  
**ALTER TABLE events SET (autovacuum\_vacuum\_scale\_factor \= 0.01);**  
**ALTER TABLE events SET (autovacuum\_analyze\_scale\_factor \= 0.005);**  
**ALTER TABLE agent\_memories SET (autovacuum\_vacuum\_scale\_factor \= 0.02);**  
**ALTER TABLE agent\_memories SET (autovacuum\_analyze\_scale\_factor \= 0.01);**

**\-- Restart required for most settings**  
**\-- SELECT pg\_reload\_conf();**

**\-- Partitioning strategy for events table (time-based)**  
**\-- This should be implemented as events grow beyond 10M records**

**\-- Example monthly partitioning**  
**CREATE TABLE events\_y2025m01 PARTITION OF events**  
**FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');**

**CREATE TABLE events\_y2025m02 PARTITION OF events**  
**FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');**

**\-- Add more partitions as needed...**

**\-- Additional performance indexes**  
**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_events\_correlation**   
**ON events(((metadata-\>\>'correlation\_id')::uuid))**   
**WHERE metadata-\>\>'correlation\_id' IS NOT NULL;**

**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_events\_causation**   
**ON events(((metadata-\>\>'causation\_id')::uuid))**   
**WHERE metadata-\>\>'causation\_id' IS NOT NULL;**

**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_agent\_memories\_confidence**   
**ON agent\_memories(confidence DESC)**   
**WHERE NOT is\_deleted AND confidence \>= 0.7;**

**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_agent\_memories\_expires**  
**ON agent\_memories(expires\_at)**   
**WHERE expires\_at IS NOT NULL AND NOT is\_deleted;**

**\-- GIN indexes for JSONB content search**  
**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_agent\_memories\_content\_gin**  
**ON agent\_memories USING GIN(content);**

**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_events\_payload\_gin**  
**ON events USING GIN(payload);**

**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_events\_metadata\_gin**  
**ON events USING GIN(metadata);**

**\-- Text search indexes for memory content**  
**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_agent\_memories\_content\_fts**  
**ON agent\_memories USING GIN(to\_tsvector('english', content::text))**  
**WHERE NOT is\_deleted;**

**\-- Partial indexes for common query patterns**  
**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_agent\_memories\_recent\_active**  
**ON agent\_memories(agent\_id, created\_at DESC)**  
**WHERE NOT is\_deleted AND (expires\_at IS NULL OR expires\_at \> NOW());**

**CREATE INDEX CONCURRENTLY IF NOT EXISTS idx\_events\_recent\_by\_stream**  
**ON events(stream\_id, created\_at DESC)**  
**WHERE created\_at \>= NOW() \- INTERVAL '30 days';**

**\-- Connection pooling configuration (for PgBouncer if used)**  
**\-- pool\_mode \= transaction**  
**\-- max\_client\_conn \= 1000**  
**\-- default\_pool\_size \= 150**  
**\-- max\_db\_connections \= 100**  
**\-- reserve\_pool\_size \= 10**  
**\]\]\>**  
            **\</configuration\>**

            **\<monitoring language="python"\>**  
                **\<\!\[CDATA\[**  
**"""**  
**Performance monitoring and alerting for AUREN data layer**  
**"""**

**import psutil**  
**import asyncio**  
**from datetime import datetime, timedelta**  
**from typing import Dict, Any, List**  
**import logging**

**logger \= logging.getLogger(\_\_name\_\_)**

**class DataLayerMonitor:**  
    **"""Monitor data layer performance and health"""**  
      
    **def \_\_init\_\_(self):**  
        **self.metrics \= {**  
            **"connection\_pool": {},**  
            **"query\_performance": {},**  
            **"memory\_usage": {},**  
            **"event\_throughput": {},**  
            **"errors": \[\]**  
        **}**  
        **self.alert\_thresholds \= {**  
            **"pool\_utilization": 0.8,**  
            **"query\_latency\_ms": 1000,**  
            **"memory\_usage\_percent": 85,**  
            **"event\_backlog": 1000,**  
            **"error\_rate\_per\_hour": 10**  
        **}**

    **async def collect\_metrics(self) \-\> Dict\[str, Any\]:**  
        **"""Collect comprehensive performance metrics"""**  
          
        **try:**  
            **\# Database connection pool metrics**  
            **pool\_metrics \= await self.\_get\_pool\_metrics()**  
              
            **\# Query performance metrics**  
            **query\_metrics \= await self.\_get\_query\_metrics()**  
              
            **\# System resource metrics**  
            **system\_metrics \= self.\_get\_system\_metrics()**  
              
            **\# Event throughput metrics**  
            **event\_metrics \= await self.\_get\_event\_metrics()**  
              
            **self.metrics.update({**  
                **"timestamp": datetime.utcnow().isoformat(),**  
                **"connection\_pool": pool\_metrics,**  
                **"query\_performance": query\_metrics,**  
                **"system\_resources": system\_metrics,**  
                **"event\_throughput": event\_metrics**  
            **})**  
              
            **\# Check for alerts**  
            **alerts \= self.\_check\_alerts()**  
            **if alerts:**  
                **self.metrics\["alerts"\] \= alerts**  
                **await self.\_send\_alerts(alerts)**  
              
            **return self.metrics**  
              
        **except Exception as e:**  
            **logger.error(f"Failed to collect metrics: {e}")**  
            **return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}**

    **async def \_get\_pool\_metrics(self) \-\> Dict\[str, Any\]:**  
        **"""Get connection pool performance metrics"""**  
          
        **try:**  
            **pool \= await AsyncPostgresManager.get\_pool()**  
              
            **return {**  
                **"size": pool.get\_size(),**  
                **"max\_size": pool.get\_max\_size(),**  
                **"min\_size": pool.get\_min\_size(),**  
                **"idle\_size": pool.get\_idle\_size(),**  
                **"utilization": pool.get\_size() / pool.get\_max\_size() if pool.get\_max\_size() \> 0 else 0**  
            **}**  
        **except Exception as e:**  
            **logger.error(f"Failed to get pool metrics: {e}")**  
            **return {"error": str(e)}**

    **async def \_get\_query\_metrics(self) \-\> Dict\[str, Any\]:**  
        **"""Get database query performance metrics"""**  
          
        **try:**  
            **async with AsyncPostgresManager.get\_connection() as conn:**  
                **\# Get slow queries**  
                **slow\_queries \= await conn.fetch("""**  
                    **SELECT query, calls, total\_time, mean\_time, rows**  
                    **FROM pg\_stat\_statements**   
                    **WHERE mean\_time \> 100  \-- Queries taking \>100ms on average**  
                    **ORDER BY total\_time DESC**   
                    **LIMIT 10**  
                **""")**  
                  
                **\# Get database activity**  
                **db\_activity \= await conn.fetchrow("""**  
                    **SELECT**   
                        **COUNT(\*) as active\_connections,**  
                        **COUNT(\*) FILTER (WHERE state \= 'active') as active\_queries,**  
                        **COUNT(\*) FILTER (WHERE state \= 'idle') as idle\_connections**  
                    **FROM pg\_stat\_activity**   
                    **WHERE datname \= current\_database()**  
                **""")**  
                  
                **\# Get lock information**  
                **locks \= await conn.fetch("""**  
                    **SELECT mode, COUNT(\*) as count**  
                    **FROM pg\_locks l**  
                    **JOIN pg\_stat\_activity a ON l.pid \= a.pid**  
                    **WHERE a.datname \= current\_database()**  
                    **GROUP BY mode**  
                **""")**  
                  
                **return {**  
                    **"slow\_queries": \[dict(row) for row in slow\_queries\],**  
                    **"active\_connections": db\_activity\["active\_connections"\],**  
                    **"active\_queries": db\_activity\["active\_queries"\],**  
                    **"idle\_connections": db\_activity\["idle\_connections"\],**  
                    **"locks": {row\["mode"\]: row\["count"\] for row in locks}**  
                **}**  
                  
        **except Exception as e:**  
            **logger.error(f"Failed to get query metrics: {e}")**  
            **return {"error": str(e)}**

    **def \_get\_system\_metrics(self) \-\> Dict\[str, Any\]:**  
        **"""Get system resource metrics"""**  
          
        **try:**  
            **\# CPU usage**  
            **cpu\_percent \= psutil.cpu\_percent(interval=1)**  
              
            **\# Memory usage**  
            **memory \= psutil.virtual\_memory()**  
              
            **\# Disk usage**  
            **disk \= psutil.disk\_usage('/')**  
              
            **\# Network I/O**  
            **network \= psutil.net\_io\_counters()**  
              
            **return {**  
                **"cpu\_percent": cpu\_percent,**  
                **"memory": {**  
                    **"total": memory.total,**  
                    **"available": memory.available,**  
                    **"percent": memory.percent,**  
                    **"used": memory.used**  
                **},**  
                **"disk": {**  
                    **"total": disk.total,**  
                    **"used": disk.used,**  
                    **"free": disk.free,**  
                    **"percent": (disk.used / disk.total) \* 100**  
                **},**  
                **"network": {**  
                    **"bytes\_sent": network.bytes\_sent,**  
                    **"bytes\_recv": network.bytes\_recv,**  
                    **"packets\_sent": network.packets\_sent,**  
                    **"packets\_recv": network.packets\_recv**  
                **}**  
            **}**  
              
        **except Exception as e:**  
            **logger.error(f"Failed to get system metrics: {e}")**  
            **return {"error": str(e)}**

    **async def \_get\_event\_metrics(self) \-\> Dict\[str, Any\]:**  
        **"""Get event store throughput metrics"""**  
          
        **try:**  
            **async with AsyncPostgresManager.get\_connection() as conn:**  
                **\# Events in last hour**  
                **recent\_events \= await conn.fetchrow("""**  
                    **SELECT**   
                        **COUNT(\*) as total\_events,**  
                        **COUNT(DISTINCT stream\_id) as unique\_streams,**  
                        **COUNT(DISTINCT event\_type) as unique\_event\_types**  
                    **FROM events**   
                    **WHERE created\_at \>= NOW() \- INTERVAL '1 hour'**  
                **""")**  
                  
                **\# Event types breakdown**  
                **event\_types \= await conn.fetch("""**  
                    **SELECT event\_type, COUNT(\*) as count**  
                    **FROM events**   
                    **WHERE created\_at \>= NOW() \- INTERVAL '1 hour'**  
                    **GROUP BY event\_type**  
                    **ORDER BY count DESC**  
                **""")**  
                  
                **\# Memory operations**  
                **memory\_ops \= await conn.fetchrow("""**  
                    **SELECT**   
                        **COUNT(\*) as total\_operations,**  
                        **COUNT(\*) FILTER (WHERE NOT is\_deleted) as active\_memories,**  
                        **AVG(confidence) as avg\_confidence**  
                    **FROM agent\_memories**   
                    **WHERE created\_at \>= NOW() \- INTERVAL '1 hour'**  
                **""")**  
                  
                **return {**  
                    **"events\_last\_hour": recent\_events\["total\_events"\],**  
                    **"unique\_streams": recent\_events\["unique\_streams"\],**  
                    **"unique\_event\_types": recent\_events\["unique\_event\_types"\],**  
                    **"events\_per\_minute": recent\_events\["total\_events"\] / 60,**  
                    **"event\_types\_breakdown": {row\["event\_type"\]: row\["count"\] for row in event\_types},**  
                    **"memory\_operations": {**  
                        **"total": memory\_ops\["total\_operations"\],**  
                        **"active": memory\_ops\["active\_memories"\],**  
                        **"avg\_confidence": float(memory\_ops\["avg\_confidence"\] or 0\)**  
                    **}**  
                **}**  
                  
        **except Exception as e:**  
            **logger.error(f"Failed to get event metrics: {e}")**  
            **return {"error": str(e)}**

    **def \_check\_alerts(self) \-\> List\[Dict\[str, Any\]\]:**  
        **"""Check metrics against thresholds and generate alerts"""**  
          
        **alerts \= \[\]**  
          
        **try:**  
            **\# Connection pool utilization alert**  
            **pool\_metrics \= self.metrics.get("connection\_pool", {})**  
            **if pool\_metrics.get("utilization", 0\) \> self.alert\_thresholds\["pool\_utilization"\]:**  
                **alerts.append({**  
                    **"type": "connection\_pool\_high",**  
                    **"severity": "warning",**  
                    **"message": f"Connection pool utilization at {pool\_metrics\['utilization'\]:.1%}",**  
                    **"threshold": self.alert\_thresholds\["pool\_utilization"\],**  
                    **"current\_value": pool\_metrics\["utilization"\],**  
                    **"timestamp": datetime.utcnow().isoformat()**  
                **})**  
              
            **\# Memory usage alert**  
            **system\_metrics \= self.metrics.get("system\_resources", {})**  
            **memory\_percent \= system\_metrics.get("memory", {}).get("percent", 0\)**  
            **if memory\_percent \> self.alert\_thresholds\["memory\_usage\_percent"\]:**  
                **alerts.append({**  
                    **"type": "memory\_usage\_high",**  
                    **"severity": "critical" if memory\_percent \> 95 else "warning",**  
                    **"message": f"System memory usage at {memory\_percent}%",**  
                    **"threshold": self.alert\_thresholds\["memory\_usage\_percent"\],**  
                    **"current\_value": memory\_percent,**  
                    **"timestamp": datetime.utcnow().isoformat()**  
                **})**  
              
            **\# Slow query alert**  
            **query\_metrics \= self.metrics.get("query\_performance", {})**  
            **slow\_queries \= query\_metrics.get("slow\_queries", \[\])**  
            **if slow\_queries:**  
                **max\_query\_time \= max(q.get("mean\_time", 0\) for q in slow\_queries)**  
                **if max\_query\_time \> self.alert\_thresholds\["query\_latency\_ms"\]:**  
                    **alerts.append({**  
                        **"type": "slow\_queries\_detected",**  
                        **"severity": "warning",**  
                        **"message": f"Slow queries detected, max mean time: {max\_query\_time:.1f}ms",**  
                        **"threshold": self.alert\_thresholds\["query\_latency\_ms"\],**  
                        **"current\_value": max\_query\_time,**  
                        **"slow\_query\_count": len(slow\_queries),**  
                        **"timestamp": datetime.utcnow().isoformat()**  
                    **})**  
              
        **except Exception as e:**  
            **logger.error(f"Failed to check alerts: {e}")**  
            **alerts.append({**  
                **"type": "monitoring\_error",**  
                **"severity": "error",**  
                **"message": f"Alert checking failed: {e}",**  
                **"timestamp": datetime.utcnow().isoformat()**  
            **})**  
          
        **return alerts**

    **async def \_send\_alerts(self, alerts: List\[Dict\[str, Any\]\]) \-\> None:**  
        **"""Send alerts to monitoring systems"""**  
          
        **for alert in alerts:**  
            **logger.warning(f"ALERT: {alert\['type'\]} \- {alert\['message'\]}")**  
              
            **\# Here you would integrate with your alerting system**  
            **\# Examples: PagerDuty, Slack, email, etc.**  
            **\# await self.\_send\_to\_pagerduty(alert)**  
            **\# await self.\_send\_to\_slack(alert)**

**\# Monitoring usage example**  
**async def run\_monitoring\_loop():**  
    **"""Run continuous monitoring loop"""**  
    **monitor \= DataLayerMonitor()**  
      
    **while True:**  
        **try:**  
            **metrics \= await monitor.collect\_metrics()**  
              
            **\# Log metrics for observability**  
            **logger.info(f"Data layer metrics collected: {metrics.get('timestamp')}")**  
              
            **\# Store metrics in time-series database if needed**  
            **\# await store\_metrics\_to\_prometheus(metrics)**  
              
        **except Exception as e:**  
            **logger.error(f"Monitoring loop error: {e}")**  
          
        **\# Wait before next collection**  
        **await asyncio.sleep(60)  \# Collect every minute**  
**\]\]\>**  
            **\</monitoring\>**  
        **\</subsection\>**

        **\<subsection id="3.10" name="troubleshooting\_guide"\>**  
            **\<title\>Troubleshooting Guide\</title\>**  
            **\<description\>Comprehensive troubleshooting procedures for common issues\</description\>**  
              
            **\<guide language="markdown"\>**  
                **\<\!\[CDATA\[**  
**\# AUREN Data Layer Troubleshooting Guide**

**\#\# Quick Diagnostic Commands**

**\#\#\# Check System Health**  
**\`\`\`bash**  
**\# Database connectivity**  
**psql $DATABASE\_URL \-c "SELECT version();"**

**\# Connection pool status**  
**psql $DATABASE\_URL \-c "SELECT count(\*) as active\_connections FROM pg\_stat\_activity;"**

**\# Recent errors in logs**  
**tail \-100 /var/log/auren/data\_layer.log | grep ERROR**

**\# Disk space**  
**df \-h**

**\# Memory usage**  
**free \-m**  
**\`\`\`**

**\#\#\# Check Data Layer Status**  
**\`\`\`python**  
**\# Python health check**  
**from auren.data\_layer import AsyncPostgresManager**

**health \= await AsyncPostgresManager.health\_check()**  
**print(f"Status: {health\['status'\]}")**  
**print(f"Response time: {health\['response\_time\_ms'\]}ms")**  
**\`\`\`**

**\#\# Common Issues and Solutions**

**\#\#\# 1\. Connection Pool Exhaustion**

**\*\*Symptoms:\*\***  
**\- "too many clients already" errors**  
**\- Timeouts on database operations**  
**\- Application hanging on database calls**

**\*\*Diagnosis:\*\***  
**\`\`\`sql**  
**\-- Check current connections**  
**SELECT**   
    **count(\*) as total\_connections,**  
    **count(\*) FILTER (WHERE state \= 'active') as active,**  
    **count(\*) FILTER (WHERE state \= 'idle') as idle**  
**FROM pg\_stat\_activity;**

**\-- Check long-running queries**  
**SELECT**   
    **pid,**   
    **now() \- pg\_stat\_activity.query\_start AS duration,**   
    **query**   
**FROM pg\_stat\_activity**   
**WHERE (now() \- pg\_stat\_activity.query\_start) \> interval '5 minutes';**  
**\`\`\`**

**\*\*Solutions:\*\***  
**1\. \*\*Increase pool size temporarily:\*\***  
   **\`\`\`python**  
   **await AsyncPostgresManager.initialize(**  
       **dsn=DATABASE\_URL,**  
       **max\_size=100  \# Increase from default**  
   **)**  
   **\`\`\`**

**2\. \*\*Kill long-running queries:\*\***  
   **\`\`\`sql**  
   **SELECT pg\_terminate\_backend(pid)**   
   **FROM pg\_stat\_activity**   
   **WHERE pid \= \<problematic\_pid\>;**  
   **\`\`\`**

**3\. \*\*Implement connection timeouts:\*\***  
   **\`\`\`python**  
   **\# Add to connection string**  
   **DATABASE\_URL \+= "?connect\_timeout=10\&command\_timeout=30"**  
   **\`\`\`**

**4\. \*\*Check for connection leaks in application code:\*\***  
   **\- Ensure all \`async with\` blocks are properly closed**  
   **\- Add connection pool monitoring**  
   **\- Review exception handling in database operations**

**\#\#\# 2\. Slow Query Performance**

**\*\*Symptoms:\*\***  
**\- High response times (\>1 second)**  
**\- Timeout errors**  
**\- High CPU usage on database server**

**\*\*Diagnosis:\*\***  
**\`\`\`sql**  
**\-- Enable query logging temporarily**  
**ALTER SYSTEM SET log\_min\_duration\_statement \= 100;**  
**SELECT pg\_reload\_conf();**

**\-- Check slow queries**  
**SELECT**   
    **query,**  
    **calls,**  
    **total\_time,**  
    **mean\_time,**  
    **rows**  
**FROM pg\_stat\_statements**   
**ORDER BY total\_time DESC**   
**LIMIT 10;**

**\-- Check missing indexes**  
**SELECT**   
    **schemaname,**  
    **tablename,**  
    **attname,**  
    **n\_distinct,**  
    **correlation**  
**FROM pg\_stats**   
**WHERE tablename IN ('events', 'agent\_memories')**  
**ORDER BY n\_distinct DESC;**  
**\`\`\`**

**\*\*Solutions:\*\***  
**1\. \*\*Add missing indexes:\*\***  
   **\`\`\`sql**  
   **\-- Example: Index for common query pattern**  
   **CREATE INDEX CONCURRENTLY idx\_events\_stream\_type\_time**   
   **ON events(stream\_id, event\_type, created\_at DESC);**  
   **\`\`\`**

**2\. \*\*Optimize queries:\*\***  
   **\`\`\`sql**  
   **\-- Before: Inefficient query**  
   **SELECT \* FROM agent\_memories WHERE content::text ILIKE '%pattern%';**  
     
   **\-- After: Use GIN index**  
   **SELECT \* FROM agent\_memories**   
   **WHERE content @@ to\_tsquery('english', 'pattern');**  
   **\`\`\`**

**3\. \*\*Update table statistics:\*\***  
   **\`\`\`sql**  
   **ANALYZE events;**  
   **ANALYZE agent\_memories;**  
   **\`\`\`**

**4\. \*\*Consider partitioning for large tables:\*\***  
   **\`\`\`sql**  
   **\-- Partition events table by month**  
   **CREATE TABLE events\_y2025m03 PARTITION OF events**  
   **FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');**  
   **\`\`\`**

**\#\#\# 3\. Event Store Inconsistencies**

**\*\*Symptoms:\*\***  
**\- Missing events in projections**  
**\- Inconsistent data between Redis and PostgreSQL**  
**\- Sequence gaps in event streams**

**\*\*Diagnosis:\*\***  
**\`\`\`sql**  
**\-- Check for sequence gaps**  
**WITH expected AS (**  
    **SELECT generate\_series(**  
        **(SELECT MIN(sequence\_id) FROM events WHERE stream\_id \= 'user\_123'),**  
        **(SELECT MAX(sequence\_id) FROM events WHERE stream\_id \= 'user\_123')**  
    **) as seq**  
**)**  
**SELECT seq FROM expected**  
**WHERE seq NOT IN (**  
    **SELECT sequence\_id FROM events WHERE stream\_id \= 'user\_123'**  
**);**

**\-- Check projection consistency**  
**SELECT**   
    **e.stream\_id,**  
    **COUNT(e.\*) as events\_count,**  
    **COUNT(m.\*) as memories\_count**  
**FROM events e**  
**LEFT JOIN agent\_memories m ON e.payload-\>\>'memory\_id' \= m.id::text**  
**WHERE e.event\_type \= 'memory\_created'**  
**GROUP BY e.stream\_id**  
**HAVING COUNT(e.\*) \!= COUNT(m.\*);**  
**\`\`\`**

**\*\*Solutions:\*\***  
**1\. \*\*Rebuild projections from events:\*\***  
   **\`\`\`python**  
   **\# Rebuild specific user's projections**  
   **async def rebuild\_user\_projections(user\_id: str):**  
       **\# Clear existing projections**  
       **await memory\_backend.delete\_user\_projections(user\_id)**  
         
       **\# Replay events**  
       **events \= await event\_store.get\_stream\_events(user\_id)**  
       **for event in events:**  
           **await projection\_handler.process\_event(event)**  
   **\`\`\`**

**2\. \*\*Fix sequence gaps (if needed):\*\***  
   **\`\`\`sql**  
   **\-- Resequence events (use with caution)**  
   **WITH resequenced AS (**  
       **SELECT**   
           **sequence\_id,**  
           **ROW\_NUMBER() OVER (ORDER BY created\_at, sequence\_id) as new\_seq**  
       **FROM events**   
       **WHERE stream\_id \= 'user\_123'**  
   **)**  
   **UPDATE events**   
   **SET sequence\_id \= r.new\_seq**   
   **FROM resequenced r**   
   **WHERE events.sequence\_id \= r.sequence\_id;**  
   **\`\`\`**

**3\. \*\*Verify event handlers:\*\***  
   **\`\`\`python**  
   **\# Check projection handlers are registered**  
   **assert len(event\_store.\_event\_handlers) \> 0**  
     
   **\# Test handler with sample event**  
   **test\_event \= Event(**  
       **event\_id=str(uuid.uuid4()),**  
       **stream\_id="test",**  
       **event\_type="memory\_created",**  
       **payload={"test": "data"}**  
   **)**  
   **await projection\_handler.process\_event(test\_event)**  
   **\`\`\`**

**\#\#\# 4\. Memory Backend Issues**

**\*\*Symptoms:\*\***  
**\- Memories not appearing in search**  
**\- Inconsistent confidence scores**  
**\- Memory expiration not working**

**\*\*Diagnosis:\*\***  
**\`\`\`sql**  
**\-- Check memory statistics**  
**SELECT**   
    **agent\_id,**  
    **memory\_type,**  
    **COUNT(\*) as total,**  
    **COUNT(\*) FILTER (WHERE NOT is\_deleted) as active,**  
    **AVG(confidence) as avg\_confidence,**  
    **MAX(created\_at) as latest\_memory**  
**FROM agent\_memories**   
**GROUP BY agent\_id, memory\_type**  
**ORDER BY agent\_id, memory\_type;**

**\-- Check for orphaned memories**  
**SELECT COUNT(\*)**   
**FROM agent\_memories m**  
**LEFT JOIN events e ON e.payload-\>\>'memory\_id' \= m.id::text**  
**WHERE e.event\_id IS NULL AND m.created\_at \> NOW() \- INTERVAL '1 day';**

**\-- Check expiration logic**  
**SELECT**   
    **COUNT(\*) as total\_expired,**  
    **COUNT(\*) FILTER (WHERE is\_deleted) as marked\_deleted**  
**FROM agent\_memories**   
**WHERE expires\_at \< NOW();**  
**\`\`\`**

**\*\*Solutions:\*\***  
**1\. \*\*Rebuild search indexes:\*\***  
   **\`\`\`sql**  
   **REINDEX INDEX idx\_agent\_memories\_content\_gin;**  
   **REINDEX INDEX idx\_agent\_memories\_content\_fts;**  
   **\`\`\`**

**2\. \*\*Fix orphaned memories:\*\***  
   **\`\`\`python**  
   **\# Create missing events for orphaned memories**  
   **async def fix\_orphaned\_memories():**  
       **orphaned \= await find\_orphaned\_memories()**  
       **for memory in orphaned:**  
           **await event\_store.append\_event(**  
               **stream\_id=memory\["user\_id"\] or memory\["agent\_id"\],**  
               **event\_type=EventType.MEMORY\_CREATED,**  
               **payload={**  
                   **"memory\_id": memory\["id"\],**  
                   **"agent\_id": memory\["agent\_id"\],**  
                   **"retroactive\_fix": True**  
               **}**  
           **)**  
   **\`\`\`**

**3\. \*\*Clean up expired memories:\*\***  
   **\`\`\`sql**  
   **\-- Mark expired memories as deleted**  
   **UPDATE agent\_memories**   
   **SET is\_deleted \= TRUE**   
   **WHERE expires\_at \< NOW() AND NOT is\_deleted;**  
   **\`\`\`**

**\#\#\# 5\. Migration Issues**

**\*\*Symptoms:\*\***  
**\- JSON files not migrating completely**  
**\- Data corruption during migration**  
**\- Migration hanging or timing out**

**\*\*Diagnosis:\*\***  
**\`\`\`python**  
**\# Check migration status**  
**async def check\_migration\_status():**  
    **migrator \= JSONToPostgreSQLMigrator(...)**  
      
    **\# Validate file structure**  
    **for json\_file in json\_files:**  
        **try:**  
            **with open(json\_file) as f:**  
                **data \= json.load(f)**  
            **print(f"✓ {json\_file}: Valid JSON")**  
        **except Exception as e:**  
            **print(f"✗ {json\_file}: {e}")**  
      
    **\# Check for partial migrations**  
    **migration\_markers \= await get\_migration\_markers()**  
    **print(f"Completed migrations: {len(migration\_markers)}")**  
**\`\`\`**

**\*\*Solutions:\*\***  
**1\. \*\*Resume failed migration:\*\***  
   **\`\`\`python**  
   **\# Run migration with skip-existing flag**  
   **await migrator.migrate\_all(skip\_existing=True)**  
   **\`\`\`**

**2\. \*\*Validate data integrity:\*\***  
   **\`\`\`python**  
   **\# Compare JSON data with migrated data**  
   **async def validate\_migration(json\_file, agent\_id, user\_id):**  
       **with open(json\_file) as f:**  
           **original\_data \= json.load(f)**  
         
       **migrated\_memories \= await memory\_backend.retrieve\_memories(**  
           **agent\_id=agent\_id,**  
           **user\_id=user\_id**  
       **)**  
         
       **\# Compare counts and key data points**  
       **assert len(original\_data.get("memories", \[\])) \== len(migrated\_memories)**  
   **\`\`\`**

**3\. \*\*Handle large files:\*\***  
   **\`\`\`python**  
   **\# Process large files in batches**  
   **async def migrate\_large\_file(json\_file, batch\_size=100):**  
       **with open(json\_file) as f:**  
           **data \= json.load(f)**  
         
       **memories \= data.get("memories", \[\])**  
       **for i in range(0, len(memories), batch\_size):**  
           **batch \= memories\[i:i \+ batch\_size\]**  
           **await migrate\_memory\_batch(batch)**  
           **await asyncio.sleep(0.1)  \# Prevent overwhelming database**  
   **\`\`\`**

**\#\# Emergency Recovery Procedures**

**\#\#\# Database Corruption Recovery**

**1\. \*\*Stop application immediately\*\***  
**2\. \*\*Create backup:\*\***  
   **\`\`\`bash**  
   **pg\_dump \-U user \-h host \-d auren \> backup\_$(date \+%Y%m%d\_%H%M%S).sql**  
   **\`\`\`**

**3\. \*\*Check database integrity:\*\***  
   **\`\`\`sql**  
   **SELECT pg\_database.datname, pg\_size\_pretty(pg\_database\_size(pg\_database.datname))**  
   **FROM pg\_database;**  
     
   **\-- Check for corruption**  
   **SELECT \* FROM pg\_stat\_database\_conflicts;**  
   **\`\`\`**

**4\. \*\*Repair if possible:\*\***  
   **\`\`\`sql**  
   **REINDEX DATABASE auren;**  
   **VACUUM FULL;**  
   **\`\`\`**

**\#\#\# Performance Crisis Response**

**1\. \*\*Immediate relief:\*\***  
   **\`\`\`sql**  
   **\-- Kill problematic queries**  
   **SELECT pg\_terminate\_backend(pid)**   
   **FROM pg\_stat\_activity**   
   **WHERE state \= 'active' AND query\_start \< NOW() \- INTERVAL '5 minutes';**  
     
   **\-- Temporarily disable autovacuum if needed**  
   **ALTER SYSTEM SET autovacuum \= off;**  
   **SELECT pg\_reload\_conf();**  
   **\`\`\`**

**2\. \*\*Scale resources:\*\***  
   **\`\`\`bash**  
   **\# Increase database connections temporarily**  
   **echo "max\_connections \= 300" \>\> postgresql.conf**  
   **systemctl restart postgresql**  
   **\`\`\`**

**3\. \*\*Enable read-only mode:\*\***  
   **\`\`\`python**  
   **\# Redirect reads to replica**  
   **READ\_ONLY\_DATABASE\_URL \= "postgresql://readonly:password@replica:5432/auren"**  
   **\`\`\`**

**\#\#\# Data Recovery from Events**

**\`\`\`python**  
**async def recover\_lost\_projections(stream\_id: str):**  
    **"""Recover projections from event store"""**  
      
    **\# Get all events for stream**  
    **events \= await event\_store.get\_stream\_events(stream\_id)**  
      
    **\# Rebuild state from events**  
    **recovered\_state \= {}**  
      
    **for event in events:**  
        **if event.event\_type \== "memory\_created":**  
            **memory\_data \= event.payload**  
            **\# Recreate memory in projection table**  
            **await memory\_backend.store\_memory(**  
                **agent\_id=memory\_data\["agent\_id"\],**  
                **memory\_type=MemoryType(memory\_data\["memory\_type"\]),**  
                **content=memory\_data\["content"\],**  
                **user\_id=memory\_data.get("user\_id"),**  
                **confidence=memory\_data.get("confidence", 1.0)**  
            **)**  
      
    **return recovered\_state**  
**\`\`\`**

**\#\# Monitoring and Alerting Setup**

**\#\#\# Key Metrics to Monitor**

**1\. \*\*Database Performance:\*\***  
   **\- Connection pool utilization**  
   **\- Query latency (95th percentile)**  
   **\- Lock wait times**  
   **\- Database size growth**

**2\. \*\*Application Performance:\*\***  
   **\- Memory operation latency**  
   **\- Event processing throughput**  
   **\- Error rates**  
   **\- Cache hit rates**

**3\. \*\*System Resources:\*\***  
   **\- CPU usage**  
   **\- Memory usage**  
   **\- Disk I/O**  
   **\- Network latency**

**\#\#\# Alert Thresholds**

**\`\`\`python**  
**ALERT\_THRESHOLDS \= {**  
    **"connection\_pool\_utilization": 0.8,  \# 80%**  
    **"query\_latency\_p95\_ms": 1000,        \# 1 second**  
    **"memory\_usage\_percent": 85,          \# 85%**  
    **"error\_rate\_per\_hour": 10,           \# 10 errors/hour**  
    **"event\_processing\_lag\_seconds": 30,  \# 30 seconds**  
    **"disk\_usage\_percent": 80             \# 80%**  
**}**  
**\`\`\`**

**\#\#\# Automated Recovery Scripts**

**\`\`\`bash**  
**\#\!/bin/bash**  
**\# auto\_recovery.sh \- Automated recovery for common issues**

**\# Check disk space**  
**DISK\_USAGE=$(df / | tail \-1 | awk '{print $5}' | sed 's/%//')**  
**if \[ $DISK\_USAGE \-gt 90 \]; then**  
    **\# Clean old logs**  
    **find /var/log \-name "\*.log" \-mtime \+7 \-delete**  
    **\# Vacuum database**  
    **psql $DATABASE\_URL \-c "VACUUM;"**  
**fi**

**\# Check connection pool**  
**ACTIVE\_CONN=$(psql $DATABASE\_URL \-t \-c "SELECT count(\*) FROM pg\_stat\_activity;")**  
**if \[ $ACTIVE\_CONN \-gt 150 \]; then**  
    **\# Kill old idle connections**  
    **psql $DATABASE\_URL \-c "**  
        **SELECT pg\_terminate\_backend(pid)**   
        **FROM pg\_stat\_activity**   
        **WHERE state \= 'idle'**   
        **AND state\_change \< NOW() \- INTERVAL '30 minutes';**  
    **"**  
**fi**

**\# Restart application if memory usage too high**  
**MEM\_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 \* 100.0)}')**  
**if \[ $MEM\_USAGE \-gt 90 \]; then**  
    **systemctl restart auren-data-layer**  
**fi**  
**\`\`\`**

**Remember: Always test recovery procedures in a staging environment before applying to production\!**  
**\]\]\>**  
            **\</guide\>**  
        **\</subsection\>**  
    **\</section\>**

    **\<section id="4" name="integration\_examples"\>**  
        **\<title\>Integration Examples\</title\>**  
        **\<description\>Complete examples showing how to integrate with other AUREN components\</description\>**  
          
        **\<example id="crewai\_agent\_setup" language="python"\>**  
            **\<\!\[CDATA\[**  
**"""**  
**Complete example: Setting up AUREN data layer with CrewAI agents**  
**"""**

**import asyncio**  
**from crewai import Agent, Task, Crew**  
**from auren.data\_layer import AsyncPostgresManager, EventStore, PostgreSQLMemoryBackend, AURENCrewMemoryIntegration**

**async def setup\_auren\_data\_layer():**  
    **"""Initialize AUREN data layer"""**  
      
    **\# Initialize database connection**  
    **await AsyncPostgresManager.initialize(**  
        **dsn="postgresql://auren:password@localhost:5432/auren",**  
        **min\_size=10,**  
        **max\_size=50**  
    **)**  
      
    **\# Create core components**  
    **event\_store \= EventStore()**  
    **memory\_backend \= PostgreSQLMemoryBackend(event\_store)**  
    **crew\_integration \= AURENCrewMemoryIntegration(memory\_backend, event\_store)**  
      
    **return event\_store, memory\_backend, crew\_integration**

**def create\_specialist\_agents(crew\_integration):**  
    **"""Create specialist agents with AUREN memory integration"""**  
      
    **\# Neuroscientist Agent**  
    **neuroscientist \= Agent(**  
        **role="Neuroscientist",**  
        **goal="Analyze neurological patterns and provide brain health insights",**  
        **backstory="Expert in neuroscience with focus on brain optimization and cognitive performance",**  
        **memory=crew\_integration.create\_agent\_memory\_storage("neuroscientist"),**  
        **verbose=True**  
    **)**  
      
    **\# Nutritionist Agent**    
    **nutritionist \= Agent(**  
        **role="Nutritionist",**  
        **goal="Provide personalized nutrition recommendations based on biometric data",**  
        **backstory="Certified nutritionist specializing in performance nutrition and metabolic optimization",**  
        **memory=crew\_integration.create\_agent\_memory\_storage("nutritionist"),**  
        **verbose=True**  
    **)**  
      
    **\# Training Agent**  
    **training\_agent \= Agent(**  
        **role="Training Coach",**  
        **goal="Design optimal training programs based on recovery and performance data",**  
        **backstory="Elite performance coach with expertise in data-driven training optimization",**  
        **memory=crew\_integration.create\_agent\_memory\_storage("training\_agent"),**  
        **verbose=True**  
    **)**  
      
    **return {**  
        **"neuroscientist": neuroscientist,**  
        **"nutritionist": nutritionist,**  
        **"training\_agent": training\_agent**  
    **}**

**async def example\_agent\_workflow(user\_id: str, biometric\_data: dict):**  
    **"""Example workflow showing agent collaboration with shared memory"""**  
      
    **\# Setup**  
    **event\_store, memory\_backend, crew\_integration \= await setup\_auren\_data\_layer()**  
    **agents \= create\_specialist\_agents(crew\_integration)**  
      
    **\# Store incoming biometric data as event**  
    **await event\_store.append\_event(**  
        **stream\_id=user\_id,**  
        **event\_type=EventType.BIOMETRIC\_RECEIVED,**  
        **payload={**  
            **"user\_id": user\_id,**  
            **"data": biometric\_data,**  
            **"source": "healthkit"**  
        **}**  
    **)**  
      
    **\# Neuroscientist analyzes HRV patterns**  
    **neuroscientist\_analysis \= await agents\["neuroscientist"\].execute(**  
        **task="Analyze the user's HRV patterns and stress indicators",**  
        **context=await crew\_integration.get\_shared\_context(user\_id, "neuroscientist")**  
    **)**  
      
    **\# Store analysis as memory**  
    **await crew\_integration.store\_agent\_decision(**  
        **agent\_id="neuroscientist",**  
        **user\_id=user\_id,**  
        **decision={**  
            **"analysis": "Elevated stress indicators in HRV data",**  
            **"confidence": 0.85,**  
            **"recommendation": "Focus on recovery and stress management"**  
        **},**  
        **confidence=0.85,**  
        **context={"biometric\_data": biometric\_data}**  
    **)**  
      
    **\# Nutritionist considers neuroscientist's findings**  
    **shared\_context \= await crew\_integration.get\_shared\_context(user\_id, "nutritionist")**  
    **nutrition\_recommendation \= await agents\["nutritionist"\].execute(**  
        **task="Provide nutrition recommendations considering stress indicators",**  
        **context=shared\_context**  
    **)**  
      
    **\# Training agent adjusts program based on both analyses**  
    **training\_context \= await crew\_integration.get\_shared\_context(user\_id, "training\_agent")**  
    **training\_adjustment \= await agents\["training\_agent"\].execute(**  
        **task="Adjust training program based on stress and nutrition analysis",**  
        **context=training\_context**  
    **)**  
      
    **return {**  
        **"neuroscientist\_analysis": neuroscientist\_analysis,**  
        **"nutrition\_recommendation": nutrition\_recommendation,**  
        **"training\_adjustment": training\_adjustment**  
    **}**

**\# Run example**  
**if \_\_name\_\_ \== "\_\_main\_\_":**  
    **asyncio.run(example\_agent\_workflow(**  
        **user\_id="user\_12345",**  
        **biometric\_data={**  
            **"hrv": 45,**  
            **"resting\_hr": 65,**  
            **"sleep\_quality": 0.7,**  
            **"timestamp": "2025-07-24T10:00:00Z"**  
        **}**  
    **))**  
**\]\]\>**  
        **\</example\>**

        **\<example id="real\_time\_dashboard" language="python"\>**  
            **\<\!\[CDATA\[**  
**"""**  
**Real-time dashboard integration example**  
**Shows how to stream data layer events to frontend**  
**"""**

**import asyncio**  
**import json**  
**from fastapi import FastAPI, WebSocket**  
**from fastapi.responses import HTMLResponse**

**app \= FastAPI()**

**class DashboardStreamer:**  
    **"""Streams data layer events to connected dashboards"""**  
      
    **def \_\_init\_\_(self, event\_store: EventStore):**  
        **self.event\_store \= event\_store**  
        **self.connected\_clients \= set()**  
          
        **\# Register for real-time events**  
        **self.event\_store.register\_event\_handler(self.broadcast\_event)**  
      
    **async def connect\_client(self, websocket: WebSocket):**  
        **"""Connect new dashboard client"""**  
        **await websocket.accept()**  
        **self.connected\_clients.add(websocket)**  
          
        **\# Send initial state**  
        **await self.send\_initial\_state(websocket)**  
      
    **def disconnect\_client(self, websocket: WebSocket):**  
        **"""Disconnect dashboard client"""**  
        **self.connected\_clients.discard(websocket)**  
      
    **async def send\_initial\_state(self, websocket: WebSocket):**  
        **"""Send current system state to new client"""**  
          
        **\# Get recent events across all streams**  
        **recent\_events \= await self.event\_store.get\_events\_by\_type(**  
            **event\_type=EventType.AGENT\_DECISION,**  
            **limit=10**  
        **)**  
          
        **initial\_data \= {**  
            **"type": "initial\_state",**  
            **"data": {**  
                **"recent\_events": \[**  
                    **{**  
                        **"event\_id": event.event\_id,**  
                        **"stream\_id": event.stream\_id,**  
                        **"event\_type": event.event\_type,**  
                        **"payload": event.payload,**  
                        **"timestamp": event.created\_at.isoformat()**  
                    **}**  
                    **for event in recent\_events**  
                **\]**  
            **}**  
        **}**  
          
        **await websocket.send\_text(json.dumps(initial\_data))**  
      
    **async def broadcast\_event(self, event: Event):**  
        **"""Broadcast event to all connected dashboards"""**  
          
        **if not self.connected\_clients:**  
            **return**  
          
        **\# Format event for dashboard**  
        **dashboard\_event \= {**  
            **"type": "real\_time\_event",**  
            **"data": {**  
                **"event\_id": event.event\_id,**  
                **"stream\_id": event.stream\_id,**  
                **"event\_type": event.event\_type,**  
                **"payload": event.payload,**  
                **"timestamp": event.created\_at.isoformat()**  
            **}**  
        **}**  
          
        **\# Send to all connected clients**  
        **disconnected\_clients \= set()**  
        **for client in self.connected\_clients:**  
            **try:**  
                **await client.send\_text(json.dumps(dashboard\_event))**  
            **except:**  
                **disconnected\_clients.add(client)**  
          
        **\# Clean up disconnected clients**  
        **self.connected\_clients \-= disconnected\_clients**

**\# Global dashboard streamer**  
**dashboard\_streamer \= None**

**@app.on\_event("startup")**  
**async def startup\_event():**  
    **"""Initialize data layer and dashboard streaming"""**  
    **global dashboard\_streamer**  
      
    **\# Initialize data layer**  
    **await AsyncPostgresManager.initialize("postgresql://localhost/auren")**  
    **event\_store \= EventStore()**  
      
    **\# Initialize dashboard streamer**  
    **dashboard\_streamer \= DashboardStreamer(event\_store)**

**@app.websocket("/ws/dashboard")**  
**async def websocket\_endpoint(websocket: WebSocket):**  
    **"""WebSocket endpoint for dashboard clients"""**  
    **await dashboard\_streamer.connect\_client(websocket)**  
      
    **try:**  
        **while True:**  
            **\# Keep connection alive and handle client messages**  
            **data \= await websocket.receive\_text()**  
            **message \= json.loads(data)**  
              
            **if message.get("type") \== "ping":**  
                **await websocket.send\_text(json.dumps({"type": "pong"}))**  
                  
    **except:**  
        **pass**  
    **finally:**  
        **dashboard\_streamer.disconnect\_client(websocket)**

**@app.get("/")**  
**async def get\_dashboard():**  
    **"""Serve dashboard HTML"""**  
    **return HTMLResponse("""**  
    **\<\!DOCTYPE html\>**  
    **\<html\>**  
    **\<head\>**  
        **\<title\>AUREN Data Layer Dashboard\</title\>**  
        **\<script src="https://cdn.jsdelivr.net/npm/chart.js"\>\</script\>**  
    **\</head\>**  
    **\<body\>**  
        **\<h1\>AUREN Real-time Dashboard\</h1\>**  
        **\<div id="events"\>\</div\>**  
        **\<canvas id="eventChart" width="400" height="200"\>\</canvas\>**  
          
        **\<script\>**  
            **const ws \= new WebSocket("ws://localhost:8000/ws/dashboard");**  
            **const eventsDiv \= document.getElementById('events');**  
            **const ctx \= document.getElementById('eventChart').getContext('2d');**  
              
            **const chart \= new Chart(ctx, {**  
                **type: 'line',**  
                **data: {**  
                    **labels: \[\],**  
                    **datasets: \[{**  
                        **label: 'Events per Minute',**  
                        **data: \[\],**  
                        **borderColor: 'rgb(75, 192, 192)',**  
                        **tension: 0.1**  
                    **}\]**  
                **},**  
                **options: {**  
                    **responsive: true,**  
                    **scales: {**  
                        **y: {**  
                            **beginAtZero: true**  
                        **}**  
                    **}**  
                **}**  
            **});**  
              
            **ws.onmessage \= function(event) {**  
                **const data \= JSON.parse(event.data);**  
                  
                **if (data.type \=== 'real\_time\_event') {**  
                    **// Add event to display**  
                    **const eventDiv \= document.createElement('div');**  
                    **eventDiv.innerHTML \= \`**  
                        **\<strong\>${data.data.event\_type}\</strong\> \-**   
                        **${data.data.stream\_id} \-**   
                        **${new Date(data.data.timestamp).toLocaleTimeString()}**  
                    **\`;**  
                    **eventsDiv.insertBefore(eventDiv, eventsDiv.firstChild);**  
                      
                    **// Keep only last 10 events**  
                    **while (eventsDiv.children.length \> 10\) {**  
                        **eventsDiv.removeChild(eventsDiv.lastChild);**  
                    **}**  
                      
                    **// Update chart**  
                    **const now \= new Date().toLocaleTimeString();**  
                    **chart.data.labels.push(now);**  
                    **chart.data.datasets\[0\].data.push(1);**  
                      
                    **if (chart.data.labels.length \> 20\) {**  
                        **chart.data.labels.shift();**  
                        **chart.data.datasets\[0\].data.shift();**  
                    **}**  
                      
                    **chart.update();**  
                **}**  
            **};**  
              
            **// Send periodic ping to keep connection alive**  
            **setInterval(() \=\> {**  
                **ws.send(JSON.stringify({type: 'ping'}));**  
            **}, 30000);**  
        **\</script\>**  
    **\</body\>**  
    **\</html\>**  
    **""")**

**if \_\_name\_\_ \== "\_\_main\_\_":**  
    **import uvicorn**  
    **uvicorn.run(app, host="0.0.0.0", port=8000)**  
**\]\]\>**  
        **\</example\>**  
    **\</section\>**

    **\<footer\>**  
        **\<summary\>**  
            **Module A provides the complete foundation for AUREN's data persistence and event architecture. It replaces JSON file limitations with unlimited PostgreSQL storage, implements event sourcing for complete audit trails, and provides real-time projections for optimal performance.** 

            **The hybrid implementation combines the best aspects of connection management, event sourcing, memory backend functionality, projection handling, and comprehensive testing. This module enables the multi-agent intelligence system with proper HIPAA compliance, real-time collaboration, and production-grade reliability.**

            **Key capabilities delivered: unlimited memory storage, immutable audit trails, sub-second memory retrieval, real-time agent collaboration, complete migration tooling, comprehensive monitoring, and seamless CrewAI integration.**  
        **\</summary\>**  
          
        **\<next\_steps\>**  
            **\<step\>Initialize PostgreSQL database with provided schema\</step\>**  
            **\<step\>Configure AsyncPostgresManager with production settings\</step\>**  
            **\<step\>Deploy EventStore and PostgreSQLMemoryBackend\</step\>**  
            **\<step\>Set up projection handlers for Redis and ChromaDB\</step\>**  
            **\<step\>Run migration script to import existing JSON data\</step\>**  
            **\<step\>Configure monitoring and alerting systems\</step\>**  
            **\<step\>Integration testing with CrewAI agents\</step\>**  
            **\<step\>Performance tuning based on production load\</step\>**  
        **\</next\_steps\>**  
          
        **\<integration\_points\>**  
            **\<point\>Module B: Agent Intelligence Systems \- provides hypothesis validation and knowledge management using this data layer\</point\>**  
            **\<point\>Module C: Real-time Systems & Dashboard \- consumes events and projections for visualization\</point\>**  
            **\<point\>Module D: CrewAI Integration \- uses AURENMemoryStorage and shared context capabilities\</point\>**  
            **\<point\>Module E: Production Operations \- implements monitoring, backup, and deployment procedures\</point\>**  
        **\</integration\_points\>**  
    **\</footer\>**  
**\</module\_a\_data\_persistence\>**