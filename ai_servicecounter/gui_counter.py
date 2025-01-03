# gui_app.py

import tkinter as tk
from tkinter import filedialog, scrolledtext
import os

class ChatGUI(tk.Tk):
    """
    tkinter を使ったチャット風の GUI アプリ。
    「メッセージ送信」時のコールバックをメインスクリプトから受け取り、
    結果を表示する。
    """
    def __init__(self):

        super().__init__()
        self.title("Chat GUI")
        self.geometry("600x500")


        # チャット表示部
        self.chat_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled')
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 下部フレーム
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        self.entry_message = tk.Entry(bottom_frame)
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 画像添付ボタン
        self.button_attach = tk.Button(bottom_frame, text="画像を添付", command=self.select_image)
        self.button_attach.pack(side=tk.LEFT, padx=5)

        # 送信ボタン
        self.button_send = tk.Button(bottom_frame, text="送信", command=self.send_message)
        self.button_send.pack(side=tk.LEFT)

        self.selected_image_path = None

    def select_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            self.selected_image_path = file_path
            # 分かりやすいようにウィンドウタイトルを変更
            self.title(f"Chat GUI - 選択画像: {os.path.basename(file_path)}")

    def send_message(self):
        """
        エントリに入力されたメッセージと、選択された画像を
        メインスクリプト（LLM バックエンド）へ渡し、応答を受けて表示する。
        """
        user_message = self.entry_message.get().strip()
        if not user_message and not self.selected_image_path:
            return

        # ユーザー投稿内容をチャットエリアに表示
        self.add_chat("User", user_message)

        # 入力欄と選択画像をリセット
        self.entry_message.delete(0, tk.END)
        self.selected_image_path = None
        self.title("Chat GUI")

    def add_chat(self, speaker: str, text: str):
        """
        チャットログ領域にメッセージを追加。
        """
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{speaker}: {text}\n\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
