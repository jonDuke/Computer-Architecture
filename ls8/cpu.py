"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        # special registers
        self.pc = 0   # program counter, address of the currently executing instruction
        self.ir = 0   # instruction register, copy of the currently executing instruction
        self.mar = 0  # memory address register, holds the address we're reading or writing
        self.mdr = 0  # memory data register, holds the value to write, or the value just read

        # storage
        self.ram = [0] * 256   # RAM storage
        self.reg = [0] * 8     # register storage
        self.reg[7] = 0xF4     # R7 defaults to 0xF4 (stack pointer)

    def load(self, program):
        """Load a program into memory."""

        address = 0
        for instruction in program:
            self.ram[address] = instruction
            address += 1


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")
    
    def ram_read(self, address):
        """
        returns the value in RAM at the given address
        """
        # Ensure it is a valid address
        if address < len(self.ram) and address >= 0:
            return self.ram[address]
        else:
            raise IndexError(f"Invalid RAM address given: %02X" % address)
    
    def ram_write(self, value, address):
        """
        Writes a value to RAM at the given address
        """
        # Ensure it is a valid address
        if address < len(self.ram) and address >= 0:
            self.ram[address] = value
        else:
            raise IndexError(f"Invalid RAM address given: %02X" % address)

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.

        Prints all values in hexidecimal.
        """

        # Print the program counter and the next 3 RAM values
        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        # Print all register values
        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        running = True
        while running:
            # Fetch the next instruction
            self.ir = self.ram_read(self.pc)

            # Decode then execute
            if self.ir == 0b10000010:  # LDI
                # Set the value of a register to an integer
                self.mar = self.ram_read(self.pc + 1)  # Load register number
                self.mdr = self.ram_read(self.pc + 2)  # Load the integer we are storing
                self.reg[self.mar] = self.mdr  # Store that value

            elif self.ir == 0b01000111:  # PRN
                # Print numeric value stored in the given register
                self.mar = self.ram_read(self.pc + 1)  # Load register number
                self.mdr = self.reg[self.mar]  # load the number from the register
                print(self.mdr)  # print the number

            elif self.ir == 0b00000001:  # HLT
                # Halt the emulator
                running = False

            else:
                raise Exception(f"Instruction code not implemented: %02X" % self.ir)
            
            # increment the program counter according to the 1st 2 bits of ir
            self.pc += (self.ir >> 6) + 1
