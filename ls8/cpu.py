"""CPU functionality."""

import sys
import time
import msvcrt

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        # special registers
        self.pc = 0   # program counter, address of the currently executing instruction
        self.ir = 0   # instruction register, copy of the currently executing instruction
        self.mar = 0  # memory address register, holds the address we're reading or writing
        self.mdr = 0  # memory data register, holds the value to write, or the value just read
        self.fl = 0   # flags register: 0b00000LGE  (<, >, ==)

        # storage
        self.ram = [0] * 256   # RAM storage
        self.reg = [0] * 8     # register storage
        self.reg[7] = 0xF4     # R7 defaults to 0xF4 (stack pointer)

        self.interrupts_enabled = True

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
            self.reg[reg_a] //= self.reg[reg_b]
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
        
        # Compare
        elif op == "CMP":
            if self.reg[reg_a] < self.reg[reg_b]:
                # less than, set the L flag
                self.fl = 0b0000100
            elif self.reg[reg_a] > self.reg[reg_b]:
                # greater than, set the G flag
                self.fl = 0b0000010
            else:
                # equal, set the E flag
                self.fl = 0b0000001

        else:
            raise Exception("Unsupported ALU operation:", op)
    
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
    
    def stack_push(self, value):
        """ pushes the value onto the stack """
        self.reg[7] -= 1  # decrement the stack pointer
        self.ram_write(value, self.reg[7])  # save to the stack

    def stack_pop(self):
        """ pops the next value off of the stack and returns it """
        self.reg[7] += 1  # increment the stack pointer
        return self.ram_read(self.reg[7]-1)  # return the value

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
        timer = 0
        last_time = time.time()
        while running:
            # -- Interrupt handling --
            # Update the system timer
            timer += time.time() - last_time
            last_time = time.time()
            if timer >= 1:
                # 1 second has passed, set timer interrupt
                self.reg[6] |= 1  # set IS bit 0 to 1
                timer -= 1  # reset timer for the next second
            
            # Check keyboard input
            if msvcrt.kbhit():
                key = ord(msvcrt.getch())  # Get value of the last key hit
                self.ram_write(key, 0xF4)  # Store in RAM at address F4
                self.reg[6] |= 2  # Set IS bit 1

            if self.interrupts_enabled:
                # Check if any interrupts have occurred
                masked_interrupts = self.reg[5] & self.reg[6]
                mask = 0b00000001
                for i in range(8):
                    # check each bit of masked_interrupts to see which
                    # interrupt occurred (if any)
                    if mask & masked_interrupts:
                        # bit i was set
                        self.interrupts_enabled = False  # disable further interrupts
                        self.reg[6] = 0  # clear the IS register
                        # Push registers onto the stack
                        self.stack_push(self.pc)
                        self.stack_push(self.fl)
                        for j in range(7):
                            self.stack_push(self.reg[j])
                        
                        # Look up the interrupt vector and set PC to it
                        self.pc = self.ram_read(248+i)  # addresses 248-255

                        break  # stop checking further
                    mask <<= 1

            # -- Main Execution --
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

            elif self.ir == 0b01001000:  # PRA
                # Print alpha character value stored in the given register
                self.mar = self.ram_read(self.pc + 1)  # Load register number
                self.mdr = self.reg[self.mar]  # load the value from the register
                print(chr(self.mdr))  # print the character
            
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

            elif self.ir == 0b10100011:  # DIV
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
            
            elif self.ir == 0b10100111:  # CMP
                # Compare the values in two registers, sets the fl register
                self.alu("CMP", self.ram_read(self.pc+1), 
                                self.ram_read(self.pc+2))
            
            elif self.ir == 0b01010100:  # JMP
                # Jump to the address stored in the given register
                self.pc = self.reg[self.ram_read(self.pc+1)]
                continue
            
            elif self.ir == 0b01010101:  # JEQ
                # Jump to the address if the Equal flag is true
                if self.fl & 0b00000001:  # E mask
                    self.pc = self.reg[self.ram_read(self.pc+1)]
                    continue

            elif self.ir == 0b01011010:  # JGE
                # Jump to the address if the Equal or Greater flags are true
                if self.fl & 0b00000011:  # GE mask
                    self.pc = self.reg[self.ram_read(self.pc+1)]
                    continue
            
            elif self.ir == 0b01010111:  # JGT
                # Jump to the address if the Greater flag is true
                if self.fl & 0b00000010:  # GE mask
                    self.pc = self.reg[self.ram_read(self.pc+1)]
                    continue
            
            elif self.ir == 0b01011001:  # JLE
                # Jump to the address if the Less than flag is true
                if self.fl & 0b00000100:  # GE mask
                    self.pc = self.reg[self.ram_read(self.pc+1)]
                    continue

            elif self.ir == 0b01011000:  # JLT
                # Jump to the address if the Equal or Lesser flags are true
                if self.fl & 0b00000101:  # GE mask
                    self.pc = self.reg[self.ram_read(self.pc+1)]
                    continue
            
            elif self.ir == 0b01010110:  # JNE
                # Jump to the address if the Equal flag is false
                if not self.fl & 0b00000001:  # E mask
                    self.pc = self.reg[self.ram_read(self.pc+1)]
                    continue
            
            elif self.ir == 0b01000101:  # PUSH
                # Push the value in the given register onto the stack
                value = self.reg[self.ram_read(self.pc+1)]  # get the value
                self.stack_push(value)  # save to the stack
            
            elif self.ir == 0b01000110:  # POP
                # Pop a value off the stack and store in the given register
                self.reg[self.ram_read(self.pc+1)] = self.stack_pop()
            
            elif self.ir == 0b10000100:  # ST
                # Store value in reg B in the address stored in reg A
                self.mar = self.reg[self.ram_read(self.pc+1)]  # value of reg A
                self.mdr = self.reg[self.ram_read(self.pc+2)]  # value of reg B
                self.ram_write(self.mdr, self.mar)

            elif self.ir == 0b10000011:  # LD
                # Loads reg A with the value at the memory address stored in reg B
                self.mar = self.reg[self.ram_read(self.pc+2)]
                self.mdr = self.ram_read(self.mar)
                self.reg[self.ram_read(self.pc+1)] = self.mdr

            elif self.ir == 0b01010010:  # INT
                # Issue the interrupt number stored in the given register
                n = self.reg[self.ram_read(self.pc+1)]  # get the register value
                self.reg[6] = 1 << n  # set the nth bit of the IS register
            
            elif self.ir == 0b00010011:  # IRET
                # Return from an interrupt handler
                # Pop registers back off the stack
                for i in range(6,-1,-1):
                    self.reg[i] = self.stack_pop()
                self.fl = self.stack_pop()
                self.pc = self.stack_pop()
                self.interrupts_enabled = True  # re-enable interrupts
                continue

            elif self.ir == 0b00000001:  # HLT
                # Halt the emulator
                running = False

            else:
                raise Exception(f"Instruction code not implemented: %02X" % self.ir)
            
            # increment the program counter according to the 1st 2 bits of ir
            self.pc += (self.ir >> 6) + 1
