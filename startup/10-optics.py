from ophyd.controls import EpicsMotor

# A Hutch
## Filter
fltr6_y = EpicsMotor('XF:28IDA-OP:0{Fltr:6-Ax:Y}Mtr', name='fltr6_y')

## DLM
dlm_c1_bnd_bi = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:1-Ax:BndBI}Mtr', name='dlm_c1_bnd_bi')
dlm_c1_bnd_bo = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:1-Ax:BndBO}Mtr', name='dlm_c1_bnd_bo')
dlm_c1_bnd_ti = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:1-Ax:BndTI}Mtr', name='dlm_c1_bnd_ti')
dlm_c1_bnd_to = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:1-Ax:BndTO}Mtr', name='dlm_c1_bnd_to')
dlm_c1_p = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:1-Ax:P}Mtr', name='dlm_c1_p')
dlm_c1_xi = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:1-Ax:XI}Mtr', name='dlm_c1_xi')
dlm_c1_xo = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:1-Ax:XO}Mtr', name='dlm_c1_xo')
dlm_c2_bnd_bi = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:2-Ax:BndBI}Mtr', name='dlm_c2_bnd_bi')
dlm_c2_bnd_bo = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:2-Ax:BndBO}Mtr', name='dlm_c2_bnd_bo')
dlm_c2_bnd_ti = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:2-Ax:BndTI}Mtr', name='dlm_c2_bnd_ti')
dlm_c2_bnd_to = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:2-Ax:BndTO}Mtr', name='dlm_c2_bnd_to')
dlm_c2_p = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:2-Ax:P}Mtr', name='dlm_c2_p')
dlm_c2_r = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:2-Ax:R}Mtr', name='dlm_c2_r')
dlm_c2_xi = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:2-Ax:XI}Mtr', name='dlm_c2_xi')
dlm_c2_xo = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:2-Ax:XO}Mtr', name='dlm_c2_xo')
dlm_c2_z = EpicsMotor('XF:28IDA-OP:1{Mono:DLM-C:2-Ax:Z}Mtr', name='dlm_c2_z')

## Fluorescent screen
fs2_y = EpicsMotor('XF:28IDA-BI:1{FS:2-Ax:Y}Mtr', name='fs2_y')

## BPM 1
bpm1_y = EpicsMotor('XF:28IDA-BI:0{BPM:1-Ax:Y}Mtr', name='bpm1_y')

## Horizontal slits
slt_h_i = EpicsMotor('XF:28IDA-OP:2{Slt:H-Ax:I}Mtr', name='slt_h_i')
slt_h_o = EpicsMotor('XF:28IDA-OP:2{Slt:H-Ax:O}Mtr', name='slt_h_o')
slt_h_xc = EpicsMotor('XF:28IDA-OP:2{Slt:H-Ax:XCtr}Mtr', name='slt_h_xc')
slt_h_xg = EpicsMotor('XF:28IDA-OP:2{Slt:H-Ax:XGap}Mtr', name='slt_h_xg')

## Filter
fltr1_y = EpicsMotor('XF:28IDA-OP:2{Fltr:1-Ax:Y}Mtr', name='fltr1_y')

## Mirror
vfm_bnd_d = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:BndD}Mtr', name='vfm_bnd_d')
vfm_bnd_ofst = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:BndOfst}Mtr', name='vfm_bnd_ofst')
vfm_bnd_u = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:BndU}Mtr', name='vfm_bnd_u')
vfm_bnd = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:Bnd}Mtr', name='vfm_bnd')
vfm_p = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:P}Mtr', name='vfm_p')
vfm_r = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:R}Mtr', name='vfm_r')
vfm_yd = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:YD}Mtr', name='vfm_yd')
vfm_yui = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:YUI}Mtr', name='vfm_yui')
vfm_yuo = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:YUO}Mtr', name='vfm_yuo')
vfm_y = EpicsMotor('XF:28IDA-OP:1{Mir:VFM-Ax:Y}Mtr', name='vfm_y')

## Mono slits
slt_mb1_b = EpicsMotor('XF:28IDA-OP:1{Slt:MB1-Ax:B}Mtr', name='slt_mb1_b')
slt_mb1_i = EpicsMotor('XF:28IDA-OP:1{Slt:MB1-Ax:I}Mtr', name='slt_mb1_i')
slt_mb1_o = EpicsMotor('XF:28IDA-OP:1{Slt:MB1-Ax:O}Mtr', name='slt_mb1_o')
slt_mb1_t = EpicsMotor('XF:28IDA-OP:1{Slt:MB1-Ax:T}Mtr', name='slt_mb1_t')
slt_mb1_xc = EpicsMotor('XF:28IDA-OP:1{Slt:MB1-Ax:XCtr}Mtr', name='slt_mb1_xc')
slt_mb1_xg = EpicsMotor('XF:28IDA-OP:1{Slt:MB1-Ax:XGap}Mtr', name='slt_mb1_xg')
slt_mb1_yc = EpicsMotor('XF:28IDA-OP:1{Slt:MB1-Ax:YCtr}Mtr', name='slt_mb1_yc')
slt_mb1_yg = EpicsMotor('XF:28IDA-OP:1{Slt:MB1-Ax:YGap}Mtr', name='slt_mb1_yg')

## BPM 2
bpm2_ydiode = EpicsMotor('XF:28IDA-BI:1{BPM:2-Ax:YDiode}Mtr', name='bpm2_ydiode')
bpm2_yfoil = EpicsMotor('XF:28IDA-BI:1{BPM:2-Ax:YFoil}Mtr', name='bpm2_yfoil')

## FS 3
fs3_y = EpicsMotor('XF:28IDA-BI:1{FS:3-Ax:Y}Mtr', name='fs3_y')


# C Hutch
## Mono slits

slt_mb2_xg = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:XGap}Mtr', name='slt_mb2_xg')
slt_mb2_xc = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:XCtr}Mtr', name='slt_mb2_xc')
slt_mb2_yg = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:YGap}Mtr', name='slt_mb2_yg')
slt_mb2_yc = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:YCtr}Mtr', name='slt_mb2_yc')

slt_mb2_t = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:T}Mtr', name='slt_mb2_t')
slt_mb2_b = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:B}Mtr', name='slt_mb2_b')
slt_mb2_i = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:I}Mtr', name='slt_mb2_i')
slt_mb2_o = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:O}Mtr', name='slt_mb2_o')
