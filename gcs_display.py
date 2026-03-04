import serial
import serial.tools.list_ports
import csv
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import collections
import tkintermapview
from datetime import datetime
import time
import math
import os
import threading

# --- นำเข้า AI ของ Google ---
try:
    import google.generativeai as genai
    HAS_AI = True
except ImportError:
    HAS_AI = False

#ใส่ API KEY ของคุณตรงนี้ (เอาคีย์ ...WEy0 มาใส่)

GEMINI_API_KEY = "AIzaSyCNEJCy0FXp8l-umw7iYCViBkkfZdVWEy0" 

if HAS_AI and len(GEMINI_API_KEY) > 20:
    genai.configure(api_key=GEMINI_API_KEY)

# --- ตั้งค่า Baud Rate และแบตเตอรี่ ---
BAUD_RATE = 115200
MAX_BATTERY_VOLTAGE = 9.0 

# --- Color Palette ---
BG_MAIN = "#0B0F19"
BG_CARD = "#1A2235"
TEXT_MAIN = "#E2E8F0"
ACCENT_CYAN = "#00F2FE"
ACCENT_PINK = "#FE0979"
ACCENT_GREEN = "#39FF14"
ACCENT_WARN = "#FFB300"
ACCENT_DIM = "#94A3B8"
ACCENT_RED = "#FF3B30"

