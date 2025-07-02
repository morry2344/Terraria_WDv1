import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import Counter
import lihzahrd

class WorldInspector(tk.Tk):
    #main window
    def __init__(self):
        super().__init__()
        self.title("Terraria World Inspector")
        self.geometry("1000x700")

        
        self.block_counts = {}
        self.wall_counts  = {}
        self.show_blocks  = True
        self.loading_win  = None

        #controls
        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=10, pady=5)
        ttk.Button(ctrl, text="Open World…", command=self.load_world).pack(side="left")
        self.toggle_btn = ttk.Button(ctrl, text="Show Walls", command=self.toggle_view)
        self.toggle_btn.pack(side="left", padx=(5,10))
        ttk.Label(ctrl, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        ent = ttk.Entry(ctrl, textvariable=self.search_var)
        ent.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.search_var.trace_add("write", lambda *a: self.refresh_list())

        #for metadata
        meta = ttk.LabelFrame(self, text="World Metadata")
        meta.pack(fill="x", padx=10, pady=5)
        self.meta_labels = {}
        for row, key in enumerate(("Name","Seed","Size","Hardmode","Corruption","Difficulty","Spawn")):
            ttk.Label(meta, text=key + ":").grid(row=row, column=0, sticky="w", padx=10, pady=2)
            val = ttk.Label(meta, text="—")
            val.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            self.meta_labels[key.lower()] = val

        #for list
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        cols = ("name","count")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        self.tree.heading ("name",  text="Name")
        self.tree.heading ("count", text="Count")
        self.tree.column  ("name",  width=450)
        self.tree.column  ("count", width=150, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

    #loading window
    def show_loading(self):
        if self.loading_win is not None:
            return

        self.loading_win = tk.Toplevel(self)
        self.loading_win.title("Loading…")
        self.loading_win.transient(self)
        self.loading_win.grab_set()

        ttk.Label(
            self.loading_win,
            text="Loading world, please wait…"
        ).pack(padx=20, pady=(20,10))
        pb = ttk.Progressbar(self.loading_win, mode="indeterminate")
        pb.pack(padx=20, pady=(0,20), fill="x")
        pb.start(50)

        self.loading_win.update_idletasks()

        mx = self.winfo_rootx()
        my = self.winfo_rooty()
        mw = self.winfo_width()
        mh = self.winfo_height()

        lw = self.loading_win.winfo_width()
        lh = self.loading_win.winfo_height()

        x = mx + (mw - lw) // 2
        y = my + (mh - lh) // 2
        self.loading_win.geometry(f"+{x}+{y}")

    #load a world
    def load_world(self):
        path = filedialog.askopenfilename(
            title="Select a Terraria .wld file",
            initialdir="Worlds",
            filetypes=[("Terraria Worlds","*.wld")]
        )
        if not path:
            return

        self.show_loading()

        #count blocks and walls
        def task():
            try:
                world = lihzahrd.World.create_from_file(path)
                w, h = world.size.x, world.size.y
                block_cnt = Counter()
                wall_cnt  = Counter()

                for y in range(h):
                    for x in range(w):
                        tile = world.tiles[x, y]
                        if tile.block:
                            block_cnt[tile.block.type.name] += 1
                        if tile.wall:
                            wall_cnt[tile.wall.type.name] += 1

                #back to main
                self.after(0, lambda: self.finish_loading(
                    world,
                    dict(block_cnt),
                    dict(wall_cnt)
                ))
            except Exception as e:
                self.after(0, lambda: self.loading_error(e))

        threading.Thread(target=task, daemon=True).start()

    #update main window
    def finish_loading(self, world, block_dict, wall_dict):
        if self.loading_win:
            self.loading_win.destroy()
            self.loading_win = None

        self.show_blocks = True
        self.toggle_btn.config(text="Show Walls")

        self.block_counts = block_dict
        self.wall_counts  = wall_dict

        sp = world.spawn_point
        w, h = world.size.x, world.size.y
        self.meta_labels["name"].config         (text=world.name)
        self.meta_labels["seed"].config         (text=world.generator.seed)
        self.meta_labels["size"].config         (text=f"{w}×{h}")
        hard = "YES" if world.is_hardmode else "NO"
        self.meta_labels["hardmode"].config     (text=hard)
        self.meta_labels["corruption"].config   (text=world.world_evil.name)
        self.meta_labels["difficulty"].config   (text=world.difficulty.name)
        self.meta_labels["spawn"].config        (text=f"({sp.x}, {sp.y})")

        self.refresh_list()

    #if error during loading
    def loading_error(self, exc):
        if self.loading_win:
            self.loading_win.destroy()
            self.loading_win = None
        messagebox.showerror("Load Error", f"Could not open world:\n{exc}")

    #toggle between blocks and walls
    def toggle_view(self):
        self.show_blocks = not self.show_blocks
        self.toggle_btn.config(text="Show Blocks" if not self.show_blocks else "Show Walls")
        self.refresh_list()

    #refresh the list
    def refresh_list(self):
        q = self.search_var.get().lower()
        counts = self.block_counts if self.show_blocks else self.wall_counts

        for iid in self.tree.get_children():
            self.tree.delete(iid)

        for name, cnt in sorted(counts.items(), key=lambda x: -x[1]):
            if q in name.lower():
                self.tree.insert("", "end", values=(name, f"{cnt:,}"))

if __name__ == "__main__":
    app = WorldInspector()
    app.mainloop()
