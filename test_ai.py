#!/usr/bin/env python3

import requests

OLLAMA_SERVER = "http://ollama.computer-wizard.com.au"

def get_models():
    """Fetch available models from the Ollama server."""
    try:
        response = requests.get(f"{OLLAMA_SERVER}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        else:
            print(f"Failed to fetch models: HTTP {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print("Connection error:", e)
        return []

def query_model(model_name, prompt):
    """Query the selected model with a given prompt."""
    try:
        data = {"model": model_name, "prompt": prompt}
        response = requests.post(f"{OLLAMA_SERVER}/api/generate", json=data)
        if response.status_code == 200:
            return response.json().get("response", "No response received.")
        else:
            return f"Error: HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Connection error: {e}"

def main():
    models = get_models()
    if not models:
        print("No models available. Exiting.")
        return
    
    print("\nAvailable models:")
    for i, model in enumerate(models):
        print(f"{i + 1}. {model}")
    
    choice = int(input("\nSelect a model (number): ")) - 1
    if choice < 0 or choice >= len(models):
        print("Invalid selection. Exiting.")
        return
    
    model_name = models[choice]
    print(f"\nSelected model: {model_name}")

    query = input("Enter your query: ")
    response = query_model(model_name, query)

    print("\nResponse from the model:")
    print(response)

if __name__ == "__main__":
    main()
