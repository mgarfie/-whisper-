import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, messagebox
import whisper
from opencc import OpenCC
import threading
import os
import subprocess
import sys

class WhisperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("语音转文字工具")
        self.root.geometry("750x550")
        self.root.resizable(False, False)

        self.model = whisper.load_model("base")
        self.cc = OpenCC('t2s')

        self.file_list = []
        self.last_filename = None

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding="10 10 10 10")
        frame.pack(fill=tk.BOTH, expand=True)

        self.btn_select = ttk.Button(frame, text="选择多个音频/视频文件", command=self.select_files)
        self.btn_select.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.btn_transcribe = ttk.Button(frame, text="开始批量转文字", command=self.run_transcribe_thread)
        self.btn_transcribe.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.btn_save = ttk.Button(frame, text="保存 TXT（可编辑后保存）", command=self.save_to_txt)
        self.btn_save.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.text_result = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, font=("微软雅黑", 11), height=25
        )
        self.text_result.grid(row=1, column=0, columnspan=3, pady=10, sticky="nsew")

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def select_files(self):
        filetypes = [("音频/视频文件", "*.mp3 *.wav *.mp4 *.m4a *.webm *.ogg"), ("所有文件", "*.*")]
        self.file_list = list(filedialog.askopenfilenames(title="选择多个文件", filetypes=filetypes))
        if self.file_list:
            self.text_result.insert(tk.END, f"\n已选择 {len(self.file_list)} 个文件\n")

    def run_transcribe_thread(self):
        if not self.file_list:
            self.text_result.insert(tk.END, "请先选择文件！\n")
            return
        threading.Thread(target=self.transcribe_files).start()

    def transcribe_files(self):
        self.btn_transcribe.config(state=tk.DISABLED)
        self.text_result.insert(tk.END, "\n开始转录...\n")

        combined_text = ""
        for file in self.file_list:
            try:
                self.text_result.insert(tk.END, f"\n正在处理：{file}\n")
                result = self.model.transcribe(file)
                text = self.cc.convert(result["text"])
                combined_text += f"\n【{os.path.basename(file)}】\n{text}\n" + "-" * 50 + "\n"
                self.text_result.insert(tk.END, f"{text}\n" + "-" * 50 + "\n")
                self.last_filename = os.path.basename(file)
            except Exception as e:
                self.text_result.insert(tk.END, f"\n[错误] {file} 转录失败：{e}\n")

        self.text_result.insert(tk.END, "\n所有文件已转录完成。\n")
        self.btn_transcribe.config(state=tk.NORMAL)

    def save_to_txt(self):
        content = self.text_result.get("1.0", tk.END).strip()
        if not content:
            self.text_result.insert(tk.END, "没有内容可保存，请先转录或编辑。\n")
            return
        default_name = (self.last_filename or "transcript").replace(" ", "_") + "_edited.txt"
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("文本文件", "*.txt")],
                                                 initialfile=default_name)
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.open_file(file_path)
            except Exception as e:
                self.text_result.insert(tk.END, f"保存失败：{e}\n")

    def open_file(self, path):
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', path])
        except Exception as e:
            self.text_result.insert(tk.END, f"无法打开文件：{e}\n")

    def on_closing(self):
        if messagebox.askokcancel("退出确认", "确定要退出程序吗？"):
            try:
                del self.model
            except:
                pass
            self.file_list = []
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure("TButton", font=("微软雅黑", 10), padding=6)
    app = WhisperApp(root)
    root.mainloop()
