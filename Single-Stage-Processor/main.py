import os
import argparse

MemSize = 1000  # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.


# convert to signed int

def signed_int(s, base, bits=32):
    number = int(s, base)
    if number >= 2 ** (bits - 1):
        number -= 2 ** bits
    return number


# convert to binary
def int_to_bin(n, width=32):
    return bin(n & (2 ** width - 1))[2:].zfill(width)


class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name

        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]
        print(self.IMem)

    def Length(self):
        return len(self.IMem)

    def readInstr(self, ReadAddress):

        if ReadAddress >= 0 and ReadAddress < (len(self.IMem)):
            start_add = ReadAddress - (ReadAddress % 4)
            instruction_b = self.IMem[start_add] + self.IMem[start_add + 1] + self.IMem[start_add + 2] + self.IMem[
                start_add + 3]

            return instruction_b
        else:
            return "00000000"


class DataMem(object):
    def __init__(self, name, iDir, oDir):
        self.id = name
        self.iDir = iDir
        self.oDir = oDir
        with open(iDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

        self.DMem += ['0'] * (MemSize - len(self.DMem))

    def readInstr(self, ReadAddress):
        # read data memory
        # return 32 bit hex val
        if ReadAddress >= 0 and ReadAddress < (len(self.DMem)):
            start_add = ReadAddress - (ReadAddress % 4)
            instruction_b = self.DMem[start_add] + self.DMem[start_add + 1] + self.DMem[start_add + 2] + self.DMem[
                start_add + 3]

            return instruction_b
        else:
            return "00000000"

    def writeDataMem(self, Address, WriteData):
        start_add = Address - (Address % 4)
        self.DMem[start_add] = WriteData[0:8]
        self.DMem[start_add + 1] = WriteData[8:16]
        self.DMem[start_add + 2] = WriteData[16:24]
        self.DMem[start_add + 3] = WriteData[24:32]

    def outputDataMem(self):
        resPath = os.path.join(self.oDir, self.id + "_DMEMResult.txt")
        with open(resPath, "w") as rp:
            rp.writelines([str(data).zfill(8) + "\n" for data in self.DMem])


class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = ['0' for i in range(32)]

    def readRF(self, Reg_addr):
        if Reg_addr >= 0 and Reg_addr <= 31:
            return self.Registers[Reg_addr]

    def writeRF(self, Reg_addr, Wrt_reg_data):
        if Reg_addr >= 0 and Reg_addr <= 31:
            self.Registers[Reg_addr] = Wrt_reg_data

    def outputRF(self, cycle):
        op = ["-" * 70 + "\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        op.extend([str(val).zfill(32) + "\n" for val in self.Registers])
        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)


class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": False, "Instr": 0}


class Core(object):
    def __init__(self, iDir, oDir, imem, dmem):
        self.myRF = RegisterFile(oDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.oDir=oDir
        self.iDir=iDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem
        self.offset = 0
        self.ALUop = 0
        self.write_back = 0
        self.wrt_mem = 0
        self.Result = 0
        self.I_type = False
        self.instruction = 0
        self.read_data1 = 0
        self.read_data2 = 0
        self.rd = 0
        self.imm = 0
        self.instruction_count = 0
        self.mem_store_data = 0
        self.mem_wrt_reg_add = 0
        self.wb_write_data = 0
        self.IC=0

    def fetch_instruction(self):
        PC = self.state.IF["PC"]
        instruction_word = self.ext_imem.readInstr(PC)

        self.instruction = instruction_word
        self.instruction_count += 1

    # Decodes the instruction and decides the operation to be performed in the execute stage; reads the operands from the register file.
    def decode_instruction(self):
        instruction_word = self.instruction
        print(instruction_word)
        instruction_b = instruction_word.zfill(32)

        opcode = instruction_b[25:32]
        func3 = instruction_b[17:20]
        func7 = instruction_b[0:7]

        # R-Type
        if opcode == '0110011':
            rs2 = instruction_b[7:12].zfill(5)  # rs2
            rs1 = instruction_b[12:17].zfill(5)  # rs1

            self.rd = instruction_b[20:25].zfill(5)

            self.read_data1 = self.myRF.readRF(int(rs1, 2))
            self.read_data2 = self.myRF.readRF(int(rs2, 2))
            self.write_back = 0
            if func7 == '0000000':
                # ADD
                if func3 == '000':
                    self.ALUop = 0
                # XOR
                elif func3 == '100':
                    self.ALUop = 1
                # OR
                elif func3 == '110':
                    self.ALUop = 2
                # AND
                elif func3 == '111':
                    self.ALUop = 3

            elif func7 == '0100000':
                # SUB
                if func3 == '000':
                    self.ALUop = 4

        # I Type
        elif opcode == '0010011':
            rs1 = instruction_b[12:17].zfill(5)  # rs1
            self.rd = instruction_b[20:25].zfill(5)  # rd
            self.imm = instruction_b[0:12].zfill(12)
            self.read_data1 = self.myRF.readRF(int(rs1, 2))
            self.read_data2 = self.imm
            self.write_back = 0
            # ADDI
            if func3 == '000':
                self.ALUop = 5
            # XORI
            elif func3 == '100':
                self.ALUop = 6
            # ORI
            elif func3 == '110':
                self.ALUop = 7
            # ANDI
            elif func3 == '111':
                self.ALUop = 8


        # LW
        elif opcode == '0000011':
            self.ALUop = 9
            rs1 = instruction_b[12:17].zfill(5)
            self.rd = instruction_b[20:25].zfill(5)
            self.imm = instruction_b[0:12].zfill(12)
            self.read_data1 = self.myRF.readRF(int(rs1, 2))
            self.read_data2 = self.imm
            self.write_back = 0

        # S Type
        elif opcode == '0100011':
            self.ALUop = 10
            rs2 = instruction_b[7:12]  # rs2
            rs1 = instruction_b[12:17]  # rs1
            self.imm = instruction_b[0:7] + instruction_b[20:25]
            self.read_data1 = self.myRF.readRF(int(rs1, 2))
            self.read_data2 = self.imm
            self.rd = self.myRF.readRF(int(rs2, 2))
            self.write_back = 1






        # JAL
        elif opcode == '1101111':
            self.ALUop = 13
            self.rd = instruction_b[20:25]
            self.imm = instruction_b[0] + instruction_b[12:20] + instruction_b[11] + instruction_b[1:11] + '0'
            self.write_back = 0
            self.I_type = True
            self.offset = self.imm

        # SB-Type
        elif opcode == '1100011':
            rs2 = instruction_b[7:12]
            rs1 = instruction_b[12:17]
            self.read_data1 = self.myRF.readRF(int(rs1, 2))
            self.read_data2 = self.myRF.readRF(int(rs2, 2))
            self.imm = instruction_b[0] + instruction_b[24] + instruction_b[1:7] + instruction_b[20:24] + '0'
            self.offset = self.imm
            self.I_type = True
            self.write_back = 1
            # BEQ
            if func3 == '000':
                self.ALUop = 11
            # BNE
            elif func3 == '001':
                self.ALUop = 12

        elif opcode == '1111111':

            self.nextState.IF["nop"] = True

    # Executes the ALU operation based on ALUop
    def execute_instruction(self):
        if self.ALUop == 0 or self.ALUop == 5:
            self.Result = int_to_bin(
                signed_int(self.read_data1, 2, len(self.read_data1)) + signed_int(self.read_data2, 2,
                                                                                  len(self.read_data2)))

        elif self.ALUop == 1 or self.ALUop == 6:
            self.Result = int_to_bin(
                signed_int(self.read_data1, 2, len(self.read_data1)) ^ signed_int(self.read_data2, 2,
                                                                                  len(self.read_data2)))

        elif self.ALUop == 3 or self.ALUop == 8:
            self.Result = int_to_bin(
                signed_int(self.read_data1, 2, len(self.read_data1)) & signed_int(self.read_data2, 2,
                                                                                  len(self.read_data2)))

        elif self.ALUop == 2 or self.ALUop == 7:
            self.Result = int_to_bin(
                signed_int(self.read_data1, 2, len(self.read_data1)) | signed_int(self.read_data2, 2,
                                                                                  len(self.read_data2)))

        elif self.ALUop == 4:
            self.Result = int_to_bin(
                signed_int(self.read_data1, 2, len(self.read_data2)) - signed_int(self.read_data2, 2,
                                                                                  len(self.read_data2)))

        elif self.ALUop == 9:
            self.mem_wrt_reg_add = int(
                signed_int(self.read_data1, 2) + signed_int(self.read_data2, 2, len(self.read_data2)))
            self.wrt_mem = 1

        elif self.ALUop == 10:
            self.mem_wrt_reg_add = int(
                signed_int(self.read_data1, 2) + signed_int(self.read_data2, 2, len(self.read_data2)))
            self.mem_store_data = self.rd
            self.wrt_mem = 2

        elif self.ALUop == 11:
            if signed_int(self.read_data1, 2) == signed_int(self.read_data2, 2):
                self.offset = signed_int(self.offset, 2, len(self.offset))
            else:
                self.I_type = False

        elif self.ALUop == 12:
            if signed_int(self.read_data1, 2) != signed_int(self.read_data2, 2):
                self.offset = signed_int(self.offset, 2, len(self.offset))
            else:
                self.I_type = False

        elif self.ALUop == 13:
            self.Result = int_to_bin(self.nextState.IF["PC"] + 4)
            self.offset = signed_int(self.offset, 2, len(self.offset))

    def memory_store(self):
        if self.wrt_mem == 1 and self.nextState.IF["nop"] == False:
            self.Result = dmem_ss.readInstr(self.mem_wrt_reg_add)

        elif self.wrt_mem == 2 and self.nextState.IF["nop"] == False:
            self.ext_dmem.writeDataMem(self.mem_wrt_reg_add, self.mem_store_data)

        #self.wb_write_data = self.Result

        if self.nextState.IF["nop"] == False:
            if self.I_type:
                self.nextState.IF["PC"] += int(self.offset)
            else:
                self.nextState.IF["PC"] += 4
        if self.state.IF["nop"] == False:
            self.IC += 1







    def write_Back_reg(self):
        if self.write_back == 0 and self.nextState.IF["nop"] == False:
            self.myRF.writeRF(int(self.rd, 2), self.Result)

    def performance_metrics(self):

        CPI = float(self.cycle) / (self.cycle - 1)
        IPC = 1 / CPI
        result_format = f"Performance of Single Stage:\n" \
                        f"Cycles ->  {self.cycle}\n" \
                        f"Instructions-> {self.cycle - 1}\n" \
                        f"CPI ->  {CPI}\n" \
                        f"IPC -> {IPC}"

        # resPath = self.ioDir + "_Peformancemetrics.txt"

        # with open(resPath, 'w') as file:
        # Write content into the file
        # file.write(result_format)
        with open(self.oDir[:-3] + "PerformanceMetrics.txt", 'w') as file:
            file.writelines(result_format)


class SingleStageCore(Core):
    def __init__(self,iDir,oDir, imem, dmem):
        super(SingleStageCore, self).__init__(iDir, os.path.join(oDir, 'SS_'), imem, dmem)
        self.opFilePath = os.path.join(oDir, 'StateResult_SS.txt')

    def step(self):
        self.fetch_instruction()
        self.decode_instruction()
        if self.state.IF["nop"]:
            self.write_back = 1
            self.wrt_mem = 0
            self.alu_op = 20
            self.I_type = False
            # print(self.instruction_count)
        if self.nextState.IF["nop"] != True:
            self.execute_instruction()
            self.memory_store()
            self.write_Back_reg()

        if self.state.IF["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        # The end of the cycle and updates the current state with the values calculated in this cycle
        self.state.IF["nop"] = self.nextState.IF["nop"]
        self.state.IF["PC"] = self.nextState.IF["PC"]
        self.cycle += 1
        self.alu_op = 0
        self.write_back = 0
        self.wrt_mem = 0
        self.I_type = False

    def printState(self, state, cycle):
        printstate = ["-" * 70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")

        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


if __name__ == "__main__":

    # parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    current_directory = os.getcwd()
    print("Current Working Directory:", current_directory)
    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)
    try:
        os.makedirs(os.path.join(ioDir, '..', 'output_nk3696'))
    except FileExistsError:
        print(f"")
    inDir = os.path.join(os.path.abspath(args.iodir), '..', 'input')
    print("Input Dir:", inDir)

    opDir = os.path.join(os.path.abspath(args.iodir), '..', 'output_nk3696')
    print("Input Directory:", opDir)

    _items = os.listdir(inDir)
    for item in _items:
        if os.path.isdir(os.path.join(inDir, item)):
            try:
                os.makedirs(os.path.join(opDir, item))
                print(f"Directory created")
            except FileExistsError:
                print(f"")

        itDir = os.path.join(inDir, item)
        otDir = os.path.join(opDir, item)

        imem = InsMem("Imem", itDir)
        dmem_ss = DataMem("SS", itDir, otDir)

        ssCore = SingleStageCore(itDir, otDir, imem, dmem_ss)

        while (True):
            if not ssCore.halted:
                ssCore.step()

            if ssCore.halted:
                break
        ssCore.performance_metrics()

        # dump SS and FS data mem.

        dmem_ss.outputDataMem()
