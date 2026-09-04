from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, validator

from database._client import document_id_from_seed


class MemoryCategory(str, Enum):
    # New primary categories
    interesting = "interesting"
    system = "system"
    manual = "manual"
    workflow = "workflow"

    # Legacy categories for backward compatibility
    core = "core"
    hobbies = "hobbies"
    lifestyle = "lifestyle"
    interests = "interests"
    habits = "habits"
    work = "work"
    skills = "skills"
    learnings = "learnings"
    other = "other"
    auto = "auto"


# Only define boosts for the primary categories
CATEGORY_BOOSTS = {
    MemoryCategory.interesting.value: 1,
    MemoryCategory.system.value: 0,
    MemoryCategory.manual.value: 1,
    MemoryCategory.workflow.value: 1,
    # Map legacy categories to appropriate new categories
    MemoryCategory.core.value: 1,
    MemoryCategory.hobbies.value: 1,
    MemoryCategory.lifestyle.value: 1,
    MemoryCategory.interests.value: 1,
    MemoryCategory.work.value: 1,
    MemoryCategory.skills.value: 1,
    MemoryCategory.learnings.value: 1,
    MemoryCategory.habits.value: 0,
    MemoryCategory.other.value: 0,
    MemoryCategory.auto.value: 0,
}


class Memory(BaseModel):
    content: str = Field(description="The content of the memory")
    category: MemoryCategory = Field(description="The category of the memory", default=MemoryCategory.interesting)
    visibility: str = Field(description="The visibility of the memory", default='private')
    tags: List[str] = Field(description="The tags of the memory and learning", default=[])
    headline: Optional[str] = Field(description="Short headline for notification preview (max 5 words)", default=None)

    @validator('category', pre=True)
    def map_legacy_categories(cls, v):
        """Map legacy categories to new ones when creating memories"""
        if isinstance(v, MemoryCategory):
            return v

        # If it's a string value
        legacy_to_new = {
            'core': 'system',
            'hobbies': 'system',
            'lifestyle': 'system',
            'interests': 'system',
            'work': 'system',
            'skills': 'system',
            'learnings': 'system',
            'habits': 'system',
            'other': 'system',
            'auto': 'system',
        }

        if isinstance(v, str):
            # If it's already one of our main categories, use it directly
            if v in ['interesting', 'system', 'manual', 'workflow']:
                return v

            # For legacy categories, map them to new ones
            if v in legacy_to_new:
                return legacy_to_new[v]

            # For any unknown string value, default to "interesting"
            return 'interesting'

        # For any other unexpected type, default to interesting
        return 'interesting'

    @staticmethod
    def get_memories_as_str(memories: List):
        result = ''
        for f in memories:
            # Include created_at if available (for MemoryDB objects)
            if hasattr(f, 'created_at') and f.created_at:
                date_str = f.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                result += f"- {f.content} ({date_str})\n"
            else:
                result += f"- {f.content}\n"

        return result


class MemoryDB(Memory):
    id: str
    uid: str
    created_at: datetime
    updated_at: datetime

    # TODO: remove these fields and use conversation_id and conversation_category after migration
    memory_id: Optional[str] = None

    conversation_id: Optional[str] = None

    reviewed: bool = False
    user_review: Optional[bool] = None
    visibility: Optional[str] = 'public'

    manually_added: bool = False
    edited: bool = False
    scoring: Optional[str] = None
    app_id: Optional[str] = None
    data_protection_level: Optional[str] = None
    is_locked: bool = False
    kg_extracted: bool = False

    # Temporal lifecycle — the "constantly updated brain". All optional, so existing
    # docs (which lack these fields) read back as active with no migration.
    #   valid_at:      when the fact became true (defaults to created_at)
    #   invalid_at:    when the fact stopped being true; None == currently active.
    #                  A superseded/retracted memory is invalidated (not deleted) so
    #                  history is kept, but it is excluded from every retrieval path.
    #   superseded_by: id of the newer memory that replaced this one (if any).
    valid_at: Optional[datetime] = None
    invalid_at: Optional[datetime] = None
    superseded_by: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.memory_id = self.conversation_id

    @property
    def is_active(self) -> bool:
        """A memory is active (currently true) until it is invalidated."""
        return self.invalid_at is None

    @staticmethod
    def calculate_score(memory: 'MemoryDB') -> 'MemoryDB':
        cat_boost = (999 - CATEGORY_BOOSTS[memory.category.value]) if memory.category.value in CATEGORY_BOOSTS else 0

        user_manual_added_boost = 1
        if memory.manually_added is False:
            user_manual_added_boost = 0

        return "{:02d}_{:02d}_{:010d}".format(user_manual_added_boost, cat_boost, int(memory.created_at.timestamp()))

    @staticmethod
    def from_memory(memory: Memory, uid: str, conversation_id: str, manually_added: bool) -> 'MemoryDB':
        now = datetime.now(timezone.utc)
        memory_db = MemoryDB(
            id=document_id_from_seed(memory.content),
            uid=uid,
            content=memory.content,
            category=memory.category,
            tags=memory.tags,
            created_at=now,
            updated_at=now,
            valid_at=now,
            conversation_id=conversation_id,
            manually_added=manually_added,
            user_review=True if manually_added else None,
            reviewed=True,
            visibility=memory.visibility,
        )
        memory_db.scoring = MemoryDB.calculate_score(memory_db)
        return memory_db
