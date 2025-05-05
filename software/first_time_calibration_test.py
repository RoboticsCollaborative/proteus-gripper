# Script by Boon Yang Koh, Northeastern University, last major revision 5/5/2025

# This script is used for the first time operation of the Moteus controller and motor combination.
# Before assembling the motor into the gripper, please calibrate and test the motors using this app.
# Steps to follow:
    # 1. Ensure this file is able to access the Moteus library, place in \moteus\moteus\lib\python
    # 2. Ensure the correct firmware is on the controller you want to calibrate.
        # a. Refer to the Moteus Reference by Josh Pieper on how to update firmware
    # 3. Open Moteus GUI (6) and ensure that the moteus is connected
    # 4. Calibrate and do compensation by running consolidated calibration and compensation (5)
    # 5. Test the motors using the command motor functions (10, 11 or 12)
    # 6. Change the Moteus Controller ID depending on use case
        #a. If used as a trigger, leave ID as default, 1
        #b. If used as a gripper, change ID to 2 on the Moteus GUI (6)
        #c. If used as a test controller or singular operating motor controller. leave as default, 1

# For detailed documentation on the Moteus GUI, refer to the Moteus Reference by Josh Pieper

import subprocess
import aioconsole
import asyncio
import moteus

# Initial Motor limits
MAX_VELOCITY = 2            # rad/s
MAX_ACCELERATION = 2        # rad/s²
MAX_TORQUE = 0.02           # Nm

MAX_VELOCITY_RESET = 2      # rad/s
MAX_ACCELERATION_RESET = 2  # rad/s²
MAX_TORQUE_RESET = 0.02     # Nm

#Set Controller ID
controller_id=1

def display_menu():
    """Display calibration options and get user input"""
    while True:

        print("\nMAIN MENU -- FIRST TIME CALIBRATION AND TEST SCRIPT")
        print("\nSet Controller ID:")
        print("0.   Set ID")

        print("\nCalibration procedures:")
        print("1.   Standard Calibration")
        print("2.   Encoder Compensation")
        print("3.   Re-run Standard Calibration")
        print("4.   Cogging Compensation")
        print("5.   Run consolidated calibration and compensation")

        print("\nRun Moteus GUI:")
        print("6.   Open Moteus GUI")

        print("\nConfigure parameters (temporary, for commanding motor):")
        print("7.  Velocity limits")
        print("8.  Acceleration limits")
        print("9.  Torque limits")

        print("\nCommand Motor:")
        print("10.  Fixed position mode (Input target correcting torque)")
        print("11.  Fixed velocity mode (Input target velocity)")
        print("12.  Move to mode (Input target position)")

        print("\nOther:")
        print("13.  Exit")

        choice = input("\nEnter your choice (1-13): ")
        
        if choice == "0":
            global controller_id
            print("\nCurrent controller ID is:", controller_id)
            controller_id = input("Enter motor controller ID (default is 1): ") or "1"
            controller_id = int(controller_id)  # Convert to integer
            print("Controller ID set to:", controller_id)
        elif choice == "1":
            run_encoder_calibration(controller_id)
        elif choice == "2":
            run_encoder_compensation()
        elif choice == "3":
            run_encoder_calibration(controller_id)
        elif choice == "4":
            run_cogging_compensation()
        elif choice == "5":
            print("Running consolidated calibration procedure, please save and close graphs when popped up!")
            run_encoder_calibration(controller_id)
            run_encoder_compensation()
            run_encoder_calibration(controller_id)
            run_cogging_compensation()
        elif choice == "6":
            run_tview()
        elif choice == "7":
            global MAX_VELOCITY
            print("\nCurrent velocity limit (temporary) is:", MAX_VELOCITY, ", reset value is: ", MAX_VELOCITY_RESET)
            vel_limit_input_choice = input("Enter your velocity limit or press 'r' to reset: ")
            if vel_limit_input_choice.strip().lower() == 'r':
                MAX_VELOCITY=MAX_VELOCITY_RESET
                print("Velocity limit reset to:", MAX_VELOCITY)
            else:
                MAX_VELOCITY=float(vel_limit_input_choice)
                print("Velocity limit set to:", MAX_VELOCITY)
        elif choice == "8":
            global MAX_ACCELERATION
            print("\nCurrent acceleration limit (temporary) is:", MAX_ACCELERATION, ", reset value is: ", MAX_ACCELERATION_RESET)
            accel_limit_input_choice = input("Enter your acceleration limit or press 'r' to reset: ")
            if accel_limit_input_choice.strip().lower() == 'r':
                MAX_ACCELERATION=MAX_ACCELERATION_RESET
                print("Acceleration limit reset to:", MAX_ACCELERATION)
            else:
                MAX_ACCELERATION=float(accel_limit_input_choice)
                print("Acceleration limit set to:", MAX_ACCELERATION)
        elif choice == "9":
            global MAX_TORQUE
            print("\nCurrent torque limit (temporary) is:", MAX_TORQUE, ", reset value is: ", MAX_TORQUE_RESET)
            torque_limit_input_choice = input("Enter your torque limit or press 'r' to reset to: ")
            if torque_limit_input_choice.strip().lower() == 'r':
                MAX_TORQUE=MAX_TORQUE_RESET
                print("Torque limit reset to:", MAX_TORQUE)
            else:
                MAX_TORQUE=float(torque_limit_input_choice)
                print("Torque limit reset to:", MAX_TORQUE)
        elif choice == "10":
            asyncio.run(fixed_position(controller_id))
        elif choice == "11":
            asyncio.run(fixed_velocity(controller_id))
        elif choice == "12":
            asyncio.run(move_to_motor_position(controller_id))
        elif choice == "13":
            print("\nExiting script.")
            break
        else:
            print("\nInvalid choice. Please enter a number between 1 and 19:")

