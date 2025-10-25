"""
Production Infrastructure Service
Provides monitoring, performance tracking, and scalability features
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from functools import wraps
import json

from src.dependencies import get_supabase_client
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    endpoint: str
    duration: float
    model_used: str
    success: bool
    error_type: Optional[str] = None
    timestamp: datetime = None
    conversation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class SystemHealth:
    """Overall system health status"""
    avg_response_time: float
    success_rate: float
    active_conversations: int
    model_availability: Dict[str, bool]
    database_status: str
    cache_hit_rate: float = 0.0

class ProductionInfrastructureService:
    """
    Production-ready infrastructure with:
    - Performance monitoring and alerting
    - Model availability tracking
    - Database health monitoring  
    - Caching and optimization
    - Error tracking and reporting
    - Scalability metrics
    """

    def __init__(self):
        self.settings = get_settings()
        self.supabase_client = get_supabase_client()
        
        # In-memory performance tracking
        self.performance_buffer = []
        self.cache_stats = {"hits": 0, "misses": 0}
        self.model_status = {}
        
        # Performance thresholds
        self.response_time_threshold = 10.0  # seconds
        self.success_rate_threshold = 0.95   # 95%
        self.error_alert_threshold = 5       # errors per minute

    def monitor_performance(self, endpoint: str):
        """Decorator to monitor endpoint performance"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_type = None
                model_used = "unknown"
                conversation_id = None
                
                try:
                    # Extract conversation_id if available
                    if 'conversation_id' in kwargs:
                        conversation_id = kwargs['conversation_id']
                    elif len(args) > 0 and hasattr(args[0], 'conversation_id'):
                        conversation_id = args[0].conversation_id
                    
                    result = await func(*args, **kwargs)
                    
                    # Extract model info if available
                    if hasattr(result, 'model'):
                        model_used = result.model
                    elif hasattr(result, 'provider'):
                        model_used = f"{result.provider.value}"
                    
                    return result
                    
                except Exception as e:
                    success = False
                    error_type = type(e).__name__
                    logger.error(f"Error in {endpoint}: {e}")
                    raise
                    
                finally:
                    duration = time.time() - start_time
                    
                    # Record performance metric
                    metric = PerformanceMetric(
                        endpoint=endpoint,
                        duration=duration,
                        model_used=model_used,
                        success=success,
                        error_type=error_type,
                        conversation_id=conversation_id
                    )
                    
                    await self._record_metric(metric)
                    
                    # Alert if performance issues
                    if duration > self.response_time_threshold:
                        await self._alert_slow_response(endpoint, duration)
            
            return wrapper
        return decorator

    async def _record_metric(self, metric: PerformanceMetric):
        """Record performance metric"""
        
        # Add to in-memory buffer
        self.performance_buffer.append(metric)
        
        # Keep buffer size manageable
        if len(self.performance_buffer) > 1000:
            self.performance_buffer = self.performance_buffer[-500:]
        
        # Store in database for long-term analytics
        try:
            self.supabase_client.table('performance_metrics').insert({
                'endpoint': metric.endpoint,
                'duration': metric.duration,
                'model_used': metric.model_used,
                'success': metric.success,
                'error_type': metric.error_type,
                'conversation_id': metric.conversation_id,
                'timestamp': metric.timestamp.isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to store metric: {e}")

    async def get_system_health(self) -> SystemHealth:
        """Get current system health status"""
        
        # Get recent metrics (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_metrics = [m for m in self.performance_buffer if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return SystemHealth(
                avg_response_time=0.0,
                success_rate=1.0,
                active_conversations=0,
                model_availability={},
                database_status="unknown"
            )
        
        # Calculate averages
        avg_response_time = sum(m.duration for m in recent_metrics) / len(recent_metrics)
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
        
        # Check model availability
        model_availability = await self._check_model_availability()
        
        # Check database status
        database_status = await self._check_database_health()
        
        # Get active conversations
        active_conversations = await self._get_active_conversation_count()
        
        # Calculate cache hit rate
        total_cache_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        cache_hit_rate = self.cache_stats["hits"] / total_cache_requests if total_cache_requests > 0 else 0.0
        
        return SystemHealth(
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            active_conversations=active_conversations,
            model_availability=model_availability,
            database_status=database_status,
            cache_hit_rate=cache_hit_rate
        )

    async def _check_model_availability(self) -> Dict[str, bool]:
        """Check if LLM providers are available"""
        
        model_availability = {}
        
        # Check OpenAI
        if self.settings.OPENAI_API_KEY:
            try:
                from src.services.llm_service import LLMService
                llm = LLMService()
                await llm.generate_response(
                    prompt="test",
                    model="gpt-4o-mini",
                    max_tokens=1
                )
                model_availability["openai"] = True
            except:
                model_availability["openai"] = False
        else:
            model_availability["openai"] = False
        
        # Check Claude
        if self.settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY)
                await client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1,
                    messages=[{"role": "user", "content": "test"}]
                )
                model_availability["claude"] = True
            except:
                model_availability["claude"] = False
        else:
            model_availability["claude"] = False
        
        # Check Gemini
        if self.settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.settings.GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                await model.generate_content_async("test")
                model_availability["gemini"] = True
            except:
                model_availability["gemini"] = False
        else:
            model_availability["gemini"] = False
        
        return model_availability

    async def _check_database_health(self) -> str:
        """Check Supabase database connectivity"""
        
        try:
            result = self.supabase_client.table('personas').select('persona_id').limit(1).execute()
            if result.data:
                return "healthy"
            else:
                return "empty_response"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return "error"

    async def _get_active_conversation_count(self) -> int:
        """Get count of active conversations"""
        
        try:
            # Count conversations active in last 24 hours
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            result = self.supabase_client.table('conversations').select(
                'id', count='exact'
            ).eq('status', 'active').gte('updated_at', cutoff).execute()
            
            return result.count if result.count else 0
        except:
            return 0

    async def _alert_slow_response(self, endpoint: str, duration: float):
        """Alert on slow response times"""
        
        logger.warning(f"PERFORMANCE ALERT: {endpoint} took {duration:.2f}s (threshold: {self.response_time_threshold}s)")
        
        # Store alert
        try:
            self.supabase_client.table('performance_alerts').insert({
                'alert_type': 'slow_response',
                'endpoint': endpoint,
                'duration': duration,
                'threshold': self.response_time_threshold,
                'created_at': datetime.now().isoformat()
            }).execute()
        except:
            pass

    def track_cache_hit(self):
        """Track cache hit"""
        self.cache_stats["hits"] += 1

    def track_cache_miss(self):
        """Track cache miss"""
        self.cache_stats["misses"] += 1

    async def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate detailed performance report"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            # Get metrics from database
            result = self.supabase_client.table('performance_metrics').select('*').gte(
                'timestamp', cutoff_time.isoformat()
            ).execute()
            
            metrics = result.data if result.data else []
            
            if not metrics:
                return {"error": "No metrics available for specified time period"}
            
            # Calculate statistics
            total_requests = len(metrics)
            successful_requests = sum(1 for m in metrics if m['success'])
            failed_requests = total_requests - successful_requests
            
            durations = [m['duration'] for m in metrics]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            # Group by endpoint
            endpoint_stats = {}
            for metric in metrics:
                endpoint = metric['endpoint']
                if endpoint not in endpoint_stats:
                    endpoint_stats[endpoint] = []
                endpoint_stats[endpoint].append(metric)
            
            # Group by model
            model_stats = {}
            for metric in metrics:
                model = metric['model_used']
                if model not in model_stats:
                    model_stats[model] = []
                model_stats[model].append(metric)
            
            return {
                "time_period_hours": hours,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": successful_requests / total_requests,
                "performance": {
                    "avg_response_time": avg_duration,
                    "max_response_time": max_duration,
                    "min_response_time": min_duration
                },
                "endpoint_breakdown": {
                    endpoint: {
                        "request_count": len(stats),
                        "avg_duration": sum(s['duration'] for s in stats) / len(stats),
                        "success_rate": sum(1 for s in stats if s['success']) / len(stats)
                    }
                    for endpoint, stats in endpoint_stats.items()
                },
                "model_breakdown": {
                    model: {
                        "request_count": len(stats),
                        "avg_duration": sum(s['duration'] for s in stats) / len(stats),
                        "success_rate": sum(1 for s in stats if s['success']) / len(stats)
                    }
                    for model, stats in model_stats.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {"error": str(e)}

    async def cleanup_old_metrics(self, days: int = 30):
        """Clean up old performance metrics"""
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            self.supabase_client.table('performance_metrics').delete().lt(
                'timestamp', cutoff_date
            ).execute()
            
            logger.info(f"Cleaned up performance metrics older than {days} days")
        except Exception as e:
            logger.error(f"Failed to cleanup metrics: {e}")

# Global instance
infrastructure_service = ProductionInfrastructureService()