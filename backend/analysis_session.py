"""
In-memory session store for multi-fighter analysis results.

After video analysis, results for both fighters are stored in a session.
The frontend retrieves fighter-specific results using the session ID.
Sessions expire after a configurable TTL.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SessionData:
    """Holds analysis results for a single analysis session."""
    session_id: str
    created_at: float
    duration_seconds: float
    video_fps: float
    # Per-fighter analysis: fighter_id -> full analysis dict
    fighter_analyses: Dict[str, dict] = field(default_factory=dict)
    # Per-fighter thumbnails: fighter_id -> base64 JPEG
    thumbnails: Dict[str, str] = field(default_factory=dict)
    # Per-fighter colors: fighter_id -> hex color
    colors: Dict[str, str] = field(default_factory=dict)
    # Per-fighter labels: fighter_id -> "Fighter A" / "Fighter B"
    labels: Dict[str, str] = field(default_factory=dict)
    # Overview frame with bounding boxes (base64)
    overview_frame_base64: str = ""


class AnalysisSessionStore:
    """Thread-safe in-memory store for analysis sessions with TTL cleanup."""

    def __init__(self, ttl_minutes: int = 30):
        self._sessions: Dict[str, SessionData] = {}
        self._lock = threading.Lock()
        self._ttl_seconds = ttl_minutes * 60

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop, daemon=True
        )
        self._cleanup_thread.start()

    def create_session(
        self,
        duration_seconds: float,
        video_fps: float,
        overview_frame_base64: str = "",
    ) -> str:
        """Create a new session and return its ID."""
        session_id = uuid.uuid4().hex[:16]
        session = SessionData(
            session_id=session_id,
            created_at=time.time(),
            duration_seconds=duration_seconds,
            video_fps=video_fps,
            overview_frame_base64=overview_frame_base64,
        )
        with self._lock:
            self._sessions[session_id] = session
        return session_id

    def add_fighter(
        self,
        session_id: str,
        fighter_id: str,
        analysis: dict,
        thumbnail_base64: str = "",
        color: str = "#FFFFFF",
        label: str = "Fighter",
    ):
        """Add a fighter's analysis results to a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(f"Session {session_id} not found")
            session.fighter_analyses[fighter_id] = analysis
            session.thumbnails[fighter_id] = thumbnail_base64
            session.colors[fighter_id] = color
            session.labels[fighter_id] = label

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get a session by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def get_fighter_analysis(self, session_id: str, fighter_id: str) -> Optional[dict]:
        """Get analysis for a specific fighter in a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            return session.fighter_analyses.get(fighter_id)

    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """Get a summary of a session (scores, thumbnails, no full analysis)."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            fighters = []
            for fid in session.fighter_analyses:
                analysis = session.fighter_analyses[fid]
                fighters.append({
                    "id": fid,
                    "thumbnail_base64": session.thumbnails.get(fid, ""),
                    "color": session.colors.get(fid, "#FFFFFF"),
                    "label": session.labels.get(fid, "Fighter"),
                    "overall_score": analysis.get("overall_score", 0),
                    "guard_type": analysis.get("guard", {}).get("guard_type", "unknown"),
                    "stance": analysis.get("stance", {}).get("dominant", "unknown"),
                })

            return {
                "session_id": session.session_id,
                "duration_seconds": session.duration_seconds,
                "overview_frame_base64": session.overview_frame_base64,
                "fighters": fighters,
            }

    def _cleanup_loop(self):
        """Periodically remove expired sessions."""
        while True:
            time.sleep(60)  # Check every minute
            now = time.time()
            with self._lock:
                expired = [
                    sid for sid, s in self._sessions.items()
                    if now - s.created_at > self._ttl_seconds
                ]
                for sid in expired:
                    del self._sessions[sid]


# Global session store instance
session_store = AnalysisSessionStore(ttl_minutes=30)
