# Script by Boon Yang Koh, Northeastern University, last major revision 5/5/2025

# This script runs as a GUI for non-haptic non-filtered tele-operation for the Proteus Gripper.

# Steps to follow:
    # 1. Ensure this file is able to access the Moteus library, place in \moteus\moteus\lib\python
    # 2. Home the trigger and gripper before operation
        #a. Ensure after trigger homing, position reads 0
        #b. Ensure after gripper homing, position reads 7
        #c. Re-home if above values don't match within +-0.05 rotations

import asyncio
import moteus
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread

class MotorControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Motor Control")
        
        # Motor control flags
        self.controller = moteus.Controller(id=2)
        self.stream = moteus.Stream(self.controller)
        self.running = False
        self.monitoring = True  # Flag for continuous monitoring
        self.homing_trigger = False
        self.homing_gripper = False
        self.loop = None
        self.control_task = None  # For motor control
        self.monitor_task = None  # For continuous monitoring
        self.controllers = {}  # To store motor controllers
        self.prevfiltpos = None # store previous pos
        self.alpha = 0.95 # filtering alpha 
        
        # Create GUI elements
        self.create_widgets()
        
        # Start monitoring immediately
        self.start_monitoring()
        
    def create_widgets(self):
        self.root.title("Basic Tele-op")
        self.root.minsize(500, 180)

        # Filtering input
            # Add this near the other GUI elements in create_widgets()
        ttk.Label(self.root, text="Filter Alpha:").grid(row=3, column=0, padx=5, pady=5)
        self.alpha_entry = ttk.Entry(self.root, width=8)
        self.alpha_entry.insert(0, str(self.alpha))  # Set default value
        self.alpha_entry.grid(row=3, column=1, padx=5, pady=5)

        self.update_alpha_btn = ttk.Button(
            self.root, 
            text="Update Alpha",
            command=self.update_alpha
        )
        self.update_alpha_btn.grid(row=3, column=2, padx=5, pady=5)

        # Position displays
        ttk.Label(self.root, text="Trigger Position:").grid(row=0, column=0, padx=5, pady=5)
        self.trigger_pos = ttk.Label(self.root, text="0.00 rot", font=('Arial', 12))
        self.trigger_pos.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.root, text="Trigger Torque:").grid(row=0, column=2, padx=5, pady=5)
        self.trigger_torque = ttk.Label(self.root, text="0.00 Nm", font=('Arial', 12))
        self.trigger_torque.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(self.root, text="Gripper Position:").grid(row=1, column=0, padx=5, pady=5)
        self.gripper_pos = ttk.Label(self.root, text="0.00 rot", font=('Arial', 12))
        self.gripper_pos.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.root, text="Gripper Torque:").grid(row=1, column=2, padx=5, pady=5)
        self.gripper_torque = ttk.Label(self.root, text="0.00 Nm", font=('Arial', 12))
        self.gripper_torque.grid(row=1, column=3, padx=5, pady=5)
        
        # Control buttons
        self.go_btn = ttk.Button(self.root, text="GO", command=self.start_control)
        self.go_btn.grid(row=2, column=0, padx=5, pady=5)
        
        self.stop_btn = ttk.Button(self.root, text="STOP", command=self.stop_control, state=tk.DISABLED)
        self.stop_btn.grid(row=2, column=1, padx=5, pady=5)
        
        self.quit_btn = ttk.Button(self.root, text="QUIT", command=self.quit_app)
        self.quit_btn.grid(row=2, column=2, padx=5, pady=5)

        self.hometrig_btn = ttk.Button(
            self.root, 
            text="Home Trigger",
            command=lambda: asyncio.run_coroutine_threadsafe(self.home_trigger(), self.loop)
        )
        self.hometrig_btn.grid(row=0, column=5, padx=5, pady=5)

        self.homegrip_btn = ttk.Button(
            self.root, 
            text="Home Gripper",
            command=lambda: asyncio.run_coroutine_threadsafe(self.home_gripper(), self.loop)
        )
        self.homegrip_btn.grid(row=1, column=5, padx=5, pady=5)
    
    def update_alpha(self):
        """Update the alpha filtering value from the GUI input"""
        try:
            new_alpha = float(self.alpha_entry.get())
            if 0 <= new_alpha <= 1:
                self.alpha = new_alpha
                #messagebox.showinfo("Success", f"Alpha updated to {new_alpha}")
            else:
                #messagebox.showerror("Error", "Alpha must be between 0 and 1")
                self.alpha_entry.delete(0, tk.END)
                self.alpha_entry.insert(0, str(self.alpha))
        except ValueError:
            #messagebox.showerror("Error", "Please enter a valid number")
            self.alpha_entry.delete(0, tk.END)
            self.alpha_entry.insert(0, str(self.alpha))
        
    def update_positions(self, trigger_pos, gripper_pos, trigger_torque, gripper_torque):
        self.trigger_pos.config(text=f"{trigger_pos:.2f} rot")
        self.gripper_pos.config(text=f"{gripper_pos:.2f} rot")
        self.trigger_torque.config(text=f"{trigger_torque:.2f} Nm")
        self.gripper_torque.config(text=f"{gripper_torque:.2f} Nm")
        self.root.update()
        
    def start_monitoring(self):
        """Start the monitoring thread when app launches"""
        self.loop = asyncio.new_event_loop()
        self.monitor_task = Thread(target=self.run_monitoring, daemon=True)
        self.monitor_task.start()
        
    def start_control(self):
        if not self.running:
            self.running = True
            self.go_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Start control in the existing event loop
            asyncio.run_coroutine_threadsafe(self.motor_control(), self.loop)
            
    def stop_control(self):
        self.running = False
        self.go_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def quit_app(self):
        """Perform stop routine before quitting"""
        # First execute the stop routine
        self.stop_control()
        
        # Then destroy the window after a small delay to let things settle
        self.root.after(100, self.root.destroy)
        
    async def initialize_controllers(self):
        """Initialize motor controllers if they don't exist"""
        if 1 not in self.controllers:
            self.controllers[1] = moteus.Controller(id=1)
            await self.controllers[1].set_stop()
        if 2 not in self.controllers:
            self.controllers[2] = moteus.Controller(id=2)
            await self.controllers[2].set_stop()
        return self.controllers[1], self.controllers[2]
        
    async def motor_control(self):
        c1, c2 = await self.initialize_controllers()
        state1 = await c1.query()
        self.prevfiltpos = state1.values[moteus.Register.POSITION]

        try:
            while self.running:
                state1 = await c1.set_position(
                    position=float('nan'),
                    velocity=float('nan'),
                    maximum_torque=0.015,
                    query=True
                )
                position = state1.values[moteus.Register.POSITION]
                filtered = self.alpha * self.prevfiltpos + (1 - self.alpha) * position
                await c2.set_position(
                    position=7-filtered,
                    maximum_torque=0.1,
                    query=True
                )
                self.prevfiltpos = position
                await asyncio.sleep(1/1000)
                
        finally:
            await c1.set_stop()
            await c2.set_stop()
            
    async def monitor_motors(self):
        """Continuous monitoring of motor positions and torques"""
        while self.monitoring:
            try:
                c1, c2 = await self.initialize_controllers()
                
                # Query motor states without sending commands
                state1 = await c1.query()
                state2 = await c2.query()
                
                if state1 and state2:
                    trigger_pos = state1.values[moteus.Register.POSITION]
                    gripper_pos = state2.values[moteus.Register.POSITION]
                    trigger_torque = state1.values[moteus.Register.TORQUE]
                    gripper_torque = state2.values[moteus.Register.TORQUE]
                    
                    self.root.after(0, self.update_positions, 
                                  trigger_pos, gripper_pos,
                                  trigger_torque, gripper_torque)
                
                await asyncio.sleep(1/1000)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(1.0)  # Wait before retrying
    
    async def home_trigger(self):
        """Home the trigger motor by moving until torque limit is reached, then zero position"""
        try:
            if self.homing_trigger:  # Already homing
                return
                
            self.homing_trigger = True
            self.hometrig_btn.config(state=tk.DISABLED)  # Disable button during homing
            
            c1, c2 = await self.initialize_controllers()
            
            # First stop any existing motion
            await c1.set_stop()
            await asyncio.sleep(0.1)  # Brief pause
            
            # Start moving slowly in negative direction
            homing__trigger_success = False
            while self.homing_trigger:
                state = await c1.set_position(
                    position=float('nan'),  # Velocity control mode
                    velocity=-0.5,         # Move slowly in negative direction
                    maximum_torque=0.03,    # Set a reasonable torque limit
                    query=True
                )
                
                # Check if we've hit the torque limit (negative torque means hitting the stop)
                if state and state.values[moteus.Register.TORQUE] < -0.02:
                    # Zero the position
                    await self.stream.command(b'd exact 0')
                    await asyncio.sleep(0.1)  # Wait for command to take effect
                    homing__trigger_success = True
                    break
                    
                await asyncio.sleep(0.01)
                
            if homing__trigger_success:
                self.root.after(0, messagebox.showinfo, "Success", "Trigger homing completed")
                
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Homing failed: {str(e)}")
        finally:
            self.homing_trigger = False
            self.root.after(0, lambda: self.hometrig_btn.config(state=tk.NORMAL))
            await c1.set_stop()

    async def home_gripper(self):
        """Home the gripper motor by moving until torque limit is reached, then zero position"""
        try:
            if self.homing_gripper:  # Already homing
                return
                
            self.homing_gripper = True
            self.homegrip_btn.config(state=tk.DISABLED)  # Disable button during homing
            
            c1, c2 = await self.initialize_controllers()
            
            # First stop any existing motion
            await c2.set_stop()
            await asyncio.sleep(0.1)  # Brief pause
            
            # Start moving slowly in negative direction
            homing__gripper_success = False
            while self.homing_gripper:
                state = await c2.set_position(
                    position=float('nan'),  # Velocity control mode
                    velocity=0.5,         # Move slowly in negative direction
                    maximum_torque=0.05,    # Set a reasonable torque limit
                    query=True
                )
                
                # Check if we've hit the torque limit (negative torque means hitting the stop)
                if state and state.values[moteus.Register.TORQUE] > 0.03:
                    # Zero the position
                    await self.stream.command(b'd exact 7')
                    await asyncio.sleep(0.1)  # Wait for command to take effect
                    homing__gripper_success = True
                    break
                    
                await asyncio.sleep(0.01)
                
            if homing__gripper_success:
                self.root.after(0, messagebox.showinfo, "Success", "Gripper homing completed")
                
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Homing failed: {str(e)}")
        finally:
            self.homing_gripper = False
            self.root.after(0, lambda: self.homegrip_btn.config(state=tk.NORMAL))
            await c2.set_stop()
            
    def run_monitoring(self):
        """Run the monitoring loop"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.monitor_motors())

def main():
    root = tk.Tk()
    app = MotorControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()

if __name__ == '__main__':
    main()