import json
from os.path import join

from custom_edge import CustomEdge
from custom_node import CustomNode
from GDM.Graph import Graph

working_dir = '../../web-projects/js/platformer_web/levels/'

G = Graph()
with open(join(working_dir, 'graph.json')) as f:
    graph = json.load(f)

    ## Create Nodes
    for node_name, node_values in graph.items():
        n = CustomNode(
            name = node_name,
            reward = node_values['reward'],
            utility = 0,
            is_terminal=False,
            neighbors=set(),
            node_id=0
        )

        G.add_node(n)

        print(node_name, node_values)

    ## Create Edges
    for node_name, node_values in graph.items():
        n = G.get_node(node_name)
        for neighbor in node_values['neighbors']:
            e = CustomEdge(
                src = node_name,
                tgt = neighbor,
                probability=[],
                line_id=0
            )
            
            G.add_edge(e)

