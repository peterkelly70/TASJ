from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
import json


@dataclass
class MissionParticulars:
    """Data class representing mission particulars in the Traveller universe."""
    content: str = "Mission particulars not available."
    map_image: Optional[str] = None
    npc_images: List[str] = field(default_factory=list)
    item_images: List[str] = field(default_factory=list)
    npcs: str = ""
    complications: str = ""
    rewards: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MissionParticulars':
        """Create a MissionParticulars instance from a dictionary."""
        # Handle JSON strings for lists
        if isinstance(data.get('npc_images'), str):
            try:
                data['npc_images'] = json.loads(data['npc_images'])
            except (json.JSONDecodeError, TypeError):
                data['npc_images'] = []
                
        if isinstance(data.get('item_images'), str):
            try:
                data['item_images'] = json.loads(data['item_images'])
            except (json.JSONDecodeError, TypeError):
                data['item_images'] = []
        
        # Filter out any keys that aren't in the class's __annotations__
        valid_keys = {k for k in cls.__annotations__ if k != 'return'}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the MissionParticulars instance to a dictionary."""
        return asdict(self)
    
    def validate(self) -> List[str]:
        """
        Validate the mission particulars data.
        
        Returns:
            List[str]: List of error messages, empty if validation passes
        """
        errors = []
        
        # Required fields validation
        if not self.content or not str(self.content).strip():
            errors.append("Mission particulars content is required.")
        
        return errors


@dataclass
class MissionDetail:
    """Data class representing a mission detail in the Traveller universe."""
    detail_type: str
    detail_name: str
    detail_id: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MissionDetail':
        """Create a MissionDetail instance from a dictionary."""
        # Filter out any keys that aren't in the class's __annotations__
        valid_keys = {k for k in cls.__annotations__ if k != 'return'}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the MissionDetail instance to a dictionary."""
        return asdict(self)


@dataclass
class MissionReference:
    """Data class representing a mission reference in the Traveller universe."""
    phase: str
    table_id: str
    result: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MissionReference':
        """Create a MissionReference instance from a dictionary."""
        # Filter out any keys that aren't in the class's __annotations__
        valid_keys = {k for k in cls.__annotations__ if k != 'return'}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the MissionReference instance to a dictionary."""
        return asdict(self)


@dataclass
class Mission:
    """Data class representing a mission in the Traveller universe.
    
    Required fields (validated in validate() method):
        - world: Dict[str, Any] - The world data for this mission
        - scenario_type: Dict[str, Any] - The scenario type for this mission
    """
    world: Dict[str, Any]
    scenario_type: Dict[str, str]
    details: Dict[str, MissionDetail] = field(default_factory=dict)
    references: List[MissionReference] = field(default_factory=list)
    particulars: MissionParticulars = field(default_factory=MissionParticulars)
    map_description: str = ""
    uwp_factors: Dict[str, str] = field(default_factory=dict)
    tech_context: str = ""
    population_density: str = ""
    port_context: str = ""
    environment: str = ""
    law_context: str = ""
    mission_id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mission':
        """Create a Mission instance from a dictionary."""
        # Handle nested objects
        if 'particulars' in data:
            data['particulars'] = MissionParticulars.from_dict(data['particulars'])
        
        if 'details' in data:
            details_dict = {}
            for detail_type, detail_data in data['details'].items():
                if isinstance(detail_data, dict):
                    details_dict[detail_type] = MissionDetail.from_dict({
                        'detail_type': detail_type,
                        'detail_name': detail_data.get('name', ''),
                        'detail_id': detail_data.get('id', '')
                    })
            data['details'] = details_dict
        
        if 'references' in data:
            references_list = []
            for ref_data in data['references']:
                if isinstance(ref_data, dict):
                    references_list.append(MissionReference.from_dict(ref_data))
            data['references'] = references_list
        
        # Filter out any keys that aren't in the class's __annotations__
        valid_keys = {k for k in cls.__annotations__ if k != 'return'}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        # Ensure required fields have default values if not provided
        if 'particulars' not in filtered_data:
            filtered_data['particulars'] = MissionParticulars()
        
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Mission instance to a dictionary."""
        mission_dict = asdict(self)
        
        # Convert nested objects
        if isinstance(self.particulars, MissionParticulars):
            mission_dict['particulars'] = self.particulars.to_dict()
            
        # Convert details dictionary
        details_dict = {}
        for detail_type, detail in self.details.items():
            if isinstance(detail, MissionDetail):
                details_dict[detail_type] = {
                    'name': detail.detail_name,
                    'id': detail.detail_id
                }
        mission_dict['details'] = details_dict
        
        # Convert references list
        references_list = []
        for ref in self.references:
            if isinstance(ref, MissionReference):
                references_list.append(ref.to_dict())
        mission_dict['references'] = references_list
        
        return mission_dict
    
    def validate(self) -> List[str]:
        """
        Validate the mission data.
        
        Returns:
            List[str]: List of error messages, empty if validation passes
        """
        errors = []
        
        # Required fields validation
        if not self.world:
            errors.append("Mission world data is required.")
            
        if not self.scenario_type:
            errors.append("Mission scenario type is required.")
        
        # Validate particulars
        if isinstance(self.particulars, MissionParticulars):
            errors.extend(self.particulars.validate())
        
        return errors
