import tkinter as tk
from dataclasses import dataclass
from typing import Set, List

from GDM.Graph.Node import Node

@dataclass
class CustomNode(Node):
    x: float
    y: float
    rect_id: int
    reward_var: tk.DoubleVar
    frame: tk.Frame
    entry: tk.Entry
    levels: List[str]
