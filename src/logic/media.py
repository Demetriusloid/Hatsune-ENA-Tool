import os
import tkinter as tk
from ..config import resource_path

try:
    from PIL import Image, ImageTk, ImageSequence
    import pygame
    MEDIA_AVAILABLE = True
except ImportError:
    MEDIA_AVAILABLE = False

class EasterEgg:
    @staticmethod
    def play(root_window):
        if not MEDIA_AVAILABLE: return
        gif_filename = "jumpscare.gif"
        audio_filename = "jumpscare.mp3"
        gif_path = resource_path(gif_filename)
        audio_path = resource_path(audio_filename)
        if not os.path.exists(gif_path) or not os.path.exists(audio_path): return

        win = tk.Toplevel(root_window)
        win.title("SURPRESA!")
        win.attributes("-fullscreen", True)
        win.configure(bg="black")
        win.focus_force()

        try:
            pygame.mixer.init()
            pygame.mixer.music.load(audio_path)
            gif_image = Image.open(gif_path)
            screen_w = win.winfo_screenwidth()
            screen_h = win.winfo_screenheight()
            frames = []
            for frame in ImageSequence.Iterator(gif_image):
                resized = frame.convert("RGBA").resize((screen_w, screen_h), Image.Resampling.NEAREST)
                frames.append(ImageTk.PhotoImage(resized))
            try: duration = gif_image.info['duration']
            except: duration = 100
            if duration < 20: duration = 50

            lbl_gif = tk.Label(win, bg="black", borderwidth=0)
            lbl_gif.pack(expand=True, fill="both")
            state = {"idx": 0}

            def stop_scare(e=None):
                try: pygame.mixer.music.stop()
                except: pass
                if win.winfo_exists(): win.destroy()

            def animate():
                if not win.winfo_exists(): return
                if pygame.mixer.music.get_busy():
                    frame_idx = state["idx"] % len(frames)
                    lbl_gif.configure(image=frames[frame_idx])
                    lbl_gif.image = frames[frame_idx] 
                    state["idx"] += 1
                    win.after(duration, animate)
                else: stop_scare()

            win.bind("<Button-1>", stop_scare)
            win.bind("<Escape>", stop_scare)
            pygame.mixer.music.play()
            animate()
        except Exception:
            if win.winfo_exists(): win.destroy()