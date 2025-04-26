"""
Module containing models related to the success widget.
"""
from __future__ import annotations

from typing import Callable

from pydantic import BaseModel


class SuccessPageModel(BaseModel):
    """This model class used for success widget page"""
    header: str
    title: str
    description: str
    button_text: str
    callback: Callable
