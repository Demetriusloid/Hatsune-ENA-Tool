import tkinter as tk
from src.app import ENATranslationTool

if __name__ == "__main__":
    root = tk.Tk()
    app = ENATranslationTool(root)
    root.mainloop()