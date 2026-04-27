import inspect, os
import tkinter as tk
from tkinter.constants import NORMAL, DISABLED
from ui_lib import all_children
import io
from contextlib import redirect_stdout

import block_lib

def get_objects():
    types=[]
    objects=[]
    for name, obj in inspect.getmembers(block_lib):
        if inspect.isclass(obj):
            types.append(name)
            objects.append(obj)
    return types, objects

def test():
    name='For'
    obj='Container'
    args='var, num_runs'
    init="super().__init__(start=['for',var,'in range(',num_runs,'):'])"
    block_lib.write_block(name,obj,args,init)

if __name__=='__main__':
    test()
    names, objects = get_objects()

    window=tk.Tk()
    window.rowconfigure([0,1,2],weight=1, minsize=50)
    window.columnconfigure([0, 1, 2],weight=1, minsize=50)

    data_entry = tk.Frame()
    super_layout = tk.Text()
    preview_frame = tk.Frame()
    output_frame = tk.Frame()

    name = tk.Entry(master=data_entry)
    obj = "Block"
    obj_frame = tk.Frame(master=data_entry)
    args = tk.Entry(master=data_entry)

    tk.Label(master=preview_frame, text="Preview").pack(side=tk.TOP, fill=tk.BOTH,expand=True)
    preview = tk.Text(master=preview_frame)
    preview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


    def update_super():
        super_layout.config(state=NORMAL)
        super_layout.delete("1.0", tk.END)
        super_layout.insert("1.0", inspect.getsource(objects[names.index(obj)]))
        super_layout.config(state=DISABLED)
    update_super()

    def get_data():
        return [name.get(),obj,args.get(),init.get('1.0',tk.END)]

    def handle_create():
        data=get_data()
        block_lib.write_block(data[0],data[1],data[2],data[3])

    def update_preview(event=None):
        data = get_data()
        preview.delete("1.0",tk.END)
        preview.insert("1.0",block_lib.create_block(data[0], data[1], data[2], data[3]))

    def create_obj_button(func_obj_type):
        def func():
            global obj
            obj=func_obj_type
            update_all()
        return tk.Button(master=obj_frame,text=func_obj_type, command=func)

    for obj_type in names:
        create_obj_button(obj_type).pack(side=tk.LEFT)

    for item in [tk.Label(text="Name",master=data_entry),name,tk.Label(text="Type",master=data_entry),obj_frame,tk.Label(text="Args",master=data_entry),args]:
        item.pack()

    tk.Label(master=data_entry, text="Init").pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    init = tk.Text(master=data_entry)
    init.insert("1.0", "super().__init__()")
    init.pack(side=tk.TOP, fill=tk.BOTH, expand=True)



    tk.Label(master=output_frame, text="Output").pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    output = tk.Text(master=output_frame)
    output.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_output(event=None):
        data = preview.get("1.0",tk.END)
        output.delete("1.0", tk.END)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            try:
                exec(data)
                out = stdout.getvalue()
            except Exception as e:
                out = e
        output.insert("1.0", out)



    def update_all(event=None):
        update_preview()
        update_output()
        update_super()

    for item in all_children(data_entry)+all_children(super_layout):
        if not item.winfo_ismapped():
            item.pack()
        item.bind("<KeyRelease>", update_all)



    data_entry.grid(row=0,column=1,sticky="news")
    super_layout.grid(row=0,column=0,sticky="news")
    preview_frame.grid(row=0,column=2,sticky="news")
    output_frame.grid(row=1,column=1, sticky="news")

    tk.Button(text="Create", command=handle_create).grid(row=2,column=0,columnspan=3)
    window.mainloop()