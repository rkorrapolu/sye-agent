import re
import subprocess
from typing import Any, Dict, List

from redis_client import RedisClient

redis_client = RedisClient()


def logparser_tool(log_text: str) -> Dict[str, Any]:
  """
  Uses coroot/logparser to extract patterns from logs.

  This tool runs the coroot/logparser Docker container to parse log text
  and extract structured information including severity, pattern, frequency, and components.

  Args:
    log_text: Raw log text to parse

  Returns:
    Dictionary with keys:
    - severity: 'ERROR', 'WARN', 'INFO', etc.
    - pattern: Normalized log template
    - frequency: Number of occurrences
    - components: List of service/component names
  """
  try:
    result = subprocess.run(
      ["docker", "run", "-i", "ghcr.io/coroot/logparser"],
      input=log_text.encode("utf-8"),
      capture_output=True,
      timeout=10,
    )

    if result.returncode == 0:
      output = result.stdout.decode("utf-8")

      parsed_data = {
        "severity": _extract_severity(log_text),
        "pattern": output.strip(),
        "frequency": 1,
        "components": _extract_components(log_text),
      }
      return parsed_data
    else:
      return {
        "severity": "UNKNOWN",
        "pattern": log_text,
        "frequency": 1,
        "components": [],
      }
  except subprocess.TimeoutExpired:
    print("⚠️ Logparser timeout, using fallback")
    return {
      "severity": _extract_severity(log_text),
      "pattern": log_text,
      "frequency": 1,
      "components": _extract_components(log_text),
    }
  except Exception as e:
    print(f"⚠️ Logparser error: {e}, using fallback")
    return {
      "severity": _extract_severity(log_text),
      "pattern": log_text,
      "frequency": 1,
      "components": _extract_components(log_text),
    }


def _extract_severity(log_text: str) -> str:
  """
  Extract severity level from log text.

  Args:
    log_text: Raw log text

  Returns:
    Severity level string (ERROR, WARN, INFO, etc.)
  """
  severity_patterns = [
    (r"\bERROR\b", "ERROR"),
    (r"\bWARN(ING)?\b", "WARN"),
    (r"\bINFO\b", "INFO"),
    (r"\bDEBUG\b", "DEBUG"),
    (r"\bCRITICAL\b", "CRITICAL"),
    (r"\bFATAL\b", "FATAL"),
  ]

  for pattern, severity in severity_patterns:
    if re.search(pattern, log_text, re.IGNORECASE):
      return severity

  return "INFO"


def _extract_components(log_text: str) -> List[str]:
  """
  Extract component names from log text.

  Args:
    log_text: Raw log text

  Returns:
    List of component names found in the log
  """
  component_patterns = [r"\[([^\]]+)\]", r"component[=:](\w+)", r"service[=:](\w+)"]

  components = []
  for pattern in component_patterns:
    matches = re.findall(pattern, log_text, re.IGNORECASE)
    components.extend(matches)

  return list(set(components))


def similarity_search_tool(text: str, node_type: str) -> List[Dict[str, Any]]:
  """
  Searches Redis for similar Symptom/Cause/Action nodes.

  This tool queries the Redis database to find entries similar to the given text,
  using simple text similarity matching. Useful for finding past incidents or
  patterns that match the current classification.

  Documentation: Uses redis-py client with SCAN for pattern matching
  Reference: https://redis.io/commands/scan/

  Args:
    text: Text to search for similarities
    node_type: Type of node - 'symptom', 'cause', or 'action'

  Returns:
    List of dictionaries with keys:
    - id: Classification ID
    - text: The text content
    - similarity_score: Float between 0 and 1
    - data: Full data dictionary
  """
  try:
    results = redis_client.search_similar(text, node_type, limit=5)
    return results
  except Exception as e:
    print(f"⚠️ Similarity search error: {e}")
    return []


def is_log_format(text: str) -> bool:
  """
  Detect if the input text is in log format.

  Checks for common log patterns like timestamps, log levels, and structured formats.

  Args:
    text: Input text to analyze

  Returns:
    True if text appears to be a log entry, False otherwise
  """
  log_indicators = [
    r"\d{4}-\d{2}-\d{2}",
    r"\d{2}:\d{2}:\d{2}",
    r"\b(ERROR|WARN|INFO|DEBUG|CRITICAL|FATAL)\b",
    r"\[[^\]]+\].*:",
  ]

  for pattern in log_indicators:
    if re.search(pattern, text, re.IGNORECASE):
      return True

  return False
