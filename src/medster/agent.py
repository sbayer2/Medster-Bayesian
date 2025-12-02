from typing import List
import json
from pathlib import Path
from datetime import datetime

from langchain_core.messages import AIMessage

from medster.model import call_llm
from medster.prompts import (
    ACTIVE_PLANNING_PROMPT,
    ACTIVE_ACTION_PROMPT,
    ACTIVE_VALIDATION_PROMPT,
    ACTIVE_ANSWER_PROMPT,
    get_tool_args_system_prompt,
    META_VALIDATION_SYSTEM_PROMPT,
    ACTIVE_PROMPTS,  # For mode information
)
from medster.schemas import (
    Answer,
    IsDone,
    ValidationResult,
    BayesianMetaValidation,
    OptimizedToolArgs,
    Task,
    TaskList
)
from medster.tools import TOOLS
from medster.utils.logger import Logger
from medster.utils.ui import show_progress
from medster.utils.context_manager import (
    format_output_for_context,
    manage_context_size,
    get_context_stats
)


class Agent:
    def __init__(
        self,
        max_steps: int = 20,
        max_steps_per_task: int = 5,
        persist_outputs: bool = False,
        output_dir: str = "./medster_outputs",
        enable_simple_refinement: bool = True,  # Simplified: One retry for both modes
        max_refinement_attempts: int = 1  # Simplified: Just 1 retry (not 2)
    ):
        self.logger = Logger()
        self.max_steps = max_steps            # global safety cap
        self.max_steps_per_task = max_steps_per_task

        # Task output persistence (optional for debugging)
        self.persist_outputs = persist_outputs
        self.output_dir = Path(output_dir)
        if self.persist_outputs:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.logger._log(f"Task outputs will be saved to: {self.output_dir}")

        # Simple refinement (works for both modes - Dexter pattern for deterministic data)
        self.enable_simple_refinement = enable_simple_refinement
        self.max_refinement_attempts = max_refinement_attempts

        # Check if Bayesian mode is active
        self.bayesian_mode = ACTIVE_PROMPTS.get("mode") == "bayesian"
        if self.enable_simple_refinement:
            self.logger._log(f"Simple refinement enabled (max {max_refinement_attempts} retry per task)")

    # ---------- task planning ----------
    @show_progress("Planning clinical analysis...", "Tasks planned")
    def plan_tasks(self, query: str) -> List[Task]:
        tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in TOOLS])
        prompt = f"""
        Given the clinical query: "{query}",
        Create a list of tasks to be completed.
        Example: {{"tasks": [{{"id": 1, "description": "some task", "done": false}}]}}
        """
        system_prompt = ACTIVE_PLANNING_PROMPT.format(tools=tool_descriptions)
        try:
            response = call_llm(prompt, system_prompt=system_prompt, output_schema=TaskList)
            tasks = response.tasks
        except Exception as e:
            self.logger._log(f"Planning failed: {e}")
            tasks = [Task(id=1, description=query, done=False)]

        task_dicts = [task.dict() for task in tasks]
        self.logger.log_task_list(task_dicts)
        return tasks

    # ---------- ask LLM what to do ----------
    @show_progress("Analyzing...", "")
    def ask_for_actions(self, task_desc: str, last_outputs: str = "") -> AIMessage:
        # Check if this is an MCP task that requires mandatory tool call
        is_mcp_task = any(keyword in task_desc.lower() for keyword in ["mcp server", "mcp", "analyze_medical_document", "submit to mcp", "send to mcp"])

        prompt = f"""
        We are working on: "{task_desc}".
        Here is a history of tool outputs from the session so far: {last_outputs}

        Based on the task and the outputs, what should be the next step?
        """

        # Add explicit MCP reminder if this is an MCP task
        if is_mcp_task and "analyze_medical_document" not in last_outputs:
            prompt += """

        **CRITICAL REMINDER**: This task REQUIRES calling the analyze_medical_document tool to send data to the MCP server.
        Simply having the data in previous outputs is NOT sufficient - you MUST call analyze_medical_document with that data.
        Extract the clinical note/document text from the previous outputs and pass it to analyze_medical_document.
        """

        try:
            ai_message = call_llm(prompt, system_prompt=ACTIVE_ACTION_PROMPT, tools=TOOLS)
            return ai_message
        except Exception as e:
            self.logger._log(f"ask_for_actions failed: {e}")
            # Return special marker to indicate failure (not completion)
            return AIMessage(content="AGENT_ERROR: " + str(e))

    # ---------- ask LLM if task is done (with optional refinement) ----------
    @show_progress("Checking if task is complete...", "")
    def ask_if_done(
        self,
        task_desc: str,
        recent_results: str,
        attempt: int = 0,
        return_validation_details: bool = False
    ):
        """
        Validate task completion with optional iterative refinement support.

        Args:
            task_desc: Description of the task being validated
            recent_results: Tool outputs from the current task
            attempt: Current refinement attempt (0 = first attempt)
            return_validation_details: If True, return ValidationResult with confidence

        Returns:
            bool or ValidationResult: Task completion status (and details if Bayesian mode)
        """
        prompt = f"""
        We were trying to complete the task: "{task_desc}".
        Here is a history of tool outputs from the session so far: {recent_results}

        Is the task done?
        """

        try:
            # Use Bayesian validation if in Bayesian mode and iterative refinement enabled
            if self.bayesian_mode and (self.enable_iterative_refinement or return_validation_details):
                resp = call_llm(
                    prompt,
                    system_prompt=ACTIVE_VALIDATION_PROMPT,
                    output_schema=ValidationResult
                )

                # Log confidence for monitoring
                self.logger._log(
                    f"Validation: done={resp.done}, confidence={resp.confidence:.2f}, "
                    f"completeness={resp.data_completeness:.2f}"
                )

                # Return full validation result if requested
                if return_validation_details:
                    return resp

                # Otherwise, return boolean (backward compatible)
                return resp.done

            else:
                # Deterministic mode: simple boolean validation
                resp = call_llm(
                    prompt,
                    system_prompt=ACTIVE_VALIDATION_PROMPT,
                    output_schema=IsDone
                )
                return resp.done

        except Exception as e:
            self.logger._log(f"Validation failed: {e}")

            # If return_validation_details requested, return ValidationResult object
            if return_validation_details:
                return ValidationResult(
                    done=False,
                    confidence=0.0,
                    data_completeness=0.0,
                    uncertainty_factors=["Validation failed due to error"],
                    refinement_suggestion=None
                )
            return False

    # ---------- ask LLM if main goal is achieved ----------
    @show_progress("Checking if analysis is complete...", "")
    def is_goal_achieved(
        self,
        query: str,
        task_outputs: list,
        tasks: list = None
    ):
        """
        Check if the overall goal is achieved.

        Args:
            query: Original clinical query
            task_outputs: All accumulated tool outputs
            tasks: List of planned tasks with completion status

        Returns:
            bool or dict: Task completion status (dict with confidence if Bayesian mode)
        """
        all_results = "\n\n".join(task_outputs)

        # Format task plan for meta-validator
        task_plan = ""
        if tasks:
            task_list = []
            for i, task in enumerate(tasks, 1):
                status = "✓ COMPLETED" if task.done else "✗ NOT COMPLETED"
                task_list.append(f"{i}. {status}: {task.description}")
            task_plan = f"""
Task Plan:
{chr(10).join(task_list)}
"""

        prompt = f"""
        Original clinical query: "{query}"
{task_plan}
        Data and results collected from tools so far:
        {all_results}

        Based on the task plan and data above, is the original clinical query sufficiently answered?
        """

        try:
            # Bayesian mode: Get confidence metrics for visibility
            if self.bayesian_mode:
                # Get meta-validation prompt from ACTIVE_PROMPTS
                meta_validation_prompt = ACTIVE_PROMPTS.get("meta_validation", META_VALIDATION_SYSTEM_PROMPT)

                resp = call_llm(
                    prompt,
                    system_prompt=meta_validation_prompt,
                    output_schema=BayesianMetaValidation
                )

                # Return dict with confidence for visibility (not used for early stopping)
                return {
                    "achieved": resp.achieved,
                    "confidence": resp.confidence,
                    "remaining_uncertainty": resp.remaining_uncertainty,
                    "missing_information": resp.missing_information
                }

            else:
                # Deterministic mode: simple boolean meta-validation
                resp = call_llm(
                    prompt,
                    system_prompt=META_VALIDATION_SYSTEM_PROMPT,
                    output_schema=IsDone
                )
                return resp.done

        except Exception as e:
            self.logger._log(f"Meta-validation failed: {e}")

            # Return appropriate error structure based on mode
            if self.bayesian_mode:
                return {
                    "achieved": False,
                    "confidence": 0.0,
                    "remaining_uncertainty": 5.0,
                    "missing_information": ["Meta-validation failed due to error"]
                }
            return False

    # ---------- optimize tool arguments ----------
    @show_progress("Optimizing data request...", "")
    def optimize_tool_args(self, tool_name: str, initial_args: dict, task_desc: str) -> dict:
        """Optimize tool arguments based on task requirements."""
        tool = next((t for t in TOOLS if t.name == tool_name), None)
        if not tool:
            return initial_args

        tool_description = tool.description
        tool_schema = tool.args_schema.schema() if hasattr(tool, 'args_schema') and tool.args_schema else {}

        prompt = f"""
        Task: "{task_desc}"
        Tool: {tool_name}
        Tool Description: {tool_description}
        Tool Parameters: {tool_schema}
        Initial Arguments: {initial_args}

        Review the task and optimize the arguments to ensure all relevant parameters are used correctly.
        Pay special attention to filtering parameters that would help narrow down results to match the task.
        """
        try:
            # Use configured primary model (not hardcoded) - respects .env LLM_MODEL
            response = call_llm(prompt, system_prompt=get_tool_args_system_prompt(), output_schema=OptimizedToolArgs)
            if isinstance(response, dict):
                optimized_args = response if response else initial_args
            else:
                optimized_args = response.arguments

            # Filter out None values to allow tool defaults to be used
            # (optimizer sometimes returns None for parameters it can't determine)
            filtered_args = {k: v for k, v in optimized_args.items() if v is not None}
            return filtered_args if filtered_args else initial_args
        except Exception as e:
            self.logger._log(f"Argument optimization failed: {e}, using original args")
            return initial_args

    # ---------- tool execution ----------
    def _execute_tool(self, tool, tool_name: str, inp_args):
        """Execute a tool with progress indication."""
        @show_progress(f"Fetching {tool_name}...", "")
        def run_tool():
            return tool.run(inp_args)
        return run_tool()

    # ---------- task output persistence ----------
    def _save_task_output(self, task_id: int, task_desc: str, outputs: list, metadata: dict = None):
        """
        Save task outputs to file system (Dexter-inspired feature).

        Args:
            task_id: Task ID number
            task_desc: Task description
            outputs: List of tool outputs for this task
            metadata: Optional metadata dictionary
        """
        if not self.persist_outputs:
            return

        try:
            timestamp = datetime.now().isoformat()
            output_data = {
                "task_id": task_id,
                "task_description": task_desc,
                "timestamp": timestamp,
                "outputs": outputs,
                "metadata": metadata or {},
                "reasoning_mode": ACTIVE_PROMPTS.get("mode", "deterministic")
            }

            output_file = self.output_dir / f"task_{task_id}_output.json"
            output_file.write_text(json.dumps(output_data, indent=2))
            self.logger._log(f"📁 Saved task {task_id} output to: {output_file}")

        except Exception as e:
            self.logger._log(f"Failed to save task output: {e}")

    # ---------- confirm action ----------
    def confirm_action(self, tool: str, input_str: str) -> bool:
        # In production, could add safety checks for sensitive operations
        return True

    # ---------- main loop ----------
    def run(self, query: str):
        """
        Executes the main agent loop to process a clinical query.

        Args:
            query (str): The user's clinical analysis query.

        Returns:
            str: A comprehensive clinical analysis response.
        """
        self.logger.log_user_query(query)

        step_count = 0
        last_actions = []
        task_outputs = []

        # 1. Decompose the clinical query into tasks
        tasks = self.plan_tasks(query)

        if not tasks:
            answer = self._generate_answer(query, task_outputs)
            self.logger.log_summary(answer)
            return answer

        # 2. Loop through tasks until complete or max steps reached
        while any(not t.done for t in tasks):
            if step_count >= self.max_steps:
                self.logger._log("Global max steps reached - stopping to prevent runaway loop.")
                break

            task = next(t for t in tasks if not t.done)
            self.logger.log_task_start(task.description)

            per_task_steps = 0
            task_step_outputs = []

            while per_task_steps < self.max_steps_per_task:
                if step_count >= self.max_steps:
                    self.logger._log("Global max steps reached - stopping.")
                    return

                # Pass outputs with context management to prevent token overflow
                # Uses truncation and prioritizes recent outputs
                all_session_outputs = manage_context_size(task_outputs + task_step_outputs)

                # Log context stats periodically for debugging
                stats = get_context_stats(task_outputs + task_step_outputs)
                if stats["at_risk"]:
                    self.logger._log(f"Context warning: {stats['estimated_tokens']}/{stats['max_tokens']} tokens ({stats['utilization_pct']}%)")

                ai_message = self.ask_for_actions(task.description, last_outputs=all_session_outputs)

                # Check for agent error (e.g., token overflow)
                if hasattr(ai_message, 'content') and isinstance(ai_message.content, str) and ai_message.content.startswith("AGENT_ERROR:"):
                    self.logger._log(f"Task failed due to agent error - NOT marking as complete")
                    # Don't mark as done - break to try next task or finish
                    break

                if not ai_message.tool_calls:
                    task.done = True
                    self.logger.log_task_done(task.description)
                    break

                for tool_call in ai_message.tool_calls:
                    if step_count >= self.max_steps:
                        break

                    tool_name = tool_call["name"]
                    initial_args = tool_call["args"]

                    optimized_args = self.optimize_tool_args(tool_name, initial_args, task.description)

                    action_sig = f"{tool_name}:{optimized_args}"

                    # Loop detection
                    last_actions.append(action_sig)
                    if len(last_actions) > 4:
                        last_actions = last_actions[-4:]
                    if len(set(last_actions)) == 1 and len(last_actions) == 4:
                        self.logger._log("Detected repeating action - aborting to avoid loop.")
                        return

                    tool_to_run = next((t for t in TOOLS if t.name == tool_name), None)
                    if tool_to_run and self.confirm_action(tool_name, str(optimized_args)):
                        try:
                            result = self._execute_tool(tool_to_run, tool_name, optimized_args)
                            self.logger.log_tool_run(optimized_args, result)
                            # Use context manager to format and truncate large outputs
                            output = format_output_for_context(tool_name, optimized_args, result)
                            task_outputs.append(output)
                            task_step_outputs.append(output)
                        except Exception as e:
                            self.logger._log(f"Tool execution failed: {e}")
                            error_output = f"Error from {tool_name} with args {optimized_args}: {e}"
                            task_outputs.append(error_output)
                            task_step_outputs.append(error_output)
                    else:
                        self.logger._log(f"Invalid tool: {tool_name}")

                    step_count += 1
                    per_task_steps += 1

                # Check if MCP task actually called the required tool
                is_mcp_task = any(kw in task.description.lower() for kw in ["mcp", "analyze_medical_document"])
                mcp_tool_called = any("analyze_medical_document" in output for output in task_step_outputs)

                if is_mcp_task and not mcp_tool_called:
                    self.logger._log(f"MCP task did not call analyze_medical_document - NOT marking as complete")
                    # Don't mark as done - the tool wasn't called
                    break

                # SIMPLIFIED VALIDATION PATTERN
                # Works for both Bayesian and Deterministic modes
                # Bayesian mode: Track confidence for visibility (but don't block on it)
                # Deterministic mode: Simple binary validation with optional retry

                if self.bayesian_mode:
                    # Bayesian mode: Get validation with confidence tracking
                    validation_result = self.ask_if_done(
                        task.description,
                        "\n".join(task_step_outputs),
                        attempt=per_task_steps,
                        return_validation_details=True
                    )

                    is_done = validation_result.done
                    confidence = validation_result.confidence
                    completeness = validation_result.data_completeness

                    # Log confidence for visibility (but don't block on it)
                    if is_done:
                        self.logger._log(
                            f"✓ Task complete: confidence={confidence:.2f}, "
                            f"data_completeness={completeness:.2f}"
                        )

                    # Save with confidence metadata
                    metadata = {
                        "confidence": confidence,
                        "data_completeness": completeness,
                        "uncertainty_factors": validation_result.uncertainty_factors
                    }
                else:
                    # Deterministic mode: Simple boolean validation
                    is_done = self.ask_if_done(task.description, "\n".join(task_step_outputs))
                    metadata = None

                # SIMPLE REFINEMENT (Dexter pattern for deterministic data endpoints)
                # If task not done and we have retries left, try once more
                if not is_done and self.enable_simple_refinement and per_task_steps <= self.max_refinement_attempts:
                    self.logger._log(
                        f"🔄 Task incomplete, retrying once... "
                        f"(attempt {per_task_steps + 1}/{self.max_refinement_attempts + 1})"
                    )
                    continue  # Retry task with same description

                # Task complete or max attempts reached
                if is_done:
                    task.done = True
                    self.logger.log_task_done(task.description)
                else:
                    # Max attempts reached but still not done - accept result
                    self.logger._log(f"⚠️  Max attempts reached, moving to next task")
                    task.done = True  # Mark done to avoid infinite loop

                # Save task output
                self._save_task_output(
                    task.id,
                    task.description,
                    task_step_outputs,
                    metadata=metadata
                )
                break

            # META-VALIDATION: Check if overall goal is achieved
            if task.done:
                goal_result = self.is_goal_achieved(query, task_outputs, tasks)

                # Bayesian mode returns dict with confidence (for visibility only)
                if isinstance(goal_result, dict):
                    if goal_result["achieved"]:
                        self.logger._log(
                            f"Goal achieved (confidence={goal_result.get('confidence', 'N/A'):.2f}). "
                            f"Generating summary."
                        )
                        break
                    # Continue to next task if goal not achieved yet

                # Deterministic mode returns boolean
                elif goal_result:
                    self.logger._log("Clinical analysis complete. Generating summary.")
                    break

        answer = self._generate_answer(query, task_outputs)
        self.logger.log_summary(answer)
        return answer

    # ---------- answer generation ----------
    @show_progress("Generating clinical summary...", "Analysis complete")
    def _generate_answer(self, query: str, task_outputs: list) -> str:
        """Generate the final clinical analysis based on collected data."""
        # Apply context management to prevent token overflow in final summary
        all_results = manage_context_size(task_outputs) if task_outputs else "No clinical data was collected."
        answer_prompt = f"""
        Original clinical query: "{query}"

        Clinical data and results collected:
        {all_results}

        Based on the data above, provide a comprehensive clinical analysis.
        Include specific values, reference ranges, trends, and clinical implications.
        Flag any critical findings that require immediate attention.
        """
        answer_obj = call_llm(answer_prompt, system_prompt=ACTIVE_ANSWER_PROMPT, output_schema=Answer)
        return answer_obj.answer
