import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import whisper
from opencc import OpenCC
import threading

class WhisperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("语音转文字工具")
        self.root.geometry("600x400")

        self.filename = None
        self.model = whisper.load_model("base")
        self.cc = OpenCC('t2s')  # 繁体转简体

        # UI 组件
        self.label = tk.Label(root, text="请选择音频/视频文件：", font=("微软雅黑", 12))
        self.label.pack(pady=10)

        self.btn_select = tk.Button(root, text="选择文件", command=self.select_file, font=("微软雅黑", 11))
        self.btn_select.pack(pady=5)

        self.btn_transcribe = tk.Button(root, text="开始转文字", command=self.run_transcribe_thread, font=("微软雅黑", 11))
        self.btn_transcribe.pack(pady=5)

        self.text_result = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("微软雅黑", 11))
        self.text_result.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def select_file(self):
        filetypes = [
            ("音频/视频文件", "*.mp3 *.wav *.mp4 *.m4a *.webm *.ogg"),
            ("所有文件", "*.*")
        ]
        self.filename = filedialog.askopenfilename(title="选择文件", filetypes=filetypes)
        if self.filename:
            self.text_result.insert(tk.END, f"已选择文件：{self.filename}\n")

    def run_transcribe_thread(self):
        thread = threading.Thread(target=self.transcribe)
        thread.start()

    def transcribe(self):
        if not self.filename:
            messagebox.showwarning("警告", "请先选择一个文件")
            return
        self.btn_transcribe.config(state=tk.DISABLED)
        self.text_result.insert(tk.END, "\n开始转录，请稍候...\n")
        try:
            result = self.model.transcribe(self.filename)
            text = result["text"]
            simplified = self.cc.convert(text)
            self.text_result.insert(tk.END, "\n转录结果（简体中文）：\n" + simplified + "\n")
        except Exception as e:
            messagebox.showerror("错误", f"转录失败：{e}")
        finally:
            self.btn_transcribe.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()