class PlanetaryGCS:
    def __init__(self, window):
        self.window = window
        self.window.title("Planetary Impactor - AI Ground Control System")
        self.window.geometry("1280x850") 
        self.window.configure(bg=BG_MAIN)

        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=BG_MAIN, borderwidth=0)
        style.configure('TNotebook.Tab', background=BG_CARD, foreground=TEXT_MAIN, font=('Segoe UI', 12, 'bold'), padding=[20, 8], borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', ACCENT_CYAN)], foreground=[('selected', BG_MAIN)])

        self.max_pts = 50
        self.history = {
            "Temperature": collections.deque([0]*self.max_pts, maxlen=self.max_pts),
            "Pressure": collections.deque([0]*self.max_pts, maxlen=self.max_pts),
            "Altitude": collections.deque([0]*self.max_pts, maxlen=self.max_pts)
        }
        self.current_graph = "Altitude" 
        self.prev_alt = 0.0
        self.max_alt = 0.0       
        self.packet_count = 0
        self.start_time = None
        self.end_time = None # เพิ่มตัวแปรเก็บเวลาตอนจบ
        self.is_connected = False
        self.log_filename = ""   

        # ================= ส่วนหัว (Header) =================
        header_frame = tk.Frame(window, bg=BG_MAIN)
        header_frame.pack(fill=tk.X, pady=15, padx=20)
        tk.Label(header_frame, text="🛰️ PLANETARY IMPACTOR", font=("Segoe UI Black", 24), bg=BG_MAIN, fg=ACCENT_CYAN).pack(side=tk.LEFT)
        
        time_frame = tk.Frame(header_frame, bg=BG_MAIN)
        time_frame.pack(side=tk.RIGHT)
        self.lbl_met = tk.Label(time_frame, text="MET: 00:00:00", font=("Consolas", 18, "bold"), bg=BG_MAIN, fg=ACCENT_WARN)
        self.lbl_met.pack(side=tk.LEFT, padx=15)
        self.lbl_clock = tk.Label(time_frame, text="SYS: 00:00:00", font=("Consolas", 18, "bold"), bg=BG_MAIN, fg=TEXT_MAIN)
        self.lbl_clock.pack(side=tk.LEFT)
        self.update_clock() 

        # --- พื้นที่หลัก ---
        self.main_frame = tk.Frame(window, bg=BG_MAIN)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # ================= บล็อกซ้าย (เหมือนเดิม) =================
        self.left_frame = tk.Frame(self.main_frame, bg=BG_CARD, bd=0, highlightbackground="#2A3441", highlightthickness=1)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15), ipadx=15, ipady=15)

        status_frame = tk.Frame(self.left_frame, bg=BG_CARD)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.lbl_state = tk.Label(status_frame, text="STATUS: STANDBY", font=("Segoe UI", 16, "bold"), bg=BG_CARD, fg=ACCENT_DIM)
        self.lbl_state.pack(anchor="w")
        
        info_frame = tk.Frame(status_frame, bg=BG_CARD)
        info_frame.pack(fill=tk.X, pady=5)
        self.lbl_max_alt = tk.Label(info_frame, text="🏆 MAX ALT: 0.0 m", font=("Consolas", 11, "bold"), bg=BG_CARD, fg=ACCENT_WARN)
        self.lbl_max_alt.pack(side=tk.LEFT)
        self.lbl_packets = tk.Label(info_frame, text="PKTS: 0", font=("Consolas", 11, "bold"), bg=BG_CARD, fg=ACCENT_DIM)
        self.lbl_packets.pack(side=tk.RIGHT)

        self.lbl_ai_warning = tk.Label(self.left_frame, text="🟢 SYSTEM NORMAL", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_GREEN)
        self.lbl_ai_warning.pack(fill=tk.X, pady=5)

        tk.Frame(self.left_frame, bg="#2A3441", height=1).pack(fill=tk.X, pady=5)

        self.data_labels = {}
        fields = [
            ("Temperature", "°C"), ("Pressure", "Pa"), ("Altitude", "m"),
            ("GPS Lat", ""), ("GPS Lon", ""), 
            ("Accel X", ""), ("Accel Y", ""), ("Accel Z", ""),
            ("Pitch", "°"), ("Roll", "°"),
            ("Voltage", "V")
        ]
        
        data_container = tk.Frame(self.left_frame, bg=BG_CARD)
        data_container.pack(fill=tk.X)

        for i, (name, unit) in enumerate(fields):
            tk.Label(data_container, text=f"{name}:", font=("Segoe UI", 11), bg=BG_CARD, fg=ACCENT_DIM).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            lbl = tk.Label(data_container, text=f"--- {unit}", font=("Consolas", 12, "bold"), bg=BG_CARD, fg=TEXT_MAIN)
            lbl.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.data_labels[name] = lbl

        self.batt_canvas = tk.Canvas(self.left_frame, width=200, height=15, bg=BG_CARD, highlightthickness=0)
        self.batt_canvas.pack(pady=(10, 5))
        self.batt_canvas.create_rectangle(2, 2, 190, 13, outline=ACCENT_DIM, width=2)
        self.batt_canvas.create_rectangle(190, 4, 196, 11, fill=ACCENT_DIM)
        self.batt_fill = self.batt_canvas.create_rectangle(4, 4, 4, 11, fill=ACCENT_GREEN)

        port_frame = tk.Frame(self.left_frame, bg=BG_CARD)
        port_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Label(port_frame, text="PORT:", font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg=ACCENT_DIM).pack(side=tk.LEFT)
        self.port_combo = ttk.Combobox(port_frame, font=("Consolas", 11), state="readonly", width=10)
        self.port_combo.pack(side=tk.LEFT, padx=(5, 5))
        tk.Button(port_frame, text="🔄", bg=BG_CARD, fg=TEXT_MAIN, bd=0, cursor="hand2", command=self.refresh_ports).pack(side=tk.LEFT)
        self.refresh_ports()

        btn_action_frame = tk.Frame(self.left_frame, bg=BG_CARD)
        btn_action_frame.pack(fill=tk.X, pady=(15, 10))
        
        self.btn_connect = tk.Button(btn_action_frame, text="CONNECT", font=("Segoe UI", 11, "bold"), bg=ACCENT_CYAN, fg=BG_MAIN, bd=0, cursor="hand2", command=self.start_serial)
        self.btn_connect.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2), ipady=6)
        
        self.btn_disconnect = tk.Button(btn_action_frame, text="DISCONNECT", font=("Segoe UI", 11, "bold"), bg="#3F1D24", fg=ACCENT_PINK, bd=0, cursor="hand2", state="disabled", command=self.stop_serial)
        self.btn_disconnect.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0), ipady=6)

        self.btn_ai_report = tk.Button(self.left_frame, text="🤖 GENERATE AI REPORT", font=("Segoe UI", 11, "bold"), bg="#6C5CE7", fg=TEXT_MAIN, bd=0, cursor="hand2", command=self.trigger_ai_report)

        tk.Label(self.left_frame, text=">_ RAW TELEMETRY", font=("Consolas", 10, "bold"), bg=BG_CARD, fg=ACCENT_DIM).pack(anchor="w")
        self.raw_term = tk.Text(self.left_frame, height=5, bg="#05080E", fg=ACCENT_GREEN, font=("Consolas", 9), bd=0, state="disabled")
        self.raw_term.pack(fill=tk.X, pady=(2, 0))

        # ================= บล็อกขวา (แท็บต่างๆ) =================
        self.right_frame = tk.Frame(self.main_frame, bg=BG_MAIN)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 📈 แท็บ 1: กราฟ
        self.tab_graph = tk.Frame(self.notebook, bg=BG_CARD)
        self.notebook.add(self.tab_graph, text=" 📈 DATA GRAPHS ")

        btn_frame = tk.Frame(self.tab_graph, bg=BG_CARD)
        btn_frame.pack(fill=tk.X, pady=15, padx=10)

        btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": BG_MAIN, "bd": 0, "padx": 15, "pady": 6, "cursor": "hand2"}
        tk.Button(btn_frame, text="Altitude", bg=ACCENT_CYAN, command=lambda: self.set_graph("Altitude"), **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Temperature", bg=ACCENT_PINK, command=lambda: self.set_graph("Temperature"), **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Pressure", bg=ACCENT_GREEN, command=lambda: self.set_graph("Pressure"), **btn_style).pack(side=tk.LEFT, padx=5)

        self.fig = Figure(figsize=(7, 5), dpi=100, facecolor=BG_CARD)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(BG_MAIN) 
        self.line, = self.ax.plot(self.history[self.current_graph], color=ACCENT_CYAN, linewidth=2.5)
        self.ax.set_title(f"LIVE: {self.current_graph.upper()}", color=TEXT_MAIN, fontname="Segoe UI", fontsize=12, pad=10)
        self.ax.tick_params(colors=ACCENT_DIM)
        for spine in ['bottom', 'top', 'right', 'left']:
            self.ax.spines[spine].set_color('#2A3441')
        self.ax.grid(True, color='#2A3441', linestyle='--', alpha=0.7)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_graph)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        # 🗺️ แท็บ 2: แผนที่
        self.tab_map = tk.Frame(self.notebook, bg=BG_CARD)
        self.notebook.add(self.tab_map, text=" 🗺️ MISSION MAP ")

        self.map_widget = tkintermapview.TkinterMapView(self.tab_map, corner_radius=0)
        self.map_widget.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.map_widget.set_position(13.7563, 100.5018) 
        self.map_widget.set_zoom(15)
        self.marker = None

        # 💬 แท็บ 3: AI COPILOT (แท็บใหม่!)
        self.tab_chat = tk.Frame(self.notebook, bg=BG_CARD)
        self.notebook.add(self.tab_chat, text=" 💬 AI COPILOT ")

        self.chat_display = tk.Text(self.tab_chat, bg=BG_MAIN, fg=TEXT_MAIN, font=("Segoe UI", 12), state="disabled", wrap=tk.WORD, bd=0, padx=15, pady=15)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 5))
        
        self.chat_display.tag_config("user", foreground=ACCENT_CYAN, justify="right")
        self.chat_display.tag_config("ai", foreground=ACCENT_GREEN, justify="left")
        
        # แจ้งเตือนเริ่มต้น
        self.append_chat("🤖 AI Copilot: สวัสดีครับ ผมพร้อมให้คำปรึกษาเกี่ยวกับข้อมูลดาวเทียมแบบ Real-time แล้วครับ ถามสถานะปัจจุบันมาได้เลย!", "ai")

        chat_input_frame = tk.Frame(self.tab_chat, bg=BG_CARD)
        chat_input_frame.pack(fill=tk.X, padx=15, pady=(5, 15))

        self.entry_chat = tk.Entry(chat_input_frame, font=("Segoe UI", 12), bg="#2A3441", fg=TEXT_MAIN, insertbackground=TEXT_MAIN, bd=0)
        self.entry_chat.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        self.entry_chat.bind("<Return>", lambda event: self.send_chat())

        self.btn_send = tk.Button(chat_input_frame, text="SEND", font=("Segoe UI", 11, "bold"), bg="#6C5CE7", fg=TEXT_MAIN, bd=0, cursor="hand2", command=self.send_chat)
        self.btn_send.pack(side=tk.RIGHT, ipadx=15, ipady=6)

        self.ser = None

    # ================= ฟังก์ชันแชท AI =================
    def append_chat(self, text, tag):
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, text + "\n\n", tag)
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")

    def send_chat(self):
        user_msg = self.entry_chat.get().strip()
        if not user_msg:
            return
        
        if not HAS_AI or len(GEMINI_API_KEY) < 20:
            messagebox.showwarning("API Key", "กรุณาใส่ API Key ในโค้ดก่อนใช้งาน AI ครับ")
            return

        # โชว์ข้อความผู้ใช้
        self.append_chat(f"🧑‍🚀 คุณ: {user_msg}", "user")
        self.entry_chat.delete(0, tk.END)
        self.btn_send.config(text="...", state="disabled")

        # รัน AI ใน Thread แยกเพื่อไม่ให้โปรแกรมค้าง
        threading.Thread(target=self.process_chat, args=(user_msg,)).start()

    def process_chat(self, user_msg):
        try:
            # ดึงข้อมูลล่าสุดจากหน้าจอไปให้ AI ทราบ
            current_status = f"""
            [TELEMETRY ปัจจุบัน]
            สถานะ: {self.lbl_state.cget('text')}
            ความสูง: {self.data_labels['Altitude'].cget('text')} (สูงสุด: {self.max_alt:.1f}m)
            อุณหภูมิ: {self.data_labels['Temperature'].cget('text')}
            แบตเตอรี่: {self.data_labels['Voltage'].cget('text')}
            การเอียง (Pitch/Roll): {self.data_labels['Pitch'].cget('text')} / {self.data_labels['Roll'].cget('text')}
            """

            prompt = f"""
            คุณคือผู้ช่วย AI ประจำศูนย์ควบคุมดาวเทียม CanSat ชื่อ 'Planetary Impactor'
            นี่คือข้อมูลดาวเทียม ณ วินาทีนี้:
            {current_status}
            
            ผู้ควบคุมสั่งการ/ถามว่า: "{user_msg}"
            
            จงตอบกลับเป็นภาษาไทยที่ดูเป็นมืออาชีพ สั้น กระชับ อ้างอิงจากตัวเลขด้านบน และให้คำแนะนำถ้าจำเป็น
            """
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            # ส่งกลับไปแสดงผลที่ GUI
            self.window.after(0, lambda: self.append_chat(f"🤖 AI Copilot: {response.text}", "ai"))
            
        except Exception as e:
            self.window.after(0, lambda: self.append_chat(f"⚠️ ข้อผิดพลาด: {str(e)}", "ai"))
        
        finally:
            self.window.after(0, lambda: self.btn_send.config(text="SEND", state="normal"))

    # ================= ฟังก์ชันระบบเดิม =================
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        if "COM9" not in port_list:
            port_list.append("COM9")
        self.port_combo['values'] = port_list
        if port_list:
            if "COM9" in port_list:
                self.port_combo.set("COM9")
            else:
                self.port_combo.current(0)
        else:
            self.port_combo.set("No Device")

    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.lbl_clock.config(text=f"SYS: {now}")
        if self.is_connected and self.start_time is not None:
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            hours, mins = divmod(mins, 60)
            self.lbl_met.config(text=f"MET: T+{hours:02d}:{mins:02d}:{secs:02d}")
        self.window.after(1000, self.update_clock) 

    def set_graph(self, graph_name):
        self.current_graph = graph_name
        self.ax.set_title(f"LIVE: {self.current_graph.upper()}", color=TEXT_MAIN)
        colors = {"Altitude": ACCENT_CYAN, "Temperature": ACCENT_PINK, "Pressure": ACCENT_GREEN}
        self.line.set_color(colors[graph_name])
        self.update_plot()

    def start_serial(self):
        selected_port = self.port_combo.get()
        if selected_port == "" or selected_port == "No Device":
            messagebox.showwarning("Port Error", "กรุณาเสียบ CanSat และเลือกพอร์ตก่อนครับ!")
            return
        try:
            self.ser = serial.Serial(selected_port, BAUD_RATE, timeout=1)
            self.is_connected = True
            
            self.btn_connect.config(state="disabled", bg="#0E1E2B", text="LINKED")
            self.btn_disconnect.config(state="normal", bg=ACCENT_RED, fg=BG_MAIN)
            self.port_combo.config(state="disabled")
            self.btn_ai_report.pack_forget() 
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_filename = f"mission_log_{timestamp}.csv"
            
            self.start_time = time.time()
            self.end_time = None
            self.max_alt = 0.0
            self.lbl_max_alt.config(text="🏆 MAX ALT: 0.0 m")
            self.lbl_ai_warning.config(text="🟢 SYSTEM NORMAL", fg=ACCENT_GREEN)

            self.raw_term.config(state="normal")
            self.raw_term.delete('1.0', tk.END)
            self.raw_term.insert(tk.END, f"SYSTEM: Logging to {self.log_filename}\n")
            self.raw_term.config(state="disabled")

            with open(self.log_filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Temp(C)", "Pressure(Pa)", "Altitude(m)", "Latitude", "Longitude", "AccelX", "AccelY", "AccelZ", "Voltage(V)"])
            
            self.read_data()
        except Exception as e:
            messagebox.showerror("Connection Error", f"เชื่อมต่อ {selected_port} ไม่สำเร็จ!\n{e}")

    def stop_serial(self):
        self.is_connected = False
        self.end_time = time.time() # บันทึกเวลาหยุด
        if self.ser:
            self.ser.close()
            self.ser = None
        
        self.btn_connect.config(state="normal", bg=ACCENT_CYAN, text="CONNECT")
        self.btn_disconnect.config(state="disabled", bg="#3F1D24", fg=ACCENT_PINK)
        self.port_combo.config(state="readonly")
        self.lbl_state.config(text="STATUS: DISCONNECTED 🛑", fg=ACCENT_RED)
        self.lbl_ai_warning.config(text="⚪ STANDBY", fg=ACCENT_DIM)
        
        if os.path.exists(self.log_filename):
            self.btn_ai_report.pack(fill=tk.X, pady=(10, 0), ipady=8)

        self.raw_term.config(state="normal")
        self.raw_term.insert(tk.END, "SYSTEM: Connection Closed.\n")
        self.raw_term.see(tk.END)
        self.raw_term.config(state="disabled")

    def update_plot(self):
        self.line.set_ydata(self.history[self.current_graph])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def update_battery_bar(self, volts):
        pct = max(0, min(1.0, volts / MAX_BATTERY_VOLTAGE))
        fill_width = 4 + int(pct * 184) 
        self.batt_canvas.coords(self.batt_fill, 4, 4, fill_width, 11)
        if pct > 0.5: color = ACCENT_GREEN
        elif pct > 0.2: color = ACCENT_WARN
        else: color = ACCENT_PINK
        self.batt_canvas.itemconfig(self.batt_fill, fill=color)

    def read_data(self):
        if self.is_connected and self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    self.raw_term.config(state="normal")
                    self.raw_term.insert(tk.END, f"{line}\n")
                    self.raw_term.see(tk.END)
                    if int(self.raw_term.index('end-1c').split('.')[0]) > 30:
                        self.raw_term.delete('1.0', '2.0')
                    self.raw_term.config(state="disabled")

                data = line.split(',')
                if len(data) == 9 and data[0] != "Temperature(C)":
                    self.packet_count += 1
                    self.lbl_packets.config(text=f"PKTS: {self.packet_count}")

                    temp, press, alt, lat, lon, ax, ay, az, volts = map(float, data)
                    pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az)) * 180.0 / math.pi
                    roll = math.atan2(ay, az) * 180.0 / math.pi

                    warning_msg = "🟢 SYSTEM NORMAL"
                    warning_color = ACCENT_GREEN
                    if volts < 6.5:
                        warning_msg = "⚠️ CRITICAL: LOW BATTERY"
                        warning_color = ACCENT_RED
                    elif abs(pitch) > 70 or abs(roll) > 70:
                        warning_msg = "⚠️ ALERT: TUMBLING DETECTED"
                        warning_color = ACCENT_WARN
                    elif alt < self.prev_alt - 15: 
                        warning_msg = "🚨 DANGER: FREEFALL DETECTED!"
                        warning_color = ACCENT_RED

                    self.lbl_ai_warning.config(text=warning_msg, fg=warning_color)

                    if alt > self.max_alt:
                        self.max_alt = alt
                        self.lbl_max_alt.config(text=f"🏆 MAX ALT: {self.max_alt:.1f} m")

                    self.data_labels["Temperature"].config(text=f"{temp:.1f} °C", fg=ACCENT_PINK)
                    self.data_labels["Pressure"].config(text=f"{press:.0f} Pa", fg=ACCENT_GREEN)
                    self.data_labels["Altitude"].config(text=f"{alt:.1f} m", fg=ACCENT_CYAN)
                    self.data_labels["GPS Lat"].config(text=f"{lat:.6f}")
                    self.data_labels["GPS Lon"].config(text=f"{lon:.6f}")
                    self.data_labels["Accel X"].config(text=f"{ax:.0f}")
                    self.data_labels["Accel Y"].config(text=f"{ay:.0f}")
                    self.data_labels["Accel Z"].config(text=f"{az:.0f}")
                    self.data_labels["Pitch"].config(text=f"{pitch:.1f} °", fg=ACCENT_WARN)
                    self.data_labels["Roll"].config(text=f"{roll:.1f} °", fg=ACCENT_WARN)
                    self.data_labels["Voltage"].config(text=f"{volts:.2f} V")

                    self.update_battery_bar(volts)

                    alt_diff = alt - self.prev_alt
                    if alt_diff > 0.5:
                        self.lbl_state.config(text="STATUS: ASCENDING 🚀", fg=ACCENT_CYAN)
                    elif alt_diff < -0.5:
                        self.lbl_state.config(text="STATUS: DESCENDING 🪂", fg=ACCENT_PINK)
                    else:
                        self.lbl_state.config(text="STATUS: IDLE 🛑", fg=ACCENT_WARN)
                    self.prev_alt = alt

                    self.history["Temperature"].append(temp)
                    self.history["Pressure"].append(press)
                    self.history["Altitude"].append(alt)
                    self.update_plot()

                    if lat != 0.0 and lon != 0.0:
                        self.map_widget.set_position(lat, lon)
                        if self.marker is None:
                            self.marker = self.map_widget.set_marker(lat, lon, text="CanSat Location")
                        else:
                            self.marker.set_position(lat, lon)

                    with open(self.log_filename, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(data)
            except Exception as e:
                pass 
        
        if self.is_connected:
            self.window.after(50, self.read_data)

    def trigger_ai_report(self):
        if not HAS_AI or len(GEMINI_API_KEY) < 20:
            messagebox.showwarning("AI Setup Required", "กรุณาใส่ Gemini API Key ให้ถูกต้องก่อนใช้งานครับ")
            return
            
        self.btn_ai_report.config(text="⏳ AI IS ANALYZING...", state="disabled")
        threading.Thread(target=self.generate_ai_report_task).start()

    def generate_ai_report_task(self):
        try:
            flight_time = "Unknown"
            if self.start_time:
                # แก้เวลาให้เป๊ะโดยใช้ self.end_time
                end = self.end_time if self.end_time else time.time()
                elapsed = int(end - self.start_time)
                mins, secs = divmod(elapsed, 60)
                flight_time = f"{mins} นาที {secs} วินาที"

            prompt = f"""
            คุณคือผู้เชี่ยวชาญด้านอวกาศและวิศวกรรมการบิน
            นี่คือข้อมูลสรุปภารกิจของดาวเทียม CanSat ชื่อ 'Planetary Impactor':
            - ความสูงสูงสุดที่ทำได้: {self.max_alt:.2f} เมตร
            - เวลาที่ใช้ในภารกิจ: {flight_time}
            - จำนวน Packet ข้อมูลที่เก็บได้: {self.packet_count} ชุด
            
            จงเขียนรายงานสรุปภารกิจสั้นๆ (ไม่เกิน 5 บรรทัด) ในภาษาไทยที่ดูเป็นทางการ
            พร้อมให้คำแนะนำ 1 ข้อสำหรับการพัฒนาครั้งต่อไป
            """
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            self.window.after(0, lambda: self.show_ai_result(response.text))
            
        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror("AI Error", f"เกิดข้อผิดพลาด:\n{e}"))
            self.window.after(0, lambda: self.btn_ai_report.config(text="🤖 GENERATE AI REPORT", state="normal"))

    def show_ai_result(self, text):
        self.btn_ai_report.config(text="🤖 GENERATE AI REPORT", state="normal")
        report_win = tk.Toplevel(self.window)
        report_win.title("AI Mission Report")
        report_win.geometry("600x400")
        report_win.configure(bg=BG_CARD)
        
        tk.Label(report_win, text="✨ AI MISSION ANALYST ✨", font=("Segoe UI Black", 16), bg=BG_CARD, fg="#6C5CE7").pack(pady=15)
        
        txt_box = tk.Text(report_win, font=("Segoe UI", 12), bg=BG_MAIN, fg=TEXT_MAIN, wrap=tk.WORD, bd=0, padx=15, pady=15)
        txt_box.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        txt_box.insert(tk.END, text)
        txt_box.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = PlanetaryGCS(root)
    root.mainloop()