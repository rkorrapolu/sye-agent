import json

from smolagents import (
  ActionStep,
  CodeAgent,
  FinalAnswerPromptTemplate,
  InferenceClientModel,
  ManagedAgentPromptTemplate,
  PlanningPromptTemplate,
  PromptTemplates,
)

from neo4j_tool import Neo4jKnowledgeGraphTool
from semantic_cache import get_semantic_cache


def display_plan(plan_content):
  """Display the plan in a formatted way"""
  print("\n" + "=" * 60)
  print("🤖 AGENT PLAN CREATED")
  print("=" * 60)
  print(plan_content)
  print("=" * 60)


def display_knowledge_graph(kg_output):
  """Display the knowledge graph in a formatted way"""
  print("\n" + "=" * 60)
  print("📊 KNOWLEDGE GRAPH GENERATED")
  print("=" * 60)

  # Try to parse as JSON for pretty printing
  try:
    if isinstance(kg_output, str):
      import json

      kg_dict = json.loads(kg_output)
      print(json.dumps(kg_dict, indent=2))
    else:
      print(kg_output)
  except:
    # If not valid JSON, just print as-is
    print(kg_output)

  print("=" * 60)


def display_existing_nodes_for_review(review_output):
  """Display existing nodes found in the database for user review."""
  print("\n" + "=" * 60)
  print("📚 EXISTING KNOWLEDGE FOUND IN DATABASE")
  print("=" * 60)

  existing_nodes = review_output.get("existing_nodes", [])
  query_summary = review_output.get("query_summary", "")

  if query_summary:
    print(f"\n{query_summary}\n")

  if not existing_nodes:
    print("  No similar nodes found in the database.")
    print("  → This appears to be new knowledge!")
    print("\n" + "=" * 60)
    return

  # Organize by type
  by_type = {"Symptom": [], "Error": [], "Action": []}

  for node in existing_nodes:
    label = node.get("label", "Unknown")
    if label in by_type:
      by_type[label].append(node)

  # Display organized by type
  print(f"  Found {len(existing_nodes)} existing nodes:\n")

  for node_type, nodes in by_type.items():
    if nodes:
      print(f"  🔹 {node_type}s ({len(nodes)}):")
      for node in nodes:
        name = node.get("properties", {}).get("name", "Unknown")
        times_seen = node.get("times_seen", 1)
        node_id = node.get("id", "?")

        frequency = "🔥" if times_seen > 5 else "⭐" if times_seen > 2 else "•"
        print(f"    {frequency} {name} (seen {times_seen}x, id: {node_id})")
      print()

  print("=" * 60)


def display_existing_context(agent):
  """
  Display existing knowledge that the agent consulted from Neo4j.
  Shows what's already in the database before the new graph is presented.
  """
  if not hasattr(agent, "memory") or not agent.memory.steps:
    print("\n⚠️  Warning: Agent did not query existing knowledge")
    return

  print("\n" + "=" * 60)
  print("📚 EXISTING KNOWLEDGE IN DATABASE")
  print("=" * 60)

  found_any = False

  # Track what was found by category
  existing_by_type = {"Symptom": [], "Error": [], "Action": []}

  for step in agent.memory.steps:
    # Look for neo4j_knowledge_graph tool calls and their results
    if hasattr(step, "action_output") and isinstance(step.action_output, str):
      try:
        import json

        output = json.loads(step.action_output)

        # Check if this is a query result with exists=True
        if output.get("exists", False):
          found_any = True
          name = output.get("name", "Unknown")
          # We need to infer the type from the query that was made
          # For now, just display the found node
          print(f"  • {name}")

      except (json.JSONDecodeError, KeyError):
        pass

  if not found_any:
    print("  No similar nodes found in database.")
    print("  → This appears to be new knowledge!")

  print("=" * 60)
  print()


def get_user_choice():
  """Get user's choice for plan approval"""
  while True:
    choice = input(
      "\nChoose an option:\n1. Approve plan\n2. Modify plan\n3. Cancel\nYour choice (1-3): "
    ).strip()
    if choice in ["1", "2", "3"]:
      return int(choice)
    print("Invalid choice. Please enter 1, 2, or 3.")


