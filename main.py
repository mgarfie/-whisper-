import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from zipfile import ZipFile
import whisper
from opencc import OpenCC

class WhisperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("语音转文字工具（使用 large 离线模型）")
        self.root.geometry("700x500")

        self.cc = OpenCC('t2s')  # 繁体转简体
        self.file_list = []
        self.transcribed_texts = []
        self.model_name = "large"
        self.model = self.load_whisper_model_with_check(self.model_name)

        self.setup_ui()

    def setup_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Button(frame, text="选择文件", command=self.select_files, width=15).grid(row=0, column=0, padx=5)
        tk.Button(frame, text="开始转录", command=self.run_transcribe_thread, width=15).grid(row=0, column=1, padx=5)
        tk.Button(frame, text="保存文本", command=self.save_text, width=15).grid(row=0, column=2, padx=5)

        self.progress = ttk.Progressbar(self.root, length=600, mode="determinate")
        self.progress.pack(pady=5)

        self.text_result = scrolledtext.ScrolledText(self.root, font=("微软雅黑", 11))
        self.text_result.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def select_files(self):
        filetypes = [("音频/视频文件", "*.mp3 *.wav *.mp4 *.m4a *.webm *.ogg"), ("所有文件", "*.*")]
        files = filedialog.askopenfilenames(title="选择多个音频/视频文件", filetypes=filetypes)
        if files:
            self.file_list = list(files)
            self.transcribed_texts = []
            self.text_result.delete("1.0", tk.END)
            self.text_result.insert(tk.END, "已选择文件:\n")
            for f in self.file_list:
                self.text_result.insert(tk.END, f"{f}\n")

    def run_transcribe_thread(self):
        if not self.file_list:
            messagebox.showwarning("警告", "请先选择文件")
            return
        threading.Thread(target=self.transcribe_all_files, daemon=True).start()

    def transcribe_all_files(self):
        self.text_result.insert(tk.END, "\n开始转录多个文件...\n")
        self.transcribed_texts = []
        total_files = len(self.file_list)
        self.progress["maximum"] = total_files
        self.progress["value"] = 0

        for idx, f in enumerate(self.file_list, 1):
            self.text_result.insert(tk.END, f"\n[{idx}/{total_files}] 正在转录: {f}\n")
            self.text_result.see(tk.END)
            try:
                result = self.model.transcribe(f)
                text = result["text"]
                simplified = self.cc.convert(text)
                self.transcribed_texts.append(simplified)
                self.text_result.insert(tk.END, simplified + "\n")
            except Exception as e:
                self.text_result.insert(tk.END, f"转录失败: {e}\n")
            self.progress["value"] = idx
            self.progress.update()
            self.text_result.see(tk.END)

        self.text_result.insert(tk.END, "\n所有文件转录完成。\n")

    def save_text(self):
        if not self.transcribed_texts:
            messagebox.showwarning("警告", "没有转录文本可保存")
            return
        text_to_save = self.text_result.get("1.0", tk.END).strip()
        if not text_to_save:
            messagebox.showwarning("警告", "预览区没有内容")
            return
        save_path = filedialog.asksaveasfilename(
            title="保存文本文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text_to_save)
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}")
            else:
                self.root.title(f"语音转文字工具 - 已保存: {os.path.basename(save_path)}")

    def on_closing(self):
        self.file_list.clear()
        self.transcribed_texts.clear()
        self.root.destroy()

    def get_whisper_cache_path(self):
        if sys.platform == "win32":
            user_profile = os.getenv("USERPROFILE")
            path = os.path.join(user_profile, ".cache", "whisper")
        else:
            home = os.path.expanduser("~")
            path = os.path.join(home, ".cache", "whisper")
        return path

    def model_exists(self, model_name):
        cache_path = self.get_whisper_cache_path()
        model_path = os.path.join(cache_path, model_name)
        return os.path.isdir(model_path)

    def extract_model_from_zip(self, model_name):
        cache_path = self.get_whisper_cache_path()
        model_path = os.path.join(cache_path, model_name)
        if not os.path.exists(model_path):
            os.makedirs(model_path, exist_ok=True)
            zip_path = os.path.join(os.getcwd(), f"{model_name}.zip")
            if not os.path.exists(zip_path):
                messagebox.showerror("错误", f"未找到模型压缩包：{zip_path}")
                return False
            try:
                with ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(model_path)
                return True
            except Exception as e:
                messagebox.showerror("错误", f"模型解压失败：{e}")
                return False
        return True

    def load_whisper_model_with_check(self, model_name):
        if not self.model_exists(model_name):
            result = messagebox.askokcancel(
                "模型提取",
                f"未检测到模型文件夹 '{model_name}'，是否从本地 zip 解压模型？"
            )
            if not result:
                sys.exit("用户取消模型提取，程序退出")
            if not self.extract_model_from_zip(model_name):
                sys.exit("模型解压失败，程序退出")
        return whisper.load_model(model_name)

if __name__ == "__main__":
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()
