"""The agent drives the same robot, through the same dispatch table.

It used to hold its own command→method map for the gantry ClawMachine, so a
voice command like "đi tiến" reached a machine that could not honour it.
"""
from __future__ import annotations

import pytest

from neoclaw.agent.claw_agent import ClawAgent
from neoclaw.agent.models import AgentMode
from neoclaw.hardware.claw_robot import ClawRobot


@pytest.fixture
def robot():
    bot = ClawRobot.create(simulator=True, smooth=False)
    yield bot
    bot.shutdown()


def test_agent_accepts_a_claw_robot(robot):
    agent = ClawAgent(robot=robot, mode=AgentMode.VOICE_CONTROL)
    assert agent.mode is AgentMode.VOICE_CONTROL


def test_vietnamese_voice_command_moves_the_robot(robot):
    agent = ClawAgent(robot=robot, mode=AgentMode.VOICE_CONTROL)
    agent.process_message("di tien")
    assert set(robot.get_state().to_dict()["base"]["wheels"].values()) != {0}


def test_student_code_drives_the_robot(robot):
    agent = ClawAgent(robot=robot, mode=AgentMode.FREE_PLAY)
    result = agent.execute_code('from claw import *\ngrip()\n')
    assert result.success is True
    assert robot.get_state().to_dict()["arm"]["gripper_holding"] is True


def test_stop_command_halts_the_wheels(robot):
    agent = ClawAgent(robot=robot, mode=AgentMode.VOICE_CONTROL)
    agent.process_message("di tien")
    agent.process_message("dung lai")
    assert set(robot.get_state().to_dict()["base"]["wheels"].values()) == {0}