def get_user_choice_for_kg():
  """Get user's choice for knowledge graph approval"""
  while True:
    choice = input(
      "\nChoose an option:\n"
      "1. Approve knowledge graph\n"
      "2. Modify knowledge graph\n"
      "3. Retry (reject and regenerate with feedback)\n"
      "4. Cancel\n"
      "Your choice (1-4): "
    ).strip()
    if choice in ["1", "2", "3", "4"]:
      return int(choice)
    print("Invalid choice. Please enter 1, 2, 3, or 4.")


def get_user_choice_for_existing():
  """Get user's choice for existing node review."""
  while True:
    choice = input(
      "\nWhat would you like to do with existing knowledge?\n"
      "1. Confirm (nodes are accurate, use as-is)\n"
      "2. Modify (edit node properties)\n"
      "3. Skip (only create new nodes, ignore existing)\n"
      "4. Cancel\n"
      "Your choice (1-4): "
    ).strip()
    if choice in ["1", "2", "3", "4"]:
      return int(choice)
    print("Invalid choice. Please enter 1, 2, 3, or 4.")


def get_modified_plan(original_plan):
  """Allow user to modify the plan"""
  print("\n" + "-" * 40)
  print("MODIFY PLAN")
  print("-" * 40)
  print("Current plan:")
  print(original_plan)
  print("-" * 40)
  print("Enter your modified plan (press Enter twice to finish):")

  lines = []
  empty_line_count = 0

  while empty_line_count < 2:
    line = input()
    if line.strip() == "":
      empty_line_count += 1
    else:
      empty_line_count = 0
    lines.append(line)

  # Remove the last two empty lines
  modified_plan = "\n".join(lines[:-2])
  return modified_plan if modified_plan.strip() else original_plan


def get_modified_knowledge_graph(original_kg):
  """Allow user to modify the knowledge graph JSON"""
  print("\n" + "-" * 40)
  print("MODIFY KNOWLEDGE GRAPH")
  print("-" * 40)
  print("Current knowledge graph:")

  # Pretty print if possible
  try:
    import json

    if isinstance(original_kg, str):
      kg_dict = json.loads(original_kg)
      formatted = json.dumps(kg_dict, indent=2)
    else:
      formatted = json.dumps(original_kg, indent=2)
    print(formatted)
  except:
    print(original_kg)

  print("-" * 40)
  print("Enter your modified JSON (press Enter twice to finish):")
  print("Tip: Copy the JSON above, paste it, make edits, then press Enter twice")
  print()

  lines = []
  empty_line_count = 0

  while empty_line_count < 2:
    line = input()
    if line.strip() == "":
      empty_line_count += 1
    else:
      empty_line_count = 0
    lines.append(line)

  # Remove the last two empty lines
  modified_json = "\n".join(lines[:-2])

  # Try to parse to validate JSON
  try:
    import json

    parsed = json.loads(modified_json)
    return parsed  # Return as dict/list
  except json.JSONDecodeError as e:
    print(f"⚠️ Warning: Invalid JSON ({e}). Using modified text as-is...")
    return modified_json if modified_json.strip() else original_kg


def get_modified_existing_nodes(existing_nodes):
  """Allow user to modify existing node properties."""
  print("\n" + "-" * 40)
  print("MODIFY EXISTING NODES")
  print("-" * 40)
  print("Current nodes:")

  import json

  print(json.dumps(existing_nodes, indent=2))

  print("-" * 40)
  print("Instructions:")
  print("- Copy the JSON above")
  print("- Make your edits (change names, add properties, etc.)")
  print("- Paste the modified JSON below")
  print("- Press Enter twice to finish")
  print()

  lines = []
  empty_line_count = 0

  while empty_line_count < 2:
    line = input()
    if line.strip() == "":
      empty_line_count += 1
    else:
      empty_line_count = 0
    lines.append(line)

  # Remove the last two empty lines
  modified_json = "\n".join(lines[:-2])

  # Try to parse to validate JSON
  try:
    parsed = json.loads(modified_json)
    return parsed  # Return as list
  except json.JSONDecodeError as e:
    print(f"⚠️ Warning: Invalid JSON ({e}). Using original nodes...")
    return existing_nodes


