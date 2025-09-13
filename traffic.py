import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
from datetime import datetime, timedelta
from enum import Enum
import json

class TrafficState(Enum):
    NS_GREEN = "NS_Green"
    NS_YELLOW = "NS_Yellow" 
    EW_GREEN = "EW_Green"
    EW_YELLOW = "EW_Yellow"
    ALL_RED = "All_Red"

class EmergencyCommand(Enum):
    NONE = 0
    NS_PRIORITY = 1
    EW_PRIORITY = 2

class DenseThinHysteresis:
    """Phân loại mật độ giao thông với hysteresis"""
    def __init__(self, dense_thresh=15, thin_thresh=8):
        self.dense_thresh = dense_thresh
        self.thin_thresh = thin_thresh
        self.current_state = 0  # 0: thin, 1: dense
    
    def classify(self, count):
        if count >= self.dense_thresh:
            self.current_state = 1  # dense
        elif count <= self.thin_thresh:
            self.current_state = 0  # thin
        # Hysteresis: giữ nguyên state nếu ở giữa 2 ngưỡng
        return self.current_state

class TrafficController:
    def __init__(self):
        # States
        self.current_state = TrafficState.NS_GREEN
        self.state_start_time = time.time()
        
        # Timing parameters
        self.base_green_time = 30  # seconds
        self.yellow_time = 3
        self.all_red_time = 2
        self.emergency_green_time = 25
        
        # ML integration
        self.hysteresis = DenseThinHysteresis()
        self.ml_enabled = True
        self.ml_adjustment_factor = 0.5  # Điều chỉnh dựa trên ML
        
        # Emergency handling
        self.emergency_active = False
        self.emergency_command = EmergencyCommand.NONE
        self.emergency_start_time = 0
        self.pre_emergency_state = TrafficState.NS_GREEN
        
        # Schedule-based timing (giờ cao điểm vs bình thường)
        self.rush_hours = [(7, 9), (17, 19)]  # 7-9AM, 5-7PM
        self.rush_hour_multiplier = 1.3
        
        # Data logging
        self.log_data = {
            'timestamp': [],
            'state': [],
            'ns_light': [],
            'ew_light': [],
            'vehicle_count': [],
            'ml_state': [],
            'emergency': [],
            'duration': []
        }

    def is_rush_hour(self):
        """Kiểm tra có phải giờ cao điểm không"""
        current_hour = datetime.now().hour
        return any(start <= current_hour < end for start, end in self.rush_hours)

    def calculate_green_duration(self, ml_state, vehicle_count):
        """Tính thời gian đèn xanh dựa trên ML và lịch"""
        base_time = self.base_green_time
        
        # Điều chỉnh theo giờ cao điểm
        if self.is_rush_hour():
            base_time *= self.rush_hour_multiplier
        
        # Điều chỉnh theo ML (dense/thin)
        if self.ml_enabled and ml_state == 1:  # dense
            adjustment = base_time * self.ml_adjustment_factor
            base_time += adjustment
        
        # Clamp trong khoảng [15, 60] giây
        return max(15, min(60, int(base_time)))

    def handle_emergency(self, emergency_cmd):
        """Xử lý tình huống khẩn cấp"""
        if emergency_cmd != EmergencyCommand.NONE and not self.emergency_active:
            self.emergency_active = True
            self.emergency_command = emergency_cmd
            self.emergency_start_time = time.time()
            self.pre_emergency_state = self.current_state
            
            # Chuyển về All Red trước
            self.current_state = TrafficState.ALL_RED
            self.state_start_time = time.time()

    def update_state(self, vehicle_count=10, emergency_cmd=EmergencyCommand.NONE):
        """Cập nhật trạng thái hệ thống"""
        current_time = time.time()
        elapsed = current_time - self.state_start_time
        
        # Xử lý emergency
        if emergency_cmd != EmergencyCommand.NONE:
            self.handle_emergency(emergency_cmd)
        
        # ML classification
        ml_state = self.hysteresis.classify(vehicle_count)
        
        # State machine logic
        if self.emergency_active:
            self._handle_emergency_states(elapsed)
        else:
            self._handle_normal_states(elapsed, ml_state, vehicle_count)
        
        # Log data
        self._log_current_state(vehicle_count, ml_state, emergency_cmd)
        
        return self.get_light_states()

    def _handle_emergency_states(self, elapsed):
        """Xử lý các trạng thái trong tình huống khẩn cấp"""
        if self.current_state == TrafficState.ALL_RED:
            if elapsed >= self.all_red_time:
                # Chuyển sang đèn xanh ưu tiên
                if self.emergency_command == EmergencyCommand.NS_PRIORITY:
                    self.current_state = TrafficState.NS_GREEN
                else:  # EW_PRIORITY
                    self.current_state = TrafficState.EW_GREEN
                self.state_start_time = time.time()
        
        elif self.current_state in [TrafficState.NS_GREEN, TrafficState.EW_GREEN]:
            if elapsed >= self.emergency_green_time:
                # Kết thúc emergency, về vàng rồi quay lại chu kỳ
                if self.current_state == TrafficState.NS_GREEN:
                    self.current_state = TrafficState.NS_YELLOW
                else:
                    self.current_state = TrafficState.EW_YELLOW
                self.state_start_time = time.time()
                self.emergency_active = False

    def _handle_normal_states(self, elapsed, ml_state, vehicle_count):
        """Xử lý chu kỳ bình thường"""
        if self.current_state == TrafficState.NS_GREEN:
            green_duration = self.calculate_green_duration(ml_state, vehicle_count)
            if elapsed >= green_duration:
                self.current_state = TrafficState.NS_YELLOW
                self.state_start_time = time.time()
        
        elif self.current_state == TrafficState.NS_YELLOW:
            if elapsed >= self.yellow_time:
                self.current_state = TrafficState.ALL_RED
                self.state_start_time = time.time()
        
        elif self.current_state == TrafficState.EW_GREEN:
            green_duration = self.calculate_green_duration(ml_state, vehicle_count)
            if elapsed >= green_duration:
                self.current_state = TrafficState.EW_YELLOW
                self.state_start_time = time.time()
        
        elif self.current_state == TrafficState.EW_YELLOW:
            if elapsed >= self.yellow_time:
                self.current_state = TrafficState.ALL_RED
                self.state_start_time = time.time()
        
        elif self.current_state == TrafficState.ALL_RED:
            if elapsed >= self.all_red_time:
                # Chuyển sang pha tiếp theo trong chu kỳ
                if self.pre_emergency_state == TrafficState.NS_YELLOW or \
                   self.current_state == TrafficState.ALL_RED:
                    self.current_state = TrafficState.EW_GREEN
                else:
                    self.current_state = TrafficState.NS_GREEN
                self.state_start_time = time.time()

    def get_light_states(self):
        """Trả về trạng thái đèn hiện tại"""
        ns_lights = {'red': False, 'yellow': False, 'green': False}
        ew_lights = {'red': False, 'yellow': False, 'green': False}
        
        if self.current_state == TrafficState.NS_GREEN:
            ns_lights['green'] = True
            ew_lights['red'] = True
        elif self.current_state == TrafficState.NS_YELLOW:
            ns_lights['yellow'] = True
            ew_lights['red'] = True
        elif self.current_state == TrafficState.EW_GREEN:
            ns_lights['red'] = True
            ew_lights['green'] = True
        elif self.current_state == TrafficState.EW_YELLOW:
            ns_lights['red'] = True
            ew_lights['yellow'] = True
        elif self.current_state == TrafficState.ALL_RED:
            ns_lights['red'] = True
            ew_lights['red'] = True
        
        return ns_lights, ew_lights

    def _log_current_state(self, vehicle_count, ml_state, emergency_cmd):
        """Ghi log dữ liệu"""
        ns_lights, ew_lights = self.get_light_states()
        
        self.log_data['timestamp'].append(datetime.now())
        self.log_data['state'].append(self.current_state.value)
        self.log_data['ns_light'].append(self._lights_to_string(ns_lights))
        self.log_data['ew_light'].append(self._lights_to_string(ew_lights))
        self.log_data['vehicle_count'].append(vehicle_count)
        self.log_data['ml_state'].append(ml_state)
        self.log_data['emergency'].append(emergency_cmd.value)
        self.log_data['duration'].append(time.time() - self.state_start_time)

    def _lights_to_string(self, lights):
        """Chuyển trạng thái đèn thành chuỗi"""
        if lights['red']:
            return 'Red'
        elif lights['yellow']:
            return 'Yellow'
        elif lights['green']:
            return 'Green'
        return 'Off'

    def save_log(self, filename='traffic_log.csv'):
        """Lưu log ra file CSV"""
        df = pd.DataFrame(self.log_data)
        df.to_csv(filename, index=False)
        print(f"Log saved to {filename}")

