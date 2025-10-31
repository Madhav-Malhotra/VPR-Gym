I got this error after running `make`:

```
/home/mdvmlhtr/VPR-Gym/utils/fasm/test/test_lut.cpp: In function ‘void {anonymous}::CATCH2_INTERNAL_TEST_2()’:
/home/mdvmlhtr/VPR-Gym/utils/fasm/test/test_lut.cpp:30:28: warning: comparison of integer expressions of different signedness: ‘size_t’ {aka ‘long unsigned int’} and ‘int’ [-Wsign-compare]
   30 |         CHECK(table.size() == (1 << num_inputs));
      |               ~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
/home/mdvmlhtr/VPR-Gym/utils/fasm/test/test_lut.cpp: In function ‘void {anonymous}::CATCH2_INTERNAL_TEST_4()’:
/home/mdvmlhtr/VPR-Gym/utils/fasm/test/test_lut.cpp:45:32: warning: comparison of integer expressions of different signedness: ‘size_t’ {aka ‘long unsigned int’} and ‘int’ [-Wsign-compare]
   45 |             CHECK(table.size() == (1 << num_inputs));
      |                   ~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
/home/mdvmlhtr/VPR-Gym/utils/fasm/test/test_lut.cpp: In function ‘void {anonymous}::CATCH2_INTERNAL_TEST_6()’:
/home/mdvmlhtr/VPR-Gym/utils/fasm/test/test_lut.cpp:61:32: warning: comparison of integer expressions of different signedness: ‘size_t’ {aka ‘long unsigned int’} and ‘int’ [-Wsign-compare]
   61 |             CHECK(table.size() == (1 << num_inputs));
      |                   ~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
[100%] Building CXX object utils/fasm/CMakeFiles/test_fasm.dir/test/test_parameters.cpp.o
[100%] Building CXX object utils/fasm/CMakeFiles/test_fasm.dir/test/test_utils.cpp.o
[100%] Linking CXX executable test_fasm
[100%] Built target vpr
[100%] Built target genfasm
[100%] Built target test_vpr
[100%] Built target test_fasm
mdvmlhtr@LAPTOP-87ISD0FH:~/VPR-Gym$ ./vtr_flow/scripts/run_vtr_task.py regression_tests/vtr_reg_basic/basic_timing
Traceback (most recent call last):
  File "/home/mdvmlhtr/VPR-Gym/./vtr_flow/scripts/run_vtr_task.py", line 19, in <module>
    from run_vtr_flow import vtr_command_main as run_vtr_flow
  File "/home/mdvmlhtr/VPR-Gym/vtr_flow/scripts/run_vtr_flow.py", line 16, in <module>
    import vtr
  File "/home/mdvmlhtr/VPR-Gym/vtr_flow/scripts/python_libs/vtr/__init__.py", line 4, in <module>
    from .util import (
  File "/home/mdvmlhtr/VPR-Gym/vtr_flow/scripts/python_libs/vtr/util.py", line 13, in <module>
    from prettytable import PrettyTable
ModuleNotFoundError: No module named 'prettytable'
mdvmlhtr@LAPTOP-87ISD0FH:~/VPR-Gym$ source .venv/bin/activate
(.venv) mdvmlhtr@LAPTOP-87ISD0FH:~/VPR-Gym$ ./vtr_flow/scripts/run_vtr_task.py regression_tests/vtr_reg_basic/basic_timing
k6_N10_mem32K_40nm/single_ff            Error: Executable abc failed
        full command:  /usr/bin/env time -v /home/mdvmlhtr/VPR-Gym/abc/abc -c echo ""; echo "Load Netlist"; echo "============"; read 0_single_ff.odin.blif; time; echo ""; echo "Circuit Info"; echo "=========="; print_stats; print_latch; time; echo ""; echo "LUT Costs"; echo "========="; print_lut; time; echo ""; echo "Logic Opt + Techmap"; echo "==================="; strash; ifraig -v; scorr -v; dc2 -v; dch -f; if -K 6 -v; mfs2 -v; print_stats; time; echo ""; echo "Output Netlist"; echo "=============="; write_hie 0_single_ff.odin.blif 0_single_ff.raw.abc.blif; time;
        returncode  :  127
        log file    :  /home/mdvmlhtr/VPR-Gym/vtr_flow/tasks/regression_tests/vtr_reg_basic/basic_timing/run002/k6_N10_mem32K_40nm.xml/single_ff.v/common_--reorder_rr_graph_nodes_algorithm_random_shuffle/abc0.out
failed: Executable abc failed (took 0.03 seconds, overall memory peak 6.00 MiB consumed by odin run)
k6_N10_mem32K_40nm/single_ff            Error: Executable abc failed
        full command:  /usr/bin/env time -v /home/mdvmlhtr/VPR-Gym/abc/abc -c echo ""; echo "Load Netlist"; echo "============"; read 0_single_ff.odin.blif; time; echo ""; echo "Circuit Info"; echo "=========="; print_stats; print_latch; time; echo ""; echo "LUT Costs"; echo "========="; print_lut; time; echo ""; echo "Logic Opt + Techmap"; echo "==================="; strash; ifraig -v; scorr -v; dc2 -v; dch -f; if -K 6 -v; mfs2 -v; print_stats; time; echo ""; echo "Output Netlist"; echo "=============="; write_hie 0_single_ff.odin.blif 0_single_ff.raw.abc.blif; time;
        returncode  :  127
        log file    :  /home/mdvmlhtr/VPR-Gym/vtr_flow/tasks/regression_tests/vtr_reg_basic/basic_timing/run002/k6_N10_mem32K_40nm.xml/single_ff.v/common/abc0.out
failed: Executable abc failed (took 0.03 seconds, overall memory peak 5.88 MiB consumed by odin run)
k6_N10_mem32K_40nm/single_wire          Error: Executable abc failed
        full command:  /usr/bin/env time -v /home/mdvmlhtr/VPR-Gym/abc/abc -c echo ""; echo "Load Netlist"; echo "============"; read 0_single_wire.odin.blif; time; echo ""; echo "Circuit Info"; echo "=========="; print_stats; print_latch; time; echo ""; echo "LUT Costs"; echo "========="; print_lut; time; echo ""; echo "Logic Opt + Techmap"; echo "==================="; strash; ifraig -v; scorr -v; dc2 -v; dch -f; if -K 6 -v; mfs2 -v; print_stats; time; echo ""; echo "Output Netlist"; echo "=============="; write_hie 0_single_wire.odin.blif 0_single_wire.raw.abc.blif; time;
        returncode  :  127
        log file    :  /home/mdvmlhtr/VPR-Gym/vtr_flow/tasks/regression_tests/vtr_reg_basic/basic_timing/run002/k6_N10_mem32K_40nm.xml/single_wire.v/common_--reorder_rr_graph_nodes_algorithm_random_shuffle/abc0.out
failed: Executable abc failed (took 0.03 seconds, overall memory peak 6.00 MiB consumed by odin run)
k6_N10_mem32K_40nm/single_wire          Error: Executable abc failed
        full command:  /usr/bin/env time -v /home/mdvmlhtr/VPR-Gym/abc/abc -c echo ""; echo "Load Netlist"; echo "============"; read 0_single_wire.odin.blif; time; echo ""; echo "Circuit Info"; echo "=========="; print_stats; print_latch; time; echo ""; echo "LUT Costs"; echo "========="; print_lut; time; echo ""; echo "Logic Opt + Techmap"; echo "==================="; strash; ifraig -v; scorr -v; dc2 -v; dch -f; if -K 6 -v; mfs2 -v; print_stats; time; echo ""; echo "Output Netlist"; echo "=============="; write_hie 0_single_wire.odin.blif 0_single_wire.raw.abc.blif; time;
        returncode  :  127
        log file    :  /home/mdvmlhtr/VPR-Gym/vtr_flow/tasks/regression_tests/vtr_reg_basic/basic_timing/run002/k6_N10_mem32K_40nm.xml/single_wire.v/common/abc0.out
failed: Executable abc failed (took 0.02 seconds, overall memory peak 6.00 MiB consumed by odin run)
k6_N10_mem32K_40nm/diffeq1              Error: Executable abc failed
        full command:  /usr/bin/env time -v /home/mdvmlhtr/VPR-Gym/abc/abc -c echo ""; echo "Load Netlist"; echo "============"; read 0_diffeq1.odin.blif; time; echo ""; echo "Circuit Info"; echo "=========="; print_stats; print_latch; time; echo ""; echo "LUT Costs"; echo "========="; print_lut; time; echo ""; echo "Logic Opt + Techmap"; echo "==================="; strash; ifraig -v; scorr -v; dc2 -v; dch -f; if -K 6 -v; mfs2 -v; print_stats; time; echo ""; echo "Output Netlist"; echo "=============="; write_hie 0_diffeq1.odin.blif 0_diffeq1.raw.abc.blif; time;
        returncode  :  127
        log file    :  /home/mdvmlhtr/VPR-Gym/vtr_flow/tasks/regression_tests/vtr_reg_basic/basic_timing/run002/k6_N10_mem32K_40nm.xml/diffeq1.v/common_--reorder_rr_graph_nodes_algorithm_random_shuffle/abc0.out
failed: Executable abc failed (took 0.06 seconds, overall memory peak 9.38 MiB consumed by odin run)
k6_N10_mem32K_40nm/diffeq1              Error: Executable abc failed
        full command:  /usr/bin/env time -v /home/mdvmlhtr/VPR-Gym/abc/abc -c echo ""; echo "Load Netlist"; echo "============"; read 0_diffeq1.odin.blif; time; echo ""; echo "Circuit Info"; echo "=========="; print_stats; print_latch; time; echo ""; echo "LUT Costs"; echo "========="; print_lut; time; echo ""; echo "Logic Opt + Techmap"; echo "==================="; strash; ifraig -v; scorr -v; dc2 -v; dch -f; if -K 6 -v; mfs2 -v; print_stats; time; echo ""; echo "Output Netlist"; echo "=============="; write_hie 0_diffeq1.odin.blif 0_diffeq1.raw.abc.blif; time;
        returncode  :  127
        log file    :  /home/mdvmlhtr/VPR-Gym/vtr_flow/tasks/regression_tests/vtr_reg_basic/basic_timing/run002/k6_N10_mem32K_40nm.xml/diffeq1.v/common/abc0.out
failed: Executable abc failed (took 0.06 seconds, overall memory peak 9.38 MiB consumed by odin run)
k6_N10_mem32K_40nm/ch_intrinsics                Error: Executable abc failed
        full command:  /usr/bin/env time -v /home/mdvmlhtr/VPR-Gym/abc/abc -c echo ""; echo "Load Netlist"; echo "============"; read 0_ch_intrinsics.odin.blif; time; echo ""; echo "Circuit Info"; echo "=========="; print_stats; print_latch; time; echo ""; echo "LUT Costs"; echo "========="; print_lut; time; echo ""; echo "Logic Opt + Techmap"; echo "==================="; strash; ifraig -v; scorr -v; dc2 -v; dch -f; if -K 6 -v; mfs2 -v; print_stats; time; echo ""; echo "Output Netlist"; echo "=============="; write_hie 0_ch_intrinsics.odin.blif 0_ch_intrinsics.raw.abc.blif; time;
        returncode  :  127
        log file    :  /home/mdvmlhtr/VPR-Gym/vtr_flow/tasks/regression_tests/vtr_reg_basic/basic_timing/run002/k6_N10_mem32K_40nm.xml/ch_intrinsics.v/common_--reorder_rr_graph_nodes_algorithm_random_shuffle/abc0.out
failed: Executable abc failed (took 0.08 seconds, overall memory peak 9.38 MiB consumed by odin run)
k6_N10_mem32K_40nm/ch_intrinsics                Error: Executable abc failed
        full command:  /usr/bin/env time -v /home/mdvmlhtr/VPR-Gym/abc/abc -c echo ""; echo "Load Netlist"; echo "============"; read 0_ch_intrinsics.odin.blif; time; echo ""; echo "Circuit Info"; echo "=========="; print_stats; print_latch; time; echo ""; echo "LUT Costs"; echo "========="; print_lut; time; echo ""; echo "Logic Opt + Techmap"; echo "==================="; strash; ifraig -v; scorr -v; dc2 -v; dch -f; if -K 6 -v; mfs2 -v; print_stats; time; echo ""; echo "Output Netlist"; echo "=============="; write_hie 0_ch_intrinsics.odin.blif 0_ch_intrinsics.raw.abc.blif; time;
        returncode  :  127
        log file    :  /home/mdvmlhtr/VPR-Gym/vtr_flow/tasks/regression_tests/vtr_reg_basic/basic_timing/run002/k6_N10_mem32K_40nm.xml/ch_intrinsics.v/common/abc0.out
failed: Executable abc failed (took 0.08 seconds, overall memory peak 9.38 MiB consumed by odin run)
Elapsed time: 0.44 seconds

Parsing test results...
Elapsed time: 0.02 seconds
```