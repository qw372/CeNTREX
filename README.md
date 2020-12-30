# SrF-Lab-Control

This is a generic program designed to interface with multiple devices at the same time. A device can be added by importing a configuration file (.ini) and a driver file (.py). Different modules — device threads, monitor, HDF writer, plotter, sequencer, etc — work together to meet data acquiring needs in atomic, molecular and optical (AMO) physics experiments. Since the original repository [CeNTREX](https://github.com/js216/CeNTREX) has included an elaborate document, here I only focus on 2 subtle things, (1) requirement of device configuration file and driver file, which is fundamental but confusing for first-timer users, and (2) the sequencer, which is not mentioned in the [CeNTREX](https://github.com/js216/CeNTREX) document and also looks very different in this program.

## Device configuration/driver file
### Configuration file (.ini)
A list of elemens in configuration file
    [device]                                # device general setting section
    name = test_fastdata                    # device name will be used in plotter, hdf writer, etc
    label = Test device                     # device label is only used in the title in device frame of the GUI
    hdf_group = test_fastdata               # name of the .hdf file group that data from this device will be saved into
    driver = test_fastdata
    constr_params = someParameter
    correct_response = the test string
    slow_data = False
    devices_frame_tab = Test
    row = 1
    column = 2
    plots_queue_maxlen = 10
    max_NaN_count = 10
    meta_device = False
    compound_dataset = False
    double_connect_dev = True
    plots_fn = 2*y
    scan_params = input(unit)
    block_thread = False

    [attributes]
    column_names = Ch1, Ch2
    units = V, V

    [enabled]
    label = Device enabled
    type = QCheckBox
    tristate = True
    row = 0
    col = 0
    value = 0

    [HDF_enabled]
    label = HDF enabled
    type = QCheckBox
    row = 1
    col = 0
    value = 1

    [dt]
    label = Loop cycle [s]:
    type = QLineEdit
    row = 2
    col = 1
    value = 5

    [someParameter]
    label = some parameter
    type = QComboBox
    row = 3
    col = 1
    value = test1
    options =
    command =

    [InfluxDB_enabled]
    type = dummy
    value = False



### Driver file (.py)
aaa


## Sequencer
aaaa
