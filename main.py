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


class Emulator:
    """
    Base class that controls the almost physical functions of stop, start, loading a rom, key presses, etc
    """

    def __init__(self):
        self.cpu = CPU()
        self.rom = False

    def start(self):
        if not self.rom:
            return print("Please load a rom")
        else:
            self.load_font_set()
            self.cpu.start()

    def load_font_set(self):
        """
        Load the base font set
        :return:
        """
        for loc, byte in enumerate(font_set):
            self.cpu.write_memory(loc, byte)

    def load_rom(self, rom):
        """
        Load a new rom into memory
        :param rom: binary
        :return:
        """
        with open(rom, mode="rb") as file:
            self.rom = file.read()
        for loc, byte in enumerate(self.rom, start=0x200):
            self.cpu.write_memory(loc, byte)


class CPU:
    """
    Base class that controls the RAM, registers, sound, and any other internal state
    """

    def __init__(self):
        self.v = [None] * 16
        self.stack = [None]
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
            self.v[num] = val
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
        :return:
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
        self.decode_opcode()
        if self.draw_flag: self.update_screen()

    def decode_opcode(self):
        op_code = self.read_memory(self.pc) << 8 | self.read_memory(self.pc + 1)
        if op_code:
            try:
                match op_code & 0xF000:
                    case 0x0000:
                        match op_code & 0x00FF:
                            case 0xE0:
                                self.clear_graphics()
                                self.pc += 2
                                self.draw_flag = True
                            case 0xEE:
                                self.pc = self.stack[self.sp]
                                self.sp -= 1
                            case _:
                                print(f"Unknown opcode 0x{hex(op_code)}")
                    case 0x1000:  # 1NNN Jumps to address NN
                        self.pc = op_code & 0x0FFF
                    case 0x2000:  # 2NNN	Calls subroutine at NNN
                        self.sp += 1
                        self.stack[self.sp] = self.pc
                        self.pc = op_code & 0x0FFF
                    case 0x3000:
                        self.pc += 4 if self.read_register((op_code & 0x0F00) >> 8) == (op_code & 0x00FF) else 2
                    case 0x4000:
                        self.pc += 4 if self.read_register((op_code & 0x0F00) >> 8) != (op_code & 0x00FF) else 2
                    case 0x5000:
                        self.pc += 4 if self.read_register((op_code & 0x0F00) >> 8) == self.read_register(
                            (op_code & 0x00F0) >> 4) else 2
                    case 0x6000:
                        self.write_register((op_code & 0x0F00) >> 8, op_code & 0x00FF)
                        self.pc += 2
                    case 0x7000:
                        reg = (op_code & 0x0F00) >> 8
                        self.write_register(reg, self.read_register(reg) + (op_code & 0x00FF))
                        self.pc += 2
                    case 0x8000:
                        match op_code & 0x000F:
                            case 0x0:
                                pass

                    case _:
                        print(f"Unknown opcode {hex(op_code)}")
                        self.pc += 2
            except TypeError:
                print(f"Couldn't decode {hex(op_code)} at {hex(self.pc)}")
                exit(1)
        else:
            print("Nothing to do...")

    def update_screen(self):
        self.draw_flag = False
        pass

    def clear_graphics(self):
        self.gfx = [None] * 2048

    def start(self):
        while not self.paused:
            self.cycle()
