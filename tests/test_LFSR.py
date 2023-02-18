import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
from cocotb.triggers import RisingEdge, ReadOnly
from collections import deque

import random
import os
import logging
import cocotb_test.simulator
import pytest
import numpy as np
import py3gpp

import importlib.util

CLK_PERIOD_NS = 2
CLK_PERIOD_S = CLK_PERIOD_NS * 0.000000001

class TB(object):
    def __init__(self,dut):
        random.seed(30) # reproducible tests
        self.dut = dut
        self.N = int(dut.N)
        self.START_VALUE = int(dut.START_VALUE)
        self.TAPS = int(dut.TAPS)

        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)        

        tests_dir = os.path.abspath(os.path.dirname(__file__))
        cocotb.fork(Clock(self.dut.clk_i, CLK_PERIOD_NS, units='ns').start())
          
    async def cycle_reset(self):
        self.dut.reset_ni.value = 0
        await RisingEdge(self.dut.clk_i)
        self.dut.reset_ni.value = 0
        await RisingEdge(self.dut.clk_i)
        self.dut.reset_ni.value = 1
        await RisingEdge(self.dut.clk_i)
        # self.model.reset()
        
def _int_to_vector(val, len):
    vec = np.empty(len, int)
    for i in range(len):
        vec[i] = (val >> i) & 1
    return vec

def _int_to_taps(val, len):
    taps = list()
    for i in range(len):
        if (val >> i) & 1:
            taps.append(i)
    return np.array(taps)
        
@cocotb.test()
async def _test_parameter(dut):
    tb = TB(dut)
    await tb.cycle_reset()
    count = 0
    num_items = 2**tb.N + 10 # +10 to include some of the sequence repetition in the test
    model = py3gpp.helper._calc_m_seq(tb.N, _int_to_vector(tb.START_VALUE, tb.N), _int_to_taps(tb.TAPS, tb.N), num_items)
    received = np.empty(num_items, int)
    while count < num_items:
        await RisingEdge(dut.clk_i)
        received[count] = int(tb.dut.data_o)
        # print(f"{received[count]} <-> {model[count]}")
        assert model[count] == received[count]
        count += 1

@cocotb.test()
async def _test_variable_config(dut):
    tb = TB(dut)

    # do reset and immediately load config
    dut.reset_ni.value = 0
    await RisingEdge(dut.clk_i)
    dut.reset_ni.value = 0
    await RisingEdge(dut.clk_i)
    dut.reset_ni.value = 1
    dut.load_config_i.value = 1
    # load start values for PSS(0)
    dut.start_value_i.value = 0x76
    dut.taps_i.value = 0x11
    await RisingEdge(dut.clk_i)
    dut.load_config_i.value = 0
    await RisingEdge(dut.clk_i)

    count = 0
    num_items = 127
    # model = py3gpp.helper._calc_m_seq(tb.N, _int_to_vector(tb.START_VALUE, tb.N), _int_to_taps(tb.TAPS, tb.N), num_items)
    model = py3gpp.nrPSS(0)
    received = np.empty(num_items, int)
    while count < num_items:
        await RisingEdge(dut.clk_i)
        received[count] = int(tb.dut.data_o.value)
        # print(f"{1-2*received[count]} <-> {model[count]}")
        assert model[count] == 1-2*received[count]
        count += 1


tests_dir = os.path.abspath(os.path.dirname(__file__))
rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'hdl'))
tools_dir = os.path.abspath(os.path.join(tests_dir, '..', 'tools'))

@pytest.mark.parametrize("N", [7])
@pytest.mark.parametrize("START_VALUE", [0x76, 0x00])
@pytest.mark.parametrize("TAPS", [0x11, 0x7F, 0x40])
def test_parameter(N, START_VALUE, TAPS):
    dut = "LFSR"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut

    verilog_sources = [
        os.path.join(rtl_dir, f"{dut}.sv"),
    ]
    includes = [
        os.path.join(rtl_dir, ""),
    ]    

    parameters = {}
    parameters['N'] = N
    parameters['START_VALUE'] = START_VALUE
    parameters['TAPS'] = TAPS
    
    sim_build="sim_build/" + "_".join(("{}={}".format(*i) for i in parameters.items()))
    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        includes=includes,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        testcase="_test_parameter",
    )

@pytest.mark.parametrize("N", [7])
@pytest.mark.parametrize("VARIABLE_CONFIG", [1])
def test_variable_config(N, VARIABLE_CONFIG):
    dut = "LFSR"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut

    verilog_sources = [
        os.path.join(rtl_dir, f"{dut}.sv"),
    ]
    includes = [
        os.path.join(rtl_dir, ""),
    ]    

    parameters = {}
    parameters['N'] = N
    parameters['VARIABLE_CONFIG'] = VARIABLE_CONFIG

    sim_build="sim_build/" + "_".join(("{}={}".format(*i) for i in parameters.items()))
    compile_args = []
    if os.environ.get('SIM') == 'verilator':
        compile_args = ['-Wno-fatal']
    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        includes=includes,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        testcase="_test_variable_config",
        compile_args = compile_args
    )

if __name__ == '__main__':
    test_variable_config(N = 7, VARIABLE_CONFIG = 1)

    START_VALUE = np.array([1, 1, 1, 0, 1, 1, 0]) # bits here are in reversed order!
    ncellid = 0
    START_VALUE = np.roll(START_VALUE, -43 * ncellid)
    # os.environ['SIM'] = 'verilator'
    test_parameter(N = 7, START_VALUE = int(''.join(map(str, START_VALUE)), 2), TAPS = 0x11)

    