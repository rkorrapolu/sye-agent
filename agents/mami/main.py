#!/usr/bin/env python3
"""
SYE-Agent MAMI: Multi-model Author Mimicry Intelligence
Main CLI interface for the classifier agent.
"""

import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from agent import MultiModelClassifier
from redis_client import RedisClient

console = Console()

def display_welcome():
  """Display welcome message with rich formatting."""
  welcome_text = """
  [bold cyan]SYE-Agent: Self-Improving Yolo Engine[/bold cyan]
  [yellow]Multi-Model Classifier (GPT → Gemini → Claude)[/yellow]
  
  Classify production errors into:
  • [green]Symptom[/green]: What's the observable problem?
  • [blue]Cause[/blue]: What's the root cause?
  • [red]Action[/red]: What's the remediation?
  """
  console.print(Panel(welcome_text, border_style="cyan"))

def display_classification_result(result: dict):
  """
  Display classification results in a formatted table.
  
  Args:
    result: Classification result dictionary
  """
  table = Table(title="Classification Result", show_header=True, header_style="bold magenta")
  table.add_column("Category", style="cyan", width=15)
  table.add_column("Description", style="white")
  table.add_column("Confidence", style="green", width=12)
  
  symptom = result["symptom"]
  cause = result["cause"]
  action = result["action"]
  
  table.add_row(
    "Symptom",
    symptom["text"],
    f"{symptom['confidence']:.2f}"
  )
  table.add_row(
    "Cause",
    cause["text"],
    f"{cause['confidence']:.2f}"
  )
  table.add_row(
    "Action",
    action["text"],
    f"{action['confidence']:.2f}"
  )
  
  console.print()
  console.print(table)
  console.print()
  console.print(f"[dim]Classification ID: {result['classification_id']}[/dim]")
  console.print(f"[dim]Stored in Redis ✓[/dim]")

def display_model_opinions(result: dict):
  """
  Display individual model opinions.
  
  Args:
    result: Classification result with model opinions
  """
  if not Confirm.ask("\nShow individual model opinions?", default=False):
    return
  
  console.print("\n[bold yellow]Model Opinions:[/bold yellow]")
  
  console.print("\n[cyan]GPT-4 Opinion:[/cyan]")
  gpt = result.get("gpt_opinion", {})
  console.print(f"  Symptom: {gpt.get('symptom', 'N/A')}")
  console.print(f"  Cause: {gpt.get('cause', 'N/A')}")
  console.print(f"  Action: {gpt.get('action', 'N/A')}")
  
  console.print("\n[cyan]Gemini Opinion:[/cyan]")
  gemini = result.get("gemini_opinion", {})
  console.print(f"  Symptom: {gemini.get('symptom', 'N/A')}")
  console.print(f"  Cause: {gemini.get('cause', 'N/A')}")
  console.print(f"  Action: {gemini.get('action', 'N/A')}")

def retrieve_classification():
  """Retrieve and display a stored classification by ID."""
  classification_id = Prompt.ask("\nEnter classification ID")
  
  redis_client = RedisClient()
  result = redis_client.get_classification(classification_id)
  
  if result:
    console.print(f"\n[green]✓ Found classification {classification_id}[/green]")
    display_classification_result(result)
  else:
    console.print(f"\n[red]✗ Classification {classification_id} not found[/red]")

def main():
  """Main CLI loop."""
  display_welcome()
  
  try:
    classifier = MultiModelClassifier()
  except ValueError as e:
    console.print(f"[red]Error: {e}[/red]")
    console.print("[yellow]Please create a .env file with required API keys:[/yellow]")
    console.print("  OPENAI_API_KEY=...")
    console.print("  GOOGLE_API_KEY=...")
    console.print("  ANTHROPIC_API_KEY=...")
    console.print("  REDIS_HOST=localhost")
    console.print("  REDIS_PORT=5769")
    sys.exit(1)
  except Exception as e:
    console.print(f"[red]Initialization error: {e}[/red]")
    sys.exit(1)
  
  console.print("[green]✓ System ready[/green]\n")
  
  while True:
    console.print("[bold]What would you like to do?[/bold]")
    console.print("  1. Classify new input")
    console.print("  2. Retrieve stored classification")
    console.print("  3. Exit")
    
    choice = Prompt.ask("\nChoice", choices=["1", "2", "3"], default="1")
    
    if choice == "1":
      console.print("\n[bold cyan]Enter production error or log:[/bold cyan]")
      console.print("[dim](Press Ctrl+D or Ctrl+Z when done)[/dim]")
      
      try:
        lines = []
        while True:
          try:
            line = input()
            lines.append(line)
          except EOFError:
            break
        
        user_input = "\n".join(lines).strip()
        
        if not user_input:
          console.print("[yellow]No input provided[/yellow]")
          continue
        
        console.print()
        result = classifier.classify(user_input)
        
        display_classification_result(result)
        display_model_opinions(result)
          
      except KeyboardInterrupt:
        console.print("\n[yellow]Classification cancelled[/yellow]")
        continue
    
    elif choice == "2":
      retrieve_classification()
    
    elif choice == "3":
      console.print("\n[cyan]Thank you for using SYE-Agent![/cyan]")
      break
    
    console.print("\n" + "="*60 + "\n")

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    console.print("\n\n[yellow]Goodbye![/yellow]")
    sys.exit(0)

