# Script by Boon Yang Koh, Northeastern University, last major revision 5/5/2025

# This script runs as a GUI for open/close (velocity based) commands for the Proteus Gripper 
# or any motor controlled by the Moteus BLDC controller. 

# Steps to follow:
    # 1. Ensure this file is able to access the Moteus library, place in \moteus\moteus\lib\python
    # 2. Set the torque limit to 0.015 and above to overcome internal friction
    # 3. Keep below a torque limit of 0.1 when using the gripper with your hands


import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import moteus
import threading

class MotorController:
    def __init__(self):
        self.controller = moteus.Controller(id=2)
        self.running = False
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, daemon=True)
        self.thread.start()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _stop(self):
        self.running = False
        await self.controller.set_stop()

    async def _run(self, velocity, max_torque):
        self.running = False
        await self.controller.set_stop()
        await asyncio.sleep(0.02)
        self.running = True
        while self.running:
            await self.controller.set_position(
                position=float('nan'),
                velocity=velocity,
                maximum_torque=max_torque
            )
            await asyncio.sleep(1/300) #300hz

    def stop(self):
        asyncio.run_coroutine_threadsafe(self._stop(), self.loop)

    def run(self, velocity, max_torque):
        asyncio.run_coroutine_threadsafe(
            self._run(velocity, max_torque), 
            self.loop
        )

class App:
    def __init__(self, root):
        self.root = root
        self.motor = MotorController()
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("Standalone Gripper Interface")
        self.root.minsize(350, 180)
        
        # Default values
        self.max_torque = tk.DoubleVar(value=0.01)
        self.max_speed = tk.DoubleVar(value=1.0)
        self.max_accel = tk.DoubleVar(value=5.0)
        
        # Torque control
        ttk.Label(self.root, text="Max Torque (0-0.47):").grid(column=1, row=1, sticky='e', padx=5, pady=5)
        ttk.Spinbox(
            self.root, 
            from_=0.01, 
            to=0.47, 
            increment=0.01,
            textvariable=self.max_torque,
            width=6
        ).grid(column=2, row=1, sticky='w', padx=5, pady=5)
        
        # Speed control
        ttk.Label(self.root, text="Max Speed (0-20):").grid(column=1, row=2, sticky='e', padx=5, pady=5)
        ttk.Spinbox(
            self.root, 
            from_=0, 
            to=20, 
            increment=0.1,
            textvariable=self.max_speed,
            width=6
        ).grid(column=2, row=2, sticky='w', padx=5, pady=5)
        
        # Acceleration control
        ttk.Label(self.root, text="Max Acceleration (0-20):").grid(column=1, row=3, sticky='e', padx=5, pady=5)
        ttk.Spinbox(
            self.root, 
            from_=0, 
            to=20, 
            increment=0.1,
            textvariable=self.max_accel,
            width=6
        ).grid(column=2, row=3, sticky='w', padx=5, pady=5)
        
        # Control buttons
        ttk.Button(
            self.root, 
            text="Open", 
            command=self.open,
            style='Green.TButton'
        ).grid(column=2, row=4, padx=5, pady=10)
        
        ttk.Button(
            self.root, 
            text="Close", 
            command=self.close,
            style='Yellow.TButton'
        ).grid(column=3, row=4, padx=5, pady=10)
        
        ttk.Button(
            self.root, 
            text="Stop", 
            command=self.stop,
            style='Orange.TButton'
        ).grid(column=4, row=4, padx=5, pady=10)
        
        ttk.Button(
            self.root, 
            text="QUIT", 
            command=self.quit_app,
            style='Red.TButton'
        ).grid(column=1, row=4, padx=5, pady=10)
        
        # Configure styles
        style = ttk.Style()
        style.configure('Green.TButton', foreground='black', background='green')
        style.configure('Yellow.TButton', foreground='black', background='yellow')
        style.configure('Orange.TButton', foreground='black', background='orange')
        style.configure('Red.TButton', foreground='black', background='red')
        
    def open(self):
        try:
            self.motor.run(
                velocity=self.max_speed.get(),
                max_torque=self.max_torque.get()
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open: {str(e)}")
    
    def close(self):
        try:
            self.motor.run(
                velocity=-self.max_speed.get(),
                max_torque=self.max_torque.get()
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to close: {str(e)}")
    
    def stop(self):
        try:
            self.motor.stop()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop: {str(e)}")
    
    def quit_app(self):
        self.stop()
        self.root.after(100, self.root.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()