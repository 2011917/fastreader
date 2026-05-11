import pygame
import sys
import threading
import customtkinter as ctk

# --- Global Configs ---
INITIAL_WIDTH, INITIAL_HEIGHT = 800, 450

# Pygame Colors (Tuples)
PG_BLACK = (0, 0, 0)
PG_WHITE = (255, 255, 255)
PG_RED = (255, 50, 50)
PG_GRAY = (100, 100, 100)

# CustomTkinter Colors (Strings/Hex)
CTK_BLACK = "#000000"
CTK_TEXT_BG = "#111111"
CTK_RED = "#FF3232"  # This is the hex equivalent of (255, 50, 50)
CTK_WHITE = "#FFFFFF"


class SpeedReader:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE
        )
        pygame.display.set_caption("RSVP Display")

        self.wpm = 450
        self.font_size = 180
        self.update_font(self.font_size)

        self.clock = pygame.time.Clock()
        self.current_word = ""
        self.running = True
        self.is_playing = False

    def update_font(self, size):
        self.font_size = int(size)
        self.font = pygame.font.SysFont("Helvetica", self.font_size, bold=True)

    def get_orp_index(self, word):
        length = len(word)
        if length <= 1:
            return 0
        if length <= 5:
            return 1
        if length <= 9:
            return 2
        return 3

    def draw_word(self, word):
        curr_w, curr_h = self.screen.get_size()
        self.screen.fill(PG_BLACK)

        if not word:
            pygame.display.flip()
            return

        idx = self.get_orp_index(word)
        part1, focus, part2 = word[:idx], word[idx], word[idx + 1 :]

        # Use PG_ colors here
        s1 = self.font.render(part1, True, PG_WHITE)
        sf = self.font.render(focus, True, PG_RED)
        s2 = self.font.render(part2, True, PG_WHITE)

        cx, cy = curr_w // 3, curr_h // 2
        fx = cx - (sf.get_width() // 2)
        fy = cy - (sf.get_height() // 2)

        self.screen.blit(s1, (fx - s1.get_width(), fy))
        self.screen.blit(sf, (fx, fy))
        self.screen.blit(s2, (fx + sf.get_width(), fy))

        # Guidelines
        pygame.draw.line(self.screen, PG_GRAY, (cx, fy - 30), (cx, fy - 50), 2)
        pygame.draw.line(
            self.screen,
            PG_GRAY,
            (cx, fy + sf.get_height() + 30),
            (cx, fy + sf.get_height() + 50),
            2,
        )

        pygame.display.flip()

    def play_text(self, text):
        self.is_playing = True
        words = text.split()
        for w in words:
            if not self.running or not self.is_playing:
                break
            self.current_word = w
            self.draw_word(w)

            ms_per_word = int(60000 / self.wpm)
            delay = ms_per_word
            if any(c in w for c in ".,!?"):
                delay *= 1.8

            pygame.time.delay(int(delay))
            pygame.event.pump()

        self.is_playing = False

    def run_display(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (event.w, event.h), pygame.RESIZABLE
                    )
                    self.draw_word(self.current_word)
            self.clock.tick(60)
        pygame.quit()


def launch_control_panel(reader):
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.title("RSVP Control")
    root.geometry("450x600")
    root.configure(fg_color=CTK_BLACK)

    header = ctk.CTkLabel(
        root, text="RSVP CONTROLS", font=("Helvetica", 14, "bold"), text_color="gray"
    )
    header.pack(pady=(20, 10))

    textbox = ctk.CTkTextbox(
        root,
        width=400,
        height=250,
        fg_color=CTK_TEXT_BG,
        border_color="#333333",
        border_width=1,
    )
    textbox.pack(padx=20, pady=10)

    # WPM Section
    wpm_label = ctk.CTkLabel(
        root, text=f"Speed: {reader.wpm} WPM", font=("Helvetica", 12)
    )
    wpm_label.pack()

    def update_wpm(val):
        reader.wpm = int(val)
        wpm_label.configure(text=f"Speed: {int(val)} WPM")

    # Fixed: Passing CTK_RED (string) instead of a tuple
    wpm_slider = ctk.CTkSlider(
        root,
        from_=100,
        to=1000,
        number_of_steps=18,
        command=update_wpm,
        button_color=CTK_RED,
        button_hover_color="#ff7777",
    )
    wpm_slider.set(reader.wpm)
    wpm_slider.pack(pady=(0, 20))

    # Font Section
    font_label = ctk.CTkLabel(
        root, text=f"Font Size: {reader.font_size}px", font=("Helvetica", 12)
    )
    font_label.pack()

    def update_fsize(val):
        reader.update_font(val)
        font_label.configure(text=f"Font Size: {int(val)}px")

    font_slider = ctk.CTkSlider(
        root,
        from_=40,
        to=300,
        command=update_fsize,
        button_color=CTK_WHITE,
        button_hover_color="#cccccc",
    )
    font_slider.set(reader.font_size)
    font_slider.pack(pady=(0, 20))

    btn_frame = ctk.CTkFrame(root, fg_color="transparent")
    btn_frame.pack(pady=20)

    def start_reading():
        txt = textbox.get("1.0", "end-1c").strip()
        if txt:
            threading.Thread(target=reader.play_text, args=(txt,), daemon=True).start()

    def stop_reading():
        reader.is_playing = False

    play_btn = ctk.CTkButton(
        btn_frame,
        text="PLAY",
        command=start_reading,
        fg_color="#222222",
        hover_color="#333333",
        width=120,
        corner_radius=5,
    )
    play_btn.pack(side="left", padx=10)

    stop_btn = ctk.CTkButton(
        btn_frame,
        text="STOP",
        command=stop_reading,
        fg_color="#880000",
        hover_color="#aa0000",
        width=120,
        corner_radius=5,
    )
    stop_btn.pack(side="left", padx=10)

    root.mainloop()
    reader.running = False


if __name__ == "__main__":
    app = SpeedReader()
    gui_thread = threading.Thread(target=launch_control_panel, args=(app,), daemon=True)
    gui_thread.start()
    app.run_display()
