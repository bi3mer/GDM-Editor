import tkinter as tk
from dataclasses import dataclass
from typing import Set

from GDM.Graph.Node import Node


@dataclass
class CustomNode(Node):
    x: float
    y: float
    rect_id: int
    reward_var: tk.DoubleVar
    incoming_edges: Set[str]
