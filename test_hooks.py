#!/usr/bin/env python3
from controller.adventure_hooks_generator import AdventureHooksGenerator

def main():
    print("Testing Adventure Hooks Generator")
    print("=================================")
    
    generator = AdventureHooksGenerator()
    
    print("\nTemplate-based hooks:")
    for i, hook in enumerate(generator.generate_multiple_hooks(3, use_gpt=False), 1):
        print(f"{i}. {hook}\n")
    
    if generator.gpt_available:
        print("\nGPT-enhanced hooks:")
        for i, hook in enumerate(generator.generate_multiple_hooks(3, use_gpt=True), 1):
            print(f"{i}. {hook}\n")
    else:
        print("\nGPT enhancement not available - API key not found")

if __name__ == "__main__":
    main()
