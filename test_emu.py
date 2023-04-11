from main import Emulator, CPU


def test_emulator_font_load():
    emu = Emulator()
    emu.load_font_set()
    assert emu.cpu.read_memory(0) == 0xF0


def test_emulator_rom_load():
    emu = Emulator()
    emu.load_rom("test.chip8")
    assert emu.cpu.read_memory(513) == 0xE0


def test_memory_write():
    emu = Emulator()
    emu.cpu.write_memory(2, 0xA)
    assert emu.cpu.read_memory(2) == 0xA


"""
def test_emulator_start():
    emu = Emulator()
    emu.load_rom("test.chip8")
    emu.load_font_set()
    emu.start()
    """


def test_00e0():
    emu = Emulator()
    emu.cpu.write_graphics(0x0, 0xF0)
    emu.cpu.write_memory_2byte(0x200, 0x00E0)
    emu.cpu.decode_opcode()
    assert emu.cpu.read_graphics(0x0) != 0xE0


def test_00ee():
    emu = Emulator()
    emu.cpu.write_memory_2byte(0x200, 0x00EE)
    ## FINISH ##


def test_3000():
    emu = Emulator()
    emu.cpu.write_register(2, 0x45)
    emu.cpu.write_memory_2byte(0x200, 0x3245)
    emu.cpu.decode_opcode()
    assert emu.cpu.pc == 0x204


def test_4000():
    emu = Emulator()
    emu.cpu.write_register(2, 0x46)
    emu.cpu.write_memory_2byte(0x200, 0x4245)
    emu.cpu.decode_opcode()
    assert emu.cpu.pc == 0x204


def test_5000():
    emu = Emulator()
    emu.cpu.write_register(2, 0x46)
    emu.cpu.write_register(3, 0x46)
    emu.cpu.write_memory_2byte(0x200, 0x5230)
    emu.cpu.decode_opcode()
    assert emu.cpu.pc == 0x204


def test_6xkk():
    emu = Emulator()
    emu.cpu.write_memory_2byte(0x200, 0x611F)
    emu.cpu.decode_opcode()
    assert emu.cpu.read_register(1) == 0x1F


def test_7xkk():
    emu = Emulator()
    emu.cpu.write_register(1, 0xA)
    emu.cpu.write_memory_2byte(0x200, 0x7101)
    emu.cpu.decode_opcode()
    assert emu.cpu.read_register(1) == 0xB


def test_font_set():
    emu = Emulator()
    emu.load_font_set()
    assert emu.cpu.read_memory(0x1) == 0x90