class TrafficSimulator:
    """Mô phỏng hệ thống điều khiển đèn giao thông"""
    def __init__(self):
        self.controller = TrafficController()
        self.running = False
        
        # Visualization
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.setup_visualization()
        
        # Simulation parameters
        self.simulation_speed = 1.0  # 1.0 = real time
        self.vehicle_counts = []
        self.timestamps = []

        # CSV-driven simulation data (Track A integration)
        self.csv_df = None
        self.csv_idx = 0
        self.csv_enabled = False
        self.csv_vehicle_col = None
        self.csv_emergency_col = None
        self.csv_vehicle_components = []
        self.last_emergency_value = 0  # Track previous emergency state
        # Prefer calibrated dataset if present
        self._try_load_csv('vehicle_counts_calibrated.csv')
        if not self.csv_enabled:
            self._try_load_csv('vehicle_counts.csv')

    def setup_visualization(self):
        """Thiết lập giao diện hiển thị"""
        # Traffic lights visualization - Single column
        self.ax1.set_xlim(-1, 1)
        self.ax1.set_ylim(-1, 3)
        self.ax1.set_title('Smart Traffic Light System')
        self.ax1.set_aspect('equal')
        
        # Single traffic light column
        self.red_light = plt.Circle((0, 2), 0.2, color='gray')
        self.yellow_light = plt.Circle((0, 1), 0.2, color='gray')
        self.green_light = plt.Circle((0, 0), 0.2, color='gray')
        
        for light in [self.red_light, self.yellow_light, self.green_light]:
            self.ax1.add_patch(light)
        
        # Labels
       
       
        
        # Status text
        self.status_text = self.ax1.text(0, -0.8, '', ha='center', fontsize=10)
        
        # Vehicle count plot
        self.ax2.set_title('Vehicle Count & ML State')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Count / State')
        self.line1, = self.ax2.plot([], [], 'b-', label='Vehicle Count')
        self.line2, = self.ax2.plot([], [], 'r-', label='ML State (Dense/Thin)', linewidth=2)
        self.ax2.legend()
        self.ax2.grid(True)

    def update_visualization(self, frame):
        """Cập nhật hiển thị"""
        current_time = frame * 0.1
        
        # Prefer CSV-driven values if available
        if self.csv_enabled and self.csv_df is not None and not self.csv_df.empty:
            if self.csv_idx >= len(self.csv_df):
                self.csv_idx = 0  # loop
            row = self.csv_df.iloc[self.csv_idx]
            # Vehicle count
            if self.csv_vehicle_col and self.csv_vehicle_col in row.index:
                vehicle_count = int(max(0, float(row[self.csv_vehicle_col])))
            elif self.csv_vehicle_components:
                total_val = 0.0
                for c in self.csv_vehicle_components:
                    try:
                        total_val += float(row.get(c, 0) or 0)
                    except Exception:
                        continue
                vehicle_count = int(max(0, total_val))
            else:
                vehicle_count = 0
            # Emergency - only trigger when CSV changes from 0 to 1
            emergency_cmd = EmergencyCommand.NONE
            if self.csv_emergency_col and self.csv_emergency_col in row.index:
                try:
                    current_emg = int(float(row[self.csv_emergency_col]))
                except Exception:
                    current_emg = 1 if str(row[self.csv_emergency_col]).lower() in ['1', 'true', 'yes', 'y'] else 0
                
                # Only trigger emergency when CSV changes from 0 to 1
                if current_emg == 1 and self.last_emergency_value == 0:
                    csv_time = float(row['time_s']) if 'time_s' in row.index else current_time
                    print(f"🚨 EMERGENCY TRIGGERED! Time: {csv_time:.1f}s, Row: {self.csv_idx}")
                
                self.last_emergency_value = current_emg
            self.csv_idx += 1
        else:
            # Simulated vehicle count
            vehicle_count = int(10 + 8 * np.sin(current_time * 0.1) + 
                              5 * np.sin(current_time * 0.05) + 
                              3 * np.random.random())
            # Simulated emergency (rare)
            emergency_cmd = EmergencyCommand.NONE
            if np.random.random() < 0.002:
                emergency_cmd = EmergencyCommand(np.random.randint(1, 3))
        
        # Update controller
        ns_lights, ew_lights = self.controller.update_state(vehicle_count, emergency_cmd)
        
        # Update light colors - Single column shows current active direction
        if self.controller.current_state in [TrafficState.NS_GREEN, TrafficState.NS_YELLOW]:
            active_lights = ns_lights
        else:
            active_lights = ew_lights
        
        self.red_light.set_color('red' if active_lights['red'] else 'gray')
        self.yellow_light.set_color('yellow' if active_lights['yellow'] else 'gray')
        self.green_light.set_color('green' if active_lights['green'] else 'gray')
        
        # Update status
        ml_state = "DENSE" if self.controller.hysteresis.current_state else "THIN"
        emergency_status = "EMERGENCY!" if self.controller.emergency_active else "Normal"
        rush_status = "Rush Hour" if self.controller.is_rush_hour() else "Regular"
        
        status = f"State: {self.controller.current_state.value}\n"
        status += f"Vehicles: {vehicle_count} | ML: {ml_state}\n"
        status += f"{rush_status} | {emergency_status}"
        self.status_text.set_text(status)
        
        # Update plots
        self.timestamps.append(current_time)
        self.vehicle_counts.append(vehicle_count)
        
        if len(self.timestamps) > 200:  # Keep last 200 points
            self.timestamps = self.timestamps[-200:]
            self.vehicle_counts = self.vehicle_counts[-200:]
        
        self.line1.set_data(self.timestamps, self.vehicle_counts)
        ml_states = [self.controller.hysteresis.classify(count) * 20 
                    for count in self.vehicle_counts]  # Scale for visibility
        self.line2.set_data(self.timestamps, ml_states)
        
        if self.timestamps:
            self.ax2.set_xlim(max(0, self.timestamps[-1] - 20), self.timestamps[-1] + 1)
            self.ax2.set_ylim(0, max(35, max(self.vehicle_counts[-50:]) + 5))

    def _try_load_csv(self, csv_path):
        """Thử tải dữ liệu từ vehicle_counts.csv và cấu hình cột cần dùng"""
        try:
            df = pd.read_csv(csv_path)
            # Detect vehicle count column (prefer 'total', then 'vehicle_count', 'count', 'counts_ts')
            candidate_vehicle_cols = ['total', 'vehicle_count', 'count', 'counts_ts', 'vehicles']
            for c in df.columns:
                if c.lower() in [cv.lower() for cv in candidate_vehicle_cols]:
                    self.csv_vehicle_col = c
                    break
            # Detect emergency column
            candidate_emg_cols = ['EMERGENCY', 'emergency', 'is_emergency', 'priority']
            for c in df.columns:
                if c in candidate_emg_cols or c.lower() in [ce.lower() for ce in candidate_emg_cols]:
                    self.csv_emergency_col = c
                    break
            # If no single vehicle count column, try to derive by summing components
            if self.csv_vehicle_col is None:
                # candidate component columns commonly found
                component_candidates = ['car', 'truck', 'bus', 'motorbike', 'bike', 'van', 'suv', 'police_car']
                detected = []
                lower_cols = {c.lower(): c for c in df.columns}
                for cand in component_candidates:
                    if cand in lower_cols:
                        detected.append(lower_cols[cand])
                # As a fallback, include all numeric columns except time-like and emergency columns
                if not detected:
                    exclude_like = ['time', 'timestamp', 'date', 'datetime']
                    for c in df.columns:
                        if c == self.csv_emergency_col:
                            continue
                        lc = c.lower()
                        if any(x in lc for x in exclude_like):
                            continue
                        if pd.api.types.is_numeric_dtype(df[c]):
                            detected.append(c)
                # keep at least one
                if detected:
                    self.csv_vehicle_components = detected
            if self.csv_vehicle_col is not None:
                self.csv_df = df
                self.csv_enabled = True
                print(f"Loaded CSV '{csv_path}' with vehicle column '{self.csv_vehicle_col}'" +
                      (f" and emergency column '{self.csv_emergency_col}'" if self.csv_emergency_col else ""))
            elif self.csv_vehicle_components:
                self.csv_df = df
                self.csv_enabled = True
                comps = ','.join(self.csv_vehicle_components)
                print(f"Loaded CSV '{csv_path}' using component columns [{comps}]" +
                      (f" and emergency column '{self.csv_emergency_col}'" if self.csv_emergency_col else ""))
            else:
                print(f"CSV '{csv_path}' found but no vehicle count column detected; using simulation")
        except FileNotFoundError:
            print(f"CSV '{csv_path}' not found; using simulation data")

    def run_simulation(self, duration=300):
        """Chạy mô phỏng"""
        print("Starting Smart Traffic Light Simulation...")
        print("Features:")
        print("- ML-based density classification with hysteresis")
        print("- Schedule-based timing (rush hour detection)")
        print("- Emergency vehicle priority")
        print("- Real-time visualization")
        print("\nPress Ctrl+C to stop simulation")
        
        try:
            # Animation
            ani = FuncAnimation(self.fig, self.update_visualization, 
                              frames=int(duration * 10), 
                              interval=100, blit=False, repeat=True)
            plt.tight_layout()
            plt.show()
            
        except KeyboardInterrupt:
            print("\nSimulation stopped by user")
        finally:
            # Save log
            self.controller.save_log('smart_traffic_log.csv')
            print("Simulation data saved!")

    def load_vehicle_data(self, csv_file):
        """Tải dữ liệu xe từ Track A (nếu có)"""
        try:
            df = pd.read_csv(csv_file)
            if 'vehicle_count' in df.columns:
                return df['vehicle_count'].tolist()
            elif 'counts_ts' in df.columns:
                return df['counts_ts'].tolist()
        except FileNotFoundError:
            print(f"File {csv_file} not found, using simulated data")
        return None

