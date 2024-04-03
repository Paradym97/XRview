import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import xarray as xr
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import argparse

class XRViewApp:
    def __init__(self, root, nc_file):
        # initialize the root window
        self.root = root
        self.root.title("Xarray Viewer")
        self.nc_file = nc_file 
        self.figure = plt.figure()
        # wheter the file is valid
        try:
            with xr.open_dataset(self.nc_file) as ds:
                # put the vars by dimension
                self.vars_by_dimension = {}
                for var_name in ds.variables:
                    var = ds[var_name]
                    dim_num = len(var.dims)
                    if dim_num not in self.vars_by_dimension:
                        self.vars_by_dimension[dim_num] = []
                    self.vars_by_dimension[dim_num].append(var_name)
        except FileNotFoundError:
            print("Error: File not found.")
            self.root.destroy()
            return
        except Exception as e:
            print(f"Error: {e}")
            self.root.destroy()
            return

        # set up the UI
        self.setup_ui()

    def setup_ui(self):
        # root window
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # set up the main frame
        main_frame = ttk.Frame(self.root)
        main_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)

        # set up the file name label
        file_name_label = ttk.Label(main_frame, text=self.nc_file)
        file_name_label.grid(column=0, row=0, pady=10, padx=10, sticky=(tk.N, tk.W, tk.E, tk.S))

        # set up the dims button
        self.button_dim_frame = ttk.Frame(main_frame)
        self.button_dim_frame.grid(column=0, row=1, pady=10, padx=10, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.put_button_dim()

        # set up the var button
        self.button_var_frame= ttk.Frame(main_frame)
        self.button_var_frame.grid(column=0, row=2, pady=10, padx=10, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.button_var_frame.grid_columnconfigure(0, weight=1)
        self.button_var_frame.grid_rowconfigure(3, weight=1)

    def put_button_dim(self):

        self.dropdown_menu = None

        sorted_dimensions = sorted(self.vars_by_dimension.keys())

        for dim_num in sorted_dimensions:
            dim_button = ttk.Button(self.button_dim_frame, 
                    text=f'{dim_num}D Variables', 
                    command=None)
            dim_button.grid(
                column=sorted_dimensions.index(dim_num), 
                row=0, padx=5, pady=5, sticky=(tk.N, tk.W, tk.E, tk.S))
            dim_button.bind("<Button-1>", lambda _, dim_num=dim_num, dim_button=dim_button:
                            self.show_dropdown_menu(dim_num, dim_button))

    def show_dropdown_menu(self, dim_num, button):
        if self.dropdown_menu:
            self.dropdown_menu.destroy()

        var_names = self.vars_by_dimension[dim_num]
        
        self.dropdown_menu = tk.Menu(button, tearoff=0)

        for var_name in var_names:
            self.dropdown_menu.add_command(
                label=var_name, 
                command=lambda var_name=var_name: self.variable_action(var_name))

        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height()
        self.dropdown_menu.post(x, y)

    def variable_action(self, var_name):
        self.VarButton = self.var_button(var_name, self.nc_file, self.button_var_frame, self.figure)

    class var_button():
        def __init__(self, var_name, nc_file, button_var_frame, figure):
            self.var_name = var_name
            self.button_var_frame = button_var_frame
            with xr.open_dataset(nc_file) as ds:
                self.var_info = ds[var_name]
            self.var_info.load()
            self.var_info_str = str(self.var_info)
            self.dims = self.var_info.dims
            self.ndims = len(self.dims)
            self.figure = figure
            self.c0 = None
            self.cbar = None
            self.display_button = [None, None]
            if self.var_info.ndim <= 1:
                self.ismutidim = False
            else:
                self.ismutidim = True
                self.reset_dims()

            # set up the the frame in the var button frame
            # set up the var display frame
            # self.button_var_frame.clear()
            self.button_display_frame = ttk.Frame(self.button_var_frame)
            self.button_display_frame.grid(column=0, row=0, pady=10, padx=10, sticky=(tk.N, tk.W, tk.E, tk.S))
            # set up the var dim frame
            self.button_var_dim_frame = ttk.Frame(self.button_var_frame)
            self.button_var_dim_frame.grid(column=0, row=1, pady=10, padx=10, sticky=(tk.N, tk.W, tk.E, tk.S))
            # set up the var info frame
            var_info_frame = ttk.Frame(self.button_var_frame)
            var_info_frame.grid(column=0, row=2, sticky=(tk.W, tk.E, tk.N, tk.S))
            var_info_frame.grid_columnconfigure(0, weight=1)
            var_info_frame.grid_rowconfigure(0, weight=1)
            var_info_text = scrolledtext.ScrolledText(var_info_frame, wrap=tk.WORD, width=40, height=10)
            var_info_text.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
            var_info_text.insert(tk.INSERT, var_name)
            var_info_text.delete(1.0, tk.END)
            var_info_text.insert(tk.END, str(self.var_info))

            self.show_button()
            self.show_dim_button()
            self.plot()

        def reset_dims(self):
            self.num_of_each_dim = [len(self.var_info[dim]) for dim in self.dims]
            self.dims_for_display = [self.ndims-2, self.ndims-1]
            self.reset_idx()

        def reset_idx(self):
            self.dims_idx = [0]*self.ndims
            self.dims_idx[self.dims_for_display[0]] = None
            self.dims_idx[self.dims_for_display[1]] = None

        def update_display(self, idx):
            self.dims_for_display[idx] = (self.dims_for_display[idx] + 1) % self.ndims
            if self.dims_for_display[idx] == self.dims_for_display[1-idx]:
                self.dims_for_display[idx] = (self.dims_for_display[idx] + 1) % self.ndims
            self.reset_idx()
            self.plot()

        def update_dims_idx(self, idx):
            self.dims_idx[idx] = (self.dims_idx[idx] + 1) % self.num_of_each_dim[idx]
            self.plot()

        def update_chosen_data(self):
            self.chosen_data = self.var_info
            lists={dim: self.dims_idx[i] for i, dim in enumerate(self.dims) if i not in self.dims_for_display}
            self.chosen_data = self.chosen_data.isel(lists).values
            if self.dims_for_display[0] > self.dims_for_display[1]:
                self.chosen_data = self.chosen_data.T
            self.show_button()
            self.show_dim_button()

        def show_button(self):
            if self.ismutidim:
                for i in range(2):
                    ttk.Button(
                        self.button_display_frame, text=f'{self.dims[self.dims_for_display[i]]}',
                        command=lambda idx=i: self.update_display(idx)
                        ).grid(column=i, row=0, padx=10, pady=5, sticky=(tk.W, tk.E))
                    
        def show_dim_button(self):
            if self.ismutidim:
                for i in range(self.ndims):
                    inner_frame = ttk.Frame(self.button_var_dim_frame)
                    inner_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
                    for i in range(self.ndims):
                        ttk.Label(inner_frame, text=f"{self.dims[i]}:").grid(row=i, column=0, sticky=tk.W)
                        ttk.Label(inner_frame, text=f"{self.var_info[self.dims[i]].values[0]}", width=12).grid(row=i, column=1, sticky=tk.W)
                        if i not in self.dims_for_display:
                            ttk.Button(inner_frame, text=f"{self.var_info[self.dims[i]].values[self.dims_idx[i]]}",
                                    command=lambda idx=i: self.update_dims_idx(idx), width=12).grid(row=i, column=2, sticky=tk.W)
                        else:
                            ttk.Button(inner_frame, text="   ",
                                    command=None, width=10).grid(row=i, column=2, sticky=tk.W)
                        ttk.Label(inner_frame, text=f"{self.var_info[self.dims[i]].values[-1]}", width=12).grid(row=i, column=3, sticky=tk.W)

        def plot(self):
            self.figure.clear()

            self.ax = self.figure.subplots()

            if self.ismutidim:
                self.update_chosen_data()
                self.c0 = self.ax.pcolormesh(self.chosen_data)
                self.cbar = plt.colorbar(self.c0, ax=self.ax)
                self.ax.set_xlabel(self.dims[self.dims_for_display[1]])
                self.ax.set_ylabel(self.dims[self.dims_for_display[0]])
            else:
                self.ax.plot(self.var_info.values)
                self.ax.set_ylabel(self.var_name)

            self.connect_hover_event()
            plt.show()

        def connect_hover_event(self):
            def on_hover(event):
                if event.inaxes == self.ax:
                    x, y = int(event.xdata), int(event.ydata)
                    if self.ismutidim:
                        self.ax.set_title('VAR=%s x=%03d, y=%03d,c=%0.3f'%(self.var_name, x, y, self.chosen_data[y, x]), loc='left')
                        plt.draw()
            self.cid = self.ax.figure.canvas.mpl_connect('motion_notify_event', on_hover)

def main():
    print('hello world')
    parser = argparse.ArgumentParser(description="Process a file.")
    parser.add_argument("file", help="Path to the file")
    args = parser.parse_args()

    file_path = args.file

    root = tk.Tk()
    app = XRViewApp(root, file_path)
    root.mainloop()

if __name__ == '__main__':
    main()
