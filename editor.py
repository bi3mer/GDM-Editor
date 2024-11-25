import json
import os
import sys
import tkinter as tk
from math import ceil
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

        self.root.bind("<Key>", self.key_press_handler)
      
        self.drag_line = 0
        self.scroll_x = 0
        self.scroll_y = 0
        self.root.bind("<Button-3>", self.scroll_start)
        self.root.bind("<B3-Motion>", self.scroll)

        self.root.bind("<MouseWheel>", self.on_scale)
       
        self.canvas = tk.Canvas(self.root, width=1800, height=980, bg="gray20")
        self.canvas.pack(fill="both", expand=1)
        

        ## Build the graph
        self.G = Graph()
        with open(join(working_dir, 'graph.json')) as f:
            data = json.load(f)
            self.scale: float = data['scale']
            graph = data['graph']

            ## Create Nodes
            for node_name, node_values in graph.items():
                self.create_node(node_name, node_values)

            ## Create Edges
            for node_name, node_values in graph.items():
                for neighbor in node_values["neighbors"]:
                    self.create_edge(node_name, neighbor)
        
        # preview box
        self.preview_frame = tk.Frame(self.canvas)
        self.preview_frame.place(x=-1000, y=-1000) # off screen
        
        self.preview_label = tk.Label(self.preview_frame, width = 32, height=17, font="TkFixedFont")
        self.preview_label.pack()
        # self.label = tk.Label(self.canvas, width=32, height=16, font="TkFixedFont")

    ############# Create
    def create_node(self, node_name, node_values):
        x = node_values["x"]
        y = node_values["y"]
        rect = self.canvas.create_rectangle(
            x * self.scale, 
            y * self.scale, 
            (x + NODE_WIDTH) * self.scale, 
            (y + NODE_HEIGHT)*self.scale, 
            fill="gray93", 
            tags="all"
        )

        frame = tk.Frame(self.canvas)
        frame.place(
            x = x * self.scale + self.scale, 
            y = y * self.scale + self.scale
        )

        label = tk.Label(frame, text=node_name, width=ceil(5*self.scale))
        label.pack()

        def on_reward_change():
            self.G.get_node(node_name).reward = reward_var.get()

        reward_var = tk.DoubleVar()
        reward_var.set(node_values["reward"])  # Initial width of the rectangle
        reward_var.trace_add(
            "write",
            lambda _var, _index, _mode: on_reward_change,
        )
        r = tk.Entry(frame, textvariable=reward_var, width=ceil(3*self.scale))
        r.pack()

        with open(join(self.working_dir, 'segments', f'{node_name}.txt')) as f:
            level = f.read()

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
            entry = r,
            level = level
        )

        self.G.add_node(N)

        ## move nodes around
        def on_node_click(event):
            self.scroll_x = event.x_root
            self.scroll_y = event.y_root

        def on_node_drag(event):
            dx = event.x_root - self.scroll_x
            dy = event.y_root - self.scroll_y
        
            self.update_node(N, dx, dy)

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
                (N.x + NODE_WIDTH) * self.scale,
                (N.y + NODE_HEIGHT / 2) * self.scale,
                event.x_root,
                event.y_root - (NODE_HEIGHT * self.scale),
                width=2*self.scale,
                fill="yellow",
                arrow=tk.LAST,
                tags="all"
            )
        
        # Line follows the user's cursor
        def dragging(event):
            coords = self.canvas.coords(self.drag_line)
            self.canvas.coords(
                self.drag_line, 
                coords[0], 
                coords[1], 
                event.x_root, 
                event.y_root - (NODE_HEIGHT * self.scale)
            )
        
        # End Drag Line
        def end_drag(event):
            coords = self.canvas.coords(self.drag_line)
            overlapping = self.canvas.find_overlapping(
                coords[2], 
                coords[3], 
                coords[2] + 10*self.scale, 
                coords[3] + 10*self.scale
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

        self.canvas.tag_bind(rect, "<ButtonPress-2>", start_drag)
        self.canvas.tag_bind(rect, "<B2-Motion>", dragging)
        self.canvas.tag_bind(rect, "<ButtonRelease-2>", end_drag)
        
        label.bind("<ButtonPress-2>", start_drag)
        label.bind("<B2-Motion>", dragging)
        label.bind("<ButtonRelease-2>", end_drag)
        
        r.bind("<ButtonPress-2>", start_drag)
        r.bind("<B2-Motion>", dragging)
        r.bind("<ButtonRelease-2>", end_drag)

        ## On Hover
        def on_enter(event):
            self.preview_label.config(text=N.level)
            self.preview_frame.place(x=(N.x + NODE_WIDTH + 1) * self.scale, y=N.y*self.scale)
        
        def on_exit(event):
            self.preview_frame.place(x=-1000, y=-1000)

        self.canvas.tag_bind(rect, '<Enter>', on_enter)
        self.canvas.tag_bind(rect, '<Leave>', on_exit)
    
        r.bind('<Enter>', on_enter)
        r.bind('<Leave>', on_exit)
        
        label.bind('<Enter>', on_enter)
        label.bind('<Leave>', on_exit)
        

    def create_edge(self, src, tgt):
        N_src: CustomNode = self.G.get_node(src)
        N_tgt: CustomNode = self.G.get_node(tgt)
        
        line = self.canvas.create_line(
            (N_src.x + NODE_WIDTH) * self.scale,
            (N_src.y + NODE_HEIGHT / 2) * self.scale,
            N_tgt.x * self.scale,
            (N_tgt.y + NODE_HEIGHT / 2) * self.scale,
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

    def update_node(self, n: CustomNode, dx: float, dy: float):
        ## Update rectangle placement
        self.canvas.move(n.rect_id, dx, dy)
        self.canvas.itemconfig(n.rect_id, tags=("rect", "dragged"))

        x1, y1, _x2, _y2 = self.canvas.coords(n.rect_id)
        # n.frame.place(x=x1+self.scale, y=y1+self.scale)
        n.x += dx
        n.y += dy


        # rectangle
        self.canvas.coords(
            n.rect_id,
            n.x * self.scale,
            n.y * self.scale,
            (n.x + NODE_WIDTH) * self.scale,
            (n.y + NODE_HEIGHT) * self.scale
        )

        # frame
        n.frame.place(
            x = (n.x + 1) * self.scale,
            y = (n.y + 1) * self.scale
        )

        # entry
        n.entry.config(width=ceil(3*self.scale))

        ## Update Edge coordinates
        # incoming
        for tgt in n.neighbors:
            line_id = self.G.get_edge(n.name, tgt).line_id
            coords = self.canvas.coords(line_id)
            self.canvas.coords(
                line_id, 
                (n.x + NODE_WIDTH) * self.scale, 
                (n.y + NODE_HEIGHT / 2) * self.scale, 
                coords[2] , 
                coords[3]  
            )

        # outgoing
        for edge in self.G.incoming_edges(n.name):
            coords = self.canvas.coords(edge.line_id)
            self.canvas.coords(
                edge.line_id, 
                coords[0],
                coords[1],
                n.x * self.scale,
                (n.y + NODE_HEIGHT / 2) * self.scale
            )

    def scroll(self, event):
        dx = event.x - self.scroll_x
        dy = event.y - self.scroll_y

        for N in self.G.nodes.values():
            self.update_node(N, dx, dy)

        self.scroll_x = event.x
        self.scroll_y = event.y

    def on_scale(self, event):
        delta = 1 if event.delta >= 0 else -1
        self.scale = min(1.0, max(0.1, self.scale + 0.01*delta))

        n: CustomNode
        for n in self.G.nodes.values():
            self.update_node(n, 0, 0)

    def on_exit(self):
        data = {
            "scale": self.scale,
        }
        graph = {}

        for node_name, N in self.G.nodes.items():
            graph[node_name] = {
                "x": N.x,
                "y": N.y,
                "reward": N.reward_var.get(),
                "neighbors": list(N.neighbors)
            } 

        data['graph'] = graph
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
