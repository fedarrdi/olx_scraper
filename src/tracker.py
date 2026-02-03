import aiohttp
import asyncio
import datetime
import json
import csv
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import time

class ClassTracker:
    def __init__(self):
        self.tracked = {}  # dict[str, set[str]]

    def add(self, url: str, selector: str):
        if url not in self.tracked:
            self.tracked[url] = {selector}
            return 1
        if selector in self.tracked[url]:
            return 0
        self.tracked[url].add(selector)
        return 2

    def remove_url(self, url: str):
        return self.tracked.pop(url, None) is not None

    def remove_selector(self, url: str, selector: str):
        if url in self.tracked and selector in self.tracked[url]:
            self.tracked[url].remove(selector)
            if not self.tracked[url]:
                del self.tracked[url]
            return True
        return False

    def extract_from_html(self, url: str, html: str) -> dict:
        soup = BeautifulSoup(html, "lxml")
        result = {}
        for selector in self.tracked[url]:
            elements = soup.select(selector)

            print(elements)
            result[selector] = [el.get_text(separator=" ", strip=True) for el in elements]
        return result

    async def fetch(self, session: aiohttp.ClientSession, url: str, timeout: int = 10) -> str:
        try:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                return await response.text()
        except Exception:
            return None

    async def extract_all_async(self, timeout: int = 10) -> dict:
        all_data = {}
        if not self.tracked:
            return all_data

        timestamp = datetime.datetime.now().isoformat()

        async with aiohttp.ClientSession() as session:
            fetch_coroutines = [self.fetch(session, url, timeout) for url in self.tracked]
            html_pages = await asyncio.gather(*fetch_coroutines)

            for url, html in zip(self.tracked.keys(), html_pages):
                if html is not None:
                    all_data[url] = self.extract_from_html(url, html)
                    #self.save_fetched_html(url, html, timestamp)
                else:
                    all_data[url] = None  # Неуспешно извличане

        return all_data

    def save_fetched_html(self, url: str, html: str, timestamp: str):
        import os

        # Създаваме безопасно име от URL (премахваме протокол и опасни символи)
        safe_url = url.removeprefix("https://").removeprefix("http://")
        for invalid in r'\/:*?"<>|':
            safe_url = safe_url.replace(invalid, "_")
        safe_url = safe_url[:150]
        if not safe_url:
            safe_url = "unknown_url"

        # Безопасно име за timestamp (заменяме : и . с _)
        timestamp_safe = timestamp.replace(":", "_").replace(".", "_")

        filename = f"{safe_url}_{timestamp_safe}.html"
        folder = "saved_htmls"
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[DEBUG] Запазен HTML за {url} в {path}")
        except Exception as e:
            print(f"[ERROR] Неуспешно запазване на HTML за {url}: {e}")


    def save_to_json(self, data: dict, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_from_json(self, filename: str) -> dict:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_to_csv(self, data: dict, filename: str):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "url", "selector", "text"])
            for timestamp, urls in data.items():
                for url, selectors in urls.items():
                    if selectors:
                        for selector, texts in selectors.items():
                            for text in texts:
                                writer.writerow([timestamp, url, selector, text])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Проследяване на уеб елементи")
        self.geometry("1100x800")
        self.tracker = ClassTracker()
        self.data_store = {}
        self.running = False
        self.thread = None
        self.q = queue.Queue()

        self.create_widgets()
        self.update_tracked_tree()
        self.update_data_display()
        self.check_queue()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tab_tracked = ttk.Frame(notebook)
        tab_data = ttk.Frame(notebook)
        tab_log = ttk.Frame(notebook)

        notebook.add(tab_tracked, text="Проследявани")
        notebook.add(tab_data, text="Данни")
        notebook.add(tab_log, text="Лог")

        # === Таб "Проследявани" ===
        add_frame = ttk.LabelFrame(tab_tracked, text="Добавяне на URL и селектор")
        add_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(add_frame, text="URL:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_url = ttk.Entry(add_frame, width=80)
        self.entry_url.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="CSS селектор:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_selector = ttk.Entry(add_frame, width=60)
        self.entry_selector.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(add_frame, text="Добави", command=self.add_tracked).grid(row=2, column=1, pady=10, sticky="e")

        # Treeview
        tree_frame = ttk.Frame(tab_tracked)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree.heading("#0", text="URL / Селектор")
        self.tree.column("#0", width=800)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Бутони за управление
        control_frame = ttk.Frame(tab_tracked)
        control_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(control_frame, text="Премахни избран елемент", command=self.remove_selected).pack(side="left", padx=5)

        # Периодично извличане
        periodic_frame = ttk.LabelFrame(tab_tracked, text="Периодично извличане")
        periodic_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(periodic_frame, text="Интервал (секунди):").pack(side="left", padx=5)
        self.entry_interval = ttk.Entry(periodic_frame, width=10)
        self.entry_interval.insert(0, "300")
        self.entry_interval.pack(side="left", padx=5)

        self.btn_start = ttk.Button(periodic_frame, text="Стартирай", command=self.start_periodic)
        self.btn_start.pack(side="left", padx=10)

        self.btn_stop = ttk.Button(periodic_frame, text="Спри", command=self.stop_periodic, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        ttk.Button(periodic_frame, text="Извлечи веднъж", command=self.manual_extract).pack(side="left", padx=20)

        # === Таб "Данни" ===
        self.data_text = scrolledtext.ScrolledText(tab_data, wrap="word")
        self.data_text.pack(fill="both", expand=True, padx=10, pady=10)

        save_frame = ttk.Frame(tab_data)
        save_frame.pack(pady=10)

        ttk.Button(save_frame, text="Запиши в JSON", command=self.save_json).pack(side="left", padx=10)
        ttk.Button(save_frame, text="Запиши в CSV", command=self.save_csv).pack(side="left", padx=10)
        ttk.Button(save_frame, text="Зареди от JSON", command=self.load_json).pack(side="left", padx=10)

        # === Таб "Лог" ===
        self.log_text = scrolledtext.ScrolledText(tab_log)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def update_tracked_tree(self):
        self.tree.delete(*self.tree.get_children())
        for url, selectors in self.tracker.tracked.items():
            url_item = self.tree.insert("", "end", iid=url, text=url, open=True)
            for sel in sorted(selectors):
                self.tree.insert(url_item, "end", text=sel)

    def update_data_display(self):
        self.data_text.delete("1.0", tk.END)
        if self.data_store:
            self.data_text.insert(tk.END, json.dumps(self.data_store, ensure_ascii=False, indent=4))
        else:
            self.data_text.insert(tk.END, "Все още няма събрани данни.")

    def add_tracked(self):
        url = self.entry_url.get().strip()
        selector = self.entry_selector.get().strip()
        if not url or not selector:
            messagebox.showerror("Грешка", "Моля, попълнете и двете полета.")
            return

        status = self.tracker.add(url, selector)
        if status == 0:
            self.log(f"Внимание: Селекторът '{selector}' вече съществува за {url}.")
        elif status == 1:
            self.log(f"Добавен нов URL: {url} с селектор '{selector}'.")
        elif status == 2:
            self.log(f"Добавен селектор '{selector}' към съществуващ URL {url}.")

        self.update_tracked_tree()
        self.entry_url.delete(0, tk.END)
        self.entry_selector.delete(0, tk.END)

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Моля, изберете елемент за премахване.")
            return

        item = selected[0]
        parent = self.tree.parent(item)

        if parent == "":  # URL
            url = self.tree.item(item, "text")
            if messagebox.askyesno("Потвърждение", f"Премахване на URL {url} и всички негови селектори?"):
                self.tracker.remove_url(url)
                self.tree.delete(item)
                self.log(f"Премахнат URL: {url}")
        else:  # Селектор
            selector = self.tree.item(item, "text")
            url = self.tree.item(parent, "text")
            if messagebox.askyesno("Потвърждение", f"Премахване на селектор '{selector}' от {url}?"):
                self.tracker.remove_selector(url, selector)
                self.tree.delete(item)
                self.log(f"Премахнат селектор '{selector}' от {url}")
                if not self.tree.get_children(parent):
                    self.tree.delete(parent)

        self.update_tracked_tree()

    def check_queue(self):
        try:
            while True:
                item = self.q.get_nowait()
                if isinstance(item, str):
                    self.log(item)
                elif isinstance(item, tuple):
                    timestamp, data = item
                    self.data_store[timestamp] = data
                    self.update_data_display()
        except queue.Empty:
            pass
        self.after(200, self.check_queue)

    def single_extract(self):
        timestamp = datetime.datetime.now().isoformat()
        self.q.put(f"[{timestamp}] Ръчно извличане започна...")
        try:
            data = asyncio.run(self.tracker.extract_all_async())
            self.q.put((timestamp, data))
            self.q.put(f"[{timestamp}] Ръчно извличане завърши успешно.")
        except Exception as e:
            self.q.put(f"[{timestamp}] Грешка при ръчно извличане: {e}")

    def manual_extract(self):
        if not self.tracker.tracked:
            messagebox.showinfo("Информация", "Няма добавени URL-и за извличане.")
            return
        threading.Thread(target=self.single_extract, daemon=True).start()

    def periodic_task(self, interval):
        while self.running:
            timestamp = datetime.datetime.now().isoformat()
            self.q.put(f"[{timestamp}] Периодично извличане започна...")
            try:
                data = asyncio.run(self.tracker.extract_all_async())
                self.q.put((timestamp, data))
                self.q.put(f"[{timestamp}] Периодично извличане завърши.")
            except Exception as e:
                self.q.put(f"[{timestamp}] Грешка при периодично извличане: {e}")
            time.sleep(interval)

    def start_periodic(self):
        if self.running:
            return
        if not self.tracker.tracked:
            messagebox.showinfo("Информация", "Добавете поне един URL преди да стартирате периодичното извличане.")
            return

        try:
            interval = int(self.entry_interval.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Грешка", "Моля, въведете положително цяло число за интервал.")
            return

        self.running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.thread = threading.Thread(target=self.periodic_task, args=(interval,), daemon=True)
        self.thread.start()
        self.log(f"Периодично извличане стартирано с интервал {interval} секунди.")

    def stop_periodic(self):
        self.running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.log("Периодичното извличане е спряно.")

    def save_json(self):
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON файлове", "*.json")])
        if file:
            self.tracker.save_to_json(self.data_store, file)
            self.log(f"Данните са записани в JSON: {file}")

    def save_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV файлове", "*.csv")])
        if file:
            self.tracker.save_to_csv(self.data_store, file)
            self.log(f"Данните са записани в CSV: {file}")

    def load_json(self):
        file = filedialog.askopenfilename(filetypes=[("JSON файлове", "*.json")])
        if file:
            try:
                self.data_store = self.tracker.load_from_json(file)
                self.update_data_display()
                self.log(f"Данните са заредени от: {file}")
            except Exception as e:
                messagebox.showerror("Грешка", f"Неуспешно зареждане: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()