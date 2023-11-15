from __future__ import annotations

from textwrap import dedent
from typing import Literal

import streamlit as st

from streamlit_extras import extra

# mypy: ignore-errors
TAGGER_COLOR_PALETTE = {
    "lightblue": "#00c0f2",
    "orange": "#ff6400",
    "bluegreen": "#00d4b1",
    "blue": "#1c83e1",
    "violet": "#803df5",
    "red": "#ff4b4b",
    "green": "#21c354",
    "yellow": "#faca2b",
}

_DEFAULT_COLOR = "#808495"

VALID_COLOR_NAMES = Literal[tuple(TAGGER_COLOR_PALETTE.keys())]  # type: ignore


def _get_html(
    content: str,
    tags: list[str],
    color_name: list[VALID_COLOR_NAMES] | VALID_COLOR_NAMES | None = None,
) -> str:
    tags_html = content + " "
    for i in range(len(tags)):
        if color_name is None:
            color = _DEFAULT_COLOR
        elif isinstance(color_name, list):
            color = TAGGER_COLOR_PALETTE[color_name[i]]
        elif isinstance(color_name, str):
            color = TAGGER_COLOR_PALETTE[color_name]
        else:
            raise ValueError(
                f"color_name must be a list or a string or None. "
                f"color_name = {color_name}, type(color_name) = {type(color_name)}"
            )

        tags_html += dedent(
            f"""
            <span style="display:inline-block;
            background-color: {color};
            padding: 0.1rem 0.5rem;
            font-size: 14px;
            font-weight: 400;
            color:white;
            margin: 5px;
            border-radius: 1rem;">{tags[i]}</span>
            """
        ).strip()

    return tags_html



def tagger_component(
    content: str,
    tags: list[str],
    color_name: list[VALID_COLOR_NAMES] | VALID_COLOR_NAMES | None = None,
):
    """
    Displays tags next to your text.

    Args:
        content (str): Content to be tagged
        tags (list): A list of tags to be displayed next to the content
        color_name: A list or a string that indicates the color of tags.
            Choose from lightblue, orange, bluegreen, blue, violet, red, green, yellow
    """
    if isinstance(color_name, str):
        if color_name not in TAGGER_COLOR_PALETTE:
            raise ValueError(
                f"color_name must contain a name from {TAGGER_COLOR_PALETTE.keys()} "
                f"not {color_name}"
            )
    elif isinstance(color_name, list):
        for color in color_name:
            if color not in TAGGER_COLOR_PALETTE:
                raise ValueError(
                    f"color_name must contain a name from {TAGGER_COLOR_PALETTE.keys()}"
                    f" not {color}"
                )
            if len(color_name) != len(tags):
                raise ValueError(
                    f"color_name must be the same length as tags. "
                    f"len(color_name) = {len(color_name)}, len(tags) = {len(tags)}"
                )

    tags_html = _get_html(content, tags, color_name)

    st.write(tags_html, unsafe_allow_html=True)
