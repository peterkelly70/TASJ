import unittest
from unittest.mock import Mock, patch
from model.mission import Mission, MissionParticulars, MissionDetail, MissionReference
from model.mission_db_manager import MissionDBManager
import json

class TestMissionModel(unittest.TestCase):
    """Test cases for the Mission model and related dataclasses."""
    
    def setUp(self):
        """Set up test fixtures."""
        # We'll mock the MissionDBManager instead of instantiating it
        self.mission_db_manager = Mock()
        
        # Sample mission data
        self.sample_mission_particulars = {
            "content": "This is a test mission content.",
            "map_image": "http://example.com/map.jpg",
            "npc_images": ["http://example.com/npc1.jpg", "http://example.com/npc2.jpg"],
            "item_images": ["http://example.com/item1.jpg"],
            "npcs": "Captain John, Engineer Smith",
            "complications": "Ship malfunction, hostile natives",
            "rewards": "10,000 credits, rare artifact"
        }
        
        self.sample_mission_detail = {
            "detail_type": "patron",
            "detail_name": "Science Foundation",
            "detail_id": "sci-1"
        }
        
        self.sample_mission_reference = {
            "phase": "contact",
            "table_id": "contact-table",
            "result": "Dr. Eliza Chen"
        }
        
        self.sample_mission_data = {
            "mission_id": 1,
            "world": {
                "name": "Xylon IV",
                "uwp": "A123456-7"
            },
            "scenario_type": {
                "name": "Rescue",
                "description": "Rescue mission"
            },
            "details": {
                "patron": {
                    "name": "Science Foundation",
                    "id": "sci-1"
                },
                "location": {
                    "name": "Research Outpost",
                    "id": "outpost-1"
                }
            },
            "references": [
                {
                    "phase": "contact",
                    "table_id": "contact-table",
                    "result": "Dr. Eliza Chen"
                },
                {
                    "phase": "opposition",
                    "table_id": "opposition-table",
                    "result": "Local Wildlife"
                }
            ],
            "particulars": self.sample_mission_particulars,
            "tech_context": "High tech level with advanced medical equipment"
        }
    
    def test_mission_creation(self):
        """Test creating a Mission instance with valid data."""
        mission = Mission.from_dict(self.sample_mission_data)
        
        self.assertEqual(mission.mission_id, 1)
        self.assertEqual(mission.world["name"], "Xylon IV")
        self.assertEqual(mission.scenario_type["name"], "Rescue")
        self.assertEqual(mission.tech_context, "High tech level with advanced medical equipment")
        
        # Test particulars
        self.assertIsInstance(mission.particulars, MissionParticulars)
        self.assertEqual(mission.particulars.content, "This is a test mission content.")
        self.assertEqual(len(mission.particulars.npc_images), 2)
        
        # Test details
        self.assertIn("patron", mission.details)
        self.assertIsInstance(mission.details["patron"], MissionDetail)
        self.assertEqual(mission.details["patron"].detail_name, "Science Foundation")
        
        # Test references
        self.assertIsInstance(mission.references, list)
        self.assertGreater(len(mission.references), 0)
        self.assertIsInstance(mission.references[0], MissionReference)
        self.assertEqual(mission.references[0].result, "Dr. Eliza Chen")
    
    def test_mission_to_dict(self):
        """Test converting a Mission instance back to a dictionary."""
        mission = Mission.from_dict(self.sample_mission_data)
        mission_dict = mission.to_dict()
        
        # Check top-level attributes
        self.assertEqual(mission_dict["mission_id"], 1)
        self.assertEqual(mission_dict["tech_context"], "High tech level with advanced medical equipment")
        
        # Check nested structures
        self.assertEqual(mission_dict["world"]["name"], "Xylon IV")
        self.assertEqual(mission_dict["scenario_type"]["name"], "Rescue")
        
        # Check particulars
        self.assertEqual(mission_dict["particulars"]["content"], "This is a test mission content.")
        self.assertEqual(len(mission_dict["particulars"]["npc_images"]), 2)
        
        # Check details and references
        self.assertEqual(mission_dict["details"]["patron"]["name"], "Science Foundation")
        self.assertIsInstance(mission_dict["references"], list)
        self.assertGreaterEqual(len(mission_dict["references"]), 1)
        self.assertEqual(mission_dict["references"][0]["result"], "Dr. Eliza Chen")
    
    def test_mission_validation_valid(self):
        """Test mission data validation with valid data."""
        mission = Mission.from_dict(self.sample_mission_data)
        errors = mission.validate()
        self.assertEqual(len(errors), 0, f"Expected no validation errors, but got: {errors}")
    
    def test_mission_validation_missing_required_fields(self):
        """Test mission validation with missing required fields."""
        # Create a mission with missing scenario_type
        mission = Mission(
            world={"name": "Xylon IV", "uwp": "A123456-7"},
            scenario_type={},  # Empty dict will fail validation
            particulars=MissionParticulars()
        )
        
        errors = mission.validate()
        self.assertGreater(len(errors), 0)
        self.assertIn("scenario type", errors[0].lower())
    
    def test_mission_validation_empty_content(self):
        """Test mission validation with empty particulars content."""
        invalid_data = self.sample_mission_data.copy()
        invalid_data["particulars"] = self.sample_mission_particulars.copy()
        invalid_data["particulars"]["content"] = ""
        mission = Mission.from_dict(invalid_data)
        
        errors = mission.validate()
        self.assertGreater(len(errors), 0)
        self.assertIn("content", errors[0].lower())
    
    def test_mission_particulars_creation(self):
        """Test creating MissionParticulars instance."""
        particulars = MissionParticulars(**self.sample_mission_particulars)
        
        self.assertEqual(particulars.content, "This is a test mission content.")
        self.assertEqual(particulars.map_image, "http://example.com/map.jpg")
        self.assertEqual(len(particulars.npc_images), 2)
        self.assertEqual(particulars.npcs, "Captain John, Engineer Smith")
    
    def test_mission_particulars_to_dict(self):
        """Test converting MissionParticulars to dictionary."""
        particulars = MissionParticulars(**self.sample_mission_particulars)
        particulars_dict = particulars.to_dict()
        
        self.assertEqual(particulars_dict["content"], "This is a test mission content.")
        self.assertEqual(particulars_dict["map_image"], "http://example.com/map.jpg")
        self.assertEqual(len(particulars_dict["npc_images"]), 2)
    
    def test_mission_detail_creation(self):
        """Test creating MissionDetail instance."""
        detail = MissionDetail(**self.sample_mission_detail)
        
        self.assertEqual(detail.detail_type, "patron")
        self.assertEqual(detail.detail_name, "Science Foundation")
        self.assertEqual(detail.detail_id, "sci-1")
    
    def test_mission_reference_creation(self):
        """Test creating MissionReference instance."""
        reference = MissionReference(**self.sample_mission_reference)
        
        self.assertEqual(reference.phase, "contact")
        self.assertEqual(reference.table_id, "contact-table")
        self.assertEqual(reference.result, "Dr. Eliza Chen")
    
    def test_json_serialization(self):
        """Test that Mission objects can be properly serialized to JSON."""
        mission = Mission.from_dict(self.sample_mission_data)
        
        # Convert to JSON string
        json_str = json.dumps(mission.to_dict())
        
        # Parse back from JSON
        parsed_dict = json.loads(json_str)
        
        # Verify key elements survived serialization
        self.assertEqual(parsed_dict["mission_id"], 1)
        self.assertEqual(parsed_dict["particulars"]["content"], "This is a test mission content.")
        self.assertEqual(parsed_dict["details"]["patron"]["name"], "Science Foundation")
    
    def test_from_dict_with_none_values(self):
        """Test creating a Mission with None values for optional fields."""
        data = self.sample_mission_data.copy()
        data["particulars"]["map_image"] = None
        data["tech_context"] = None
        
        mission = Mission.from_dict(data)
        
        self.assertIsNone(mission.particulars.map_image)
        self.assertIsNone(mission.tech_context)
        
        # Convert back to dict and ensure None values are preserved
        mission_dict = mission.to_dict()
        self.assertIsNone(mission_dict["particulars"]["map_image"])
        self.assertIsNone(mission_dict["tech_context"])
    
    def test_nested_dataclass_conversion(self):
        """Test that nested dataclasses are properly converted."""
        # Create a mission with nested dataclasses
        particulars = MissionParticulars(**self.sample_mission_particulars)
        details = {
            "patron": MissionDetail(**self.sample_mission_detail)
        }
        references = [
            MissionReference(**self.sample_mission_reference)
        ]
        
        mission = Mission(
            mission_id=1,
            world={"name": "Xylon IV", "uwp": "A123456-7"},
            scenario_type={"name": "Rescue", "description": "Rescue mission"},
            details=details,
            references=references,
            particulars=particulars,
            tech_context="High tech level"
        )
        
        # Convert to dict
        mission_dict = mission.to_dict()
        
        # Verify nested structures
        self.assertEqual(mission_dict["particulars"]["content"], "This is a test mission content.")
        self.assertEqual(mission_dict["details"]["patron"]["name"], "Science Foundation")
        self.assertIsInstance(mission_dict["references"], list)
        self.assertEqual(mission_dict["references"][0]["result"], "Dr. Eliza Chen")
        
        # Convert back to Mission
        new_mission = Mission.from_dict(mission_dict)
        
        # Verify nested dataclasses
        self.assertIsInstance(new_mission.particulars, MissionParticulars)
        self.assertIsInstance(new_mission.details["patron"], MissionDetail)
        self.assertIsInstance(new_mission.references, list)
        self.assertIsInstance(new_mission.references[0], MissionReference)

if __name__ == '__main__':
    unittest.main()
