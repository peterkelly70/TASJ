import random
import logging
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Try to import OpenAI, but don't fail if it's not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available. GPT-enhanced hooks will be disabled.")

logger = logging.getLogger(__name__)

class AdventureHooksGenerator:
    """
    Generator for Traveller RPG adventure hooks using both template-based generation
    and OpenAI's GPT API for enhanced creativity.
    """
    
    def __init__(self):
        """Initialize the adventure hooks generator."""
        # Load environment variables
        load_dotenv("config/.env")
        load_dotenv("tasj.env")
        load_dotenv()  # Also try default .env in root
        
        # Set up OpenAI API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key and OPENAI_AVAILABLE:
            openai.api_key = self.api_key
            self.gpt_available = True
            logger.info("OpenAI API key loaded successfully")
        else:
            self.gpt_available = False
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI package not available. GPT-enhanced hooks will be unavailable.")
            elif not self.api_key:
                logger.warning("No OpenAI API key found. GPT-enhanced hooks will be unavailable.")
        
        # Sample world profile (replace with database access)
        self.worlds = [
            {
                "name": "Anaxias",
                "UWP": "A553A85-D",
                "remarks": "Hi In Cp",
                "zone": "",
                "bases": "NS",
                "stellar": "M2 V",
                "trade_codes": ["High Pop", "Industrial", "Capital"]
            },
            {
                "name": "Zarvok",
                "UWP": "B879530-9",
                "remarks": "Ag Ni",
                "zone": "",
                "bases": "",
                "stellar": "K0 V",
                "trade_codes": ["Agricultural", "Non-Industrial"]
            },
            # Add more worlds...
        ]
        
        # Hook templates
        self.hook_templates = [
            "A mysterious {event} has occurred on {world}, a {summary}. The local {faction} is asking for outside help.",
            "Rumors spread of a {object} hidden on {world}, known for its {feature}. Several factions are racing to find it.",
            "A {threat} has emerged near {world}, disrupting {activity}. The Travellers are offered {reward} to intervene.",
            "An urgent diplomatic mission is needed on {world}, where tensions between {faction} and {faction2} are about to explode."
        ]
        
        # Random options
        self.events = ["sabotage", "power outage", "assassination", "plague", "AI awakening"]
        self.objects = ["prototype ship", "pre-Imperial archive", "ancient alien relic", "lost noble heir"]
        self.threats = ["pirate fleet", "rogue AI", "xeno incursion", "viral outbreak"]
        self.activities = ["jump travel", "trade", "communications", "terraforming operations"]
        self.rewards = ["a ship upgrade", "a noble title", "100,000 Cr", "information on a hidden route"]
        self.factions = ["Imperial Intelligence", "Megacorp agents", "local nobility", "religious zealots", "rebel miners"]
    
    def load_worlds_from_db(self, db_controller) -> None:
        """
        Load worlds from the database.
        
        Args:
            db_controller: Database controller with access to planet data
        """
        try:
            # This is a placeholder - implement actual DB access based on your model
            self.worlds = db_controller.get_all_planets()
            logger.info(f"Loaded {len(self.worlds)} worlds from database")
        except Exception as e:
            logger.error(f"Failed to load worlds from database: {e}")
    
    def uwp_summary(self, uwp: str) -> str:
        """
        Creates a brief description based on UWP stats.
        
        Args:
            uwp: Universal World Profile string
            
        Returns:
            A text description of the world based on UWP
        """
        starport = uwp[0]
        pop_code = uwp[4]
        tech_level = uwp[-1]
        
        pop_desc = {
            '0': 'uninhabited',
            '1': 'barely populated',
            '2': 'very sparsely populated',
            '3': 'sparsely populated',
            '4': 'low population',
            '5': 'moderate population',
            '6': 'moderate population',
            '7': 'densely populated',
            '8': 'large urban population',
            '9': 'very densely populated',
            'A': 'teeming megacities',
            'B': 'extremely overcrowded',
            'C': 'impossibly dense arcologies',
            'D': 'world-spanning ecumenopolis',
            'E': 'artificial population density',
            'F': 'maximum theoretical population'
        }.get(pop_code, "unknown population")
        
        return f"{pop_desc} world with a class {starport} starport and TL-{tech_level}"
    
    def generate_template_hook(self) -> str:
        """
        Generate an adventure hook using templates.
        
        Returns:
            A generated adventure hook string
        """
        world = random.choice(self.worlds)
        template = random.choice(self.hook_templates)
        
        # Ensure we don't pick the same faction twice
        faction = random.choice(self.factions)
        faction2 = random.choice([f for f in self.factions if f != faction])
        
        # Get a feature from the world's trade codes or a generic one if none available
        feature = random.choice(world.get("trade_codes", ["mysterious", "remote", "strategic"]))
        
        hook = template.format(
            event=random.choice(self.events),
            world=world["name"],
            summary=self.uwp_summary(world["UWP"]),
            faction=faction,
            faction2=faction2,
            object=random.choice(self.objects),
            feature=feature,
            threat=random.choice(self.threats),
            activity=random.choice(self.activities),
            reward=random.choice(self.rewards)
        )
        
        return hook
    
    def generate_gpt_hook(self, world_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate an adventure hook using OpenAI's GPT.
        
        Args:
            world_data: Optional world data to use for the hook
            
        Returns:
            A GPT-generated adventure hook or None if API is unavailable
        """
        if not self.gpt_available:
            logger.warning("GPT hook generation attempted but API key not available")
            return None
            
        try:
            # Select a random world if none provided
            if world_data is None:
                world_data = random.choice(self.worlds)
            
            # Create a prompt for GPT
            prompt = f"""
            Generate a compelling Traveller RPG adventure hook for the following world:
            
            Name: {world_data['name']}
            UWP: {world_data['UWP']}
            Trade Codes: {', '.join(world_data.get('trade_codes', []))}
            Stellar: {world_data.get('stellar', 'Unknown')}
            
            The hook should include:
            1. An interesting situation or problem
            2. Potential factions or NPCs involved
            3. A hook for player involvement
            4. Possible rewards or consequences
            
            Format as a single paragraph adventure hook that a Referee could use.
            """
            
            # Call the OpenAI API if available
            if OPENAI_AVAILABLE:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",  # Or another appropriate model
                    messages=[
                        {"role": "system", "content": "You are an experienced Traveller RPG Referee creating adventure hooks."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=250,
                    temperature=0.7
                )
                
                # Extract and return the hook
                hook = response.choices[0].message.content.strip()
                return hook
            else:
                logger.warning("OpenAI package not available but generate_gpt_hook was called")
                return None
            
        except Exception as e:
            logger.error(f"Error generating GPT hook: {e}")
            return None
    
    def generate_adventure_hook(self, use_gpt: bool = False) -> str:
        """
        Generate an adventure hook using either template-based or GPT-enhanced generation.
        
        Args:
            use_gpt: Whether to use GPT for generation if available
            
        Returns:
            A generated adventure hook string
        """
        if use_gpt and self.gpt_available:
            gpt_hook = self.generate_gpt_hook()
            if gpt_hook:
                return gpt_hook
                
        # Fall back to template-based generation
        return self.generate_template_hook()
    
    def generate_multiple_hooks(self, count: int = 5, use_gpt: bool = False) -> List[str]:
        """
        Generate multiple adventure hooks.
        
        Args:
            count: Number of hooks to generate
            use_gpt: Whether to use GPT for generation if available
            
        Returns:
            A list of generated adventure hooks
        """
        hooks = []
        for _ in range(count):
            hooks.append(self.generate_adventure_hook(use_gpt))
        return hooks


# Example usage
if __name__ == "__main__":
    generator = AdventureHooksGenerator()
    
    print("Template-based hooks:")
    for i, hook in enumerate(generator.generate_multiple_hooks(3, use_gpt=False), 1):
        print(f"{i}. {hook}\n")
    
    if generator.gpt_available:
        print("\nGPT-enhanced hooks:")
        for i, hook in enumerate(generator.generate_multiple_hooks(3, use_gpt=True), 1):
            print(f"{i}. {hook}\n")
