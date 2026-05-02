"""
Vista de gestión de motocicletas.
Incluye asignación y visualización de foto de moto.
Las fotos se almacenan en la carpeta Motos/ del proyecto.
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import os
import shutil
from config import MOTOS_FOTOS_DIR


def _get_moto_foto_key(moto):
    """Genera un identificador único para buscar la foto de una moto."""
    nombre = moto.get('Nombre Comercial', '')
    placa = moto.get('Placa', '')
    if placa:
        return f"{nombre} {placa}"
    return nombre


def get_moto_foto_path(moto):
    """
    Busca la foto de la moto en la carpeta de fotos.
    Busca por 'Nombre Comercial Placa' o 'Nombre Comercial'.
    Retorna la ruta completa o None.
    """
    if not moto:
        return None
    key = _get_moto_foto_key(moto)
    if not key:
        return None

    for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
        path = os.path.join(MOTOS_FOTOS_DIR, key + ext)
        if os.path.exists(path):
            return path

    # Buscar solo por nombre comercial
    nombre = moto.get('Nombre Comercial', '')
    if nombre:
        for f in os.listdir(MOTOS_FOTOS_DIR):
            name_part = os.path.splitext(f)[0]
            if nombre.lower() in name_part.lower():
                return os.path.join(MOTOS_FOTOS_DIR, f)

    return None


def show_gestion_motos(app):
    """Muestra la vista de gestión de motos."""
    app.clear_window()

    # Asegurar que la carpeta de fotos existe
    if not os.path.exists(MOTOS_FOTOS_DIR):
        os.makedirs(MOTOS_FOTOS_DIR)

    ctk.CTkLabel(app, text="Gestión de Motocicletas", font=("Arial", 24, "bold")).pack(pady=20)

    # ── Layout principal: tabla (izquierda) + foto (derecha) ──
    main_frame = ctk.CTkFrame(app, fg_color="transparent")
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Tabla de motos (izquierda)
    left_frame = ctk.CTkFrame(main_frame)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

    table_frame = ctk.CTkScrollableFrame(left_frame)
    table_frame.pack(fill="both", expand=True)

    headers = ["Nom. Comercial", "Cod. Modelo", "Placa", "Origen", "Cilindraje", "Chasis", "Motor", "Peso", "Pot.", "Torq.", "Foto"]
    widths = [130, 100, 80, 80, 70, 100, 100, 60, 55, 55, 50]

    header_f = ctk.CTkFrame(table_frame, fg_color="gray30")
    header_f.pack(fill="x", pady=2)
    for i, h in enumerate(headers):
        ctk.CTkLabel(header_f, text=h, width=widths[i], font=("Arial", 11, "bold")).pack(side="left", padx=1)

    # Panel de foto (derecha)
    right_frame = ctk.CTkFrame(main_frame, width=300)
    right_frame.pack(side="right", fill="y", padx=(10, 0))
    right_frame.pack_propagate(False)

    ctk.CTkLabel(right_frame, text="Foto de la Moto", font=("Arial", 14, "bold")).pack(pady=10)

    photo_label = ctk.CTkLabel(right_frame, text="Seleccione una moto\npara ver su foto",
                               font=("Arial", 12), text_color="gray", width=260, height=250)
    photo_label.pack(pady=10, padx=20)

    moto_name_label = ctk.CTkLabel(right_frame, text="", font=("Arial", 16, "bold"))
    moto_name_label.pack(pady=5)

    moto_info_label = ctk.CTkLabel(right_frame, text="", font=("Arial", 12), text_color="gray",
                                   wraplength=260)
    moto_info_label.pack(pady=5)

    selected = {'val': None, 'widget': None, 'moto': None}

    def _show_photo(moto):
        """Muestra la foto de la moto en el panel derecho."""
        nombre = moto.get('Nombre Comercial', '')
        moto_name_label.configure(text=nombre)

        info_parts = []
        if moto.get('Código Modelo'):
            info_parts.append(f"Modelo: {moto['Código Modelo']}")
        if moto.get('Placa'):
            info_parts.append(f"Placa: {moto['Placa']}")
        if moto.get('Origen'):
            info_parts.append(f"Origen: {moto['Origen']}")
        moto_info_label.configure(text="  |  ".join(info_parts))

        foto_path = get_moto_foto_path(moto)
        if foto_path and os.path.exists(foto_path):
            try:
                pil_img = Image.open(foto_path)
                max_w, max_h = 260, 250
                ratio = min(max_w / pil_img.width, max_h / pil_img.height)
                new_w = int(pil_img.width * ratio)
                new_h = int(pil_img.height * ratio)

                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img,
                                       size=(new_w, new_h))
                photo_label.configure(image=ctk_img, text="")
                photo_label._ctk_image = ctk_img  # Mantener referencia
            except Exception as e:
                photo_label.configure(image=None, text=f"Error cargando foto:\n{e}")
        else:
            photo_label.configure(image=None, text="Sin foto asignada\n\nUse '📷 Asignar Foto'\npara agregar una")

    def refresh_table():
        for w in table_frame.winfo_children():
            if w != header_f:
                w.destroy()
        motos = app.data_handler.load_motos()
        selected['val'], selected['widget'], selected['moto'] = None, None, None
        btn_del.configure(state="disabled")
        btn_foto.configure(state="disabled")

        # Limpiar panel de foto
        photo_label.configure(image=None, text="Seleccione una moto\npara ver su foto")
        moto_name_label.configure(text="")
        moto_info_label.configure(text="")

        def select_row(idx, moto_data, row_w):
            if selected['widget']:
                try:
                    selected['widget'].configure(fg_color=["gray86", "gray17"])
                except Exception:
                    pass
            selected['val'] = idx
            selected['moto'] = moto_data
            selected['widget'] = row_w
            row_w.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            btn_del.configure(state="normal")
            btn_foto.configure(state="normal")
            _show_photo(moto_data)

        for i, m in enumerate(motos):
            row = ctk.CTkFrame(table_frame)
            row.pack(fill="x", pady=1)
            row.bind("<Button-1>", lambda e, x=i, md=m, r=row: select_row(x, md, r))

            has_foto = "✅" if get_moto_foto_path(m) else "❌"
            vals = [m.get('Nombre Comercial', ''), m.get('Código Modelo', ''), m.get('Placa', ''),
                    m.get('Origen', ''), m.get('Cilindraje (cc)', ''), m.get('Chasis', ''),
                    m.get('Motor', ''), m.get('Peso (Kg)', ''), m.get('Potencia (Hp)', ''),
                    m.get('Torque (Nm)', ''), has_foto]

            for j, v in enumerate(vals):
                lbl = ctk.CTkLabel(row, text=v, width=widths[j])
                lbl.pack(side="left", padx=1)
                lbl.bind("<Button-1>", lambda e, x=i, md=m, r=row: select_row(x, md, r))

    ctrl = ctk.CTkFrame(app, fg_color="transparent")
    ctrl.pack(fill="x", padx=20, pady=10)

    def add_moto():
        win = ctk.CTkToplevel(app)
        win.title("Agregar Motocicleta")
        win.geometry("400x700")
        win.attributes("-topmost", True)

        fields = ["Fecha", "Nombre Comercial", "Placa", "Código Modelo", "Origen",
                  "Chasis", "Motor", "Cilindraje (cc)", "Peso (Kg)", "Potencia (Hp)", "Torque (Nm)"]
        entries = {}
        for f in fields:
            r = ctk.CTkFrame(win)
            r.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(r, text=f).pack(side="left", padx=5)
            e = ctk.CTkEntry(r)
            e.pack(side="right", fill="x", expand=True, padx=5)
            entries[f] = e

        # Selector de foto
        foto_path_var = {'path': ''}
        foto_frame = ctk.CTkFrame(win)
        foto_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(foto_frame, text="Foto:").pack(side="left", padx=5)
        foto_lbl = ctk.CTkLabel(foto_frame, text="Sin foto seleccionada", text_color="gray")
        foto_lbl.pack(side="left", padx=5, fill="x", expand=True)

        def browse_foto():
            f = filedialog.askopenfilename(
                filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.PNG *.JPG *.JPEG")],
                parent=win)
            if f:
                foto_path_var['path'] = f
                foto_lbl.configure(text=os.path.basename(f), text_color="green")

        ctk.CTkButton(foto_frame, text="Buscar", width=60, command=browse_foto).pack(side="right", padx=5)

        def save():
            data = {f: entries[f].get() for f in fields}

            # Copiar foto si se seleccionó una
            if foto_path_var['path']:
                nombre = data.get('Nombre Comercial', 'Moto')
                placa = data.get('Placa', '')
                key = f"{nombre} {placa}".strip() if placa else nombre
                ext = os.path.splitext(foto_path_var['path'])[1]
                dest = os.path.join(MOTOS_FOTOS_DIR, key + ext)
                try:
                    shutil.copy2(foto_path_var['path'], dest)
                except Exception as e:
                    print(f"Error copiando foto de moto: {e}")

            app.data_handler.add_moto(data)
            refresh_table()
            win.destroy()

        ctk.CTkButton(win, text="Guardar", command=save).pack(pady=20)

    def assign_foto():
        """Asigna o cambia la foto de la moto seleccionada."""
        if selected['moto'] is None:
            return
        f = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.PNG *.JPG *.JPEG")])
        if f:
            key = _get_moto_foto_key(selected['moto'])
            ext = os.path.splitext(f)[1]
            dest = os.path.join(MOTOS_FOTOS_DIR, key + ext)
            try:
                # Eliminar foto anterior si existe con extensión diferente
                old_foto = get_moto_foto_path(selected['moto'])
                if old_foto and os.path.exists(old_foto) and old_foto != dest:
                    os.remove(old_foto)
                shutil.copy2(f, dest)
                _show_photo(selected['moto'])
                refresh_table()
                messagebox.showinfo("Foto actualizada",
                                   f"Foto asignada a {selected['moto'].get('Nombre Comercial', '')}")
            except Exception as e:
                messagebox.showerror("Error", f"Error asignando foto:\n{e}")

    def delete_moto():
        if selected['val'] is not None:
            if messagebox.askyesno("Confirmar", "¿Eliminar motocicleta seleccionada?"):
                app.data_handler.delete_moto(selected['val'])
                refresh_table()

    ctk.CTkButton(ctrl, text="Agregar Moto", font=("Arial", 14, "bold"),
                  command=add_moto).pack(side="left", padx=10)
    btn_foto = ctk.CTkButton(ctrl, text="📷 Asignar Foto", font=("Arial", 14, "bold"),
                             fg_color="#2196F3", hover_color="#1976D2",
                             state="disabled", command=assign_foto)
    btn_foto.pack(side="left", padx=10)
    btn_del = ctk.CTkButton(ctrl, text="Eliminar Moto", font=("Arial", 14, "bold"),
                            fg_color="red", hover_color="darkred", state="disabled",
                            command=delete_moto)
    btn_del.pack(side="right", padx=10)

    bottom = ctk.CTkFrame(app, fg_color="transparent")
    bottom.pack(fill="x", side="bottom", padx=10, pady=20)
    ctk.CTkButton(bottom, text="⬅ Regresar", font=("Arial", 14, "bold"),
                  fg_color="gray", hover_color="darkgray",
                  command=app.show_main_menu).pack(side="left")

    refresh_table()
