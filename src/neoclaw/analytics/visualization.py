"""Visualization helpers for analytics data."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def plot_sensor_timeline(
    readings: list[dict],
    sensor_name: str,
    output_path: Optional[str] = None,
) -> None:
    """Plot sensor readings over time using matplotlib."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not installed")
        return

    timestamps = [r["timestamp"] for r in readings if r["sensor_name"] == sensor_name]
    values = [r["value"] for r in readings if r["sensor_name"] == sensor_name]

    if not timestamps:
        logger.warning(f"No data for sensor: {sensor_name}")
        return

    import datetime
    times = [datetime.datetime.fromtimestamp(t) for t in timestamps]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, values, marker=".", markersize=3)
    ax.set_title(f"Sensor: {sensor_name}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.grid(True, alpha=0.3)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Chart saved to {output_path}")
    else:
        plt.show()

    plt.close(fig)


def plot_progress_radar(
    skill_levels: dict[str, int],
    output_path: Optional[str] = None,
) -> None:
    """Plot skill level radar chart."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        logger.warning("matplotlib not installed")
        return

    labels = list(skill_levels.keys())
    values = list(skill_levels.values())

    if not labels:
        return

    num = len(labels)
    angles = np.linspace(0, 2 * np.pi, num, endpoint=False).tolist()
    values_plot = values + [values[0]]
    angles += [angles[0]]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, values_plot, "o-", linewidth=2)
    ax.fill(angles, values_plot, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_ylim(0, 5)
    ax.set_title("Skill Levels")

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()

    plt.close(fig)


def create_plotly_dashboard(summary: dict) -> Optional[str]:
    """Create an interactive Plotly dashboard HTML."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        logger.warning("plotly not installed")
        return None

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "scatterpolar"}]],
        subplot_titles=("Progress", "Skills"),
    )

    # Progress gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=summary.get("completion_rate", 0),
            title={"text": "Completion Rate (%)"},
            gauge={"axis": {"range": [0, 100]}},
        ),
        row=1, col=1,
    )

    # Skill radar
    skills = summary.get("skill_levels", {})
    if skills:
        categories = list(skills.keys())
        values = list(skills.values())
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name="Skills",
            ),
            row=1, col=2,
        )

    fig.update_layout(title="NeoClaw Student Dashboard", height=400)
    return fig.to_html(full_html=False)
