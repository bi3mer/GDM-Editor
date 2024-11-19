from ast import Call
from typing import Callable, Set, Dict, List, Tuple
from .Edge import Edge
from .Node import Node

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}

    ##### Node Operations
    def get_node(self, node_name: str) -> Node:
        return self.nodes[node_name]

    def has_node(self, node_name: str) -> bool:
        return node_name in self.nodes

    def add_node(self, node: Node):
        assert isinstance(node, Node)
        assert node.name not in self.nodes
        self.nodes[node.name] = node

    def add_default_node(self, node_name: str, reward: float=1.0, utility: float=0.0, 
                         terminal: bool=False, neighbors: Set[str]=None):

        assert node_name not in self.nodes
        if neighbors == None:
            neighbors = set()

        self.nodes[node_name] = Node(node_name, reward, utility, terminal, neighbors)

    def remove_node(self, node_name: str):
        assert node_name in self.nodes

        edges_to_remove: List[Edge] = []
        for e in self.edges.values():
            # add to list to remove from edges
            if e.src == node_name or e.tgt == node_name:
                edges_to_remove.append(e)

            # check if node occurs in the probabilities array
            probabilities = e.probability
            index = -1
            for i, (name, _) in enumerate(probabilities):
                if name == node_name:
                    index = i
                    break

            if index == -1:
                continue

            # if it is in the array remove it and spread the probability to the
            # other values in the probabilities array
            p_value = probabilities[index][1]
            probabilities.pop(index)
            p_value /= len(probabilities)
            e.probability = [(name, p + p_value) for name, p in probabilities]
        
        for e in edges_to_remove:
            self.remove_edge(e.src, e.tgt)

        del self.nodes[node_name]

    ##### Edge Operations
    def get_edge(self, src_name: str, tgt_name: str) -> Edge:
        return self.edges[(src_name, tgt_name)]

    def has_edge(self, src_name: str, tgt_name: str) -> bool:
        return (src_name, tgt_name) in self.edges

    def add_edge(self, edge: Edge):
        assert isinstance(edge, Edge)
        assert edge.src in self.nodes
        assert edge.tgt in self.nodes
        assert (edge.src, edge.tgt) not in self.edges
        self.edges[(edge.src, edge.tgt)] = edge
        
        neighbors = self.nodes[edge.src].neighbors
        if edge.tgt not in neighbors:
            neighbors.add(edge.tgt)

    def add_default_edge(self, src_name: str, tgt_name: str, p: List[Tuple[str, float]]=None):
        if p == None:
            p = []

        self.add_edge(Edge(src_name, tgt_name, p))

    def remove_edge(self, src_node: str, tgt_node: str):
        assert src_node in self.nodes
        assert tgt_node in self.nodes
        assert (src_node, tgt_node) in self.edges

        self.neighbors(src_node).remove(tgt_node)
        del self.edges[(src_node, tgt_node)]

    ##### Useful Functions
    def neighbors(self, node_name: str) -> Set[str]:
        return self.nodes[node_name].neighbors

    def set_node_utilities(self, utilities: Dict[str, float]):
        for node_name, utility in utilities.items():
            self.nodes[node_name].utility = utility

    def utility(self, node_name: str) -> float:
        return self.nodes[node_name].utility

    def reward(self, node_name: str) -> float:
        return self.nodes[node_name].reward

    def is_terminal(self, node_name: str) -> bool:
        return self.nodes[node_name].is_terminal

    def map_nodes(self, func: Callable[[Node], None]):
        for n in self.nodes.values():
            func(n)

    def map_edges(self, func: Callable[[Edge], None]):
        for e in self.edges.values():
            func(e)
