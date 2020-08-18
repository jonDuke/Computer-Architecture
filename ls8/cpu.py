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

        # Standard operations
        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "DIV":
            self.reg[reg_a] /= self.reg[reg_b]
        elif op == "MOD":
            self.reg[reg_a] %= self.reg[reg_b]
        elif op == "DEC":
            self.reg[reg_a] -= 1
        elif op == "INC":
            self.reg[reg_a] += 1
        
        # Bitwise operations
        elif op == "AND":
            self.reg[reg_a] &= self.reg[reg_b]
        elif op == "OR":
            self.reg[reg_a] |= self.reg[reg_b]
        elif op == "XOR":
            self.reg[reg_a] ^= self.reg[reg_b]
        elif op == "NOT":
            self.reg[reg_a] = ~self.reg[reg_a]
        elif op == "SHL":
            self.reg[reg_a] <<= self.reg[reg_b]
        elif op == "SHR":
            self.reg[reg_a] >>= self.reg[reg_b]

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
            
            elif self.ir == 0b10100000:  # ADD
                # Add the values of two registers, store in reg A
                self.alu("ADD", self.ram_read(self.pc+1),
                                self.ram_read(self.pc+2))
            
            elif self.ir == 0b10100001:  # SUB
                # Subtract the value of reg A from reg B, store in reg A
                self.alu("SUB", self.ram_read(self.pc+1),
                                self.ram_read(self.pc+2))
            
            elif self.ir == 0b10100010:  # MUL
                # Multiply the values of two registers, store in reg A
                self.alu("MUL", self.ram_read(self.pc+1),
                                self.ram_read(self.pc+2))

            elif self.ir == 0b10100001:  # DIV
                # Divide the value of reg A by reg B, store in reg A
                self.alu("DIV", self.ram_read(self.pc+1),
                                self.ram_read(self.pc+2))
            
            elif self.ir == 0b10100100:  # MOD
                # Divide the value of reg A by reg B, store the remainder in reg A
                self.alu("MOD", self.ram_read(self.pc+1),
                                self.ram_read(self.pc+2))
            
            elif self.ir == 0b10101000:  # AND
                # Perform a bitwise AND on two registers, store in reg A
                self.alu("AND", self.ram_read(self.pc+1),
                                self.ram_read(self.pc+2))
            
            elif self.ir == 0b10101010:  # OR
                # Perform a bitwise OR on two registers, store in reg A
                self.alu("OR", self.ram_read(self.pc+1),
                               self.ram_read(self.pc+2))
            
            elif self.ir == 0b10101011:  # XOR
                # Perform a bitwise XOR on two registers, store in reg A
                self.alu("XOR", self.ram_read(self.pc+1),
                                self.ram_read(self.pc+2))
            
            elif self.ir == 0b01101001:  # NOT
                # Perform a bitwise NOT on one register
                self.alu("NOT", self.ram_read(self.pc+1), 0)
            
            elif self.ir == 0b10101100:  # SHL
                # Shift the value in reg A to the left by the number in reg B
                self.alu("SHL", self.ram_read(self.pc+1),
                                self.ram_read(self.pc+2))
            
            elif self.ir == 0b10101101:  # SHR
                # Shift the value in reg A to the right by the number in reg B
                self.alu("SHR", self.ram_read(self.pc+1),
                                self.ram_read(self.pc+2))
            
            elif self.ir == 0b01100110:  # DEC
                # Decrement the value in the given register by 1
                self.alu("DEC", self.ram_read(self.pc+1), 0)
            
            elif self.ir == 0b01100101:  # INC
                # Increment the value in the given register by 1
                self.alu("INC", self.ram_read(self.pc+1), 0)

            elif self.ir == 0b00000001:  # HLT
                # Halt the emulator
                running = False

            else:
                raise Exception(f"Instruction code not implemented: %02X" % self.ir)
            
            # increment the program counter according to the 1st 2 bits of ir
            self.pc += (self.ir >> 6) + 1
