import base64
import io
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, scrolledtext
import os
from PIL import Image, ImageTk

class ChatGUI(tk.Tk):
    """
    tkinter を使ったチャット風の GUI アプリ。
    「メッセージ送信」時のコールバックをメインルーチンから受け取り、
    結果を表示する。
    """
    def __init__(self):
        super().__init__()
        self.title("Chat GUI")
        self.geometry("700x500")

        # ---------- スタイル設定 ----------
        self.style = ttk.Style()
        # システムにあるテーマを指定 (clam, default, alt, etc.)
        self.style.theme_use("clam")

        # 背景色やボタンなどのスタイルを設定
        background_color = "#fafafa"
        accent_color = "#1a73e8"
        text_color = "#333333"
        font_family = "Helvetica"   # 好みのフォントに変更可 (例: "Century Gothic", "Arial")

        # フレームの背景色
        self.style.configure("TFrame", background=background_color)

        # ラベルのデザイン
        self.style.configure(
            "TLabel",
            background=background_color,
            foreground=text_color,
            font=(font_family, 11)
        )

        # ボタンのデザイン
        self.style.configure(
            "TButton",
            background=accent_color,
            foreground="#ffffff",
            font=(font_family, 10, "bold"),
            padding=6
        )

        # エントリーのデザイン
        self.style.configure(
            "TEntry",
            font=(font_family, 11),
            padding=5
        )

        # ウィンドウ全体の背景色を設定
        self.configure(bg=background_color)

        # ---------- 上部：チャット表示部 ----------
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

        # ---------- 下部：メッセージ入力＆プレビュー ----------
        bottom_frame = ttk.Frame(self, style="TFrame")
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        self.entry_message = ttk.Entry(bottom_frame, style="TEntry")
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_message.bind("<Return>", self.on_enter_key)

        self.button_attach = ttk.Button(bottom_frame, text="attach image", command=self.select_image, state=tk.DISABLED)
        self.button_attach.pack(side=tk.LEFT, padx=5)

        self.button_send = ttk.Button(bottom_frame, text="send", command=self.send_message)
        self.button_send.pack(side=tk.LEFT, padx=5)

        # プレビュー用フレーム
        preview_frame = ttk.Frame(self, style="TFrame")
        preview_frame.pack(fill=tk.X, padx=10, pady=5)

        self.label_image_preview = ttk.Label(preview_frame, text="", style="TLabel")
        self.label_image_preview.pack(side=tk.LEFT, padx=5)

        self.button_cancel_selection = ttk.Button(preview_frame, text="cancel", command=self.cancel_selection)
        self.button_cancel_selection.pack(side=tk.LEFT, padx=5)
        self.button_cancel_selection.config(state=tk.DISABLED)

        # --- フラグ＆データ ---
        self.user_input_flag = False
        self.user_message = None

        # base64 を保持するための変数
        self.user_image_b64 = None

        # 表示用のサムネイルオブジェクト
        self.selected_image_thumbnail = None
        self.thumbnail_refs = []

        # 画像送信が可能かどうかのフラグ
        self.can_send_images = False

        # テスト用: 実行時すぐに画像添付を許可（必要に応じて削除）
        self.enable_image_sending()

    def on_enter_key(self, event):
        self.send_message()
        return "break"

    def enable_image_sending(self):
        """
        何らかの条件が満たされ、画像送信を許可する。
        """
        self.can_send_images = True
        self.button_attach.config(state=tk.NORMAL)

    def select_image(self):
        """
        画像を選択する処理。
        実際にはファイルパスを使わず、base64化したバイナリを保持する。
        """
        if not self.can_send_images:
            self.add_chat("System", "image sending is not allowed yet.")
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            # ★ ファイルを開いてバイナリを読み込み & base64化
            with open(file_path, "rb") as f:
                raw_data = f.read()
                self.user_image_b64 = base64.b64encode(raw_data).decode("utf-8")

            # 選択された画像をプレビュー表示 (base64→PIL→PhotoImage化)
            self.update_image_preview(self.user_image_b64)
            self.button_cancel_selection.config(state=tk.NORMAL)

    def update_image_preview(self, image_b64: str):
        """
        base64文字列から画像を生成し、プレビューラベルに表示する。
        """
        try:
            # base64文字列をデコード → BytesIO に載せて Pillowで開く
            decoded_data = base64.b64decode(image_b64)
            img_io = io.BytesIO(decoded_data)
            img = Image.open(img_io)
            img.thumbnail((150, 150))
            self.selected_image_thumbnail = ImageTk.PhotoImage(img)

            self.label_image_preview.config(image=self.selected_image_thumbnail, text="")
        except Exception as e:
            self.label_image_preview.config(text=f"Preview failed: {e}", image="")

    def cancel_selection(self):
        """
        選択を解除し、プレビューを消す。
        """
        self.user_image_b64 = None
        self.selected_image_thumbnail = None
        self.label_image_preview.configure(text="", image="")
        self.button_cancel_selection.config(state=tk.DISABLED)

    def send_message(self):
        """
        送信ボタンが押されたときに発火。
        """
        if self.user_input_flag:
            return

        user_message = self.entry_message.get().strip()
        # 画像があるかどうかは user_image_b64 を見る
        if not user_message and not self.user_image_b64:
            return

        # チャット画面にユーザーの発言を表示
        self.add_chat("User", user_message, image_b64=self.user_image_b64)

        # 入力内容をクラス変数にセット
        self.user_message = user_message

        # フラグを立てて送信ボタンを無効化
        self.add_chat("System", text="Thinking...")
        self.set_input_in_progress(True)

        # 入力欄リセット
        self.entry_message.delete(0, tk.END)

        # 画像もリセット
        self.cancel_selection()

    def set_input_in_progress(self, in_progress: bool):
        self.user_input_flag = in_progress
        if in_progress:
            self.button_send.config(state=tk.DISABLED)
        else:
            self.button_send.config(state=tk.NORMAL)

    def add_chat(self, speaker: str, text: str, image_b64: str = None):
        """
        チャットログ領域にメッセージを追加。
        image_b64 があればサムネイルを表示。
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
                self.chat_display.insert(tk.END, f"\n[画像の読み込み失敗: {e}]\n")

        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

def main():
    app = ChatGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
