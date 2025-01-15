import base64
import io
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, scrolledtext
import os
from PIL import Image, ImageTk


class ChatGUI(tk.Tk):
    """
    A chat-style GUI application using tkinter.
    Receives callbacks from the main routine when "sending messages"
    and displays the results.
    """

    def __init__(self):
        super().__init__()
        self.title("Chat GUI")
        self.geometry("800x600")

        # ---------- Style Settings ----------
        self.style = ttk.Style()
        # Specify a system theme (clam, default, alt, etc.)
        self.style.theme_use("clam")

        # Set styles for background color, buttons etc.
        background_color = "#fafafa"
        accent_color = "#1a73e8"
        text_color = "#333333"
        # Font can be changed to preference (e.g. "Century Gothic", "Arial")
        font_family = "Helvetica"

        # Frame background color
        self.style.configure("TFrame", background=background_color)

        # Label design
        self.style.configure(
            "TLabel",
            background=background_color,
            foreground=text_color,
            font=(font_family, 11)
        )

        # Button design
        self.style.configure(
            "TButton",
            background=accent_color,
            foreground="#ffffff",
            font=(font_family, 10, "bold"),
            padding=6
        )

        # Entry design
        self.style.configure(
            "TEntry",
            font=(font_family, 11),
            padding=5
        )

        # Set background color for entire window
        self.configure(bg=background_color)

        # ---------- Top: Chat Display Area ----------
        self.chat_display = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=(font_family, 11),
            bg="#ffffff",
            fg=text_color,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#e0e0e0"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chat_display.config(state="disabled")
        # ---------- Bottom: Message Input & Preview Area ----------
        bottom_frame = ttk.Frame(self, style="TFrame")
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        self.entry_message = ttk.Entry(bottom_frame, style="TEntry")
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_message.bind("<Return>", self.on_enter_key)

        # Disable image button initially
        self.button_attach = ttk.Button(
            bottom_frame, text="attach image", command=self.select_image, state=tk.DISABLED)
        self.button_attach.pack(side=tk.LEFT, padx=5)

        self.button_send = ttk.Button(
            bottom_frame, text="send", command=self.send_message)
        self.button_send.pack(side=tk.LEFT, padx=5)

        # Preview frame
        preview_frame = ttk.Frame(self, style="TFrame")
        preview_frame.pack(fill=tk.X, padx=10, pady=5)

        self.label_image_preview = ttk.Label(
            preview_frame, text="", style="TLabel")
        self.label_image_preview.pack(side=tk.LEFT, padx=5)

        self.button_cancel_selection = ttk.Button(
            preview_frame, text="cancel", command=self.cancel_selection)
        self.button_cancel_selection.pack(side=tk.LEFT, padx=5)
        self.button_cancel_selection.config(state=tk.DISABLED)

        # --- Flags & Data ---
        self.user_input_flag = False
        self.user_message = None

        # Variable to store base64 data
        self.user_image_b64 = None

        # Thumbnail object for display
        self.selected_image_thumbnail = None
        self.thumbnail_refs = []

        # Flag to check if image sending is allowed
        self.can_send_images = False

        # Variable to store user submitted image
        self.for_llm_image_b64 = None

    def on_enter_key(self, event):
        self.send_message()
        return "break"

    def enable_image_sending(self):
        """
        Allow image sending when some condition is met.
        """
        self.can_send_images = True
        self.button_attach.config(state=tk.NORMAL)

    def select_image(self):
        """
        Process to select an image.
        In practice, the file path is not used, but the binary is stored in base64.
        """
        if not self.can_send_images:
            self.add_chat("System", "image sending is not allowed yet.")
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            # Read the file and encode it in base64
            with open(file_path, "rb") as f:
                raw_data = f.read()
                self.user_image_b64 = base64.b64encode(
                    raw_data).decode("utf-8")

            # Display the selected image (base64→PIL→PhotoImage)
            self.update_image_preview(self.user_image_b64)
            self.button_cancel_selection.config(state=tk.NORMAL)

    def update_image_preview(self, image_b64: str):
        """
        Generate an image from a base64 string and display it in the preview label.
        """
        try:
            # Decode the base64 string and load it into a BytesIO object with Pillow
            decoded_data = base64.b64decode(image_b64)
            img_io = io.BytesIO(decoded_data)
            img = Image.open(img_io)
            img.thumbnail((150, 150))
            self.selected_image_thumbnail = ImageTk.PhotoImage(img)

            self.label_image_preview.config(
                image=self.selected_image_thumbnail, text="")
        except Exception as e:
            self.label_image_preview.config(
                text=f"Preview failed: {e}", image="")

    def cancel_preview(self):
        """
        Reset the selection and remove the preview.
        """
        self.selected_image_thumbnail = None
        self.label_image_preview.configure(text="", image="")
        self.button_cancel_selection.config(state=tk.DISABLED)

    def cancel_selection(self):
        """
        Reset the selection and remove the preview.
        """
        self.user_image_b64 = None
        self.selected_image_thumbnail = None
        self.label_image_preview.configure(text="", image="")
        self.button_cancel_selection.config(state=tk.DISABLED)

    def send_message(self):
        """
        Triggered when the send button is pressed.
        """
        if self.user_input_flag:
            return

        user_message = self.entry_message.get().strip()
        # Check if there is an image by looking at user_image_b64
        if not user_message and not self.user_image_b64:
            return

        # Display the user's message in the chat window
        self.add_chat("User", user_message, image_b64=self.user_image_b64)

        # Set the input content to a class variable
        self.user_message = user_message

        # Set the flag to disable the send button
        self.add_chat("System", text="Thinking...")
        self.set_input_in_progress(True)

        # Reset the input field
        self.entry_message.delete(0, tk.END)

        # Reset the image
        self.cancel_preview()

        self.for_llm_image_b64 = self.user_image_b64
        self.user_image_b64 = None

    def set_input_in_progress(self, in_progress: bool):
        self.user_input_flag = in_progress
        if in_progress:
            self.button_send.config(state=tk.DISABLED)
        else:
            self.button_send.config(state=tk.NORMAL)

    def add_chat(self, speaker: str, text: str, image_b64: str = None):
        """
        Add a message to the chat log area.
        If image_b64 is present, display the thumbnail.
        """
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{speaker}: {text}\n\n")

        if image_b64:
            try:
                decoded_data = base64.b64decode(image_b64)
                img_io = io.BytesIO(decoded_data)
                img = Image.open(img_io)
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)

                self.thumbnail_refs.append(photo)
                self.chat_display.image_create(tk.END, image=photo)
            except Exception as e:
                self.chat_display.insert(
                    tk.END, f"\n[Image loading failed: {e}]\n")

        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)


def main():
    app = ChatGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
