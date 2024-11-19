from dataclasses import dataclass
from GDM.Graph.Edge import Edge

@dataclass
class CustomEdge(Edge):
    line_id: int
