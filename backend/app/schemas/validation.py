from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class ValidationIssue(BaseModel):
    code: str
    severity: str = "blocking"  # "blocking" | "warning"
    entity_type: str            # "show" | "season" | "episode" | "artwork" | "other"
    entity_id: str
    problem: str
    action: str
    title: Optional[str] = None
    show_id: Optional[str] = None
    show_title: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None

class GroupedValidationIssues(BaseModel):
    shows: List[ValidationIssue] = []
    seasons: List[ValidationIssue] = []
    episodes: List[ValidationIssue] = []
    artwork: List[ValidationIssue] = []
    other: List[ValidationIssue] = []

class ValidationReportResponse(BaseModel):
    can_publish: bool
    total_issues: int
    blocking_count: int
    warning_count: int
    grouped_by_entity: GroupedValidationIssues
    all_issues: List[ValidationIssue]
