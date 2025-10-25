"""
Basic Analytics Tracking Service
Tracks session duration, message count, trust progression metrics
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class SessionMetrics:
    """Metrics for a single session"""
    session_id: str
    persona_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    message_count: int = 0
    user_messages: int = 0
    persona_messages: int = 0
    initial_trust_level: Optional[float] = None
    final_trust_level: Optional[float] = None
    peak_trust_level: Optional[float] = None
    trust_progression: List[float] = None
    interaction_qualities: List[str] = None
    session_duration_minutes: Optional[float] = None
    knowledge_tiers_unlocked: List[str] = None
    
    def __post_init__(self):
        if self.trust_progression is None:
            self.trust_progression = []
        if self.interaction_qualities is None:
            self.interaction_qualities = []
        if self.knowledge_tiers_unlocked is None:
            self.knowledge_tiers_unlocked = []

@dataclass  
class DailyMetrics:
    """Daily aggregated metrics"""
    date: str
    total_sessions: int = 0
    total_messages: int = 0
    avg_session_duration: float = 0.0
    avg_messages_per_session: float = 0.0
    avg_trust_progression: float = 0.0
    top_personas: List[Dict[str, int]] = None
    interaction_quality_distribution: Dict[str, int] = None
    
    def __post_init__(self):
        if self.top_personas is None:
            self.top_personas = []
        if self.interaction_quality_distribution is None:
            self.interaction_quality_distribution = {
                "poor": 0, "adequate": 0, "good": 0, "excellent": 0
            }

class AnalyticsService:
    """
    Service for tracking and analyzing user engagement metrics
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionMetrics] = {}
        self.completed_sessions: List[SessionMetrics] = []
        self.daily_metrics: Dict[str, DailyMetrics] = {}
        
        logger.info("📊 Analytics service initialized")
    
    def start_session(self, session_id: str, persona_id: str) -> None:
        """
        Start tracking a new session
        
        Args:
            session_id: Session identifier
            persona_id: Persona being used in session
        """
        if session_id in self.active_sessions:
            logger.warning(f"Session {session_id} already being tracked")
            return
        
        metrics = SessionMetrics(
            session_id=session_id,
            persona_id=persona_id,
            start_time=datetime.utcnow()
        )
        
        self.active_sessions[session_id] = metrics
        logger.debug(f"📈 Started tracking session {session_id} with persona {persona_id}")
    
    def add_message(self, session_id: str, role: str, trust_level: Optional[float] = None, 
                   interaction_quality: Optional[str] = None, knowledge_tier: Optional[str] = None) -> None:
        """
        Track a new message in the session
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'persona')
            trust_level: Current trust level
            interaction_quality: Quality of the interaction
            knowledge_tier: Knowledge tier unlocked
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not being tracked")
            return
        
        metrics = self.active_sessions[session_id]
        metrics.message_count += 1
        
        if role == 'user':
            metrics.user_messages += 1
        elif role in ['persona', 'assistant']:
            metrics.persona_messages += 1
        
        # Track trust progression
        if trust_level is not None:
            if metrics.initial_trust_level is None:
                metrics.initial_trust_level = trust_level
            metrics.final_trust_level = trust_level
            metrics.trust_progression.append(trust_level)
            
            if metrics.peak_trust_level is None or trust_level > metrics.peak_trust_level:
                metrics.peak_trust_level = trust_level
        
        # Track interaction quality
        if interaction_quality:
            metrics.interaction_qualities.append(interaction_quality)
        
        # Track knowledge tiers
        if knowledge_tier and knowledge_tier not in metrics.knowledge_tiers_unlocked:
            metrics.knowledge_tiers_unlocked.append(knowledge_tier)
        
        logger.debug(f"📝 Added message to session {session_id}: {role} (trust: {trust_level})")
    
    def end_session(self, session_id: str) -> Optional[SessionMetrics]:
        """
        End tracking for a session and calculate final metrics
        
        Args:
            session_id: Session identifier
            
        Returns:
            Final session metrics or None if session not found
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not being tracked")
            return None
        
        metrics = self.active_sessions[session_id]
        metrics.end_time = datetime.utcnow()
        
        # Calculate session duration
        duration = metrics.end_time - metrics.start_time
        metrics.session_duration_minutes = duration.total_seconds() / 60
        
        # Move to completed sessions
        self.completed_sessions.append(metrics)
        del self.active_sessions[session_id]
        
        # Update daily metrics
        self._update_daily_metrics(metrics)
        
        logger.info(f"🏁 Session {session_id} completed: {metrics.message_count} messages, " +
                   f"{metrics.session_duration_minutes:.1f}min duration")
        
        return metrics
    
    def _update_daily_metrics(self, session_metrics: SessionMetrics) -> None:
        """Update daily aggregated metrics"""
        date_str = session_metrics.start_time.strftime('%Y-%m-%d')
        
        if date_str not in self.daily_metrics:
            self.daily_metrics[date_str] = DailyMetrics(date=date_str)
        
        daily = self.daily_metrics[date_str]
        daily.total_sessions += 1
        daily.total_messages += session_metrics.message_count
        
        # Update averages
        daily.avg_session_duration = (
            (daily.avg_session_duration * (daily.total_sessions - 1) + 
             session_metrics.session_duration_minutes) / daily.total_sessions
        )
        daily.avg_messages_per_session = daily.total_messages / daily.total_sessions
        
        # Update trust progression
        if session_metrics.trust_progression:
            trust_change = session_metrics.final_trust_level - session_metrics.initial_trust_level
            daily.avg_trust_progression = (
                (daily.avg_trust_progression * (daily.total_sessions - 1) + trust_change) 
                / daily.total_sessions
            )
        
        # Update persona usage
        persona_found = False
        for persona_stat in daily.top_personas:
            if persona_stat['persona_id'] == session_metrics.persona_id:
                persona_stat['count'] += 1
                persona_found = True
                break
        
        if not persona_found:
            daily.top_personas.append({
                'persona_id': session_metrics.persona_id,
                'count': 1
            })
        
        # Sort personas by usage
        daily.top_personas.sort(key=lambda x: x['count'], reverse=True)
        
        # Update interaction quality distribution
        for quality in session_metrics.interaction_qualities:
            if quality in daily.interaction_quality_distribution:
                daily.interaction_quality_distribution[quality] += 1
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """
        Get current statistics for an active session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session statistics or None if session not found
        """
        if session_id in self.active_sessions:
            metrics = self.active_sessions[session_id]
        else:
            # Look in completed sessions
            completed = [s for s in self.completed_sessions if s.session_id == session_id]
            if not completed:
                return None
            metrics = completed[0]
        
        current_time = datetime.utcnow()
        duration = (current_time - metrics.start_time).total_seconds() / 60
        
        trust_change = None
        if metrics.initial_trust_level and metrics.final_trust_level:
            trust_change = metrics.final_trust_level - metrics.initial_trust_level
        
        return {
            'session_id': session_id,
            'persona_id': metrics.persona_id,
            'message_count': metrics.message_count,
            'user_messages': metrics.user_messages,
            'persona_messages': metrics.persona_messages,
            'session_duration_minutes': round(duration, 2),
            'trust_levels': {
                'initial': metrics.initial_trust_level,
                'current': metrics.final_trust_level,
                'peak': metrics.peak_trust_level,
                'change': round(trust_change, 3) if trust_change else None
            },
            'interaction_qualities': metrics.interaction_qualities,
            'knowledge_tiers_unlocked': metrics.knowledge_tiers_unlocked
        }
    
    def get_daily_stats(self, date: str = None) -> Optional[Dict]:
        """
        Get daily statistics
        
        Args:
            date: Date string in YYYY-MM-DD format (default: today)
            
        Returns:
            Daily statistics or None if no data for date
        """
        if date is None:
            date = datetime.utcnow().strftime('%Y-%m-%d')
        
        if date not in self.daily_metrics:
            return None
        
        daily = self.daily_metrics[date]
        return asdict(daily)
    
    def get_overall_stats(self, days: int = 7) -> Dict:
        """
        Get overall statistics for the last N days
        
        Args:
            days: Number of days to include in stats
            
        Returns:
            Overall statistics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        relevant_sessions = [
            s for s in self.completed_sessions 
            if s.start_time >= start_date
        ]
        
        if not relevant_sessions:
            return {
                'period_days': days,
                'total_sessions': 0,
                'total_messages': 0,
                'avg_session_duration': 0,
                'avg_trust_progression': 0,
                'most_popular_personas': [],
                'interaction_quality_breakdown': {}
            }
        
        total_messages = sum(s.message_count for s in relevant_sessions)
        avg_duration = sum(s.session_duration_minutes or 0 for s in relevant_sessions) / len(relevant_sessions)
        
        # Trust progression analysis
        trust_changes = []
        for session in relevant_sessions:
            if session.initial_trust_level and session.final_trust_level:
                trust_changes.append(session.final_trust_level - session.initial_trust_level)
        
        avg_trust_change = sum(trust_changes) / len(trust_changes) if trust_changes else 0
        
        # Persona popularity
        persona_counts = {}
        for session in relevant_sessions:
            persona_counts[session.persona_id] = persona_counts.get(session.persona_id, 0) + 1
        
        top_personas = sorted(persona_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Interaction quality breakdown
        quality_counts = {"poor": 0, "adequate": 0, "good": 0, "excellent": 0}
        for session in relevant_sessions:
            for quality in session.interaction_qualities:
                if quality in quality_counts:
                    quality_counts[quality] += 1
        
        return {
            'period_days': days,
            'total_sessions': len(relevant_sessions),
            'total_messages': total_messages,
            'avg_session_duration': round(avg_duration, 2),
            'avg_messages_per_session': round(total_messages / len(relevant_sessions), 1),
            'avg_trust_progression': round(avg_trust_change, 3),
            'most_popular_personas': [{'persona_id': p[0], 'sessions': p[1]} for p in top_personas],
            'interaction_quality_breakdown': quality_counts,
            'active_sessions': len(self.active_sessions)
        }
    
    def get_trust_analysis(self, persona_id: str = None, days: int = 7) -> Dict:
        """
        Get detailed trust progression analysis
        
        Args:
            persona_id: Filter by specific persona (optional)
            days: Number of days to analyze
            
        Returns:
            Trust progression analysis
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        sessions = [
            s for s in self.completed_sessions 
            if s.start_time >= start_date and 
            (persona_id is None or s.persona_id == persona_id) and
            s.trust_progression
        ]
        
        if not sessions:
            return {'error': 'No trust data available for the specified period'}
        
        # Analyze trust trajectories
        trust_improvements = [s for s in sessions if s.final_trust_level > s.initial_trust_level]
        trust_declines = [s for s in sessions if s.final_trust_level < s.initial_trust_level]
        trust_stable = [s for s in sessions if s.final_trust_level == s.initial_trust_level]
        
        return {
            'period_days': days,
            'persona_id': persona_id,
            'total_sessions_analyzed': len(sessions),
            'trust_outcomes': {
                'improved': len(trust_improvements),
                'declined': len(trust_declines),
                'stable': len(trust_stable)
            },
            'avg_trust_change': round(
                sum(s.final_trust_level - s.initial_trust_level for s in sessions) / len(sessions), 3
            ),
            'peak_trust_achieved': round(max(s.peak_trust_level for s in sessions), 3),
            'sessions_reaching_high_trust': len([s for s in sessions if s.peak_trust_level >= 0.8])
        }

# Global analytics instance
analytics = AnalyticsService()