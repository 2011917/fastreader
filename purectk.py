import customtkinter as ctk
from tkinter import filedialog
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io

# --- Styling Configs ---
CTK_BLACK = "#000000"
CTK_TEXT_BG = "#111111"
CTK_RED = "#FF3232"
CTK_WHITE = "#FFFFFF"
CTK_GRAY = "#646464"


class SpeedReaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Logic State ---
        self.wpm = 450
        self.font_size = 180
        self.is_playing = False
        self.queue = []  # Words or PIL Images
        self.current_idx = 0
        self.temp_img = None

        # --- 1. Main Window: Control Panel ---
        self.title("RSVP Control")
        self.geometry("450x650")
        self.configure(fg_color=CTK_BLACK)
        self.setup_control_panel()

        # --- 2. Second Window: RSVP Display ---
        self.display_window = ctk.CTkToplevel(self)
        self.display_window.title("RSVP Display")
        self.display_window.geometry("800x450")
        self.display_window.configure(fg_color=CTK_BLACK)

        self.canvas = ctk.CTkCanvas(
            self.display_window, bg=CTK_BLACK, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.setup_canvas_items()

        self.display_window.bind("<Configure>", self.on_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.display_window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_control_panel(self):
        ctk.CTkLabel(
            self,
            text="RSVP CONTROLS",
            font=("Helvetica", 14, "bold"),
            text_color="gray",
        ).pack(pady=(20, 10))

        self.textbox = ctk.CTkTextbox(
            self,
            width=400,
            height=200,
            fg_color=CTK_TEXT_BG,
            border_color="#333",
            border_width=1,
        )
        self.textbox.pack(padx=20, pady=10)
        self.textbox.insert("1.0", "Paste text or upload your Cooking Project PDF...")

        self.pdf_btn = ctk.CTkButton(
            self,
            text="UPLOAD PDF",
            command=self.load_pdf,
            fg_color="#333",
            hover_color="#444",
        )
        self.pdf_btn.pack(pady=10)

        self.wpm_label = ctk.CTkLabel(self, text=f"Speed: {self.wpm} WPM")
        self.wpm_label.pack()
        self.wpm_slider = ctk.CTkSlider(
            self,
            from_=100,
            to=1000,
            number_of_steps=18,
            command=self.update_wpm,
            button_color=CTK_RED,
        )
        self.wpm_slider.set(self.wpm)
        self.wpm_slider.pack(pady=(0, 20))

        self.font_label = ctk.CTkLabel(self, text=f"Font Size: {self.font_size}px")
        self.font_label.pack()
        self.font_slider = ctk.CTkSlider(
            self, from_=40, to=300, command=self.update_font, button_color=CTK_WHITE
        )
        self.font_slider.set(self.font_size)
        self.font_slider.pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        self.play_btn = ctk.CTkButton(
            btn_frame, text="PLAY", command=self.toggle_play, fg_color="#222", width=120
        )
        self.play_btn.pack(side="left", padx=10)
        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="STOP",
            command=self.reset_reader,
            fg_color="#800",
            width=120,
        )
        self.stop_btn.pack(side="left", padx=10)

    def setup_canvas_items(self):
        f_style = ("Helvetica", self.font_size, "bold")
        self.line_top = self.canvas.create_line(0, 0, 0, 0, fill=CTK_GRAY, width=2)
        self.line_bottom = self.canvas.create_line(0, 0, 0, 0, fill=CTK_GRAY, width=2)
        self.txt_focus = self.canvas.create_text(
            0, 0, text="", fill=CTK_RED, font=f_style, anchor="center"
        )
        self.txt_part1 = self.canvas.create_text(
            0, 0, text="", fill=CTK_WHITE, font=f_style, anchor="e"
        )
        self.txt_part2 = self.canvas.create_text(
            0, 0, text="", fill=CTK_WHITE, font=f_style, anchor="w"
        )
        self.img_item = self.canvas.create_image(0, 0, anchor="center")

    def load_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return
        try:
            doc = fitz.open(file_path)
            new_queue = []
            for page in doc:
                text = page.get_text()
                for word in text.split():
                    new_queue.append(word)
                image_list = page.get_images(full=True)
                for img in image_list:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    pil_img = Image.open(io.BytesIO(base_image["image"]))
                    new_queue.append(pil_img)
            self.queue = new_queue
            self.current_idx = 0
            self.textbox.delete("1.0", "end")
            self.textbox.insert(
                "1.0", f"Success: {len(self.queue)} words/images loaded."
            )
        except Exception as e:
            print(f"PDF Load Error: {e}")

    def on_resize(self, event=None):
        try:
            w, h = self.display_window.winfo_width(), self.display_window.winfo_height()
            fx, cy = w // 3, h // 2
            line_offset = self.font_size * 0.6
            self.canvas.coords(
                self.line_top, fx, cy - line_offset, fx, cy - line_offset - 20
            )
            self.canvas.coords(
                self.line_bottom, fx, cy + line_offset, fx, cy + line_offset + 20
            )
            self.canvas.coords(self.txt_focus, fx, cy)
            self.canvas.coords(self.txt_part1, fx, cy)
            self.canvas.coords(self.txt_part2, fx, cy)
            self.canvas.coords(self.img_item, w // 2, h // 2)
        except:
            pass

    def run_reader_loop(self):
        try:
            if not self.winfo_exists() or not self.display_window.winfo_exists():
                return
        except:
            return

        if not self.is_playing or self.current_idx >= len(self.queue):
            if self.current_idx >= len(self.queue) and len(self.queue) > 0:
                self.reset_reader()
            return

        item = self.queue[self.current_idx]
        # CRITICAL FIX: Cast to int to prevent 'bad argument' error
        delay = int(60000 / self.wpm)

        try:
            self.canvas.itemconfig(self.txt_part1, text="")
            self.canvas.itemconfig(self.txt_focus, text="")
            self.canvas.itemconfig(self.txt_part2, text="")
            self.canvas.itemconfig(self.img_item, image="")

            if isinstance(item, str):
                idx = self.get_orp_index(item)
                self.canvas.itemconfig(self.txt_part1, text=item[:idx])
                self.canvas.itemconfig(self.txt_focus, text=item[idx])
                self.canvas.itemconfig(self.txt_part2, text=item[idx + 1 :])

                bbox = self.canvas.bbox(self.txt_focus)
                if bbox:
                    fw_half = (bbox[2] - bbox[0]) / 2
                    fx, cy = (
                        self.display_window.winfo_width() // 3,
                        self.display_window.winfo_height() // 2,
                    )
                    self.canvas.coords(self.txt_part1, fx - fw_half, cy)
                    self.canvas.coords(self.txt_part2, fx + fw_half, cy)

                if any(c in item for c in ".,!?"):
                    delay = int(delay * 1.8)

            elif isinstance(item, Image.Image):
                win_w, win_h = (
                    self.display_window.winfo_width() * 0.8,
                    self.display_window.winfo_height() * 0.8,
                )
                display_img = item.copy()
                display_img.thumbnail((win_w, win_h))
                self.temp_img = ImageTk.PhotoImage(display_img)
                self.canvas.itemconfig(self.img_item, image=self.temp_img)
                delay = 2000

            self.current_idx += 1
            if self.is_playing:
                self.after(int(delay), self.run_reader_loop)
        except Exception as e:
            print(f"Playback error: {e}")
            self.is_playing = False

    def get_orp_index(self, word):
        length = len(word)
        if length <= 1:
            return 0
        if length <= 5:
            return 1
        if length <= 9:
            return 2
        return 3

    def toggle_play(self):
        if not self.is_playing:
            if not self.queue:
                txt = self.textbox.get("1.0", "end-1c").strip()
                if txt:
                    self.queue = txt.split()
            if self.queue:
                self.is_playing = True
                self.play_btn.configure(text="PAUSE")
                self.run_reader_loop()
        else:
            self.is_playing = False
            self.play_btn.configure(text="RESUME")

    def reset_reader(self):
        self.is_playing = False
        self.current_idx = 0
        self.queue = []
        self.play_btn.configure(text="PLAY")
        try:
            self.canvas.itemconfig(self.txt_focus, text="")
            self.canvas.itemconfig(self.img_item, image="")
        except:
            pass

    def update_wpm(self, val):
        self.wpm = int(val)
        self.wpm_label.configure(text=f"Speed: {self.wpm} WPM")

    def update_font(self, val):
        self.font_size = int(val)
        self.font_label.configure(text=f"Font Size: {self.font_size}px")
        f_style = ("Helvetica", self.font_size, "bold")
        try:
            for item in [self.txt_focus, self.txt_part1, self.txt_part2]:
                self.canvas.itemconfig(item, font=f_style)
            self.on_resize()
        except:
            pass

    def on_closing(self):
        self.is_playing = False
        self.destroy()


if __name__ == "__main__":
    app = SpeedReaderApp()
    app.mainloop()
