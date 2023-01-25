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
        # model_dir = os.path.abspath(os.path.join(tests_dir, '../model/LFSR.py'))
        # spec = importlib.util.spec_from_file_location("lfsr_mode", model_dir)
        # foo = importlib.util.module_from_spec(spec)
        # spec.loader.exec_module(foo)
        # self.model = foo.Model(self.LEN, self.START_VALUE, self.TAPS) 
        cocotb.fork(Clock(self.dut.clk_i, CLK_PERIOD_NS, units='ns').start())
        # cocotb.fork(self.model_clk(CLK_PERIOD_NS, 'ns'))    
          
    async def model_clk(self, period, period_units):
        timer = Timer(period, period_units)
        while True:
            #self.model.tick()
            await timer

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
        print(f"{received[count]} <-> {model[count]}")
        assert model[count] == received[count]
        count += 1
# cocotb-test


tests_dir = os.path.abspath(os.path.dirname(__file__))
rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'hdl'))
tools_dir = os.path.abspath(os.path.join(tests_dir, '..', 'tools'))

@pytest.mark.parametrize("N", [7])
@pytest.mark.parametrize("START_VALUE", [0x76, 0x00])
@pytest.mark.parametrize("TAPS", [0x11, 0x7F, 0x40])
def test(N, START_VALUE, TAPS):
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
    
    extra_env = {f'PARAM_{k}': str(v) for k, v in parameters.items()}
    sim_build="sim_build/" + "_".join(("{}={}".format(*i) for i in parameters.items()))
    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        includes=includes,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        extra_env=extra_env,
        testcase="_test_parameter",
    )

if __name__ == '__main__':
    START_VALUE = np.array([1, 1, 1, 0, 1, 1, 0]) # bits here are in reversed order!
    ncellid = 0
    START_VALUE = np.roll(START_VALUE, -43 * ncellid)
    test(N = 7, START_VALUE = int(''.join(map(str, START_VALUE)), 2), TAPS = 0x11)

    