import json
import os
import sys
import tkinter as tk
from os.path import join

from custom_edge import CustomEdge
from custom_node import CustomNode
from GDM.Graph import Graph

NODE_WIDTH  = 60
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
      
        self.scroll_x = 0
        self.scroll_y = 0
        self.root.bind("<Button-3>", self.scroll_start)
        self.root.bind("<B3-Motion>", self.scroll)
        # self.root.bind("<MouseWheel>", self.zoom)
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
            x, y, x + NODE_WIDTH, y + NODE_HEIGHT, fill="gray93", tags="all"
        )

        frame = tk.Frame(self.canvas)
        frame.place(x=x+1, y=y+1)

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
            reward = 0,
            utility = 0,
            is_terminal=False,
            neighbors=set(),
            x = x,
            y = y,
            rect_id = rect,
            reward_var=reward_var,
            frame = frame, 
            entry = r
        )

        self.G.add_node(N)

        ## move nodes around
        def on_node_click(event):
            self.scroll_x = event.x_root
            self.scroll_y = event.y_root

        def on_node_drag(event):
            dx = event.x_root - self.scroll_x
            dy = event.y_root - self.scroll_y
        
            self.move_node(N, dx, dy)

            self.scroll_x = event.x_root
            self.scroll_y = event.y_root

        self.canvas.tag_bind(rect, "<Button-1>", on_node_click)
        self.canvas.tag_bind(rect, "<B1-Motion>", on_node_drag)

        label.bind("<Button-1>", on_node_click)
        label.bind("<B1-Motion>", on_node_drag)

        r.bind("<Button-1>", on_node_click)
        r.bind("<B1-Motion>", on_node_drag)

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
                tags="all"
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
            tags="all"
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

    def scroll_start(self, event):
        self.scroll_x = event.x
        self.scroll_y = event.y

    def move_node(self, n: CustomNode, dx: float, dy: float):
        ## Update rectangle placement
        self.canvas.move(n.rect_id, dx, dy)
        self.canvas.itemconfig(n.rect_id, tags=("rect", "dragged"))

        x1, y1, _x2, _y2 = self.canvas.coords(n.rect_id)
        n.frame.place(x=x1+1, y=y1+1)
        n.x = x1
        n.y = y1

        ## Update Edge coordinates
        # outgoing
        for tgt in n.neighbors:
            line_id = self.G.get_edge(n.name, tgt).line_id
            coords = self.canvas.coords(line_id)
            self.canvas.coords(
                line_id, 
                x1 + NODE_WIDTH, 
                y1 + NODE_HEIGHT / 2, 
                coords[2], 
                coords[3]
            )
        #
        for edge in self.G.incoming_edges(n.name):
            coords = self.canvas.coords(edge.line_id)
            self.canvas.coords(
                edge.line_id, 
                coords[0],
                coords[1],
                x1,
                y1 + NODE_HEIGHT / 2
            )


    def scroll(self, event):
        dx = event.x - self.scroll_x
        dy = event.y - self.scroll_y

        for N in self.G.nodes.values():
            self.move_node(N, dx, dy)

        self.scroll_x = event.x
        self.scroll_y = event.y


    def on_exit(self):
        data = {}
        for node_name, N in self.G.nodes.items():
            data[node_name] = {
                "x": N.x,
                "y": N.y,
                "reward": N.reward_var.get(),
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
