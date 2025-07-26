"""
auren/realtime/s3_event_archiver.py
Production S3 archival with intelligent tiered retention and Parquet formatting
"""

import asyncio
import json
import gzip
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import boto3
from botocore.exceptions import ClientError
import redis.asyncio as redis
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from io import BytesIO
import uuid

logger = logging.getLogger(__name__)


class S3EventArchiver:
    """
    Unified archival system with intelligent tier-based retention.
    Archives events to S3 in Parquet format with proper partitioning.
    """
    
    def __init__(self, s3_client, redis_client: redis.Redis, bucket_name: str = "auren-events"):
        self.s3_client = s3_client
        self.redis_client = redis_client
        self.bucket_name = bucket_name
        
        # Redis retention by tier (before S3 archival)
        self.redis_retention_hours = {
            "critical": 72,      # 3 days - for incident investigation
            "operational": 24,   # 1 day - for daily operations
            "analytical": 6      # 6 hours - move to S3 quickly
        }
        
        # S3 partitioning strategy
        self.s3_prefix_pattern = "events/year={year}/month={month}/day={day}/hour={hour}/tier={tier}/"
        
        # Buffering for efficiency
        self.buffers = {
            "critical": [],
            "operational": [],
            "analytical": []
        }
        self.buffer_limits = {
            "critical": 500,      # Smaller batches for important events
            "operational": 1000,  # Medium batches
            "analytical": 2000    # Large batches for efficiency
        }
        
        # Track last flush times
        self.last_flush = {
            "critical": datetime.now(timezone.utc),
            "operational": datetime.now(timezone.utc),
            "analytical": datetime.now(timezone.utc)
        }
        
        # Flush intervals (seconds)
        self.flush_intervals = {
            "critical": 60,      # Every minute
            "operational": 120,  # Every 2 minutes
            "analytical": 300    # Every 5 minutes
        }
        
        # Archive statistics
        self.stats = defaultdict(lambda: {"events_archived": 0, "batches_written": 0, "bytes_written": 0})
        
    async def start_archival_loop(self):
        """
        Main archival loop - runs continuously
        """
        logger.info("Starting S3 archival loop")
        
        # Start separate tasks for each tier
        tasks = [
            asyncio.create_task(self._tier_archival_loop("critical")),
            asyncio.create_task(self._tier_archival_loop("operational")),
            asyncio.create_task(self._tier_archival_loop("analytical")),
            asyncio.create_task(self._cleanup_expired_redis_events())
        ]
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
    
    async def _tier_archival_loop(self, tier: str):
        """
        Dedicated archival loop for a specific tier
        """
        while True:
            try:
                # Check if we should flush this tier
                should_flush = await self._should_flush_tier(tier)
                
                if should_flush:
                    await self._flush_tier_to_s3(tier)
                
                # Brief sleep to prevent CPU spinning
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in {tier} archival loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Back off on error
    
    async def _should_flush_tier(self, tier: str) -> bool:
        """
        Determine if a tier should be flushed based on buffer size or time
        """
        # Check buffer size
        if len(self.buffers[tier]) >= self.buffer_limits[tier]:
            return True
        
        # Check time since last flush
        time_since_flush = (datetime.now(timezone.utc) - self.last_flush[tier]).seconds
        if time_since_flush >= self.flush_intervals[tier] and self.buffers[tier]:
            return True
        
        return False
    
    async def add_event(self, event: Dict[str, Any], tier: str):
        """
        Add an event to the appropriate buffer
        """
        # Enrich event with archival metadata
        event["_archival_metadata"] = {
            "tier": tier,
            "buffered_at": datetime.now(timezone.utc).isoformat(),
            "archival_batch_id": str(uuid.uuid4())
        }
        
        self.buffers[tier].append(event)
        
        # Check if immediate flush needed
        if len(self.buffers[tier]) >= self.buffer_limits[tier]:
            await self._flush_tier_to_s3(tier)
    
    async def _flush_tier_to_s3(self, tier: str):
        """
        Flush a tier's buffer to S3 in Parquet format
        """
        if not self.buffers[tier]:
            return
        
        try:
            # Get events to archive
            events_to_archive = self.buffers[tier].copy()
            self.buffers[tier].clear()
            self.last_flush[tier] = datetime.now(timezone.utc)
            
            # Convert to DataFrame for Parquet
            df = self._events_to_dataframe(events_to_archive)
            
            # Generate S3 key
            now = datetime.now(timezone.utc)
            s3_key = self._generate_s3_key(tier, now)
            
            # Convert to Parquet
            parquet_buffer = BytesIO()
            df.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy')
            parquet_buffer.seek(0)
            
            # Upload to S3
            await self._upload_to_s3(s3_key, parquet_buffer.getvalue())
            
            # Update statistics
            self.stats[tier]["events_archived"] += len(events_to_archive)
            self.stats[tier]["batches_written"] += 1
            self.stats[tier]["bytes_written"] += len(parquet_buffer.getvalue())
            
            logger.info(f"Archived {len(events_to_archive)} {tier} events to {s3_key}")
            
            # Emit archival event
            await self._emit_archival_event(tier, len(events_to_archive), s3_key)
            
        except Exception as e:
            logger.error(f"Failed to archive {tier} events: {e}", exc_info=True)
            # Re-add events to buffer on failure
            self.buffers[tier].extend(events_to_archive)
    
    def _events_to_dataframe(self, events: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert events to a pandas DataFrame with proper schema
        """
        # Flatten nested structures for better Parquet compatibility
        flattened_events = []
        
        for event in events:
            flat_event = {
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "timestamp": event.get("timestamp"),
                "agent_id": event.get("agent_id"),
                "session_id": event.get("session_id"),
                "user_id": event.get("user_id"),
                "tier": event.get("_archival_metadata", {}).get("tier"),
                "archival_batch_id": event.get("_archival_metadata", {}).get("archival_batch_id")
            }
            
            # Flatten payload
            payload = event.get("payload", {})
            for key, value in payload.items():
                if isinstance(value, (str, int, float, bool)):
                    flat_event[f"payload_{key}"] = value
                else:
                    flat_event[f"payload_{key}"] = json.dumps(value)
            
            # Flatten performance metrics if present
            metrics = event.get("performance_metrics", {})
            for key, value in metrics.items():
                flat_event[f"metrics_{key}"] = value
            
            flattened_events.append(flat_event)
        
        return pd.DataFrame(flattened_events)
    
    def _generate_s3_key(self, tier: str, timestamp: datetime) -> str:
        """
        Generate S3 key with proper partitioning
        """
        key = self.s3_prefix_pattern.format(
            year=timestamp.year,
            month=timestamp.month,
            day=timestamp.day,
            hour=timestamp.hour,
            tier=tier
        )
        
        # Add unique filename
        filename = f"events_{timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.parquet"
        
        return key + filename
    
    async def _upload_to_s3(self, key: str, data: bytes):
        """
        Upload data to S3 with retry logic
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=data,
                    ContentType='application/octet-stream',
                    Metadata={
                        'archived_at': datetime.now(timezone.utc).isoformat(),
                        'archiver_version': '1.0.0'
                    }
                )
                return
                
            except ClientError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
    
    async def _cleanup_expired_redis_events(self):
        """
        Remove events from Redis that have been successfully archived
        """
        while True:
            try:
                for tier, retention_hours in self.redis_retention_hours.items():
                    stream_key = f"auren:events:{tier}"
                    
                    # Calculate cutoff time
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
                    cutoff_timestamp = int(cutoff_time.timestamp() * 1000)
                    
                    # Trim stream to remove old events
                    await self.redis_client.xtrim(
                        stream_key,
                        minid=f"{cutoff_timestamp}-0",
                        approximate=True
                    )
                
                # Run cleanup every hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in Redis cleanup: {e}", exc_info=True)
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    async def _emit_archival_event(self, tier: str, event_count: int, s3_key: str):
        """
        Emit an event about successful archival
        """
        archival_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "archival_completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tier": "operational",  # Archival events are operational
            "payload": {
                "archived_tier": tier,
                "event_count": event_count,
                "s3_key": s3_key,
                "bucket": self.bucket_name,
                "stats": dict(self.stats[tier])
            }
        }
        
        # Add to operational stream
        await self.redis_client.xadd(
            "auren:events:operational",
            archival_event
        )
    
    async def query_archived_events(
        self,
        start_time: datetime,
        end_time: datetime,
        tier: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query archived events from S3
        """
        events = []
        
        # Generate S3 prefixes to search
        prefixes = self._generate_query_prefixes(start_time, end_time, tier)
        
        for prefix in prefixes:
            try:
                # List objects in prefix
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                
                if 'Contents' not in response:
                    continue
                
                # Download and read each Parquet file
                for obj in response['Contents']:
                    parquet_data = self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )['Body'].read()
                    
                    # Read Parquet
                    df = pd.read_parquet(BytesIO(parquet_data))
                    
                    # Apply filters if provided
                    if filters:
                        for column, value in filters.items():
                            if column in df.columns:
                                df = df[df[column] == value]
                    
                    # Convert back to events
                    events.extend(df.to_dict('records'))
                    
            except Exception as e:
                logger.error(f"Error querying prefix {prefix}: {e}")
        
        return events
    
    def _generate_query_prefixes(
        self,
        start_time: datetime,
        end_time: datetime,
        tier: Optional[str] = None
    ) -> List[str]:
        """
        Generate S3 prefixes for time range query
        """
        prefixes = []
        current = start_time.replace(minute=0, second=0, microsecond=0)
        
        while current <= end_time:
            if tier:
                prefix = self.s3_prefix_pattern.format(
                    year=current.year,
                    month=current.month,
                    day=current.day,
                    hour=current.hour,
                    tier=tier
                )
                prefixes.append(prefix)
            else:
                # Query all tiers
                for t in ["critical", "operational", "analytical"]:
                    prefix = self.s3_prefix_pattern.format(
                        year=current.year,
                        month=current.month,
                        day=current.day,
                        hour=current.hour,
                        tier=t
                    )
                    prefixes.append(prefix)
            
            current += timedelta(hours=1)
        
        return prefixes
    
    def get_archival_stats(self) -> Dict[str, Any]:
        """
        Get current archival statistics
        """
        return {
            "stats_by_tier": dict(self.stats),
            "buffer_sizes": {
                tier: len(buffer) for tier, buffer in self.buffers.items()
            },
            "last_flush_times": {
                tier: timestamp.isoformat() for tier, timestamp in self.last_flush.items()
            }
        }


# S3 Lifecycle Policy Manager
class S3LifecycleManager:
    """
    Manages S3 lifecycle policies for intelligent data tiering
    """
    
    def __init__(self, s3_client, bucket_name: str):
        self.s3_client = s3_client
        self.bucket_name = bucket_name
    
    def setup_lifecycle_policies(self):
        """
        Configure S3 lifecycle policies for cost optimization
        """
        lifecycle_config = {
            'Rules': [
                {
                    'ID': 'critical-events-lifecycle',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'events/year=*/month=*/day=*/hour=*/tier=critical/'},
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'STANDARD_IA'  # Infrequent Access after 30 days
                        },
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER'  # Glacier after 90 days
                        }
                    ]
                },
                {
                    'ID': 'operational-events-lifecycle',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'events/year=*/month=*/day=*/hour=*/tier=operational/'},
                    'Transitions': [
                        {
                            'Days': 7,
                            'StorageClass': 'STANDARD_IA'  # IA after 1 week
                        },
                        {
                            'Days': 30,
                            'StorageClass': 'GLACIER'  # Glacier after 30 days
                        }
                    ],
                    'Expiration': {
                        'Days': 365  # Delete after 1 year
                    }
                },
                {
                    'ID': 'analytical-events-lifecycle',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'events/year=*/month=*/day=*/hour=*/tier=analytical/'},
                    'Transitions': [
                        {
                            'Days': 1,
                            'StorageClass': 'STANDARD_IA'  # IA after 1 day
                        },
                        {
                            'Days': 7,
                            'StorageClass': 'GLACIER'  # Glacier after 1 week
                        }
                    ],
                    'Expiration': {
                        'Days': 180  # Delete after 6 months
                    }
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            logger.info(f"Lifecycle policies configured for bucket {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Failed to configure lifecycle policies: {e}") 