# gui_app.py

import tkinter as tk
from tkinter import filedialog, scrolledtext
import os
from PIL import Image, ImageTk
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

        # 画像パスの一時保存
        self.selected_image_path = None
        # Enterキーで送信ボタンを押す
        self.entry_message.bind("<Return>", self.on_enter_key)

        # --- フラグ＆データ ---
        # ユーザー入力中フラグ (Trueなら送信完了待ちでボタン押下不可)
        self.user_input_flag = False
        # ユーザーの入力データを保持
        self.user_message = None
        self.user_image_path = None

        self.thumbnail_refs = []

    def on_enter_key(self, event):
        """
        Entry 上で Enter キーが押されたときに呼ばれる。
        送信ボタンを押したのと同じ処理を行う。
        """
        self.send_message()
        return "break"

    def select_image(self):
        """
        画像ファイルを選択し、そのサムネイルをチャット欄に表示する。
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            self.selected_image_path = file_path
            self.title(f"選択画像: {os.path.basename(file_path)}")

            # 選択したことをチャット欄に表示 (System発言として)
            self.add_chat(
                speaker="System",
                text="画像が選択されました。",
                image_path=file_path  # 選択直後のサムネイルを表示
            )

    def send_message(self):
        """
        送信ボタンが押されたときに発火。
        フラグが立っていない場合だけ処理し、押したらフラグを立ててボタンを無効化する。
        """
        if self.user_input_flag:
            # すでにフラグが立っているなら押せない
            return

        # メッセージが空か & 画像がない場合は送信しない
        user_message = self.entry_message.get().strip()
        if not user_message and not self.selected_image_path:
            return

        # チャット画面にユーザーの発言を表示
        self.add_chat("User", user_message, image_path=self.selected_image_path)

        # 入力データを変数にセット
        self.user_message = user_message
        self.user_image_path = self.selected_image_path

        # フラグを立てて送信ボタンを無効化
        self.add_chat("System", text="Thinking...")
        self.set_input_in_progress(True)

        # 入力欄リセット
        self.entry_message.delete(0, tk.END)
        self.selected_image_path = None
        self.title("Chat GUI")

    def set_input_in_progress(self, in_progress: bool):
        """
        フラグを管理し、True ならボタンを無効化、False なら再度有効化する。
        """
        self.user_input_flag = in_progress
        if in_progress:
            self.button_send.config(state=tk.DISABLED)
        else:
            self.button_send.config(state=tk.NORMAL)


    def add_chat(self, speaker: str, text: str, image_path: str =None):
        """
        チャットログ領域にメッセージを追加。
        """
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{speaker}: {text}\n\n")
        if image_path:
            try:
                img = Image.open(image_path)
                img.thumbnail((150, 150))  # 150x150ピクセルに縮小 (適宜調整)
                photo = ImageTk.PhotoImage(img)

                # 画像参照をリストに保存 (GC回避)
                self.thumbnail_refs.append(photo)

                # チャット欄に画像を埋め込み表示
                self.chat_display.image_create(tk.END, image=photo)

            except Exception as e:
                self.chat_display.insert(tk.END, f"\n[画像の読み込み失敗: {e}]\n")

        # 改行を入れて余白を作る
        self.chat_display.insert(tk.END, "\n\n")

        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