def get_retry_feedback():
  """Get feedback from user for knowledge graph regeneration"""
  print("\n" + "-" * 40)
  print("PROVIDE FEEDBACK FOR REGENERATION")
  print("-" * 40)
  print("What should the agent improve or change?")
  print("(Press Enter twice to finish)")
  print()

  lines = []
  empty_line_count = 0

  while empty_line_count < 2:
    line = input()
    if line.strip() == "":
      empty_line_count += 1
    else:
      empty_line_count = 0
    lines.append(line)

  # Remove the last two empty lines
  feedback = "\n".join(lines[:-2])
  return (
    feedback.strip() if feedback.strip() else "Please try again with better extraction."
  )


def check_neo4j_connection():
  """Check if Neo4j is accessible before starting."""
  try:
    from neo4j_utils import Neo4jConnection

    conn = Neo4jConnection()
    conn.close()
    return True
  except Exception as e:
    print("\n⚠️ Warning: Cannot connect to Neo4j")
    print(f"Error: {e}")
    print("The agent will work but graphs won't be persisted.")
    print("To fix: docker-compose up -d")
    return False


def check_redis_connection():
  """Check if Redis is accessible before starting."""
  try:
    cache = get_semantic_cache()
    stats = cache.stats()
    print(f"✅ Redis connected: {stats.get('redis_memory_used', 'N/A')} used")
    return True
  except Exception as e:
    print("\n⚠️ Warning: Cannot connect to Redis")
    print(f"Error: {e}")
    print("Semantic caching will be disabled.")
    print("To fix: docker-compose up -d")
    return False


def check_agent_queried_neo4j(agent):
  """
  Check if the agent queried Neo4j before generating the final answer.
  Returns (queried: bool, query_results: list)
  """
  if not hasattr(agent, "memory") or not agent.memory.steps:
    return False, []

  query_results = []
  has_queries = False

  for step in agent.memory.steps:
    # Check if step is a tool call to neo4j_knowledge_graph
    if hasattr(step, "tool_calls") and step.tool_calls:
      for tool_call in step.tool_calls:
        if tool_call.get("name") == "neo4j_knowledge_graph":
          has_queries = True
          if hasattr(step, "observations"):
            query_results.append(step.observations)

  return has_queries, query_results


def interrupt_on_existing_node_review(memory_step, agent):
  """
  Interrupt when agent presents existing nodes for user review.
  This happens BEFORE final graph generation.
  MUST happen for every execution - even with empty results.
  """
  # Only interrupt if this is a final answer step
  if not memory_step.is_final_answer:
    return

  # Check if this is the existing node review phase
  try:
    kg_output = memory_step.action_output

    if isinstance(kg_output, str):
      import json

      output_dict = json.loads(kg_output)
    else:
      output_dict = kg_output

    # Check if this is the existing_node_review phase
    if output_dict.get("phase") != "existing_node_review":
      return  # Not this phase, let other callbacks handle it

    print("\n🔍 Agent completed existing knowledge search...")

    existing_nodes = output_dict.get("existing_nodes", [])

    # NEW: Handle empty results explicitly
    if not existing_nodes:
      print("\n" + "=" * 60)
      print("📭 NO EXISTING KNOWLEDGE FOUND")
      print("=" * 60)
      print("  The agent searched Neo4j but found no similar nodes.")
      print("  This appears to be entirely new knowledge.")
      print("=" * 60)

      # Get user confirmation to proceed
      proceed = input("\n⚠️  Proceed to generate new graph? (y/n): ").strip().lower()

      if proceed == "y":
        print("✅ Approved. Agent will now generate the knowledge graph...")
        memory_step.observations = "User confirmed: No existing nodes found. Proceed with generating a new knowledge graph."
        memory_step.is_final_answer = False
        return
      else:
        print("❌ Cancelled by user.")
        agent.interrupt()
        return

    # EXISTING: Display existing nodes for review
    display_existing_nodes_for_review(output_dict)

    # Get user choice
    choice = get_user_choice_for_existing()

    if choice == 1:  # Confirm as-is
      print("✅ Existing nodes confirmed. Agent will now generate complete graph...")

      # Add confirmation to agent's observations
      memory_step.observations = (
        "User confirmed existing nodes are accurate. "
        "Proceed with generating the complete knowledge graph that includes these existing nodes."
      )

      # Clear final answer flag so agent continues
      memory_step.is_final_answer = False
      return

    elif choice == 2:  # Modify
      modified_nodes = get_modified_existing_nodes(
        output_dict.get("existing_nodes", [])
      )

      print("✅ Existing nodes updated. Agent will incorporate changes...")

      # Add modifications to agent's observations
      import json

      memory_step.observations = (
        f"User modified existing nodes. Updated nodes: {json.dumps(modified_nodes, indent=2)}\n"
        "Proceed with generating the complete knowledge graph using these modified nodes."
      )

      # Clear final answer flag so agent continues
      memory_step.is_final_answer = False
      return

    elif choice == 3:  # Skip existing, only new
      print("⏭️  Agent will only create new nodes...")

      memory_step.observations = (
        "User requested to skip existing nodes. "
        "Generate a knowledge graph with ONLY new nodes from the user's input. "
        "Do not include the existing nodes in your output."
      )

      # Clear final answer flag so agent continues
      memory_step.is_final_answer = False
      return

    elif choice == 4:  # Cancel
      print("❌ Execution cancelled by user.")
      agent.interrupt()
      return

  except Exception as e:
    print(f"❌ Error processing existing node review: {e}")
    print("Allowing execution to continue...")
    return


