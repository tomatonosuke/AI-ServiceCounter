# gui_app.py

import tkinter as tk
import tkinter.ttk as ttk
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
        # Windowsなどで background が反映されない場合は、以下のオプションを適宜調整要
        # self.style.map("TButton", background=[("active", "#1669c1")])

        # エントリーのデザイン
        self.style.configure(
            "TEntry",
            font=(font_family, 11),
            padding=5
        )

        # ウィンドウ全体の背景色を設定
        self.configure(bg=background_color)

        # ---------- 上部：チャット表示部 ----------
        # tk の ScrolledText にフォントなどを直接設定する
        self.chat_display = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=(font_family, 11),
            bg="#ffffff",       # 背景は白
            fg=text_color,      # 文字色
            relief=tk.FLAT,     # 枠線をフラットに
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#e0e0e0"  # 薄いグレーで枠を付ける
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chat_display.config(state="disabled")

        # ---------- 下部：メッセージ入力＆プレビュー ----------
        # フレームでまとめる
        bottom_frame = ttk.Frame(self, style="TFrame")
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        # 入力欄 (ttk.Entry)
        self.entry_message = ttk.Entry(bottom_frame, style="TEntry")
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_message.bind("<Return>", self.on_enter_key)

        # 画像選択ボタン
        self.button_attach = ttk.Button(bottom_frame, text="attach image", command=self.select_image, state=tk.DISABLED)
        self.button_attach.pack(side=tk.LEFT, padx=5)

        # 送信ボタン
        self.button_send = ttk.Button(bottom_frame, text="send", command=self.send_message)
        self.button_send.pack(side=tk.LEFT, padx=5)

        # プレビュー用フレーム
        preview_frame = ttk.Frame(self, style="TFrame")
        preview_frame.pack(fill=tk.X, padx=10, pady=5)
        self.button_attach.config(state=tk.NORMAL)

        # サムネイル表示ラベル
        self.label_image_preview = ttk.Label(preview_frame, text="", style="TLabel")
        self.label_image_preview.pack(side=tk.LEFT, padx=5)

        # 画像選択を取り消すボタン
        self.button_cancel_selection = ttk.Button(preview_frame, text="cancel", command=self.cancel_selection)
        self.button_cancel_selection.pack(side=tk.LEFT, padx=5)
        self.button_cancel_selection.config(state=tk.DISABLED)


        # --- フラグ＆データ ---
        # ユーザー入力中フラグ (Trueなら送信完了待ちでボタン押下不可)
        self.user_input_flag = False
        # ユーザーの入力データを保持
        self.user_message = None
        self.user_image_path = None

        self.selected_image_path = None
        self.selected_image_thumbnail = None

        self.thumbnail_refs = []

        self.can_send_images = False

    def on_enter_key(self, event):
        """
        Entry 上で Enter キーが押されたときに呼ばれる。
        送信ボタンを押したのと同じ処理を行う。
        """
        self.send_message()
        return "break"

    def enable_image_sending(self):
        """
        何らかの条件が満たされ、フラグを立てるときに呼ぶ。
        """
        self.can_send_images = True
        self.button_attach.config(state=tk.NORMAL)

    def select_image(self):
        """
        画像を選択する処理。フラグがFalseなら選択できないようにする。
        """
        if not self.can_send_images:
            self.add_chat("System", "image sending is not allowed yet.")
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            self.selected_image_path = file_path
            self.update_image_preview(file_path)
            self.button_cancel_selection.config(state=tk.NORMAL)

    def update_image_preview(self, image_path):
        """
        指定した画像パスをサムネイル化して、プレビューラベルに表示する。
        """
        try:
            img = Image.open(image_path)
            img.thumbnail((150, 150))
            self.selected_image_thumbnail = ImageTk.PhotoImage(img)
            self.label_image_preview.config(image=self.selected_image_thumbnail, text="")
        except Exception as e:
            self.label_image_preview.config(text=f"Preview failed: {e}", image="")

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

    def cancel_selection(self):
        self.selected_image_path = None
        self.selected_image_thumbnail = None
        self.label_image_preview.configure(text="", image="")
        self.button_cancel_selection.config(state=tk.DISABLED)

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
