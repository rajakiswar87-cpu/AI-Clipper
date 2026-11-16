import tkinter as tk
from tkinter import filedialog, messagebox
import threading, sys, io, contextlib
from pathlib import Path
import clipper

class App:
    def __init__(self, root):
        self.root = root
        root.title('AI Clipper')
        root.geometry('620x500')
        root.resizable(False, False)
        tk.Label(root, text='AI Clipper', font=('Segoe UI', 20, 'bold')).pack(pady=(14, 8))
        self.video = tk.StringVar()
        self.output = tk.StringVar(value=str(Path.home() / 'Videos' / 'AI Clips'))
        self.count = tk.StringVar(value='5')
        self.length = tk.StringVar(value='30')
        self.keywords = tk.StringVar()
        self.vertical = tk.BooleanVar(value=True)
        self.row('Video file:', self.video, self.pick_video)
        self.row('Save clips in:', self.output, self.pick_output)
        form = tk.Frame(root); form.pack(fill='x', padx=24, pady=7)
        tk.Label(form, text='Number of clips:').grid(row=0, column=0, sticky='w')
        tk.Entry(form, textvariable=self.count, width=8).grid(row=0, column=1, padx=8, sticky='w')
        tk.Label(form, text='Target length (seconds):').grid(row=0, column=2, sticky='w', padx=(18,0))
        tk.Entry(form, textvariable=self.length, width=8).grid(row=0, column=3, padx=8, sticky='w')
        tk.Checkbutton(root, text='Make vertical videos (9:16)', variable=self.vertical).pack(anchor='w', padx=24, pady=4)
        kw = tk.Frame(root); kw.pack(fill='x', padx=24, pady=5)
        tk.Label(kw, text='Extra keywords (optional):').pack(anchor='w')
        tk.Entry(kw, textvariable=self.keywords, width=75).pack(fill='x', pady=4)
        self.button = tk.Button(root, text='CREATE CLIPS', command=self.start, font=('Segoe UI', 11, 'bold'), bg='#2478d4', fg='white')
        self.button.pack(pady=10)
        self.log = tk.Text(root, height=11, width=72, state='disabled', wrap='word')
        self.log.pack(padx=18, pady=6)
        tk.Label(root, text='FFmpeg and ffprobe must be installed on this PC. Lively moments are detected; virality is not guaranteed.', fg='gray').pack(pady=4)

    def row(self, label, var, command):
        f = tk.Frame(self.root); f.pack(fill='x', padx=24, pady=5)
        tk.Label(f, text=label, width=16, anchor='w').pack(side='left')
        tk.Entry(f, textvariable=var, width=52).pack(side='left', padx=4)
        tk.Button(f, text='Browse', command=command).pack(side='left')

    def pick_video(self):
        p = filedialog.askopenfilename(filetypes=[('Video files', '*.mp4 *.mov *.mkv *.avi'), ('All files', '*.*')])
        if p: self.video.set(p)

    def pick_output(self):
        p = filedialog.askdirectory()
        if p: self.output.set(p)

    def write(self, message):
        self.log.configure(state='normal'); self.log.insert('end', message); self.log.see('end'); self.log.configure(state='disabled')

    def start(self):
        if not self.video.get():
            messagebox.showwarning('Choose a video', 'Please select a video file first.'); return
        try:
            n, length = int(self.count.get()), float(self.length.get())
            if n < 1 or length <= 0: raise ValueError()
        except ValueError:
            messagebox.showerror('Check settings', 'Enter a positive clip count and target length.'); return
        self.button.config(state='disabled')
        self.log.configure(state='normal'); self.log.delete('1.0', 'end'); self.log.configure(state='disabled')
        args = (n, length, self.vertical.get(), self.keywords.get(), self.video.get(), self.output.get())
        threading.Thread(target=self.run_clipper, args=args, daemon=True).start()

    def run_clipper(self, n, length, vertical, keywords, video, output):
        old_argv = sys.argv[:]; buffer = io.StringIO()
        try:
            sys.argv = ['clipper.py', video, '--count', str(n), '--length', str(length), '--min', str(max(5, int(length * .75))), '--max', str(max(10, int(length * 1.25))), '--out', output]
            if vertical: sys.argv.append('--vertical')
            if keywords.strip(): sys.argv += ['--keywords', keywords.strip()]
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer): clipper.main()
            self.root.after(0, self.write, buffer.getvalue() + '\nFinished. Check your output folder.\n')
            self.root.after(0, lambda: messagebox.showinfo('Finished', 'Clip creation is complete.'))
        except SystemExit as e:
            self.root.after(0, self.write, buffer.getvalue() + '\n' + str(e) + '\n')
            self.root.after(0, lambda: messagebox.showerror('Could not create clips', str(e)))
        except Exception as e:
            self.root.after(0, self.write, buffer.getvalue() + '\nError: ' + str(e) + '\n')
            self.root.after(0, lambda: messagebox.showerror('Error', str(e)))
        finally:
            sys.argv = old_argv
            self.root.after(0, lambda: self.button.config(state='normal'))

if __name__ == '__main__':
    root = tk.Tk(); App(root); root.mainloop()
