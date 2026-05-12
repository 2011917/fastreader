import customtkinter as ctk

# --- Global Configs ---
CTK_BLACK = "#000000"
CTK_TEXT_BG = "#111111"
CTK_RED = "#FF3232"
CTK_WHITE = "#FFFFFF"
CTK_GRAY = "#646464"


class SpeedReaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Main Window: Control Panel ---
        self.title("RSVP Control")
        self.geometry("450x600")
        self.configure(fg_color=CTK_BLACK)

        self.wpm = 450
        self.font_size = 180
        self.is_playing = False
        self.words = []
        self.current_idx = 0

        self.setup_control_panel()

        # --- Second Window: RSVP Display ---
        self.display_window = ctk.CTkToplevel(self)
        self.display_window.title("RSVP Display")
        self.display_window.geometry("800x450")
        self.display_window.configure(fg_color=CTK_BLACK)

        # Create Canvas for drawing (This replaces the Labels)
        self.canvas = ctk.CTkCanvas(
            self.display_window, bg=CTK_BLACK, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Bind resize event to keep things centered
        self.display_window.bind("<Configure>", self.on_resize)

        # Initialize the text items on canvas
        self.setup_canvas_items()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.display_window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.destroy()

    def setup_control_panel(self):
        header = ctk.CTkLabel(
            self,
            text="RSVP CONTROLS",
            font=("Helvetica", 14, "bold"),
            text_color="gray",
        )
        header.pack(pady=(20, 10))

        self.textbox = ctk.CTkTextbox(
            self,
            width=400,
            height=250,
            fg_color=CTK_TEXT_BG,
            border_color="#333333",
            border_width=1,
        )
        self.textbox.pack(padx=20, pady=10)

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
        # We create the items once and move/update them later
        f_style = ("Helvetica", self.font_size, "bold")

        # Guide Lines
        self.line_top = self.canvas.create_line(0, 0, 0, 0, fill=CTK_GRAY, width=2)
        self.line_bottom = self.canvas.create_line(0, 0, 0, 0, fill=CTK_GRAY, width=2)

        # Text Parts (All sharing the same x-coord anchor)
        self.txt_focus = self.canvas.create_text(
            0, 0, text="", fill=CTK_RED, font=f_style, anchor="center"
        )
        self.txt_part1 = self.canvas.create_text(
            0, 0, text="", fill=CTK_WHITE, font=f_style, anchor="e"
        )
        self.txt_part2 = self.canvas.create_text(
            0, 0, text="", fill=CTK_WHITE, font=f_style, anchor="w"
        )

    def on_resize(self, event=None):
        w = self.display_window.winfo_width()
        h = self.display_window.winfo_height()

        # 1/3rd focus point
        fx = w // 3
        cy = h // 2

        # Update line positions
        self.canvas.coords(
            self.line_top,
            fx,
            cy - (self.font_size * 0.6),
            fx,
            cy - (self.font_size * 0.8),
        )
        self.canvas.coords(
            self.line_bottom,
            fx,
            cy + (self.font_size * 0.6),
            fx,
            cy + (self.font_size * 0.8),
        )

        # Update text positions
        self.canvas.coords(self.txt_focus, fx, cy)
        self.canvas.coords(self.txt_part1, fx, cy)  # anchor 'e' will push it left
        self.canvas.coords(self.txt_part2, fx, cy)  # anchor 'w' will push it right

        # Re-tweak part1 and part2 positions slightly to account for red character width
        # This is handled dynamically in run_reader_loop

    def update_wpm(self, val):
        self.wpm = int(val)
        self.wpm_label.configure(text=f"Speed: {self.wpm} WPM")

    def update_font(self, val):
        self.font_size = int(val)
        self.font_label.configure(text=f"Font Size: {self.font_size}px")
        f_style = ("Helvetica", self.font_size, "bold")
        self.canvas.itemconfig(self.txt_focus, font=f_style)
        self.canvas.itemconfig(self.txt_part1, font=f_style)
        self.canvas.itemconfig(self.txt_part2, font=f_style)
        self.on_resize()

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
            txt = self.textbox.get("1.0", "end-1c").strip()
            if txt:
                if not self.words:
                    self.words = txt.split()
                self.is_playing = True
                self.play_btn.configure(text="PAUSE")
                self.run_reader_loop()
        else:
            self.is_playing = False
            self.play_btn.configure(text="RESUME")

    def reset_reader(self):
        self.is_playing = False
        self.current_idx = 0
        self.words = []
        self.play_btn.configure(text="PLAY")
        self.canvas.itemconfig(self.txt_focus, text="")
        self.canvas.itemconfig(self.txt_part1, text="")
        self.canvas.itemconfig(self.txt_part2, text="")

    def run_reader_loop(self):
        if not self.is_playing or self.current_idx >= len(self.words):
            if self.current_idx >= len(self.words) and len(self.words) > 0:
                self.reset_reader()
            return

        word = self.words[self.current_idx]
        idx = self.get_orp_index(word)

        # 1. Update text
        self.canvas.itemconfig(self.txt_part1, text=word[:idx])
        self.canvas.itemconfig(self.txt_focus, text=word[idx])
        self.canvas.itemconfig(self.txt_part2, text=word[idx + 1 :])

        # 2. Adjust X-offsets for Part 1 and Part 2 based on the Focus character's width
        # This solves the "spacing issue" by measuring the actual rendered width of the focus letter
        bbox = self.canvas.bbox(self.txt_focus)
        if bbox:
            fw = (bbox[2] - bbox[0]) / 2  # Half width of focus char
            fx = self.display_window.winfo_width() // 3
            cy = self.display_window.winfo_height() // 2

            # Place part1 just to the left of the focus char boundaries
            self.canvas.coords(self.txt_part1, fx - fw, cy)
            # Place part2 just to the right
            self.canvas.coords(self.txt_part2, fx + fw, cy)

        # Timing logic
        base_delay = int(60000 / self.wpm)
        if any(c in word for c in ".,!?"):
            base_delay = int(base_delay * 1.8)

        self.current_idx += 1
        self.after(base_delay, self.run_reader_loop)


if __name__ == "__main__":
    app = SpeedReaderApp()
    app.mainloop()
