import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import tkinter as tk
from pymongo import MongoClient
# Connect to MongoDB
client = MongoClient("mongodb://localhost:27018")
db = client["flight_database"]  # Use your database name
collection = db["flights"]  # Use your collection name

def submit(self):
    # Collect flight information
    # ...

    # Insert flight information into MongoDB
    flight_document = {
        "flight_number": self.flight_info["Flight Number"],
        "model": self.flight_info["Model"],
        "source": self.flight_info["Source"],
        "destination": self.flight_info["Destination"],
        "heading": self.flight_info["Heading"],
        "status": self.flight_info["Status"],
        "runway_number": self.flight_info.get("Runway Number"),
        "gate_number": self.flight_info.get("Gate Number"),
        "level": self.flight_info.get("Level")
    }
    collection.insert_one(flight_document)

    # Destroy entry widgets and update UI
    # ...

# everything except mongo db is done
class Window:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Flight Information")
        self.root.geometry("250x250")

class FlightWindow:
    def __init__(self, flight_info, blimp, button, radar_display):
        self.flight_info = flight_info
        self.blimp = blimp
        self.button = button
        self.radar_display = radar_display
        self.root = tk.Tk()
        self.root.title("Flight Details")
        self.root.geometry("400x300")  # Set a larger size for the window
        self.cancel_id = None  # Initialize cancel_id attribute

        for i, (key, value) in enumerate(flight_info.items()):
            if key == "Status":
                if value == "Passing":
                    tk.Label(self.root, text="Status: Passing").grid(row=i, column=0, sticky="w")
                else:
                    tk.Label(self.root, text=f"{key}: {value}").grid(row=i, column=0, sticky="w")
            elif key not in ["Source", "Destination"]:  # Exclude source and destination
                tk.Label(self.root, text=f"{key}: {value}").grid(row=i, column=0, sticky="w")

        if flight_info["Status"] != "Passing":
            if flight_info["Status"] == "Takeoff":
                tk.Label(self.root, text="Destination:").grid(row=i+1, column=0, sticky="w")
                tk.Label(self.root, text=flight_info["Destination"]).grid(row=i+1, column=1, sticky="w")
            if flight_info["Status"] == "Landing":
                tk.Label(self.root, text="Source:").grid(row=i+2, column=0, sticky="w")
                tk.Label(self.root, text=flight_info["Source"]).grid(row=i+2, column=1, sticky="w")
            if flight_info["Status"] != "Passing":
                tk.Label(self.root, text="Runway Number:").grid(row=i+3, column=0, sticky="w")
                self.runway_entry = tk.Entry(self.root)
                self.runway_entry.grid(row=i+3, column=1)

                tk.Label(self.root, text="Boarding/Arrival Gate Number:").grid(row=i+4, column=0, sticky="w")
                self.gate_entry = tk.Entry(self.root)
                self.gate_entry.grid(row=i+4, column=1)

        tk.Label(self.root, text="Heading:").grid(row=i+5, column=0, sticky="w")
        self.heading_entry = tk.Entry(self.root)
        self.heading_entry.grid(row=i+5, column=1)

        tk.Label(self.root, text="Level:").grid(row=i+6, column=0, sticky="w")
        self.level_entry = tk.Entry(self.root)
        self.level_entry.grid(row=i+6, column=1)

        tk.Button(self.root, text="Submit", command=self.submit).grid(row=i+7, columnspan=2)

    def submit(self):
        if self.flight_info["Status"] != "Passing":
            runway = self.runway_entry.get()
            gate = self.gate_entry.get()
            self.flight_info["Runway Number"] = runway
            self.flight_info["Gate Number"] = gate

        heading = self.heading_entry.get()
        level = self.level_entry.get()
        self.flight_info["Heading"] = heading
        self.flight_info["Level"] = level

        # Store references to entry widgets
        entries = [self.heading_entry, self.level_entry]
        if self.flight_info["Status"] != "Passing":
            entries.extend([self.runway_entry, self.gate_entry])

        # Destroy entry widgets
        for entry in entries:
            entry.destroy()

        # Display flight information labels
        row = 0
        for key, value in self.flight_info.items():
            if key == "Status":
                if value == "Passing":
                    tk.Label(self.root, text="Status: Passing").grid(row=row, column=0, sticky="w")
                else:
                    tk.Label(self.root, text=f"{key}: {value}").grid(row=row, column=0, sticky="w")
            elif key not in ["Source", "Destination"]:  # Exclude source and destination
                tk.Label(self.root, text=f"{key}: {value}").grid(row=row, column=0, sticky="w")
            row += 1

        # Schedule blimp and button removal after a random time interval between 10 to 20 seconds
        delay = random.randint(1000, 2000)  # milliseconds
        self.cancel_id = self.root.after(delay, self.remove_blimp_and_button)

        print("Flight Info Dict Length:", len(self.radar_display.flight_info))
        print("Finished Dict Length:", len(self.radar_display.finished))

    def remove_blimp_and_button(self):
        del self.radar_display.blimps[self.blimp]  # Remove blimp from the dictionary
        self.button.destroy()
        self.radar_display.redraw_plot()
        self.radar_display.add_blimp_and_button_delayed()  # Add new blimp and button after a delay
        self.radar_display.move_to_finished(self.flight_info)  # Move flight to finished dictionary

        # Cancel the scheduled event
        if self.cancel_id:
            self.root.after_cancel(self.cancel_id)



