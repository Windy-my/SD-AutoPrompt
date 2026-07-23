"""Skill registry for managing style preferences."""

from typing import Dict, List, Optional

from skills.base import Skill, BUILTIN_SKILLS


class SkillRegistry:
    """
    Registry for managing style skill profiles.
    
    Allows adding custom skills and querying available skills.
    """
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._load_builtin()
    
    def _load_builtin(self):
        """Load built-in skills into the registry."""
        for skill_id, skill in BUILTIN_SKILLS.items():
            self._skills[skill_id] = skill
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by its ID."""
        return self._skills.get(skill_id)
    
    def get_all_skills(self) -> List[Skill]:
        """Get all registered skills."""
        return list(self._skills.values())
    
    def get_skill_names(self) -> List[str]:
        """Get display names of all skills."""
        return [s.name for s in self._skills.values()]
    
    def get_skill_choices(self) -> List[str]:
        """Get skill names as a list for UI dropdown, with a default option."""
        return ["默认（自动识别）"] + [s.name for s in self._skills.values()]
    
    def get_instruction_for_skill(self, skill_name: str) -> str:
        """
        Get the prompt instruction for a skill by its display name.
        
        Args:
            skill_name: The display name of the skill (e.g., "写实摄影")
            
        Returns:
            The instruction text to append to system prompt, or "" if not found
        """
        for skill in self._skills.values():
            if skill.name == skill_name:
                return skill.prompt_instruction
        return ""
    
    def get_id_from_name(self, skill_name: str) -> Optional[str]:
        """Get skill ID from display name."""
        for skill_id, skill in self._skills.items():
            if skill.name == skill_name:
                return skill_id
        return None
    
    def add_skill(self, skill: Skill) -> None:
        """Add a custom skill to the registry."""
        self._skills[skill.id] = skill


# Global singleton registry
registry = SkillRegistry()
