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
        self.drag_line = 0

        ## Build the graph
        self.G = Graph()
        with open(join(working_dir, 'graph.json')) as f:
            graph = json.load(f)

            ## Create Nodes
            for node_name, node_values in graph.items():
                self.create_node(node_name, node_values)

            ## Create Edges
            for node_name, node_values in graph.items():
                for neighbor in node_values["neighbors"]:
                    self.create_edge(node_name, neighbor)

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

        ## create edges between nodes
        # Start Drag Line
        def start_drag(event):
            self.drag_line = self.canvas.create_line(
                N.x + NODE_WIDTH,
                N.y + NODE_HEIGHT / 2,
                event.x,
                event.y,
                width=2,
                fill="yellow",
                arrow=tk.LAST,
            )
        
        self.canvas.tag_bind(rect, "<ButtonPress-2>", lambda e: start_drag(e))

        # Line follows the user's cursor
        def dragging(event):
            coords = self.canvas.coords(self.drag_line)
            self.canvas.coords(self.drag_line, coords[0], coords[1], event.x, event.y)

        self.canvas.tag_bind(rect, "<B2-Motion>", lambda e: dragging(e))
        
        # End Drag Line
        def end_drag(event):
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
                for n in self.G.nodes:
                    if self.G.nodes[n].rect_id == tgt_node_tkid:
                        tgt_id = n
                        break

                neighbor = self.G.nodes[tgt_id]
               
                # cannot connect to self and cannot add duplicate edges
                if tgt_id != node_name and tgt_id not in N.neighbors:
                    self.create_edge(node_name, tgt_id)
        
            # Delet the drag line regardless
            self.canvas.delete(self.drag_line)

        self.canvas.tag_bind(rect, "<ButtonRelease-2>", lambda e: end_drag(e))

    def create_edge(self, src, tgt):
        N_src: CustomNode = self.G.get_node(src)
        N_tgt: CustomNode = self.G.get_node(tgt)
        
        line = self.canvas.create_line(
            N_src.x + NODE_WIDTH,
            N_src.y + NODE_HEIGHT / 2,
            N_tgt.x,
            N_tgt.y + NODE_HEIGHT / 2,
            width=2,
            fill="yellow",
            arrow=tk.LAST,
        )

        self.G.add_edge(CustomEdge(
            src=src,
            tgt=tgt,
            probability=[],
            line_id=line
        ))

        ## Remove Edge
        def remove_edge_event():
            self.canvas.delete(line)
            self.G.remove_edge(src, tgt)

        self.canvas.tag_bind(
            line, "<Button-2>", lambda event: remove_edge_event()
        )

    ############# TKinter interactions that are not related to the Graph directly
    def key_press_handler(self, event):
        if event.keysym == 'Escape':
            self.on_exit()

    def on_canvas_motion(self, event):
        pass
        # self.canvas.yview_scroll(-1, "units")

    def on_exit(self):
        data = {}
        for node_name, N in self.G.nodes.items():
            data[node_name] = {
                "x": N.x,
                "y": N.y,
                "reward": N.reward,
                "neighbors": list(N.neighbors)
            } 

        print("saving graph before exiting :D")
        with open(join(self.working_dir, "graph.json"), "w") as f:
            json.dump(data, f, indent=2)

        exit(0)


if __name__ == "__main__":
    working_dir = sys.argv[1] if len(sys.argv) == 2 else '.'
    print(f'Working dir: {working_dir}')

    root = tk.Tk()
    app = Editor(root, working_dir)
    root.mainloop()