# Iterated on 2026-09-04T07:35:10.015Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:36:07.051Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:37:06.991Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:38:06.964Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:39:06.984Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:40:06.986Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:41:06.987Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:42:06.986Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:43:06.992Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:44:06.986Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:45:07.003Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:46:06.982Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:47:06.996Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:48:06.998Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:49:06.992Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:50:07.049Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:51:07.039Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:52:07.016Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:53:07.026Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:54:07.008Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:55:07.035Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:56:07.059Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:57:07.427Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:58:07.445Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T07:59:08.076Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:00:06.959Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:01:06.957Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:02:06.959Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:03:06.953Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:04:06.965Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:05:06.958Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:06:06.960Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:07:06.966Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:08:07.000Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:09:07.005Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:10:07.000Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:11:07.006Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:12:06.995Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:13:07.004Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:14:06.990Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:15:07.000Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:16:07.003Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:17:06.992Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:18:07.001Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:19:07.002Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:20:07.005Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:21:07.005Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:22:07.008Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:23:07.009Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:24:07.040Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:25:07.041Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:26:07.037Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:27:07.047Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:28:07.047Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:29:07.045Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:30:07.054Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:31:07.044Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:32:07.056Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:33:07.056Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:34:07.067Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:35:07.063Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:36:07.067Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:37:07.068Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:38:07.070Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:39:07.070Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:40:07.086Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:41:07.076Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:42:07.074Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:43:07.081Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:44:07.075Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:45:07.074Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:46:07.085Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:47:07.077Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:48:07.075Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:49:07.083Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:50:07.085Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:51:07.098Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:52:07.080Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:53:07.083Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:54:07.093Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:55:07.087Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:56:07.089Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:57:07.090Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:58:07.093Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T08:59:07.092Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:00:07.094Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:01:07.102Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:02:07.097Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:03:07.094Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:04:07.104Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:05:07.103Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:06:07.099Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:07:07.106Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:08:07.104Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:09:07.119Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:10:07.114Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:11:07.120Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:12:07.116Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:13:07.123Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:14:07.116Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:15:07.127Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:16:07.123Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:17:07.133Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:18:07.126Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:19:07.139Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:20:07.128Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:21:07.130Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:22:07.133Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:23:07.138Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:24:07.142Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:25:07.140Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:26:07.141Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:27:07.151Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:28:07.154Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:29:07.141Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:30:07.144Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:31:07.146Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:32:07.147Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:33:07.149Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:34:07.150Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:35:07.167Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:36:07.177Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:37:07.185Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:38:07.194Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:39:07.201Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:40:07.202Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:41:07.201Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:42:07.200Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:43:07.211Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:44:07.205Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:45:07.204Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:46:07.208Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:47:07.222Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:48:07.211Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:49:07.203Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:50:07.208Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:51:07.212Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:52:07.211Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:53:07.214Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:54:07.192Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:55:07.185Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:56:07.189Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:57:07.186Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:58:07.196Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T09:59:07.187Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:00:07.195Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:01:07.201Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:02:07.191Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:03:07.213Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:04:07.206Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:05:07.208Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:06:07.209Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:07:07.214Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:08:07.213Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:09:07.211Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:10:07.228Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:11:07.237Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:12:07.239Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:13:07.241Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:14:07.232Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:15:07.240Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:16:07.253Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:17:07.240Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:18:07.238Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:19:07.252Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:20:07.258Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:21:07.248Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:22:07.257Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:23:07.263Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:24:07.263Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:25:07.270Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:26:07.267Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:27:07.272Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:28:07.291Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:29:07.287Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:30:07.290Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:31:07.291Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:32:07.288Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:33:07.293Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:34:07.296Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:35:07.300Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:36:07.299Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:37:07.315Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:38:07.321Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:39:07.309Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:40:07.310Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:41:07.314Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:42:07.315Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:43:07.318Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:44:07.325Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:45:07.324Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:46:07.326Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:47:07.342Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:48:07.328Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:49:07.322Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:50:07.347Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:51:07.349Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:52:07.340Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:53:07.338Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:54:07.337Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:55:07.347Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:56:07.340Z: ISSUE BUG FIX MEM
# Iterated on 2026-09-04T10:57:07.345Z: ISSUE BUG FIX MEM
