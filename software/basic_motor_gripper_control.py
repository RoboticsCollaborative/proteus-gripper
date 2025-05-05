# Script by Boon Yang Koh, Northeastern University, last major revision 5/5/2025

# This script runs as a GUI for position-based motor commands for the Proteus Gripper 
# or any motor controlled by the Moteus BLDC controller. 

# Steps to follow:
    # 1. Ensure this file is able to access the Moteus library, place in \moteus\moteus\lib\python
    # 2. Zero the proteus gripper at it's maximum opening
        #a. Zero in this script refers to setting the maximum opening position to 7.
        #b. For true zero at 0.0, go to line 57 and change to 'd exact 0'. 
    # 3. Keep below a torque limit of 0.1 when using the gripper with your hands

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import moteus
import threading

class MotorController:
    def __init__(self):
        self.controller = moteus.Controller(id=2)
        self.stream = moteus.Stream(self.controller)
        self.running = False
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, daemon=True)
        self.thread.start()
        self.status = {"position": 0.0, "velocity": 0.0, "torque": 0.0}
        self.polling = True
        self.poll_thread = threading.Thread(target=self.poll_motor_status, daemon=True)
        self.poll_thread.start()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _stop(self):
        self.running = False
        await self.controller.set_stop()

    async def _run(self, target_position, target_kp_scale, target_kd_scale, target_velocity, target_torque):
        self.running = False
        await self.controller.set_stop()
        await asyncio.sleep(0.02)
        self.running = True
        while self.running:
            await self.controller.set_position(
                position=target_position,
                
                kp_scale=target_kp_scale,
                kd_scale=target_kd_scale,
                velocity_limit=target_velocity,
                maximum_torque=target_torque
            )
            await asyncio.sleep(1/300) #300hz

    async def _zero(self):
        await self.stream.command(f'd exact 7'.encode('utf8'))

    def stop(self):
        asyncio.run_coroutine_threadsafe(self._stop(), self.loop)

    def run(self, target_position, target_kp_scale, target_kd_scale, target_velocity, target_torque):
        asyncio.run_coroutine_threadsafe(
            self._run(target_position, target_kp_scale, target_kd_scale, target_velocity, target_torque), 
            self.loop
        )
    
    def poll_motor_status(self):
        while self.polling:
            try:
                state = asyncio.run_coroutine_threadsafe(self.controller.query(), self.loop).result()
                self.status["position"] = state.values[moteus.Register.POSITION]
                self.status["velocity"] = state.values[moteus.Register.VELOCITY]
                self.status["torque"] = state.values[moteus.Register.TORQUE]
            except:
                pass
            
            asyncio.run_coroutine_threadsafe(asyncio.sleep(0.01), self.loop)

    def zero(self):
        asyncio.run_coroutine_threadsafe(self._zero(), self.loop)


