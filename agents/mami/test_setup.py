#!/usr/bin/env python3
"""
Setup verification script - tests all components without making API calls
"""

import os
import sys
from rich.console import Console
from rich.table import Table

console = Console()

def test_python_version():
  """Test Python version is 3.11+"""
  version = sys.version_info
  if version.major >= 3 and version.minor >= 11:
    return True, f"Python {version.major}.{version.minor}.{version.micro}"
  return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)"

def test_env_file():
  """Test .env file exists and has required keys"""
  if not os.path.exists(".env"):
    return False, ".env file not found"
  
  from dotenv import load_dotenv
  load_dotenv()
  
  required_keys = [
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "REDIS_HOST",
    "REDIS_PORT"
  ]
  
  missing_keys = []
  for key in required_keys:
    value = os.getenv(key)
    if not value or "your_" in value or "..." in value:
      missing_keys.append(key)
  
  if missing_keys:
    return False, f"Missing or invalid keys: {', '.join(missing_keys)}"
  
  return True, "All environment variables set"

def test_imports():
  """Test all required imports"""
  try:
    import redis
    import openai
    from google import genai
    from anthropic import Anthropic
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    return True, "All dependencies installed"
  except ImportError as e:
    return False, f"Import error: {str(e)}"

def test_redis_connection():
  """Test Redis connection"""
  try:
    import redis
    from dotenv import load_dotenv
    
    load_dotenv()
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "5769"))
    
    client = redis.Redis(host=host, port=port, decode_responses=True)
    client.ping()
    
    return True, f"Connected to Redis at {host}:{port}"
  except Exception as e:
      return False, f"Redis connection failed: {str(e)}"

def test_docker():
  """Test Docker availability"""
  import subprocess
  
  try:
    result = subprocess.run(
      ["docker", "--version"],
      capture_output=True,
      timeout=5
    )
    if result.returncode == 0:
      version = result.stdout.decode('utf-8').strip()
      return True, version
    return False, "Docker command failed"
  except FileNotFoundError:
    return False, "Docker not found (for logparser)"
  except Exception as e:
    return False, f"Docker check failed: {str(e)}"

def test_redis_client():
  """Test RedisClient class"""
  try:
    from redis_client import RedisClient
    client = RedisClient()
    return True, "RedisClient initialized"
  except Exception as e:
    return False, f"RedisClient error: {str(e)}"

def test_tools():
  """Test tools module"""
  try:
    from tools import is_log_format, similarity_search_tool
    
    test_log = "2024-10-25 ERROR database timeout"
    is_log = is_log_format(test_log)
    
    if is_log:
      return True, "Tools module working"
    return False, "Log detection failed"
  except Exception as e:
    return False, f"Tools error: {str(e)}"

def test_project_structure():
  """Test all required files exist"""
  required_files = [
    "agent.py",
    "redis_client.py",
    "tools.py",
    "main.py",
    "pyproject.toml"
  ]
  
  missing = []
  for file in required_files:
    if not os.path.exists(file):
      missing.append(file)
  
  if missing:
    return False, f"Missing files: {', '.join(missing)}"
  
  return True, f"All {len(required_files)} required files present"

def run_tests():
  """Run all tests and display results"""
  console.print("\n[bold cyan]SYE-Agent MAMI Setup Verification[/bold cyan]\n")
  
  tests = [
    ("Python Version", test_python_version),
    ("Project Structure", test_project_structure),
    ("Environment File", test_env_file),
    ("Python Dependencies", test_imports),
    ("Redis Connection", test_redis_connection),
    ("Redis Client", test_redis_client),
    ("Tools Module", test_tools),
    ("Docker", test_docker),
  ]
  
  table = Table(show_header=True, header_style="bold magenta")
  table.add_column("Test", style="cyan", width=25)
  table.add_column("Status", width=10)
  table.add_column("Details", style="white")
  
  passed = 0
  failed = 0
  warnings = 0
  
  for test_name, test_func in tests:
    try:
      success, message = test_func()
      if success:
        table.add_row(test_name, "[green]✓ PASS[/green]", message)
        passed += 1
      else:
        if "Optional" in test_name:
          table.add_row(test_name, "[yellow]⚠ WARN[/yellow]", message)
          warnings += 1
        else:
          table.add_row(test_name, "[red]✗ FAIL[/red]", message)
          failed += 1
    except Exception as e:
      table.add_row(test_name, "[red]✗ ERROR[/red]", str(e))
      failed += 1
  
  console.print(table)
  console.print()
  
  console.print(f"[green]✓ Passed: {passed}[/green]")
  if warnings > 0:
    console.print(f"[yellow]⚠ Warnings: {warnings}[/yellow]")
  if failed > 0:
    console.print(f"[red]✗ Failed: {failed}[/red]")
  
  console.print()
  
  if failed == 0:
    console.print("[bold green]✅ All critical tests passed! System is ready.[/bold green]")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print("  1. Run: [bold]uv run python main.py[/bold]")
    console.print("  2. Or try: [bold]uv run python example.py 1[/bold]")
    return 0
  else:
    console.print("[bold red]❌ Some tests failed. Please fix the issues above.[/bold red]")
    console.print("\n[cyan]Common fixes:[/cyan]")
    console.print("  1. Environment: [bold]cp .env.example .env[/bold] and edit")
    console.print("  2. Dependencies: [bold]uv sync[/bold]")
    console.print("  3. Redis: [bold]redis-server --port 5769[/bold]")
    return 1

if __name__ == "__main__":
  exit_code = run_tests()
  sys.exit(exit_code)