def stop_and_reset_motor(controller_id):
    """Stop the motor and reset its state for calibration."""
    c = moteus.Controller(controller_id)
    c.set_stop()  # Stop and de-energize the motor
    print(f"Motor {controller_id} stopped and reset for calibration.")

#1, 3 - Encoder calibration
def run_encoder_calibration(controller_id):
    """Run the standard calibration script"""
    print("\nRunning standard calibration...")
    encoder_calibration_command = f"python -m moteus.moteus_tool --target {controller_id} --calibrate"
    subprocess.run(encoder_calibration_command, shell=True)

#2 - Encoder compensation
def run_encoder_compensation():
    """Run the encoder compensation script"""
    print("\nRunning encoder compensation...")
    encoder_compensation_command = f"python moteus/moteus/utils/compensate_encoder.py --plot"
    subprocess.run(encoder_compensation_command, shell=True)

#4 - Cogging compensation
def run_cogging_compensation():
    """Run the cogging compensation script"""
    print("\nRunning cogging compensation...")
    cogging_compensation_command = f"python moteus/moteus/utils/compensate_cogging.py --store --plot-results"
    subprocess.run(cogging_compensation_command, shell=True)

#5 - All in one calibration (done above)

#6 - Run TVIEW
def run_tview():
    """Opening Moteus GUI (tview)"""
    print("\nRunning Moteus GUI (tview)...")
    print("Close GUI window to return to main menu!")
    tview_command = f"python -m moteus_gui.tview --devices={controller_id}"
    subprocess.run(tview_command, shell=True)

#7 - Set velocity limits (done above)
#8 - Set acceleration limits (done above)
#9 - Set torque limits (done above)