class RadarDisplay:
    def __init__(self, window):
        self.window = window
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_aspect('equal')
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.set_facecolor('black')  # Set black background for the radar display
        self.blimps = {}  # Dictionary to store blimp plots
        self.buttons = {}  # Dictionary to store button widgets
        self.flight_info = []  # List to store flight information dictionaries
        self.finished = {}  # Dictionary to store finished flight information
        self.current_flight_index = 0  # Track the current flight index
        self.create_flight_info()  # Generate flight information
        self.create_initial_blimps()  # Create initial blimps to display

        # Add rotating lime-colored line
        self.rotating_line, = self.ax.plot([], [], color='lime', linewidth=2)
        self.animation = animation.FuncAnimation(self.fig, self.update_rotation, frames=360, interval=10)

    def create_flight_info(self):
        # Generate flight information dictionaries
        num_flights = random.randint(10, 20)
        for _ in range(num_flights):
            flight_info = self.generate_flight_info()
            self.flight_info.append({"info": flight_info, "taken_care_of": False})  # Mark flights as not taken care of initially

    def create_initial_blimps(self):
        # Create initial blimps to display (up to 5)
        for _ in range(5):
            self.add_blimp_and_button()

    def add_blimp_and_button(self):
        if self.current_flight_index < len(self.flight_info):
            flight_info = self.flight_info[self.current_flight_index]["info"]
            x = random.uniform(-10, 10)
            y = random.uniform(-10, 10)
            flight_number = flight_info["Flight Number"]
            blimp = self.ax.annotate(flight_number, (x, y), color='lime', fontsize=15, ha='center')  # Set blimp color to green
            self.blimps[blimp] = flight_info
            button_text = f"{flight_number}\n(Blimp {self.current_flight_index + 1})"
            button = tk.Button(self.window.root, text=button_text)
            button.grid(row=len(self.blimps) + 1, column=0, pady=5)
            self.buttons[blimp] = button
            button.config(command=lambda b=blimp: self.open_flight_window(b))
            self.current_flight_index += 1

    def add_blimp_and_button_delayed(self):
        if self.current_flight_index < len(self.flight_info):
            delay = random.randint(10000, 20000)  # milliseconds
            self.window.root.after(delay, lambda: self.add_blimp_and_button())

    def open_flight_window(self, blimp):
        flight_info = self.blimps[blimp]
        button = self.buttons[blimp]
        FlightWindow(flight_info, blimp, button, self)  # Pass blimp object as argument

    def move_to_finished(self, flight_info):
        for flight in self.flight_info:
            if flight["info"] == flight_info:
                self.finished[flight_info["Flight Number"]] = flight_info
                self.flight_info.remove(flight)
                break

    def update_rotation(self, frame):
        radius = 10
        x = [0, radius * np.sin(np.radians(frame))]
        y = [0, radius * np.cos(np.radians(frame))]
        self.rotating_line.set_data(x, y)
        return self.rotating_line,

    def generate_flight_info(self):
        # Generate random flight information
        flight_number = f"FL{random.randint(1, 100)}"
        model = random.choice(["Boeing 737", "Airbus A320", "Boeing 787", "Airbus A380"])
        source = random.choice(["New York", "Los Angeles", "London", "Tokyo", "Paris"])
        destination = random.choice(["Sydney", "Dubai", "Beijing", "Singapore", "Toronto"])
        heading = random.randint(0, 360)  # Random heading in degrees
        status = random.choice(["Landing", "Takeoff", "Passing"])
        return {
            "Flight Number": flight_number,
            "Model": model,
            "Source": source,
            "Destination": destination,
            "Heading": heading,
            "Status": status
        }

    def redraw_plot(self):
        self.ax.clear()
        self.ax.set_aspect('equal')
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.rotating_line, = self.ax.plot([], [], color='lime', linewidth=2)
        self.animation = animation.FuncAnimation(self.fig, self.update_rotation, frames=360, interval=10, init_func=self.init_rotation)
        for blimp, flight_info in self.blimps.items():
            x, y = blimp.get_position()  # Retrieve position of the blimp annotation
            flight_number = flight_info["Flight Number"]
            self.ax.annotate(flight_number, (x, y), color='lime', fontsize=15, ha='center')  # Annotate blimps with flight number
        plt.draw()

    def init_rotation(self):
        self.rotating_line.set_data([], [])
        return self.rotating_line,


# Usage
if __name__ == "__main__":
    window = Window()
    radar_display = RadarDisplay(window)
    plt.show()
