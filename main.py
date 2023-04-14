from math import floor
from random import random
from sys import argv
from easygraphics import *

font_set = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
]

scalar = 15


class Emulator:
    """
    Base class that controls the almost physical functions of stop, start, loading a rom, key presses, etc
    """

    def __init__(self):
        self.cpu = CPU()
        self.rom = False

    def start(self):
        """
        Start the emulator
        :return: None
        """
        if not self.rom:
            print("Please load a rom")
        else:
            self.load_font_set()
            self.cpu.start()

    def load_font_set(self):
        """
        Load the base font set
        :return: None
        """
        for loc, byte in enumerate(font_set):
            self.cpu.write_memory(loc, byte)

    def load_rom(self, rom):
        """
        Load a new rom into memory
        :param rom: binary
        :return: None
        """
        try:
            with open(rom, mode="rb") as file:
                self.rom = file.read()
            for loc, byte in enumerate(self.rom, start=0x200):
                self.cpu.write_memory(loc, byte)
        except FileNotFoundError:
            print(f"File {rom} not found")
            exit(1)


class CPU:
    """
    Base class that controls the RAM, registers, sound, and any other internal state
    """

    def __init__(self):
        self.keypad = None
        self.v = [None] * 16
        self.stack = [None] * 255
        self.memory = [None] * 4096
        self.gfx = [None] * 2048
        self.pc = 0x200
        self.I = 0
        self.sp = 0
        self.draw_flag = False
        self.delay_timer = 0
        self.sound_timer = 0
        self.paused = False

    def write_register(self, num, val):
        """
        Write to a given register
        :param num: register index
        :param val: value
        :return: None
        """
        try:
            self.v[num] = val & 0xFF
        except IndexError:
            print(f"Invalid register index {num}")
            exit(1)

    def read_register(self, num):
        """
        Read a given register
        :param num: number
        :return: value
        """
        try:
            return self.v[num]
        except IndexError:
            print(f"Invalid register at {num}")
            exit(1)

    def write_memory(self, loc, val):
        """
        Write to a given memory location
        :param loc: memory location
        :param val: value to be written
        :return: None
        """
        self.memory[loc] = val

    def write_memory_2byte(self, loc, val):
        """
        Write a 2 byte value to a starting memory location
        :param loc: starting address
        :param val:  value to be written
        :return: None
        """
        self.write_memory(loc, (val & 0xFF00) >> 8)
        self.write_memory(loc + 1, val & 0xFF)

    def write_graphics(self, loc, val):
        """
        Write to a given graphics memory location
        :param loc: memory location
        :param val: value to be written
        :return: None
        """
        self.gfx[loc] = val

    def read_memory(self, loc):
        """
        Read a given memory location
        :param loc: memory location
        :return: value
        """
        try:
            return self.memory[loc]
        except IndexError:
            print(f"Memory access error at {loc}")

    def read_graphics(self, loc):
        """
        Read a given graphics memory location
        :param loc: memory location
        :return: value
        """
        try:
            return self.gfx[loc]
        except IndexError:
            print(f"Graphics memory access error at {loc}")

    def cycle(self):
        """
        Lookup the next instruction and update screen if necessary
        :return: None
        """
        self.decode_opcode()
        if self.draw_flag: self.update_screen()

    def decode_opcode(self):
        """
        Decode the next instruction
        :return: None
        """
        op_code = self.read_memory(self.pc) << 8 | self.read_memory(self.pc + 1)
        if op_code:
            try:
                match op_code & 0xF000:
                    case 0x0000:
                        match op_code & 0x00FF:
                            case 0xE0:  # 00E0  Clears the screen
                                self.clear_graphics()
                                self.pc += 2
                                self.draw_flag = True
                            case 0xEE:  # 00EE Returns from subroutine
                                self.sp -= 1
                                self.pc = self.stack[self.sp]
                                self.pc += 2
                            case _:
                                print(f"Unknown opcode 0x{hex(op_code)}")
                    case 0x1000:  # 1NNN    Jumps to address NN
                        self.pc = op_code & 0x0FFF
                    case 0x2000:  # 2NNN	Calls subroutine at NNN
                        self.stack[self.sp] = self.pc
                        self.sp += 1
                        self.pc = op_code & 0x0FFF
                    case 0x3000:  # 3XNN	Skips the next instruction if VX equals NN
                        self.pc += 4 if self.read_register((op_code & 0x0F00) >> 8) == (op_code & 0x00FF) else 2
                    case 0x4000:  # 4XNN	Skips the next instruction if VX doesn't equal NN
                        self.pc += 4 if self.read_register((op_code & 0x0F00) >> 8) != (op_code & 0x00FF) else 2
                    case 0x5000:  # 5XY0	Skips the next instruction if VX equals VY
                        self.pc += 4 if self.read_register((op_code & 0x0F00) >> 8) == self.read_register(
                            (op_code & 0x00F0) >> 4) else 2
                    case 0x6000:  # 6XNN	Sets VX to NN
                        self.write_register((op_code & 0x0F00) >> 8, op_code & 0x00FF)
                        self.pc += 2
                    case 0x7000:  # 7XNN    Adds NN to VX
                        reg = (op_code & 0x0F00) >> 8
                        val = self.read_register(reg) + (op_code & 0x00FF)
                        self.write_register(reg, val & 0xFF)
                        self.pc += 2
                    case 0x8000:  # 8XYN
                        v_x = (op_code & 0x0F00) >> 8
                        v_y = (op_code & 0x00F0) >> 4
                        match op_code & 0x000F:
                            case 0x0:  # 8XY0	Sets VX to the value of VY
                                self.write_register(v_x, self.read_register(v_y))
                                self.pc += 2
                            case 0x1:  # 8XY1	Sets VX to VX or VY
                                self.write_register(v_x, self.read_register(v_x) | self.read_register(v_y))
                                self.pc += 2
                            case 0x2:  # 8XY2	Sets VX to VX and VY
                                self.write_register(v_x, self.read_register(v_x) & self.read_register(v_y))
                                self.pc += 2
                            case 0x3:  # 8XY3	Sets VX to VX xor VY
                                self.write_register(v_x, self.read_register(v_x) ^ self.read_register(v_y))
                                self.pc += 2
                            case 0x4:  # 8XY4	Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when
                                # there isn't
                                total = self.read_register(v_x) + self.read_register(v_y)
                                self.write_register(v_x, total & 0xFF)
                                self.write_register(0xF, 1) if total > 255 else self.write_register(0xF, 0)
                                self.pc += 2
                            case 0x5:  # 8XY5	VY is subtracted from VX. VF is set to 0 when there's a borrow,
                                # and 1 when there isn't
                                total = self.read_register(v_x) - self.read_register(v_y)
                                self.write_register(v_x, total & 0xFF)
                                self.write_register(0xF, 0) if total < 0 else self.write_register(0xF, 1)
                                self.pc += 2
                            case 0x6:  # 8XY6	Shifts VX right by one. VF is set to the value of the least
                                # significant bit of VX before the shift
                                self.write_register(v_x, self.read_register(v_x) >> 1)
                                self.write_register(0xF, self.read_register(v_x) & 0x1)
                                self.pc += 2
                            case 0x7:  # 8XY7	Sets VX to VY minus VX. VF is set to 0 when there's a borrow,
                                # and 1 when there isn't
                                total = self.read_register(v_y) - self.read_register(v_x)
                                self.write_register(v_x, total & 0xFF)
                                self.write_register(0xF, 0) if total < 0 else self.write_register(0xF, 1)
                                self.pc += 2
                            case 0xE:  # 8XYE	Shifts VX left by one. VF is set to the value of the most significant
                                # bit of VX before the shift
                                self.write_register(v_x, self.read_register(v_x) << 1)
                                self.write_register(0xF, self.read_register(v_x) >> 7)
                                self.pc += 2
                            case _:
                                print(f"Unknown opcode 0x{hex(op_code)}")
                                exit(1)
                    case 0x9000:  # 9XY0	Skips the next instruction if VX doesn't equal VY
                        self.pc += 4 if self.read_register((op_code & 0x0F00) >> 8) != self.read_register(
                            (op_code & 0x00F0) >> 4) else 2
                    case 0xA000:  # ANNN	Sets I to the address NNN
                        self.I = op_code & 0x0FFF
                        self.pc += 2
                    case 0xB000:  # BNNN	Jumps to the address NNN plus V0
                        self.pc = (op_code & 0x0FFF) + self.read_register(0)
                    case 0xC000:  # CXNN	Sets VX to the result of a bitwise and operation on a random number (
                        # Typically: 0 to 255) and NN
                        self.write_register((op_code & 0x0F00) >> 8, random.randint(0, 255) & (op_code & 0x00FF))
                        self.pc += 2
                    case 0xD000:  # DXYN - DRW Vx, Vy, nibble
                        self.write_register(0xF, 0)
                        v_x = self.read_register((op_code & 0x0F00) >> 8)
                        v_y = self.read_register((op_code & 0x00F0) >> 4)
                        n = op_code & 0x000F

                        for y in range(n):
                            sprite = self.read_memory(self.I + y)
                            for x in range(8):
                                if (sprite & (0x80 >> x)) != 0:
                                    t_x = (v_x + x) % 64
                                    t_y = (v_y + y) % 32
                                    indx = t_x + (t_y * 64)
                                    val = self.read_graphics(indx)
                                    val ^= 1
                                    self.write_graphics(indx, val)
                                    if self.read_graphics(indx) == 0:
                                        self.write_register(0xF, 1)
                        self.draw_flag = True
                        self.pc += 2
                    case 0xE000:
                        match op_code & 0x00FF:
                            case 0x9E:  # EX9E	Skips the next instruction if the key stored in VX is pressed
                                self.pc += 4 if self.keypad[self.read_register((op_code & 0x0F00) >> 8)] else 2
                            case 0xA1:  # EXA1	Skips the next instruction if the key stored in VX isn't pressed
                                self.pc += 4 if not self.keypad[self.read_register((op_code & 0x0F00) >> 8)] else 2
                            case _:
                                print(f"Unknown opcode 0x{hex(op_code)}")
                    case 0xF000:
                        match op_code & 0x00FF:
                            case 0x07:  # FX07	Sets VX to the value of the delay timer
                                self.write_register((op_code & 0x0F00) >> 8, self.delay_timer)
                                self.pc += 2
                            case 0x0A:  # FX0A	A key press is awaited, and then stored in VX
                                key_pressed = False
                                for i in range(16):
                                    if self.keypad[i]:
                                        self.write_register((op_code & 0x0F00) >> 8, i)
                                        key_pressed = True
                                if not key_pressed:
                                    return
                            case 0x15:  # FX15	Sets the delay timer to VX
                                self.delay_timer = self.read_register((op_code & 0x0F00) >> 8)
                                self.pc += 2
                            case 0x18:  # FX18	Sets the sound timer to VX
                                self.sound_timer = self.read_register((op_code & 0x0F00) >> 8)
                                self.pc += 2
                            case 0x1E:  # FX1E	Adds VX to I
                                self.I += self.read_register((op_code & 0x0F00) >> 8)
                                self.pc += 2
                            case 0x29:  # FX29	Sets I to the location of the sprite for the character in VX.
                                # Characters 0-F (in hexadecimal) are represented by a 4x5 font
                                self.I = self.read_register((op_code & 0x0F00) >> 8) * 5
                                self.pc += 2
                            case 0x33:  # FX33	Stores the Binary-coded decimal representation of VX, with the most
                                # significant of three digits at the address in I, the middle digit at I plus 1,
                                # and the least significant digit at I plus 2
                                reg = (op_code & 0x0F00) >> 8
                                val = self.read_register(reg)
                                self.write_memory(self.I, floor(val / 100))
                                self.write_memory(self.I + 1, floor(val / 10) % 10)
                                self.write_memory(self.I + 2, floor(val % 10))
                                self.pc += 2
                            case 0x55:  # FX55	Stores V0 to VX in memory starting at address I
                                reg = (op_code & 0x0F00) >> 8
                                for i in range(reg + 1):
                                    self.write_memory(self.I + i, self.read_register(i))
                                self.pc += 2
                            case 0x65:  # FX65	Fills V0 to VX with values from memory starting at address I
                                reg = (op_code & 0x0F00) >> 8
                                for i in range(reg + 1):
                                    self.write_register(i, self.read_memory(self.I + i))
                                self.pc += 2
                    case _:
                        print(f"Unknown opcode {hex(op_code)}")
                        self.pc += 2
            except TypeError as inst:
                print(f"Couldn't decode {hex(op_code)} at {hex(self.pc)}")
                print(type(inst))
                print(inst.args)
                print(inst)

                exit(1)
        else:
            print("Nothing to do...")

    def update_screen(self):
        """
        Draw the screen
        :return: None
        """
        for y in range(32):
            for x in range(64):
                if self.read_graphics(x + (y * 64)) == 1:
                    set_fill_color(Color.BLUE)
                else:
                    set_fill_color(Color.RED)
                draw_rect(x * scalar, y * scalar, (x + scalar) * scalar, (y + scalar) * scalar)
        delay_fps(1000)
        self.draw_flag = False

    def clear_graphics(self):
        """
        Clear graphics memory
        :return:
        """
        self.gfx = [0] * 2048

    def start(self):
        """
        Start the CPU
        :return: None
        """
        while is_run():
            while not self.paused:
                print(f"PC: {hex(self.pc)}")
                self.cycle()


def main():
    """
    Main function
    :return: 
    """
    init_graph(64 * scalar, 32 * scalar)
    set_render_mode(RenderMode.RENDER_MANUAL)
    set_caption("Chip-8 Emulator")

    emu = Emulator()
    emu.load_rom(argv[1])
    emu.load_font_set()
    emu.start()
    close_graph()


if __name__ == '__main__':
    easy_run(main)
