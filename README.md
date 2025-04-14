The goal of this project is to implement a cycle-accurate simulator for a subset of the RISC-V instruction set architecture (ISA). Specifically:

-The simulator will read imem.txt for instruction memory initialization and dmem.txt for data memory initialization.

-Each cycle, the simulator updates the processor state (PC, registers, control signals, etc.) according to the microarchitectural logic.

-After execution completes, the simulator outputs detailed logs:

 - Register file state after each cycle.
  
 - Microarchitectural state per cycle (control signals, pipeline stages, etc. if relevant).
  
 - Final data memory state at program completion.
  