def interrupt_on_final_answer(memory_step, agent):
  """
  Step callback that interrupts the agent after a final answer is generated.
  This allows for user interaction to review and potentially modify the knowledge graph output.
  """
  # Only interrupt if this is the final answer step
  if not memory_step.is_final_answer:
    return  # Not a final answer yet, continue execution

  print("\n🛑 Agent generated a final answer...")

  # Display what existing knowledge was consulted
  display_existing_context(agent)

  # Extract the knowledge graph JSON
  try:
    kg_output = memory_step.action_output

    # Display the knowledge graph
    display_knowledge_graph(kg_output)

    # Get user choice
    choice = get_user_choice_for_kg()

    if choice == 1:  # Approve
      print("✅ Knowledge graph approved! Finalizing...")

      # Write to Neo4j
      try:
        from neo4j_utils import Neo4jConnection, write_knowledge_graph

        print("\n📝 Writing to Neo4j...")
        conn = Neo4jConnection()
        num_nodes, num_rels, run_id = write_knowledge_graph(conn, kg_output)
        conn.close()

        print(f"✅ Written to Neo4j: {num_nodes} nodes, {num_rels} relationships")
        print(f"🔗 Run ID: {run_id}")
        print("🔗 View in Neo4j Browser: http://localhost:7474/browser/")

      except Exception as e:
        print(f"⚠️ Warning: Failed to write to Neo4j: {e}")
        print("Knowledge graph is approved but not persisted.")

      # Don't interrupt - let the agent complete
      return

    elif choice == 2:  # Modify
      # Get modified knowledge graph from user
      modified_kg = get_modified_knowledge_graph(kg_output)

      # Update the action output with modified graph
      memory_step.action_output = modified_kg

      print("\n✅ Knowledge graph updated!")
      display_knowledge_graph(modified_kg)
      print("Continuing with modified output...")
      # Don't interrupt - let the agent complete with modified output
      return

    elif choice == 3:  # Retry with feedback
      print("\n🔄 Requesting regeneration...")
      feedback = get_retry_feedback()

      # Add feedback to observations to guide the agent
      memory_step.observations = (
        f"⚠️ The knowledge graph was rejected. User feedback: {feedback}\n"
        "Please generate a revised knowledge graph considering this feedback."
      )

      # Clear the final answer flag to force agent to continue
      memory_step.is_final_answer = False

      print("Agent will regenerate the knowledge graph...")
      # Don't interrupt - let the agent continue with feedback
      return

    elif choice == 4:  # Cancel
      print("❌ Execution cancelled by user.")
      agent.interrupt()
      return

  except Exception as e:
    print(f"❌ Error processing final answer: {e}")
    print("Allowing execution to continue...")
    return


