import json
import os
import sys
import tkinter as tk
from os.path import join

from custom_edge import CustomEdge
from custom_node import CustomNode
from GDM.Graph import Graph

NODE_WIDTH = 100
NODE_HEIGHT = 60


class Editor:
    def __init__(self, root, working_dir):
        self.working_dir = working_dir

        root.protocol("WM_DELETE_WINDOW", self.on_exit)
        root.createcommand("::tk::mac::Quit", self.on_exit)

        self.root = root
        self.root.title("Level Graph Editor")

        self.canvas = tk.Canvas(self.root, width=1800, height=980, bg="gray20")
        self.canvas.pack(fill="both", expand=1)

        self.root.bind("<Key>", self.key_press_handler)

        ## Build the graph
        self.G = Graph()
        with open(join(working_dir, 'graph.json')) as f:
            graph = json.load(f)

            ## Create Nodes
            for node_name, node_values in graph.items():
                self.create_node(node_name, node_values)

            ## Create Edges
            for node_name, node_values in graph.items():
                self.create_edges(node_name, node_values)

    ############# Create
    def create_node(self, node_name, node_values):
        x = node_values["x"]
        y = node_values["y"]
        rect = self.canvas.create_rectangle(
            x, y, x + NODE_WIDTH, y + NODE_HEIGHT, fill="gray66"
        )

        frame = tk.Frame(self.root)
        frame.place(x=x, y=y)

        label = tk.Label(frame, text=node_name, width=5)
        label.pack()

        def on_reward_change():
            self.G.get_node(node_name).reward = reward_var.get()

        reward_var = tk.DoubleVar()
        reward_var.set(node_values["reward"])  # Initial width of the rectangle
        reward_var.trace_add(
            "write",
            lambda _var, _index, _mode: on_reward_change,
        )
        r = tk.Entry(frame, textvariable=reward_var, width=3)
        r.pack()

        ## Add node to the graph
        N = CustomNode(
            name = node_name,
            reward = reward_var.get(),
            utility = 0,
            is_terminal=False,
            neighbors=set(),
            x = x,
            y = y,
            rect_id = rect,
            reward_var=reward_var,
        )

        self.G.add_node(N)

        ## move nodes around
        def on_drag_node(event):
            ## Update rectangle placement
            x1, y1, _x2, _y2 = self.canvas.coords(rect)
            dx = event.x - x1
            dy = event.y - y1
            self.canvas.move(rect, dx, dy)
            self.canvas.itemconfig(rect, tags=("rect", "dragged"))

            frame.place(x=x1, y=y1)
            N.x = x1
            N.y = y1

            ## Update Edge coordinates
            # outgoing
            for tgt in self.G.neighbors(node_name):
                line_id = self.G.get_edge(node_name, tgt).line_id
                coords = self.canvas.coords(line_id)
                self.canvas.coords(
                    line_id, 
                    x1 + NODE_WIDTH, 
                    y1 + NODE_HEIGHT / 2, 
                    coords[2], 
                    coords[3]
                )

            for edge in self.G.incoming_edges(node_name):
                coords = self.canvas.coords(edge.line_id)
                self.canvas.coords(
                    edge.line_id, 
                    coords[0],
                    coords[1],
                    x1,
                    y1 + NODE_HEIGHT / 2
                )

        self.canvas.tag_bind(
            rect,
            "<B1-Motion>",
            lambda event: on_drag_node(event),
        )

        # create edges between nodes
        self.canvas.tag_bind(rect, "<ButtonPress-2>", lambda e: self.start_drag(id, e))
        self.canvas.tag_bind(rect, "<B2-Motion>", lambda e: self.dragging(id, e))
        self.canvas.tag_bind(rect, "<ButtonRelease-2>", lambda e: self.end_drag(id, e))

    def create_edges(self, node_name, node_values):
        N: CustomNode = self.G.get_node(node_name)

        for neighbor in node_values["neighbors"]:
            _nodeNeighbor: CustomNode = self.G.get_node(neighbor)

            line = self.canvas.create_line(
                N.x + NODE_WIDTH,
                N.y + NODE_HEIGHT / 2,
                _nodeNeighbor.x,
                _nodeNeighbor.y + NODE_HEIGHT / 2,
                width=2,
                fill="yellow",
                arrow=tk.LAST,
            )

            self.G.add_edge(CustomEdge(
                src=node_name,
                tgt=neighbor,
                probability=[],
                line_id=line
            ))

            ######
            def remove_edge_event():
                print('remove edge commented out')
                # remove from the graphics
                # self.canvas.delete()

                # # remove from nodes
                # for n in self.nodes:
                #     N = self.nodes[n]
                #     if line_id in N["outgoing_lines"]:
                #         # remove from both the graph and the nodes internal represenation
                #         index = N["outgoing_lines"].index(line_id)
                #         N["outgoing_lines"].remove(line_id)
                #         self.g[n]["neighbors"].remove(N['id'])
                #
                #     if line_id in N["incoming_lines"]:
                #         N["incoming_lines"].remove(line_id)

                # del self.edges[line_id]

            self.canvas.tag_bind(
                line, "<Button-2>", lambda event: remove_edge_event()
            )


    ############# TBD

    def key_press_handler(self, event):
        if event.keysym == 'Escape':
            self.on_exit()


    def start_drag(self, id, event):
        N = self.g[id]
        self.drag_id = id
        self.drag_line = self.canvas.create_line(
            N["x"] + NODE_WIDTH,
            N["y"] + NODE_HEIGHT / 2,
            event.x,
            event.y,
            width=2,
            fill="yellow",
            arrow=tk.LAST,
        )

    def dragging(self, id, event):
        coords = self.canvas.coords(self.drag_line)
        self.canvas.coords(self.drag_line, coords[0], coords[1], event.x, event.y)

    def end_drag(self, id, event):
        coords = self.canvas.coords(self.drag_line)
        overlapping = self.canvas.find_overlapping(
            coords[2], coords[3], coords[2] + 10, coords[3] + 10
        )

        if len(overlapping) == 2:
            # found connection
            tgt_node_tkid = (
                overlapping[0] if overlapping[0] != self.drag_line else overlapping[1]
            )

            tgt_id = "1-a"
            for n in self.g:
                if self.nodes[n]["rect"] == tgt_node_tkid:
                    tgt_id = n
                    break

            # Set position of the line
            if tgt_id == id or tgt_id in self.g[id]["neighbors"]:
                self.canvas.delete(self.drag_line)
            else:
                tgt_ng = self.g[tgt_id]
                self.canvas.coords(
                    self.drag_line,
                    coords[0],
                    coords[1],
                    tgt_ng["x"],
                    tgt_ng["y"] + NODE_HEIGHT / 2,
                )

                # add to internal data structuresi
                self.g[self.drag_id]["neighbors"].append(tgt_id)

                tgt_nn = self.nodes[tgt_id]
                tgt_nn["incoming_lines"].append(self.drag_id)
                self.nodes[self.drag_id]["outgoing_lines"].append(tgt_id)
        else:
            # no connection found
            self.canvas.delete(self.drag_line)

    def on_canvas_motion(self, event):
        pass
        # self.canvas.yview_scroll(-1, "units")

    def on_drag_node(self, event, node_name):
        N: CustomNode = self.G.get_node(node_name)


    def on_exit(self):
        print('Graph.json save currently disabled')
        # print("saving graph before exiting :D")
        # with open(join(self.working_dir, "graph.json"), "w") as f:
        #     json.dump(self.g, f, indent=2)

        exit(0)


if __name__ == "__main__":
    working_dir = sys.argv[1] if len(sys.argv) == 2 else '.'
    print(f'Working dir: {working_dir}')

    root = tk.Tk()
    app = Editor(root, working_dir)
    root.mainloop()