#10 - Fixed Position motor command
async def fixed_position(controller_id):
    # Initialize the moteus controller
    c = moteus.Controller(controller_id)
    await c.set_stop()  # Ensure the motor is stopped initially

    target_position = 0.0  # Initial target position
    target_torque = MAX_TORQUE #Initial target torque
    running = True  # Flag to control the main loop

    async def read_user_input():
        """Coroutine to read user input asynchronously."""
        nonlocal target_position, target_torque, running
        while running:
            try:
                # Use aioconsole for non-blocking input
                user_input = await aioconsole.ainput("Enter a torque limit (Nm) or 'e' to exit: ")
                
                # Check if the user wants to exit
                if user_input.strip().lower() == 'e':
                    print("Exiting...")
                    running = False
                    break

                # Update the target position
                target_torque = float(user_input)
                print(f"New torque limit set: {target_torque:.3f} ")
            except ValueError:
                print("Invalid input. Please enter a number or 'e' to exit.")

    async def run_motor():
        """Coroutine to control the motor."""
        while running:
            # Command the motor to move to the target position
            await c.set_position(
                position=target_position,
                velocity_limit=MAX_VELOCITY,
                accel_limit=MAX_ACCELERATION,  # Use accel_limit instead of acceleration_limit
                maximum_torque=target_torque,
                query=False
            )
            await asyncio.sleep(0.01)  # Small delay to prevent busy-waiting

    # Run both coroutines concurrently
    await asyncio.gather(read_user_input(), run_motor())

    # Stop the motor before exiting
    print("Stopping motor...")
    await c.set_stop()

#11 - Fixed Position motor command
async def fixed_velocity(controller_id):
    # Initialize the moteus controller
    c = moteus.Controller(controller_id)
    await c.set_stop()  # Ensure the motor is stopped initially

    target_velocity = 0.0 #Initial target velocity
    running = True  # Flag to control the main loop

    async def read_user_input():
        """Coroutine to read user input asynchronously."""
        nonlocal target_velocity, running
        while running:
            try:
                # Use aioconsole for non-blocking input
                user_input = await aioconsole.ainput("Enter a fixed velocity (rad/s) or 'e' to exit: ")
                
                # Check if the user wants to exit
                if user_input.strip().lower() == 'e':
                    print("Exiting...")
                    running = False
                    break

                # Update the target position
                target_velocity = float(user_input)
                print(f"New velocity set: {target_velocity:.3f} ")
            except ValueError:
                print("Invalid input. Please enter a number or 'e' to exit.")

    async def run_motor():
        """Coroutine to control the motor."""
        while running:
            # Command the motor to move to the target position
            await c.set_position(
                position=float('nan'),
                velocity=target_velocity,
                maximum_torque=MAX_TORQUE,
                query=False
            )
            await asyncio.sleep(0.01)  # Small delay to prevent busy-waiting

    # Run both coroutines concurrently
    await asyncio.gather(read_user_input(), run_motor())

    # Stop the motor before exiting
    print("Stopping motor...")
    await c.set_stop()

#12 - Move-to motor command
async def move_to_motor_position(controller_id):
    # Initialize the moteus controller
    c = moteus.Controller(controller_id)
    await c.set_stop()  # Ensure the motor is stopped initially

    target_position = 0.0  # Initial target position
    running = True  # Flag to control the main loop

    async def read_user_input():
        """Coroutine to read user input asynchronously."""
        nonlocal target_position, running
        while running:
            try:
                # Use aioconsole for non-blocking input
                user_input = await aioconsole.ainput("Enter target position (rot) or 'e' to exit: ")
                
                # Check if the user wants to exit
                if user_input.strip().lower() == 'e':
                    print("Exiting...")
                    running = False
                    break

                # Update the target position
                target_position = float(user_input)
                print(f"New target position set: {target_position:.3f} ")
            except ValueError:
                print("Invalid input. Please enter a number or 'e' to exit.")

    async def run_motor():
        """Coroutine to control the motor."""
        while running:
            # Command the motor to move to the target position
            await c.set_position(
                position=target_position,
                velocity_limit=MAX_VELOCITY,
                accel_limit=MAX_ACCELERATION,  # Use accel_limit instead of acceleration_limit
                maximum_torque=MAX_TORQUE,
                query=False
            )
            await asyncio.sleep(0.01)  # Small delay to prevent busy-waiting

    # Run both coroutines concurrently
    await asyncio.gather(read_user_input(), run_motor())

    # Stop the motor before exiting
    print("Stopping motor...")
    await c.set_stop()

if __name__ == "__main__":
    display_menu()
