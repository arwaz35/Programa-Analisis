"""
Vista de gestión de lugares de prueba.
"""
import customtkinter as ctk
from tkinter import messagebox


def show_gestion_lugares(app):
    """Muestra la vista de gestión de lugares."""
    app.clear_window()
    ctk.CTkLabel(app, text="Gestión de Lugares", font=("Arial", 24, "bold")).pack(pady=20)

    table_frame = ctk.CTkScrollableFrame(app)
    table_frame.pack(fill="both", expand=True, padx=20, pady=10)

    headers = ["Nombre del Lugar", "Altitud (msnm)", "Coordenadas"]
    widths = [300, 150, 400]

    header_f = ctk.CTkFrame(table_frame, fg_color="gray30")
    header_f.pack(fill="x", pady=2)
    for i, h in enumerate(headers):
        ctk.CTkLabel(header_f, text=h, width=widths[i], font=("Arial", 12, "bold")).pack(side="left", padx=2)

    selected = {'val': None, 'widget': None}

    def refresh_table():
        for w in table_frame.winfo_children():
            if w != header_f:
                w.destroy()
        lugares = app.data_handler.load_lugares()
        selected['val'], selected['widget'] = None, None
        btn_del.configure(state="disabled")

        def select_row(idx, row_w):
            if selected['widget']:
                try:
                    selected['widget'].configure(fg_color=["gray86", "gray17"])
                except Exception:
                    pass
            selected['val'] = idx
            selected['widget'] = row_w
            row_w.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            btn_del.configure(state="normal")

        for i, l in enumerate(lugares):
            row = ctk.CTkFrame(table_frame)
            row.pack(fill="x", pady=1)
            row.bind("<Button-1>", lambda e, x=i, r=row: select_row(x, r))
            vals = [l.get('Nombre', ''), l.get('Altitud (msnm)', ''), l.get('Coordenadas (Lat, Lon)', '')]
            for j, v in enumerate(vals):
                lbl = ctk.CTkLabel(row, text=v, width=widths[j])
                lbl.pack(side="left", padx=2)
                lbl.bind("<Button-1>", lambda e, x=i, r=row: select_row(x, r))

    ctrl = ctk.CTkFrame(app, fg_color="transparent")
    ctrl.pack(fill="x", padx=20, pady=10)

    def add_lugar():
        win = ctk.CTkToplevel(app)
        win.title("Agregar Lugar")
        win.geometry("400x300")
        win.attributes("-topmost", True)
        fields = ["Nombre", "Altitud (msnm)", "Coordenadas (Lat, Lon)"]
        entries = {}
        for f in fields:
            r = ctk.CTkFrame(win)
            r.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(r, text=f).pack(side="left", padx=5)
            e = ctk.CTkEntry(r)
            e.pack(side="right", fill="x", expand=True, padx=5)
            entries[f] = e

        def save():
            data = {f: entries[f].get() for f in fields}
            if not data['Nombre']:
                messagebox.showerror("Error", "Nombre es obligatorio", parent=win)
                return
            app.data_handler.add_lugar(data)
            refresh_table()
            win.destroy()
        ctk.CTkButton(win, text="Guardar", command=save).pack(pady=20)

    def delete_lugar():
        if selected['val'] is not None:
            if messagebox.askyesno("Confirmar", "¿Eliminar lugar seleccionado?"):
                app.data_handler.delete_lugar(selected['val'])
                refresh_table()

    ctk.CTkButton(ctrl, text="Agregar Lugar", font=("Arial", 14, "bold"), command=add_lugar).pack(side="left", padx=10)
    btn_del = ctk.CTkButton(ctrl, text="Eliminar Lugar", font=("Arial", 14, "bold"),
                            fg_color="red", hover_color="darkred", state="disabled", command=delete_lugar)
    btn_del.pack(side="right", padx=10)

    bottom = ctk.CTkFrame(app, fg_color="transparent")
    bottom.pack(fill="x", side="bottom", padx=10, pady=20)
    ctk.CTkButton(bottom, text="⬅ Regresar", font=("Arial", 14, "bold"),
                  fg_color="gray", hover_color="darkgray",
                  command=app.show_main_menu).pack(side="left")
    refresh_table()
