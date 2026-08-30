"""Main agentic controller for the claw machine."""
from __future__ import annotations

import logging
from typing import Optional

from neoclaw.agent.code_executor import ExecutionResult, execute_student_code
from neoclaw.agent.conversation import ConversationManager
from neoclaw.agent.llm_client import LLMClient
from neoclaw.agent.models import AgentAction, AgentMode, ClawCommand
from neoclaw.agent.nl_interpreter import NLInterpreter
from neoclaw.agent.prompt_templates import (
    CLAW_CHALLENGE_SYSTEM,
    CLAW_FREE_PLAY_SYSTEM,
    CLAW_TUTOR_SYSTEM,
)
from neoclaw.hardware.claw_robot import ClawRobot
from neoclaw.hardware.dispatch import apply_command

logger = logging.getLogger(__name__)


class ClawAgent:
    """Agentic AI controller for the claw machine.

    Supports 4 modes:
    - TEACH: Guided Python lessons with hints
    - FREE_PLAY: Open-ended exploration
    - VOICE_CONTROL: Natural language → claw commands
    - CHALLENGE: Gamified challenges
    """

    def __init__(
        self,
        robot: ClawRobot,
        mode: AgentMode = AgentMode.TEACH,
        llm_client: Optional[LLMClient] = None,
    ):
        self._robot = robot
        self._mode = mode
        self._llm = llm_client or LLMClient()
        self._nl = NLInterpreter(self._llm)
        self._conversation = ConversationManager()
        self._current_exercise: Optional[str] = None

    @property
    def mode(self) -> AgentMode:
        return self._mode

    def set_mode(self, mode: AgentMode) -> None:
        self._mode = mode
        self._conversation.clear()

    def process_message(self, user_input: str) -> AgentAction:
        """Process a user message and return an action."""
        self._conversation.add_user(user_input)

        if self._mode == AgentMode.VOICE_CONTROL:
            return self._handle_voice(user_input)
        elif self._mode == AgentMode.TEACH:
            return self._handle_teach(user_input)
        elif self._mode == AgentMode.CHALLENGE:
            return self._handle_challenge(user_input)
        else:
            return self._handle_free_play(user_input)

    def execute_code(self, code: str) -> ExecutionResult:
        """Execute student code and apply the commands it produced."""
        result = execute_student_code(code)

        if result.success:
            self._apply_commands(result.commands)

        return result

    def _apply_commands(self, commands: list[ClawCommand]) -> None:
        """Run parsed commands on the robot.

        No local command table: neoclaw.hardware.dispatch owns the one mapping
        that the sandbox, the CLI and the web API all share.
        """
        for cmd in commands:
            try:
                apply_command(self._robot, cmd)
            except KeyError:
                logger.warning("Unhandled command: %s", cmd.command_type.name)

    def _handle_voice(self, text: str) -> AgentAction:
        """Parse NL and execute commands."""
        commands = self._nl.interpret(text)
        if commands:
            self._apply_commands(commands)
            cmd_names = [c.command_type.name for c in commands]
            response = f"Executed: {', '.join(cmd_names)}"
            self._conversation.add_assistant(response)
            return AgentAction(action_type="run_command", content=response)

        response = "I didn't understand that command. Try: left, right, up, down, grab, release."
        self._conversation.add_assistant(response)
        return AgentAction(action_type="explain", content=response)

    def _handle_teach(self, user_input: str) -> AgentAction:
        """Handle teaching mode with LLM assistance."""
        if not self._llm.is_available():
            return AgentAction(
                action_type="explain",
                content="AI not available. Use 'neoclaw teach --offline' for offline mode.",
            )

        response = self._llm.generate(
            prompt=user_input,
            system_prompt=CLAW_TUTOR_SYSTEM,
            history=self._conversation.get_history()[:-1],  # exclude current
        )
        self._conversation.add_assistant(response)
        return AgentAction(action_type="explain", content=response)

    def _handle_free_play(self, user_input: str) -> AgentAction:
        """Handle free play mode."""
        if self._llm.is_available():
            response = self._llm.generate(
                prompt=user_input,
                system_prompt=CLAW_FREE_PLAY_SYSTEM,
                history=self._conversation.get_history()[:-1],
            )
        else:
            response = "Free play mode. Type commands or code to control the robot."
        self._conversation.add_assistant(response)
        return AgentAction(action_type="explain", content=response)

    def _handle_challenge(self, user_input: str) -> AgentAction:
        """Handle challenge mode."""
        if self._llm.is_available():
            response = self._llm.generate(
                prompt=user_input,
                system_prompt=CLAW_CHALLENGE_SYSTEM,
                history=self._conversation.get_history()[:-1],
            )
        else:
            response = "Challenge mode requires AI. Set GEMINI_API_KEY or use Ollama."
        self._conversation.add_assistant(response)
        return AgentAction(action_type="explain", content=response)