def main():
  # Check connections
  neo4j_ok = check_neo4j_connection()
  redis_ok = check_redis_connection()

  if not neo4j_ok:
    print("\n❌ Neo4j required. Exiting.")
    return

  if not redis_ok:
    print("\n⚠️  Continuing without cache (performance may be slower)")

  NODES = json.dumps(
    {
      "Symptom": "A symptom describes what the error looks like.",
      "Error": "An error describes the root cause of the symptom.",
      "Action": "An action describes a way to fix the error.",
    }
  )
  RELATIONSHIPS = {
    "CAUSES": "Causes relate symptoms to errors.",
    "RELATES": "Relates relate symptoms to other symptoms.",
    "FIXES": "Relate actions to errors they fixed.",
    "TRIGGERS": "Relates an error to an action.",
  }
  agent = CodeAgent(
    model=InferenceClientModel(),
    tools=[Neo4jKnowledgeGraphTool()],  # Neo4j tool for graph persistence
    prompt_templates=PromptTemplates(
      system_prompt=f"""You are an assistant tasked with helping the user create a knowledge graph.
The knowledge graph has the following node types: {NODES}.
The knowledge graph has the following relationship types: {RELATIONSHIPS}.

CRITICAL CONSTRAINTS:
- You MUST only use the information from the user's input text.
- Do NOT add any information that is not explicitly stated in the input.
- Do NOT make assumptions or add external knowledge.
- Do NOT search for additional information.

MANDATORY WORKFLOW (YOU MUST FOLLOW THESE STEPS IN ORDER):

Step 1: EXTRACT KEY TERMS
   First, identify the key symptoms, errors, and actions mentioned in the user's input.
   List them out clearly.

Step 2: QUERY EXISTING KNOWLEDGE (REQUIRED - DO NOT SKIP)
   For EACH key term identified, you MUST query Neo4j to check if similar nodes already exist:

   Use the neo4j_knowledge_graph tool with "query_existing" operation:
   <code>
   neo4j_knowledge_graph("query_existing", '{{"name": "database connection", "label": "Symptom"}}')
   </code>

   Example queries you MUST perform:
   - If user mentions "connection drops": neo4j_knowledge_graph("query_existing", '{{"name": "connection drops", "label": "Symptom"}}')
   - If user mentions "timeout error": neo4j_knowledge_graph("query_existing", '{{"name": "timeout", "label": "Error"}}')
   - If user mentions "restart server": neo4j_knowledge_graph("query_existing", '{{"name": "restart", "label": "Action"}}')

   This is NOT optional - you MUST query before generating the graph.

Step 3: PRESENT EXISTING KNOWLEDGE TO USER
   After querying, you MUST present the existing nodes to the user for review.

   Output the existing nodes in JSON format using final_answer():

   <code>
   final_answer({{"phase": "existing_node_review", "existing_nodes": [{{"id": "neo4j_id", "label": "Symptom", "properties": {{"name": "connection drops"}}, "times_seen": 5}}], "query_summary": "Found 2 existing nodes related to your input"}})
   </code>

   If no existing nodes are found, output:
   <code>
   final_answer({{"phase": "existing_node_review", "existing_nodes": [], "query_summary": "No existing nodes found. This appears to be new knowledge."}})
   </code>

   IMPORTANT: You MUST call final_answer() after querying and BEFORE generating the knowledge graph.
   The user will review this information and may provide modifications.

Step 4: WAIT FOR USER FEEDBACK
   After presenting existing nodes, the system will automatically pause.
   The user will review the existing knowledge and may:
   - Confirm the nodes are accurate
   - Modify node properties (names, descriptions)
   - Add additional context

   You will receive user feedback in your observations. Use this feedback when generating the final graph.

Step 5: GENERATE KNOWLEDGE GRAPH
   After receiving user feedback about existing nodes, create the complete knowledge graph.

   Your graph should include:
   1. Existing nodes (as confirmed or modified by the user)
   2. New nodes from the user's original input
   3. Relationships between existing and new nodes

   Output format:
   <code>
   final_answer({{"phase": "final_graph", "nodes": [{{"id": "0", "label": "Symptom", "properties": {{"name": "connection drops"}}, "source": "existing"}}, {{"id": "1", "label": "Action", "properties": {{"name": "check network"}}, "source": "new"}}], "relationships": [{{"type": "FIXES", "start_node_id": "1", "end_node_id": "0", "properties": {{"details": "..."}}}}]}})
   </code>

   CRITICAL: Mark each node with "source": "existing" or "source": "new" so the system knows which nodes to merge vs create.

Step 6: RETURN FINAL ANSWER
   When you have completed the knowledge graph, you MUST call final_answer() tool with the JSON:

   <code>
   final_answer({{"phase": "final_graph", "nodes": [...], "relationships": [...]}})
   </code>

IMPORTANT:
- You MUST wrap your final_answer() call in <code> tags (shown above)
- Do NOT return the JSON without using final_answer()
- Do NOT forget the <code> tags
- Do NOT skip the querying step (Step 2)

NOTE: The Neo4j write will happen automatically after user approval. You don't need to call write_graph yourself.

WHY THIS WORKFLOW MATTERS:
- Prevents duplicate nodes in the database
- Builds on existing knowledge rather than recreating it
- Shows the user what already exists before proposing new nodes
- Enables accurate merge statistics after approval
""",
      planning=PlanningPromptTemplate(
        initial_plan="",
        update_plan_pre_messages="",
        update_plan_post_messages="",
      ),
      managed_agent=ManagedAgentPromptTemplate(task="", report=""),
      final_answer=FinalAnswerPromptTemplate(pre_messages="", post_messages=""),
    ),
    # planning_interval=5,  # Plan every 5 steps for demonstration
    step_callbacks={
      ActionStep: [interrupt_on_existing_node_review, interrupt_on_final_answer]
    },
    max_steps=15,  # Allow more steps for regeneration after retry
    verbosity_level=1,  # Show agent thoughts
  )

  # Prompt user for input
  print("\n" + "=" * 60)
  print("🎯 KNOWLEDGE GRAPH BUILDER")
  print("=" * 60)
  print("\nDescribe the problem or situation you want to analyze.")
  print(
    "The agent will extract symptoms, errors, and actions to build a knowledge graph."
  )
  print("\nExamples:")
  print("  - 'The database connection drops randomly in my application.'")
  print("  - 'Users report slow page loads during peak hours.'")
  print("  - 'The authentication service fails after server restarts.'")
  print("\n" + "-" * 60)

  task = input("Enter your description: ").strip()

  # Validate input
  if not task:
    print("\n❌ Error: No input provided. Exiting.")
    return

  if len(task) < 10:
    print("\n⚠️  Warning: Input seems very short. Consider providing more details.")
    proceed = input("Continue anyway? (y/n): ").strip().lower()
    if proceed != "y":
      print("Cancelled.")
      return

  try:
    print(f"\n📋 Task: {task}")
    print("\n🤖 Agent starting execution...")

    # First run - will create plan and potentially get interrupted
    result = agent.run(task, reset=False)

    # If we get here, the plan was approved or execution completed
    print("\n✅ Task completed successfully!")
    print("\n📄 Final Result:")
    print("-" * 40)
    print(result)

  except Exception as e:
    if "interrupted" in str(e).lower():
      print("\n🛑 Agent execution was cancelled by user.")
      print("\nTo resume execution later, you could call:")
      print("agent.run(task, reset=False)  # This preserves the agent's memory")

      # Demonstrate resuming with reset=False
      print("\n" + "=" * 60)
      print("DEMONSTRATION: Resuming with reset=False")
      print("=" * 60)

      # Show current memory state
      print(f"\n📚 Current memory contains {len(agent.memory.steps)} steps:")
      for i, step in enumerate(agent.memory.steps):
        step_type = type(step).__name__
        print(f"  {i + 1}. {step_type}")

      # Ask if user wants to see resume demonstration
      resume_choice = (
        input("\nWould you like to see resume demonstration? (y/n): ").strip().lower()
      )
      if resume_choice == "y":
        print("\n🔄 Resuming execution...")
        try:
          # Resume without resetting - preserves memory
          agent.run(task, reset=False)
          print("\n✅ Task completed after resume!")
          print("\n📄 Final Result:")
          print("-" * 40)
        except Exception as resume_error:
          print(f"\n❌ Error during resume: {resume_error}")
        else:
          print(f"\n❌ An error occurred: {e}")
  return


if __name__ == "__main__":
  main()
