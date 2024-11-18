import json
import os
import sys
import tkinter as tk
from collections import namedtuple
from os.path import join

NODE_WIDTH = 100
NODE_HEIGHT = 60

Node = namedtuple("Node", ["rect", "frame"])


class Editor:
    def __init__(self, root, working_dir):
        self.working_dir = working_dir

        root.protocol("WM_DELETE_WINDOW", self.on_exit)
        root.createcommand("::tk::mac::Quit", self.on_exit)

        self.root = root
        self.root.title("Level Graph Editor")

        self.canvas = tk.Canvas(self.root, width=1800, height=980, bg="gray20")
        self.canvas.pack(fill="both", expand=1)

        # self.canvas.bind_all("<B3-Motion>", self.on_canvas_motion)

        self.id_to_tk = {}
        self.nodes = {}
        with open(join(self.working_dir, "graph.json"), "r") as f:
            self.g = json.load(f)

            # check segments directory for any new segments and add anode
            for filename in os.listdir(join(self.working_dir, "segments")):
                id = filename[:-4]  # remove .txt from end
                if id not in self.g:
                    self.g[id] = {
                        "reward": 1000,
                        "neighbors": [],
                        "x": 0,
                        "y": 0,
                    }

            # nodes
            for id in self.g:
                self.add_node(id)

            # create edges
            for id in self.g:
                self.add_edge_for_node(id)

    def add_edge_for_node(self, id):
        N = self.g[id]
        x = N["x"]
        y = N["y"]

        def make_edge(neighbor):
            _nodeNeighbor = self.g[neighbor]

            line = self.canvas.create_line(
                x + NODE_WIDTH,
                y + NODE_HEIGHT / 2,
                _nodeNeighbor["x"],
                _nodeNeighbor["y"] + NODE_HEIGHT / 2,
                width=2,
                fill="yellow",
                arrow=tk.LAST,
            )

            self.canvas.tag_bind(
                line, "<Button-2>", lambda event: self.remove_edge_event(line)
            )

            self.nodes[id]["outgoing_lines"].append(line)
            self.nodes[neighbor]["incoming_lines"].append(line)

        for neighbor in self.g[id]["neighbors"]:
            make_edge(neighbor)

    def remove_edge_event(self, line_id):
        # remove from the graphics
        self.canvas.delete(line_id)

        # remove from nodes
        for n in self.nodes:
            N = self.nodes[n]
            if line_id in N["outgoing_lines"]:
                # remove from both the graph and the nodes internal represenation
                index = N["outgoing_lines"].index(line_id)
                N["outgoing_lines"].remove(line_id)
                self.g[n]["neighbors"].pop(index)

            if line_id in N["incoming_lines"]:
                N["incoming_lines"].remove(line_id)

    def add_node(self, id):
        N = self.g[id]
        x = N["x"]
        y = N["y"]
        rect = self.canvas.create_rectangle(
            x, y, x + NODE_WIDTH, y + NODE_HEIGHT, fill="gray66"
        )

        frame = tk.Frame(self.root)
        frame.place(x=x, y=y)

        label = tk.Label(frame, text=id, width=5)
        label.pack()

        reward_var = tk.DoubleVar()
        reward_var.set(N["reward"])  # Initial width of the rectangle
        reward_var.trace_add(
            "write",
            lambda _var, _index, _mode: self.on_reward_change(id, reward_var.get()),
        )
        r = tk.Entry(frame, textvariable=reward_var, width=3)
        r.pack()

        self.id_to_tk[id] = Node(rect, frame)

        self.nodes[id] = {
            "rect": rect,
            "reward": reward_var,
            "frame": frame,
            "outgoing_lines": [],
            "incoming_lines": [],
        }

        # move nodes around
        self.canvas.tag_bind(
            rect,
            "<B1-Motion>",
            lambda event: self.on_drag(event, id),
        )

        # create edges between nodes
        self.canvas.tag_bind(rect, "<ButtonPress-2>", lambda e: self.start_drag(id, e))
        self.canvas.tag_bind(rect, "<B2-Motion>", lambda e: self.dragging(id, e))
        self.canvas.tag_bind(rect, "<ButtonRelease-2>", lambda e: self.end_drag(id, e))

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

    def on_reward_change(self, id, val):
        try:
            self.g[id]["reward"] = float(val)
        except:
            print(f"Invalid value: {val}")

    def on_canvas_motion(self, event):
        pass
        # self.canvas.yview_scroll(-1, "units")

    def on_drag(self, event, id):
        N = self.nodes[id]
        RECT = N["rect"]

        x1, y1, _x2, _y2 = self.canvas.coords(RECT)
        dx = event.x - x1
        dy = event.y - y1
        self.canvas.move(RECT, dx, dy)
        self.canvas.itemconfig(RECT, tags=("rect", "dragged"))

        N["frame"].place(x=x1, y=y1)
        self.g[id]["x"] = x1
        self.g[id]["y"] = y1

        for neighbor in self.nodes[id]["incoming_lines"]:
            coords = self.canvas.coords(neighbor)
            self.canvas.coords(neighbor, coords[0], coords[1], x1, y1 + NODE_HEIGHT / 2)

        for neighbor in self.nodes[id]["outgoing_lines"]:
            coords = self.canvas.coords(neighbor)
            self.canvas.coords(
                neighbor, x1 + NODE_WIDTH, y1 + NODE_HEIGHT / 2, coords[2], coords[3]
            )

    def on_exit(self):
        print("saving graph before exiting :D")
        with open(join(self.working_dir, "graph.json"), "w") as f:
            json.dump(self.g, f, indent=2)

        exit(0)


if __name__ == "__main__":
    working_dir = sys.argv[1] if len(sys.argv) == 2 else '.'
    print(f'Working dir: {working_dir}')

    root = tk.Tk()
    app = Editor(root, working_dir)
    root.mainloop()
