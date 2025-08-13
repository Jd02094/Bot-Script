
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Spinbox
import pyautogui
import pygetwindow as gw
import json
import os
import time
from pynput import mouse, keyboard

SCRIPTS_FILE = "scripts.json"

KEY_MAP = {
    "windows": "win", "ctrl": "ctrl", "shift": "shift", "alt": "alt",
    "enter": "enter", "espacio": "space", "space": "space", "tab": "tab",
    "esc": "esc", "escape": "esc",
    "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
    "f5": "f5", "f6": "f6", "f7": "f7", "f8": "f8",
    "f9": "f9", "f10": "f10", "f11": "f11", "f12": "f12",
    "arriba": "up", "abajo": "down", "izquierda": "left", "derecha": "right",
    "delete": "delete", "supr": "delete", "backspace": "backspace"
}

ventana_seleccionada = None
temporizador_id = None
contador_id = None
is_auto_executing = False
tiempo_restante = 0

is_recording = False
recorded_actions = []
mouse_listener = None
keyboard_listener = None

def cargar_scripts():
    if os.path.exists(SCRIPTS_FILE):
        with open(SCRIPTS_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_scripts(scripts):
    with open(SCRIPTS_FILE, "w") as f:
        json.dump(scripts, f, indent=4)

def parse_teclas(texto):
    pasos = texto.lower().split(",")
    secuencia = []
    for paso in pasos:
        combinacion = paso.strip().split("+")
        teclas = [KEY_MAP.get(tecla.strip(), tecla.strip()) for tecla in combinacion]
        secuencia.append(teclas)
    return secuencia

def seleccionar_ventana():
    global ventana_seleccionada
    titulo = ventana_combo.get()
    if not titulo:
        messagebox.showwarning("⚠ Advertencia", "Selecciona una ventana")
        return
    try:
        matching_windows = gw.getWindowsWithTitle(titulo)
        if not matching_windows:
            messagebox.showerror("❌ Error", "No se encontró la ventana seleccionada")
            return
        if len(matching_windows) > 1:
            messagebox.showwarning("⚠ Advertencia", f"Se encontraron {len(matching_windows)} ventanas con el título '{titulo}'. Seleccionando la primera.")
        ventana_seleccionada = matching_windows[0]
        if not is_auto_executing:
            messagebox.showinfo("✅ Ventana seleccionada", f"Usando: {titulo}")
    except IndexError:
        messagebox.showerror("❌ Error", "No se encontró la ventana seleccionada")

def activar_ventana():
    if ventana_seleccionada:
        if ventana_seleccionada.isMinimized:
            ventana_seleccionada.restore()
        ventana_seleccionada.activate()
        time.sleep(0.5)
        return True
    else:
        if not is_auto_executing:
            messagebox.showwarning("⚠ Advertencia", "No has seleccionado una ventana")
        return False

campos_teclas = []
campos_textos = []
campos_mouse = []

def validate_order(new_value):
    if new_value == "":
        return True
    if new_value.isdigit() and int(new_value) > 0:
        return True
    return False

def check_duplicate_orders():
    orders = [int(campo['order'].get()) for campo in campos_textos + campos_teclas + campos_mouse if campo['order'].get().isdigit()]
    return len(orders) != len(set(orders))

def agregar_campo_teclas(order=None, content=""):
    inner_frame = ttk.Frame(frame_teclas)
    inner_frame.pack(anchor="center", pady=2, before=botones_frame_teclas)

    fila_frame = ttk.Frame(inner_frame)
    fila_frame.pack()

    vcmd = (root.register(validate_order), '%P')
    order_spin = Spinbox(fila_frame, from_=1, to=100, width=5, validate="key", validatecommand=vcmd)
    order_spin.pack(side="left", padx=5)
    
    if order is None:
        used_orders = [int(campo['order'].get()) for campo in campos_textos + campos_teclas + campos_mouse if campo['order'].get().isdigit()]
        next_order = max(used_orders + [0]) + 1
        order_spin.delete(0, tk.END)
        order_spin.insert(0, str(next_order))
    else:
        order_spin.delete(0, tk.END)
        order_spin.insert(0, str(order))

    entry = ttk.Entry(fila_frame, width=35)
    entry.pack(side="left", padx=(0,5))
    entry.insert(0, content)

    def eliminar_campo():
        inner_frame.destroy()
        campos_teclas.remove({'frame': inner_frame, 'entry': entry, 'order': order_spin})

    btn_eliminar = tk.Button(fila_frame, text="🗑", command=eliminar_campo, bg="#dc3545", fg="white", width=3)
    btn_eliminar.pack(side="left")

    campos_teclas.append({'frame': inner_frame, 'entry': entry, 'order': order_spin})

def agregar_campo_texto(order=None, content=""):
    inner_frame = ttk.Frame(frame_texto)
    inner_frame.pack(anchor="center", pady=2, before=botones_frame_texto)

    fila_frame = ttk.Frame(inner_frame)
    fila_frame.pack()

    vcmd = (root.register(validate_order), '%P')
    order_spin = Spinbox(fila_frame, from_=1, to=100, width=5, validate="key", validatecommand=vcmd)
    order_spin.pack(side="left", padx=5)

    if order is None:
        used_orders = [int(campo['order'].get()) for campo in campos_textos + campos_teclas + campos_mouse if campo['order'].get().isdigit()]
        next_order = max(used_orders + [0]) + 1
        order_spin.delete(0, tk.END)
        order_spin.insert(0, str(next_order))
    else:
        order_spin.delete(0, tk.END)
        order_spin.insert(0, str(order))

    entry = ttk.Entry(fila_frame, width=35)
    entry.pack(side="left", padx=(0,5))
    entry.insert(0, content)

    def eliminar_campo():
        inner_frame.destroy()
        campos_textos.remove({'frame': inner_frame, 'entry': entry, 'order': order_spin})

    btn_eliminar = tk.Button(fila_frame, text="🗑", command=eliminar_campo, bg="#dc3545", fg="white", width=3)
    btn_eliminar.pack(side="left")

    campos_textos.append({'frame': inner_frame, 'entry': entry, 'order': order_spin})

def agregar_campo_mouse(order=None, x=None, y=None):
    inner_frame = ttk.Frame(frame_mouse)
    inner_frame.pack(anchor="center", pady=2, before=botones_frame_mouse)

    fila_frame = ttk.Frame(inner_frame)
    fila_frame.pack()

    vcmd = (root.register(validate_order), '%P')
    order_spin = Spinbox(fila_frame, from_=1, to=100, width=5, validate="key", validatecommand=vcmd)
    order_spin.pack(side="left", padx=5)

    if order is None:
        used_orders = [int(campo['order'].get()) for campo in campos_textos + campos_teclas + campos_mouse if campo['order'].get().isdigit()]
        next_order = max(used_orders + [0]) + 1
        order_spin.delete(0, tk.END)
        order_spin.insert(0, str(next_order))
    else:
        order_spin.delete(0, tk.END)
        order_spin.insert(0, str(order))

    x_entry = ttk.Entry(fila_frame, width=10)
    x_entry.pack(side="left", padx=(0,5))
    y_entry = ttk.Entry(fila_frame, width=10)
    y_entry.pack(side="left", padx=(0,5))

    if x is not None and y is not None:
        x_entry.insert(0, str(x))
        y_entry.insert(0, str(y))

    def eliminar_campo():
        inner_frame.destroy()
        campos_mouse.remove({'frame': inner_frame, 'x_entry': x_entry, 'y_entry': y_entry, 'order': order_spin})

    btn_eliminar = tk.Button(fila_frame, text="🗑", command=eliminar_campo, bg="#dc3545", fg="white", width=3)
    btn_eliminar.pack(side="left")

    campos_mouse.append({'frame': inner_frame, 'x_entry': x_entry, 'y_entry': y_entry, 'order': order_spin})

def obtener_acciones_ordenadas():
    acciones = []
    for campo in campos_textos:
        order_str = campo['order'].get()
        if not order_str.isdigit():
            messagebox.showwarning("⚠ Advertencia", f"Orden inválido en campo de texto: '{campo['entry'].get()}'. Usa números enteros positivos.")
            return []
        texto = campo['entry'].get().strip()
        if texto:
            acciones.append({'order': int(order_str), 'type': 'text', 'content': texto})
    for campo in campos_teclas:
        order_str = campo['order'].get()
        if not order_str.isdigit():
            messagebox.showwarning("⚠ Advertencia", f"Orden inválido en campo de teclas: '{campo['entry'].get()}'. Usa números enteros positivos.")
            return []
        teclas = campo['entry'].get().strip()
        if teclas:
            acciones.append({'order': int(order_str), 'type': 'key', 'content': teclas})
    for campo in campos_mouse:
        order_str = campo['order'].get()
        x_str = campo['x_entry'].get()
        y_str = campo['y_entry'].get()
        if not order_str.isdigit() or not x_str.isdigit() or not y_str.isdigit():
            messagebox.showwarning("⚠ Advertencia", f"Orden o coordenadas inválidas en campo de mouse. Usa números enteros positivos.")
            return []
        acciones.append({'order': int(order_str), 'type': 'mouse', 'x': int(x_str), 'y': int(y_str)})

    if check_duplicate_orders():
        messagebox.showwarning("⚠ Advertencia", "Hay órdenes duplicados. Asegúrate de que cada acción tenga un número de orden único.")
        return []
    acciones.sort(key=lambda x: x['order'])
    return acciones

def ejecutar_acciones():
    if not activar_ventana():
        return
    acciones = obtener_acciones_ordenadas()
    if not acciones:
        if not check_duplicate_orders():
            messagebox.showwarning("⚠ Advertencia", "No hay acciones válidas para ejecutar")
        return
    if not is_auto_executing:
        preview = "\n".join([f"{accion['order']}: {'Texto' if accion['type'] == 'text' else 'Teclas' if accion['type'] == 'key' else 'Mouse'}: {accion.get('content', f'({accion.get("x", "")}, {accion.get("y", "")})')}" for accion in acciones])
        messagebox.showinfo("📋 Orden de Ejecución", f"Acciones a ejecutar:\n{preview}")
    for accion in acciones:
        if accion['type'] == 'text':
            pyautogui.typewrite(accion['content'])
        elif accion['type'] == 'key':
            secuencia = parse_teclas(accion['content'])
            for combinacion in secuencia:
                if len(combinacion) > 1:
                    pyautogui.hotkey(*combinacion)
                else:
                    pyautogui.press(combinacion[0])
                time.sleep(0.2)
        elif accion['type'] == 'mouse':
            pyautogui.click(x=accion['x'], y=accion['y'])
        time.sleep(0.2)

def guardar_script_acciones():
    nombre = simpledialog.askstring("💾 Guardar Script", "Nombre del script:")
    if not nombre:
        return
    ventana = ventana_combo.get()
    if not ventana:
        messagebox.showwarning("⚠ Advertencia", "Selecciona una ventana antes de guardar")
        return
    acciones = obtener_acciones_ordenadas()
    if not acciones:
        return
    scripts = cargar_scripts()
    scripts[nombre] = {
        "ventana": ventana,
        "acciones": acciones
    }
    guardar_scripts(scripts)
    actualizar_lista_scripts()
    messagebox.showinfo("✅ Guardado", f"Script '{nombre}' guardado correctamente.")

def ejecutar_script_guardado():
    seleccion = scripts_listbox.curselection()
    if not seleccion:
        return
    nombre = scripts_listbox.get(seleccion)
    scripts = cargar_scripts()
    contenido = scripts.get(nombre)
    
    if isinstance(contenido, dict):
        ventana = contenido.get("ventana", "")
        acciones = contenido.get("acciones", [])
        
        ventana_combo.set(ventana)
        seleccionar_ventana()
        
        for campo in campos_textos[:]:
            campo['frame'].destroy()
            campos_textos.remove(campo)
        for campo in campos_teclas[:]:
            campo['frame'].destroy()
            campos_teclas.remove(campo)
        for campo in campos_mouse[:]:
            campo['frame'].destroy()
            campos_mouse.remove(campo)
        
        for accion in sorted(acciones, key=lambda x: x['order']):
            if accion['type'] == 'text':
                agregar_campo_texto(accion['order'], accion['content'])
            elif accion['type'] == 'key':
                agregar_campo_teclas(accion['order'], accion['content'])
            elif accion['type'] == 'mouse':
                agregar_campo_mouse(accion['order'], accion['x'], accion['y'])
        
        if activar_ventana():
            ejecutar_acciones()
    else:
        agregar_campo_teclas()
        last_campo = campos_teclas[-1]
        last_campo['entry'].insert(0, contenido)
        last_campo['order'].delete(0, tk.END)
        last_campo['order'].insert(0, "1")
        if activar_ventana():
            ejecutar_acciones()

def eliminar_script():
    seleccion = scripts_listbox.curselection()
    if not seleccion:
        return
    nombre = scripts_listbox.get(seleccion)
    scripts = cargar_scripts()
    del scripts[nombre]
    guardar_scripts(scripts)
    actualizar_lista_scripts()

def editar_script():
    seleccion = scripts_listbox.curselection()
    if not seleccion:
        return
    nombre = scripts_listbox.get(seleccion)
    valor_actual = cargar_scripts()[nombre]
    if isinstance(valor_actual, dict):
        nuevo_valor = simpledialog.askstring("✏ Editar Script Completo", "Edita JSON manualmente:", initialvalue=json.dumps(valor_actual))
        if nuevo_valor:
            try:
                nuevo_dict = json.loads(nuevo_valor)
                scripts = cargar_scripts()
                scripts[nombre] = nuevo_dict
                guardar_scripts(scripts)
                actualizar_lista_scripts()
            except json.JSONDecodeError:
                messagebox.showerror("❌ Error", "JSON inválido.")
    else:
        nuevo_valor = simpledialog.askstring("✏ Editar Script", "Nuevas teclas:", initialvalue=valor_actual)
        if nuevo_valor:
            scripts = cargar_scripts()
            scripts[nombre] = nuevo_valor
            guardar_scripts(scripts)
            actualizar_lista_scripts()

def mostrar_diccionario():
    texto = "\n".join([f"{k} -> {v}" for k, v in KEY_MAP.items()])
    messagebox.showinfo("📖 Diccionario de Teclas", texto)

def actualizar_lista_scripts():
    scripts_listbox.delete(0, tk.END)
    for nombre in cargar_scripts():
        scripts_listbox.insert(tk.END, nombre)

def actualizar_ventanas():
    ventana_combo["values"] = [w.title for w in gw.getAllWindows() if w.title.strip()]

def actualizar_contador():
    global contador_id, tiempo_restante
    if tiempo_restante > 0:
        tiempo_restante -= 1
        contador_label.config(text=f"Próxima ejecución en: {tiempo_restante} seg")
        contador_id = root.after(1000, actualizar_contador)
    else:
        contador_label.config(text="Ejecutando...")

def ejecutar_script_repetido():
    global temporizador_id, is_auto_executing, tiempo_restante, contador_id
    seleccion = scripts_listbox.curselection()
    if not seleccion:
        messagebox.showwarning("⚠ Advertencia", "Selecciona un script para la ejecución automática")
        return
    is_auto_executing = True
    try:
        intervalo = int(intervalo_entry.get())
        if intervalo <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("❌ Error", "El intervalo debe ser un número entero positivo")
        is_auto_executing = False
        contador_label.config(text="Próxima ejecución en: -- seg")
        return
    tiempo_restante = intervalo
    actualizar_contador()
    ejecutar_script_guardado()
    temporizador_id = root.after(intervalo * 1000, ejecutar_script_repetido)

def detener_temporizador():
    global temporizador_id, is_auto_executing, tiempo_restante, contador_id
    if temporizador_id is not None:
        root.after_cancel(temporizador_id)
        temporizador_id = None
    if contador_id is not None:
        root.after_cancel(contador_id)
        contador_id = None
    is_auto_executing = False
    tiempo_restante = 0
    contador_label.config(text="Próxima ejecución en: -- seg")
    messagebox.showinfo("🛑 Detenido", "La ejecución automática fue detenida")

def on_mouse_click(x, y, button, pressed):
    global recorded_actions
    if pressed:
        recorded_actions.append({'type': 'mouse', 'x': x, 'y': y})

def on_key_press(key):
    global recorded_actions
    try:
        if key == keyboard.Key.esc:
            stop_recording_gui()
            return False
        recorded_actions.append({'type': 'key', 'content': key.name if hasattr(key, 'name') else key.char})
    except AttributeError:
        recorded_actions.append({'type': 'key', 'content': str(key)})

def start_recording_gui():
    global is_recording, recorded_actions, mouse_listener, keyboard_listener
    if is_recording:
        messagebox.showwarning("⚠ Advertencia", "Ya se está grabando. Detén la grabación actual primero.")
        return
    
    is_recording = True
    recorded_actions = []
    
    messagebox.showinfo("Grabar acciones", "La grabación ha comenzado. Haz tus acciones y presiona la tecla ESC para detenerla.")
    
    mouse_listener = mouse.Listener(on_click=on_mouse_click)
    keyboard_listener = keyboard.Listener(on_press=on_key_press)
    
    mouse_listener.start()
    keyboard_listener.start()
    
    btn_record_start.config(state="disabled")
    btn_record_stop.config(state="normal")

def stop_recording_gui():
    global is_recording, recorded_actions, mouse_listener, keyboard_listener
    if not is_recording:
        return
        
    is_recording = False
    
    if mouse_listener:
        mouse_listener.stop()
        mouse_listener = None
    if keyboard_listener:
        keyboard_listener.stop()
        keyboard_listener = None
        
    messagebox.showinfo("Grabación terminada", "La grabación se ha detenido. Las acciones se han cargado en la interfaz.")
    
    # Clear existing fields
    for campo in campos_textos[:]:
        campo['frame'].destroy()
        campos_textos.remove(campo)
    for campo in campos_teclas[:]:
        campo['frame'].destroy()
        campos_teclas.remove(campo)
    for campo in campos_mouse[:]:
        campo['frame'].destroy()
        campos_mouse.remove(campo)
        
    # Populate fields from recorded actions
    order = 1
    for action in recorded_actions:
        if action['type'] == 'mouse':
            agregar_campo_mouse(order, action['x'], action['y'])
        elif action['type'] == 'key':
            agregar_campo_teclas(order, action['content'])
        order += 1
        
    btn_record_start.config(state="normal")
    btn_record_stop.config(state="disabled")

# --- Interfaz ---
root = tk.Tk()
root.title("⚡ Bot-Script")
root.geometry("800x600")
root.configure(bg="white")

style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
style.configure("TLabel", background="white", font=("Segoe UI", 10))
style.configure("TEntry", padding=5)

GREEN_BTN = {"background": "#28a745", "foreground": "white"}
RED_BTN = {"background": "#dc3545", "foreground": "white"}
BLUE_BTN = {"background": "#007bff", "foreground": "white"}

canvas = tk.Canvas(root, bg="white", highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

content_frame = ttk.Frame(canvas)
content_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=content_frame, anchor="nw")

def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

header = tk.Label(content_frame, text="⚡ Bot-Script", font=("Segoe UI", 16, "bold"), bg="#007bff", fg="white", pady=10)
header.pack(fill="x")

frame_ventana = ttk.LabelFrame(content_frame, text="🖥 Ventana", padding=10)
frame_ventana.pack(fill="x", padx=10, pady=5)

ventana_combo = ttk.Combobox(frame_ventana, width=50)
ventana_combo.pack(pady=3, anchor="center")

ventana_btn_frame = ttk.Frame(frame_ventana)
ventana_btn_frame.pack(anchor="center", pady=5)
tk.Button(ventana_btn_frame, text="🔄 Actualizar", command=actualizar_ventanas, **BLUE_BTN).pack(side="left", padx=5)
tk.Button(ventana_btn_frame, text="📌 Usar Ventana", command=seleccionar_ventana, **BLUE_BTN).pack(side="left", padx=5)

frame_grabacion = ttk.LabelFrame(content_frame, text="🔴 Grabación de Acciones", padding=10)
frame_grabacion.pack(fill="x", padx=10, pady=5)

botones_grabacion = ttk.Frame(frame_grabacion)
botones_grabacion.pack(anchor="center")
btn_record_start = tk.Button(botones_grabacion, text="▶ Empezar a Grabar (Esc para Detener)", command=start_recording_gui, bg="#dc3545", fg="white")
btn_record_start.pack(side="left", padx=5)
btn_record_stop = tk.Button(botones_grabacion, text="■ Detener Grabación", command=stop_recording_gui, bg="#6c757d", fg="white", state="disabled")
btn_record_stop.pack(side="left", padx=5)

frame_acciones = ttk.LabelFrame(content_frame, text="📝 Acciones a Ejecutar", padding=10)
frame_acciones.pack(fill="x", padx=10, pady=5)

botones_ejecucion_principal = ttk.Frame(frame_acciones)
botones_ejecucion_principal.pack(anchor="center", pady=5)
tk.Button(botones_ejecucion_principal, text="▶ Ejecutar Todo", command=ejecutar_acciones, **GREEN_BTN).pack(side="left", padx=5)
tk.Button(botones_ejecucion_principal, text="💾 Guardar Script", command=guardar_script_acciones, **BLUE_BTN).pack(side="left", padx=5)

frame_texto = ttk.LabelFrame(frame_acciones, text="💬 Textos a Enviar (Orden + Texto)", padding=5)
frame_texto.pack(fill="x", padx=5, pady=2)
botones_frame_texto = ttk.Frame(frame_texto)
botones_frame_texto.pack(anchor="center", pady=5)
btn_add_texto = tk.Button(botones_frame_texto, text="+ Añadir Texto", command=agregar_campo_texto, **BLUE_BTN)
btn_add_texto.pack(side="left", padx=5)

frame_teclas = ttk.LabelFrame(frame_acciones, text="⌨ Comandos de Teclas (Orden + Comando)", padding=5)
frame_teclas.pack(fill="x", padx=5, pady=2)
botones_frame_teclas = ttk.Frame(frame_teclas)
botones_frame_teclas.pack(anchor="center", pady=5)
tk.Button(botones_frame_teclas, text="📖 Diccionario", command=mostrar_diccionario, **BLUE_BTN).pack(side="left", padx=5)
btn_add_teclas = tk.Button(botones_frame_teclas, text="+ Añadir Comando", command=agregar_campo_teclas, **BLUE_BTN)
btn_add_teclas.pack(side="left", padx=5)

frame_mouse = ttk.LabelFrame(frame_acciones, text="🖱 Clics de Mouse (Orden + X, Y)", padding=5)
frame_mouse.pack(fill="x", padx=5, pady=2)
botones_frame_mouse = ttk.Frame(frame_mouse)
botones_frame_mouse.pack(anchor="center", pady=5)
btn_add_mouse = tk.Button(botones_frame_mouse, text="+ Añadir Clic", command=agregar_campo_mouse, **BLUE_BTN)
btn_add_mouse.pack(side="left", padx=5)

campos_textos.clear()
campos_teclas.clear()
campos_mouse.clear()
agregar_campo_texto()
agregar_campo_teclas()
agregar_campo_mouse()

frame_scripts = ttk.LabelFrame(content_frame, text="📂 Scripts Guardados", padding=10)
frame_scripts.pack(fill="both", padx=10, pady=5, expand=True)

scripts_listbox = tk.Listbox(frame_scripts, height=8, width=50)
scripts_listbox.pack(anchor="center")

btn_frame = ttk.Frame(frame_scripts)
btn_frame.pack(anchor="center", pady=5)
tk.Button(btn_frame, text="▶ Ejecutar", command=ejecutar_script_guardado, **GREEN_BTN).pack(side="left", padx=5)
tk.Button(btn_frame, text="✏ Editar", command=editar_script, **BLUE_BTN).pack(side="left", padx=5)
tk.Button(btn_frame, text="🗑 Eliminar", command=eliminar_script, **RED_BTN).pack(side="left", padx=5)

intervalo_frame = ttk.LabelFrame(content_frame, text="⏰ Temporizador de Ejecución Automática", padding=10)
intervalo_frame.pack(fill="x", padx=10, pady=5)

intervalo_inner_frame = ttk.Frame(intervalo_frame)
intervalo_inner_frame.pack(anchor="center")
ttk.Label(intervalo_inner_frame, text="Intervalo (segundos):").pack(side="left", padx=5)
intervalo_entry = ttk.Entry(intervalo_inner_frame, width=10)
intervalo_entry.pack(side="left", padx=5)
intervalo_entry.insert(0, "5")
ttk.Label(intervalo_inner_frame, text="   ").pack(side="left")
contador_label = ttk.Label(intervalo_inner_frame, text="Próxima ejecución en: -- seg")
contador_label.pack(side="left", padx=5)
tk.Button(intervalo_inner_frame, text="▶ Iniciar Autoejecución", command=ejecutar_script_repetido, **GREEN_BTN).pack(side="left", padx=10)
tk.Button(intervalo_inner_frame, text="🛑 Detener Autoejecución", command=detener_temporizador, **RED_BTN).pack(side="left", padx=10)

actualizar_lista_scripts()
actualizar_ventanas()

root.mainloop()