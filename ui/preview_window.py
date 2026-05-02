"""
Ventana de previsualización de resultados.
Muestra gráficas y tablas antes de generar el reporte Excel.
"""
import customtkinter as ctk
from PIL import Image
import io


class PreviewWindow(ctk.CTkToplevel):
    def __init__(self, parent, title_text, sections, on_excel_callback=None,
                 contexto_gps=None, context_map=None, preview_data=None):
        """
        sections: lista de dicts con título, imágenes y tabla.
        on_excel_callback: función para generar Excel.
        """
        super().__init__(parent)
        self.title("Previsualización de Resultados")
        self.geometry("900x800")
        self.after(200, lambda: self.state('zoomed'))

        self.sections_data = sections
        self.contexto_gps = contexto_gps
        self.context_map = context_map
        self.on_excel_callback = on_excel_callback
        self.preview_data = preview_data

        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(header, text=title_text, font=("Arial", 20, "bold")).pack(pady=10)

        # Contenido scrollable
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self._build_sections()

        # Footer
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(footer, text="Cancelar", fg_color="gray",
                      hover_color="darkgray", command=self.destroy).pack(side="left", padx=20)

        if self.on_excel_callback and self.preview_data is not None:
            ctk.CTkButton(footer, text="📊 Generar Reporte Excel",
                         fg_color="#107C41", hover_color="#0b5e31",
                         font=("Arial", 14, "bold"),
                         command=self._excel).pack(side="right", padx=20)

    def _build_sections(self):
        # Contexto GPS
        if self.contexto_gps or self.context_map:
            ctk.CTkLabel(self.scroll_frame, text="Ubicación de la prueba",
                        font=("Arial", 20, "bold"), text_color="#1f538d"
                        ).pack(pady=(20, 10), anchor="center")

            if self.context_map:
                self._add_image(self.context_map)

            if self.contexto_gps and self.contexto_gps.get('google_maps_link'):
                link = self.contexto_gps.get('google_maps_link')
                import webbrowser
                def open_map(url=link):
                    webbrowser.open(url)
                ctk.CTkButton(self.scroll_frame, text="Ver en Google Maps",
                             fg_color="#4285F4", hover_color="#3367D6",
                             command=open_map).pack(pady=(10, 20), anchor="center")

            ctk.CTkFrame(self.scroll_frame, height=2, fg_color="gray"
                        ).pack(fill="x", padx=20, pady=20)

        # Secciones de datos
        for sec in self.sections_data:
            if sec.get('title'):
                ctk.CTkLabel(self.scroll_frame, text=sec['title'],
                            font=("Arial", 16, "bold"), text_color="#1f538d"
                            ).pack(pady=(20, 10), anchor="w", padx=10)

            for img_bytes in sec.get('images', []):
                self._add_image(img_bytes)

            if sec.get('table_data'):
                self._add_table(sec['table_data'])

            ctk.CTkFrame(self.scroll_frame, height=2, fg_color="gray"
                        ).pack(fill="x", padx=20, pady=20)

    def _add_image(self, img_bytes):
        try:
            if isinstance(img_bytes, dict):
                img_bytes = img_bytes.get('bytes')
            if not img_bytes:
                return

            image = Image.open(io.BytesIO(img_bytes))
            target_width = 800
            ratio = target_width / float(image.size[0])
            hsize = int(float(image.size[1]) * ratio)

            ctk_img = ctk.CTkImage(light_image=image, dark_image=image,
                                   size=(target_width, hsize))
            lbl = ctk.CTkLabel(self.scroll_frame, image=ctk_img, text="")
            lbl.pack(pady=10)
        except Exception as e:
            ctk.CTkLabel(self.scroll_frame, text=f"Error cargando imagen: {e}",
                        text_color="red").pack()

    def _add_table(self, table_data):
        if not table_data:
            return

        table_frame = ctk.CTkFrame(self.scroll_frame)
        table_frame.pack(pady=10, padx=20, fill="x")

        cols = len(table_data[0]) if table_data else 1
        for i in range(cols):
            table_frame.grid_columnconfigure(i, weight=1)

        for row_idx, row in enumerate(table_data):
            for col_idx, value in enumerate(row):
                font = ("Arial", 12, "bold") if row_idx == 0 else ("Arial", 12)
                bg = ("#1f538d", "#1f538d") if row_idx == 0 else ("white", "white")
                txt = "white" if row_idx == 0 else ("black", "black")

                cell = ctk.CTkLabel(table_frame, text=str(value), font=font,
                                   fg_color=bg, text_color=txt, corner_radius=0)
                cell.grid(row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)

    def _excel(self):
        if self.on_excel_callback and self.preview_data is not None:
            self.on_excel_callback(self.preview_data)
