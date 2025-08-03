
# ML/AI-Integrated Traffic Lights with MATLAB/Simulink

An intelligent traffic light control system developed in **MATLAB & Simulink**, leveraging machine learning and AI to optimize traffic flow through simulation and real-time decision-making.

---

## Key Features 
- **Simulink-based traffic modeling** with dynamic signal control
- **Machine Learning integration** (MATLAB’s Statistics and ML Toolbox)
- **Computer vision** for vehicle detection (using MATLAB’s Image Processing Toolbox)
- **Stateflow** for adaptive traffic light state management
- **Hardware-in-the-loop (HIL) support** (e.g., Arduino/Raspberry Pi deployment)

---

## System Architecture 
```mermaid
graph TD
    A[Traffic Camera Input] --> B(MATLAB Image Processing)
    B --> C{ML Model: Vehicle/Pedestrian Detection}
    C --> D[Simulink Traffic Light Controller]
    D --> E[Stateflow Logic]
    E --> F[Output: Signal Timing Adjustments]