# Demo và test functions
def demo_controller():
    """Demo cơ bản controller"""
    print("=== Traffic Controller Demo ===")
    controller = TrafficController()
    
    for i in range(20):
        # Simulate varying vehicle counts
        vehicle_count = 10 + int(10 * np.sin(i * 0.5))
        
        # Random emergency
        emergency = EmergencyCommand.NONE
        if i == 10:  # Emergency at step 10
            emergency = EmergencyCommand.NS_PRIORITY
        
        ns_lights, ew_lights = controller.update_state(vehicle_count, emergency)
        
        print(f"Step {i+1}: Vehicles={vehicle_count}, "
              f"NS={controller._lights_to_string(ns_lights)}, "
              f"EW={controller._lights_to_string(ew_lights)}, "
              f"State={controller.current_state.value}")
        
        time.sleep(0.5)
    
    # Save log
    controller.save_log('demo_log.csv')

def main():
    """Main function"""
    print("Smart Traffic Light Control System (Track B)")
    print("=" * 50)
    print("1. Run full simulation with visualization")
    print("2. Run basic controller demo")
    print("3. Exit")
    
    choice = input("Select option (1-3): ")
    
    if choice == '1':
        simulator = TrafficSimulator()
        simulator.run_simulation(300)  # 5 minutes
    elif choice == '2':
        demo_controller()
    elif choice == '3':
        print("Goodbye!")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()