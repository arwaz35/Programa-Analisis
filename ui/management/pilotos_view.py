"""
Vista de gestión de pilotos.
Incluye asignación y visualización de foto de piloto.
Las fotos se almacenan en la carpeta Pilotos/ del proyecto.
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import os
import shutil
from config import PILOTOS_FOTOS_DIR


def get_piloto_foto_path(nombre):
    """
    Busca la foto del piloto en la carpeta de fotos.
    Retorna la ruta completa o None.
    Función a nivel de módulo para poder importarla desde excel_reporter.
    """
    if not nombre:
        return None
    for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
        path = os.path.join(PILOTOS_FOTOS_DIR, nombre + ext)
        if os.path.exists(path):
            return path
    # Buscar por nombre parcial
    if os.path.exists(PILOTOS_FOTOS_DIR):
        for f in os.listdir(PILOTOS_FOTOS_DIR):
            name_part = os.path.splitext(f)[0]
            if nombre.lower() in name_part.lower():
                return os.path.join(PILOTOS_FOTOS_DIR, f)
    return None


def show_gestion_pilotos(app):
    """Muestra la vista de gestión de pilotos."""
    app.clear_window()
    ctk.CTkLabel(app, text="Gestión de Pilotos", font=("Arial", 24, "bold")).pack(pady=20)

    # Asegurar que la carpeta de fotos existe
    if not os.path.exists(PILOTOS_FOTOS_DIR):
        os.makedirs(PILOTOS_FOTOS_DIR)

    # ── Layout principal: tabla (izquierda) + foto (derecha) ──
    main_frame = ctk.CTkFrame(app, fg_color="transparent")
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Tabla de pilotos (izquierda)
    left_frame = ctk.CTkFrame(main_frame)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

    table_frame = ctk.CTkScrollableFrame(left_frame)
    table_frame.pack(fill="both", expand=True)

    headers = ["Nombre del Piloto", "Peso (Kg)", "Altura (cm)", "Foto"]
    widths = [200, 100, 100, 80]

    header_f = ctk.CTkFrame(table_frame, fg_color="gray30")
    header_f.pack(fill="x", pady=2)
    for i, h in enumerate(headers):
        ctk.CTkLabel(header_f, text=h, width=widths[i], font=("Arial", 12, "bold")).pack(side="left", padx=2)

    # Panel de foto (derecha)
    right_frame = ctk.CTkFrame(main_frame, width=300)
    right_frame.pack(side="right", fill="y", padx=(10, 0))
    right_frame.pack_propagate(False)

    ctk.CTkLabel(right_frame, text="Foto del Piloto", font=("Arial", 14, "bold")).pack(pady=10)

    photo_label = ctk.CTkLabel(right_frame, text="Seleccione un piloto\npara ver su foto",
                               font=("Arial", 12), text_color="gray", width=260, height=300)
    photo_label.pack(pady=10, padx=20)

    pilot_name_label = ctk.CTkLabel(right_frame, text="", font=("Arial", 16, "bold"))
    pilot_name_label.pack(pady=5)

    pilot_info_label = ctk.CTkLabel(right_frame, text="", font=("Arial", 12), text_color="gray")
    pilot_info_label.pack(pady=5)

    selected = {'nombre': None, 'widget': None, 'peso': 0, 'altura': 0}

    def _show_photo(nombre, peso=0, altura=0):
        """Muestra la foto del piloto en el panel derecho."""
        nonlocal photo_label

        pilot_name_label.configure(text=nombre)
        pilot_info_label.configure(text=f"Peso: {peso} Kg  |  Altura: {altura} cm")

        # Destruir label anterior y crear uno nuevo para evitar TclError
        photo_label.destroy()

        foto_path = get_piloto_foto_path(nombre)
        if foto_path and os.path.exists(foto_path):
            try:
                pil_img = Image.open(foto_path)
                max_w, max_h = 260, 300
                ratio = min(max_w / pil_img.width, max_h / pil_img.height)
                new_w = int(pil_img.width * ratio)
                new_h = int(pil_img.height * ratio)

                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img,
                                       size=(new_w, new_h))
                photo_label = ctk.CTkLabel(right_frame, image=ctk_img, text="",
                                           width=260, height=300)
                photo_label._ctk_image = ctk_img
            except Exception:
                photo_label = ctk.CTkLabel(right_frame, text="Error cargando foto",
                                           font=("Arial", 12), text_color="red",
                                           width=260, height=300)
        else:
            photo_label = ctk.CTkLabel(right_frame, text="Sin foto asignada\n\nUse 'Asignar Foto'\npara agregar una",
                                       font=("Arial", 12), text_color="gray",
                                       width=260, height=300)

        photo_label.pack(pady=10, padx=20, before=pilot_name_label)

    def refresh_table():
        for w in table_frame.winfo_children():
            if w != header_f:
                w.destroy()
        pilotos = app.data_handler.load_pilotos()
        selected['nombre'], selected['widget'] = None, None
        btn_del.configure(state="disabled")
        btn_upd.configure(state="disabled")
        btn_foto.configure(state="disabled")

        def select_row(nombre, peso, altura, row_w):
            if selected['widget']:
                try:
                    selected['widget'].configure(fg_color=["gray86", "gray17"])
                except Exception:
                    pass
            selected['nombre'] = nombre
            selected['peso'] = peso
            selected['altura'] = altura
            selected['widget'] = row_w
            row_w.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            btn_del.configure(state="normal")
            btn_upd.configure(state="normal")
            btn_foto.configure(state="normal")
            _show_photo(nombre, peso, altura)

        for p in pilotos:
            row = ctk.CTkFrame(table_frame)
            row.pack(fill="x", pady=1)
            nom = p.get('nombre', '')
            pes = p.get('peso', 0)
            alt = p.get('altura', 0)
            has_foto = "✅" if get_piloto_foto_path(nom) else "❌"
            row.bind("<Button-1>", lambda e, n=nom, w=pes, a=alt, r=row: select_row(n, w, a, r))
            for j, v in enumerate([nom, str(pes), str(alt), has_foto]):
                lbl = ctk.CTkLabel(row, text=v, width=widths[j])
                lbl.pack(side="left", padx=2)
                lbl.bind("<Button-1>", lambda e, n=nom, w=pes, a=alt, r=row: select_row(n, w, a, r))

    # ── Controles ──
    ctrl = ctk.CTkFrame(app, fg_color="transparent")
    ctrl.pack(fill="x", padx=20, pady=10)

    def add_piloto():
        win = ctk.CTkToplevel(app)
        win.title("Agregar Piloto")
        win.geometry("400x350")
        win.attributes("-topmost", True)

        entries = []
        for label_text in ["Nombre:", "Peso (Kg):", "Altura (cm):"]:
            r = ctk.CTkFrame(win)
            r.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(r, text=label_text).pack(side="left", padx=5)
            e = ctk.CTkEntry(r)
            e.pack(side="right", fill="x", expand=True, padx=5)
            entries.append(e)

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
            npm = entries[0].get().strip()
            try:
                p_val = float(entries[1].get().replace(',', '.')) if entries[1].get() else 0.0
            except ValueError:
                p_val = 0.0
            try:
                a_val = float(entries[2].get().replace(',', '.')) if entries[2].get() else 0.0
            except ValueError:
                a_val = 0.0
            if not npm:
                messagebox.showerror("Error", "Nombre es obligatorio", parent=win)
                return

            # Copiar foto si se seleccionó una
            if foto_path_var['path']:
                ext = os.path.splitext(foto_path_var['path'])[1]
                dest = os.path.join(PILOTOS_FOTOS_DIR, npm + ext)
                try:
                    shutil.copy2(foto_path_var['path'], dest)
                except Exception as e:
                    print(f"Error copiando foto: {e}")

            app.data_handler.add_piloto(npm, p_val, a_val)
            refresh_table()
            win.destroy()

        ctk.CTkButton(win, text="Guardar", command=save).pack(pady=20)

    def assign_foto():
        """Asigna o cambia la foto del piloto seleccionado."""
        if selected['nombre'] is None:
            return
        f = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.PNG *.JPG *.JPEG")])
        if f:
            ext = os.path.splitext(f)[1]
            dest = os.path.join(PILOTOS_FOTOS_DIR, selected['nombre'] + ext)
            try:
                # Eliminar foto anterior si existe con extensión diferente
                old_foto = get_piloto_foto_path(selected['nombre'])
                if old_foto and os.path.exists(old_foto) and old_foto != dest:
                    os.remove(old_foto)
                shutil.copy2(f, dest)
                _show_photo(selected['nombre'], selected['peso'], selected['altura'])
                refresh_table()
                messagebox.showinfo("Foto actualizada",
                                   f"Foto asignada a {selected['nombre']}")
            except Exception as e:
                messagebox.showerror("Error", f"Error asignando foto:\n{e}")

    def update_piloto():
        if selected['nombre'] is None:
            return
        win = ctk.CTkToplevel(app)
        win.title("Actualizar Piloto")
        win.geometry("400x250")
        win.attributes("-topmost", True)
        old = (selected['nombre'], selected['peso'], selected['altura'])
        entries = []
        for label_text, default in [("Nombre:", old[0]), ("Peso (Kg):", str(old[1])), ("Altura (cm):", str(old[2]))]:
            r = ctk.CTkFrame(win)
            r.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(r, text=label_text).pack(side="left", padx=5)
            e = ctk.CTkEntry(r)
            e.pack(side="right", fill="x", expand=True, padx=5)
            e.insert(0, default)
            entries.append(e)

        def save():
            npm = entries[0].get().strip()
            try:
                p_val = float(entries[1].get().replace(',', '.')) if entries[1].get() else 0.0
            except ValueError:
                p_val = 0.0
            try:
                a_val = float(entries[2].get().replace(',', '.')) if entries[2].get() else 0.0
            except ValueError:
                a_val = 0.0
            if not npm:
                return

            # Si cambió el nombre, renombrar la foto
            if npm != old[0]:
                old_foto = get_piloto_foto_path(old[0])
                if old_foto and os.path.exists(old_foto):
                    ext = os.path.splitext(old_foto)[1]
                    new_foto = os.path.join(PILOTOS_FOTOS_DIR, npm + ext)
                    try:
                        os.rename(old_foto, new_foto)
                    except Exception as e:
                        print(f"Error renombrando foto: {e}")

            app.data_handler.update_piloto(old[0], npm, p_val, a_val)
            refresh_table()
            win.destroy()

        ctk.CTkButton(win, text="Actualizar", command=save).pack(pady=20)

    def delete_piloto():
        if selected['nombre'] is not None:
            if messagebox.askyesno("Confirmar", "¿Eliminar piloto seleccionado?"):
                app.data_handler.delete_piloto(selected['nombre'])
                refresh_table()

    ctk.CTkButton(ctrl, text="Agregar Piloto", font=("Arial", 14, "bold"),
                  command=add_piloto).pack(side="left", padx=10)
    btn_foto = ctk.CTkButton(ctrl, text="📷 Asignar Foto", font=("Arial", 14, "bold"),
                             fg_color="#2196F3", hover_color="#1976D2",
                             state="disabled", command=assign_foto)
    btn_foto.pack(side="left", padx=10)
    btn_upd = ctk.CTkButton(ctrl, text="Actualizar Datos", font=("Arial", 14, "bold"),
                            fg_color="#F29F05", hover_color="#C27A04", text_color="black",
                            state="disabled", command=update_piloto)
    btn_upd.pack(side="left", padx=10)
    btn_del = ctk.CTkButton(ctrl, text="Eliminar Piloto", font=("Arial", 14, "bold"),
                            fg_color="red", hover_color="darkred", state="disabled",
                            command=delete_piloto)
    btn_del.pack(side="right", padx=10)

    bottom = ctk.CTkFrame(app, fg_color="transparent")
    bottom.pack(fill="x", side="bottom", padx=10, pady=20)
    ctk.CTkButton(bottom, text="⬅ Regresar", font=("Arial", 14, "bold"),
                  fg_color="gray", hover_color="darkgray",
                  command=app.show_main_menu).pack(side="left")
    refresh_table()