class App:
    def __init__(self, root):
        self.root = root
        self.motor = MotorController()
        self.setup_ui()
        self.update_live_readings()
        
    def setup_ui(self):
        self.root.title("Basic Motor/Gripper Control")
        self.root.minsize(350, 180)
        
        # Default values
        self.set_position = tk.DoubleVar(value=0)
        self.set_kp_scale=tk.DoubleVar(value=1.0)
        self.set_kd_scale=tk.DoubleVar(value=1.0)
        self.set_velocity = tk.DoubleVar(value=1.0)
        self.set_torque = tk.DoubleVar(value=0.01)

        # Initialize Live Readings
        self.current_position = tk.StringVar(value="0.0")
        self.current_velocity = tk.StringVar(value="0.0")
        self.current_torque = tk.StringVar(value="0.0")
        
        # Position Control
        ttk.Label(self.root, text="Set Position:").grid(column=1, row=1, sticky='e', padx=5, pady=5)
        ttk.Spinbox(
            self.root, 
            from_=-7.0, 
            to=7.0, 
            increment=0.5,
            textvariable=self.set_position,
            width=6
        ).grid(column=2, row=1, sticky='w', padx=5, pady=5)

        # Position (Current Reading)
        ttk.Label(self.root, text="Current Position: ").grid(column=3, row=1, padx=5, pady=5)
        ttk.Label(self.root, textvariable=self.current_position).grid(column=4, row=1, padx=5, pady=5)
        
        # KP Scale Control
        ttk.Label(self.root, text="Set KP Scale (0 to 1):").grid(column=1, row=2, sticky='e', padx=5, pady=5)
        ttk.Spinbox(
            self.root, 
            from_=0, 
            to=1, 
            increment=0.05,
            textvariable=self.set_kp_scale,
            width=6
        ).grid(column=2, row=2, sticky='w', padx=5, pady=5)
        
        # KD Scale Control
        ttk.Label(self.root, text="Set KD Scale (0 to 1):").grid(column=1, row=3, sticky='e', padx=5, pady=5)
        ttk.Spinbox(
            self.root, 
            from_=0, 
            to=1, 
            increment=0.05,
            textvariable=self.set_kd_scale,
            width=6
        ).grid(column=2, row=3, sticky='w', padx=5, pady=5)

        # Max Velocity Control
        ttk.Label(self.root, text="Set Max Velocity:").grid(column=1, row=4, sticky='e', padx=5, pady=5)
        ttk.Spinbox(
            self.root, 
            from_=0, 
            to=50, 
            increment=1.0,
            textvariable=self.set_velocity,
            width=6
        ).grid(column=2, row=4, sticky='w', padx=5, pady=5)

        # Velocity (Current Reading)
        ttk.Label(self.root, text="Current Velocity: ").grid(column=3, row=4, padx=5, pady=5)
        ttk.Label(self.root, textvariable=self.current_velocity).grid(column=4, row=4, padx=5, pady=5)

        # Max Torque Control
        ttk.Label(self.root, text="Set Max Torque (0 to 0.47):").grid(column=1, row=5, sticky='e', padx=5, pady=5)
        ttk.Spinbox(
            self.root, 
            from_=0, 
            to=0.470, 
            increment=0.005,
            textvariable=self.set_torque,
            width=6
        ).grid(column=2, row=5, sticky='w', padx=5, pady=5)

        # Torque (Current Readings)
        ttk.Label(self.root, text="Current Torque: ").grid(column=3, row=5, padx=5, pady=5)
        ttk.Label(self.root, textvariable=self.current_torque).grid(column=4, row=5, padx=5, pady=5)
        
        # Control buttons
        ttk.Button(
            self.root, 
            text="Go", 
            command=self.go,
            style='Green.TButton'
        ).grid(column=2, row=6, padx=5, pady=10)
        
        ttk.Button(
            self.root, 
            text="Stop", 
            command=self.stop,
            style='Orange.TButton'
        ).grid(column=4, row=6, padx=5, pady=10)
        
        ttk.Button(
            self.root, 
            text="QUIT", 
            command=self.quit_app,
            style='Red.TButton'
        ).grid(column=1, row=6, padx=5, pady=10)

        ttk.Button(
            self.root, 
            text="Zero", 
            command=self.zero,
            style='Black.TButton'
        ).grid(column=5, row=1, padx=5, pady=10)
        
        # Configure styles
        style = ttk.Style()
        style.configure('Green.TButton', foreground='black', background='green')
        style.configure('Orange.TButton', foreground='black', background='orange')
        style.configure('Red.TButton', foreground='black', background='red')

    def update_live_readings(self):
        self.current_position.set(f"{self.motor.status['position']:.3f}")
        self.current_velocity.set(f"{self.motor.status['velocity']:.3f}")
        self.current_torque.set(f"{self.motor.status['torque']:.3f}")
        self.root.after(100, self.update_live_readings)

    def go(self):
        try:
            self.motor.run(
                target_position=self.set_position.get(),
                target_kp_scale=self.set_kp_scale.get(),
                target_kd_scale=self.set_kd_scale.get(),
                target_velocity=self.set_velocity.get(),
                target_torque=self.set_torque.get(),

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

    def zero(self):
        try:
            self.motor.zero()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to zero: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()