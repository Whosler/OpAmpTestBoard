from machine import Pin, ADC, DAC
import time

cvs = [150, 900, 1200, 1700, 2400]
toggle_ps = Pin(27)
adc = ADC(Pin(28))
adc.width(ADC.WIDTH_12BIT)
dac = Pin(30, Pin.OUT) # no need for variable voltage

sel_out_dut_inv = Pin(16, Pin.OUT)
sel_out_dut_x100 = Pin(13, Pin.OUT)
sel_out_aux_inv = Pin(23, Pin.OUT)
sel_out_aux_x100 = Pin(27, Pin.OUT)

sel_dut = Pin(12, Pin.OUT)
sel_aux = Pin(8, Pin.OUT)

amp_sel = [sel_dut, sel_out_dut_x100, sel_out_dut_inv, sel_aux, sel_out_aux_x100, sel_out_aux_inv]

adc.width(adc.width(ADC.WIDTH_12BIT))
calibration_consts = {0: [0.2343855, 74.08035], 1: [0.3111147, 75.87675], 2: [0.4307876, 103.8019], 3: [0.8009325, 140.5917]}
db_0 = []
db_1 = []
db_2 = []
db_3 = []

#k1, k2, k3/k6, k4, k5, k7, k8
#sel_s1, sel_s3, sel_hilo, sel_out_mode, sel_out_res, sel_s2, sel_dac_inv
sel_s1 = Pin(33, Pin.OUT)
sel_s3 = Pin(31, Pin.OUT)
sel_hilo = Pin(24, Pin.OUT)
sel_out_mode = Pin(26, Pin.OUT)
sel_out_res = Pin(29, Pin.OUT)
sel_s2 = Pin(36, Pin.OUT)
sel_dac_inv = Pin(14, Pin.OUT)

c_sel = [sel_s1, sel_s3, sel_hilo, sel_out_mode, sel_out_res, sel_s2, sel_dac_inv]

Vos_c = [1,0,0,0,0,1,0]
Ibn_c = [0,0,0,0,0,1,0]
Ibp_c = [1,0,0,0,0,0,0]
Aol_c = [1,1,0,0,0,1,0]
CMRR_c = [1,0,0,0,0,1,0]
PSRR_c = [1,0,0,0,0,1,0]
hi_c = [0,0,1,1,1,0,0]
lo_c = [0,0,1,1,1,0,1]
Isc_c = [0,0,1,1,0,0,0]

#k16/k18, k17/k19, dac
sel_1V = Pin(37, Pin.OUT)
sel_0_5V = Pin(10, Pin.OUT)
dac = Pin(30, Pin.OUT) # no need for variable voltage

p_sel = [sel_1V, sel_0_5V, dac]

Vos_p = [0,0,0]
Ibn_p = [0,0,0]
Ibn_p = [0,0,0]
Aol_p = [0,0,0]
CMRR_p = [1,0,0]
PSRR_p = [0,1,0]
hi_c = [0,0,1]
lo_c = [0,0,1]
Isc_p = [0,0,1]

en_dut = Pin(11, Pin.OUT)

def lin_reg(x, y):
    N = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(x[i] * y[i] for i in range(N))
    sum_x_squared = sum(x[i] ** 2 for i in range(N))

    # Calculating the slope (m)
    m = (N * sum_xy - sum_x * sum_y) / (N * sum_x_squared - sum_x ** 2)

    # Calculating the intercept (b)
    b = (sum_y - m * sum_x) / N
    return [m, b]

def calibrate(index, adc):
    #record voltage
    if index < 2:
        adc.atten(ADC.ATTN_0DB)
        db_0.append(adc.read())
        adc.atten(ADC.ATTN_2_5DB)
        db_1.append(adc.read())
        adc.atten(ADC.ATTN_6DB)
        db_2.append(adc.read())
        adc.atten(ADC.ATTN_11DB)
        db_3.append(adc.read())
        return None
    elif index < 3:
        adc.atten(ADC.ATTN_0DB)
        db_0.append(adc.read())
        adc.atten(ADC.ATTN_2_5DB)
        db_1.append(adc.read())
        adc.atten(ADC.ATTN_6DB)
        db_2.append(adc.read())
        adc.atten(ADC.ATTN_11DB)
        db_3.append(adc.read())
        return None
    elif index < 4:
        adc.atten(ADC.ATTN_6DB)
        db_2.append(adc.read())
        adc.atten(ADC.ATTN_11DB)
        db_3.append(adc.read())
    else:
        adc.atten(ADC.ATTN_11DB)
        db_3.append(adc.read())
        calibration_consts[0] = lin_reg(db_0, cvs[0:2])
        calibration_consts[1] = lin_reg(db_1, cvs[0:3])
        calibration_consts[2] = lin_reg(db_2, cvs[0:4])
        calibration_consts[3] = lin_reg(db_3, cvs[0:5])
        calibrate_dac(adc)

def read_adc(adc):
    adc.atten(ADC.ATTN_11DB) #150-2450mv
    adc_vals = [0]*500
    for i in range(500):
        adc_vals[i] = adc.read()
    avg = sum(adc_vals)/len(adc_vals)
    avg = avg * calibration_consts[3][0] + calibration_consts[3][1]
    if avg < 950:
        adc.atten(ADC.ATTN_0DB) #100-900mv
        for i in range(500):
            adc_vals[i] = adc.read()
        avg = sum(adc_vals)/len(adc_vals)
        return avg * calibration_consts[0][0] + calibration_consts[0][1]
    elif avg < 1250:
        adc.atten(ADC.ATTN_2_5DB) #100-1250mv
        for i in range(500):
            adc_vals[i] = adc.read()
        avg = sum(adc_vals)/len(adc_vals)
        return avg * calibration_consts[1][0] + calibration_consts[1][1]
    elif avg < 1750:
        adc.atten(ADC.ATTN_6DB) #150-1750mv
        for i in range(500):
            adc_vals[i] = adc.read()
        avg = sum(adc_vals)/len(adc_vals)
        return avg * calibration_consts[2][0] + calibration_consts[2][1]
    return avg

def set_amp_sel(sels):
    for i, pin in enumerate(amp_sel):
        if sels[i]:
            pin.on()
        else:
            pin.off()

def quick_read(adc):
    adc_vals = []
    for i in range(10):
        adc_vals.append(adc.read_uv())
    return sum(adc_vals) / len(adc_vals)

mults = [1,-1,100,-100,-1000,1000,-100_000,100_000]
mult_dict = {0: [0,0,0,0,0,0], 1: [1,0,0,0,0,0], -1: [1,0,1,0,0,0], 100: [1,1,1,0,0,0], -100: [1,1,0,0,0,0], -1000: [0,0,0,1,0,0], 1000: [0,0,0,1,0,1], -100_000: [0,0,0,1,1,1], 100_000: [0,0,0,1,1,0]}

def get_v(adc):
    low_thresh = calibration_consts[0][1] + 10
    for mult in mults:
        set_amp_sels(mult_dict[mult])
        time.sleep(0.5)
        if quick_read(adc) > low_thresh:
            set_amp_sels(mult_dict[0])
            return read_adc() * 1000 / mult

names_dict = {"vos": "Offset Voltage", "ibn": "Negative Bias Current", "ibp": "Positive Bias Current", "ios": "Offset Current", "aol": "Open Loop Gain", "psrr": "Power Supply Rejection Ratio", "cmrr": "Common Mode Rejection Ratio", "hilo": "Output Levek Hi/Lo", "isc": "Short Circuit Current"}

def setup_test(prop_c, prop_p):
    for i, pin in c_sel:
        if prop_c[i]:
            pin.on()
        else:
            pin.off()
    for i, pin in prop_p:
        if prop_p[i]:
            pin.on()
        else:
            pin.off()
    time.sleep(0.5) # wait for relays to activate and circuit to settle
        
rf = 100_000
rg = 100
rb = 100_000
rs = 0.1
G = 1 + rf/ rg
def run_props(props):
    en_dut.off()
    #run first one, get voa
    voa = 0
    props_dict = {}
    if names_dict["vos"] in props or names_dict["ibn"] in props or names_dict["ibp"] in props or names_dict["aol"] in props or names_dict["ios"] in props or names_dict["psrr"] in props or names_dict["cmrr"] in props:
        setup_test(Vos_c, Vos_p)
        en_dut.on()
        time.sleep(0.5)
        voa = get_v(adc)
        vos = -1 * voa / G
        props_dict["vos"] = vos
        en_dut.off()
    if names_dict["ibn"] in props or names_dict["ios"] in props:
        setup_test(Ibn_c, Ibn_p)
        en_dut.on()
        time.sleep(0.5)
        vob = get_v(adc)
        props_dict["ibn"] = (vob-voa)/rb/G
        en_dut.off()
    if names_dict["ibp"] in props or names_dict["ios"] in props:
        setup_test(Ibp_c, Ibp_p)
        en_dut.on()
        time.sleep(0.5)
        voc = get_v(adc)
        props_dict["ibn"] = (voa-voc)/rb/G
        en_dut.off()
    if names_dict["ios"] in props:
        props_dict["ios"] = props_dict["ibp"] - props_dict["ibn"]
    if names_dict["aol"] in props:
        setup_test(Aol_c, Aol_p)
        en_dut.on()
        time.sleep(0.5)
        vod = get_v(adc)
        props_dict["aol"] = G/(voa-vod)
        en_dut.off()
    if names_dict["psrr"] in props:
        setup_test(Psrr_c, Psrr_p)
        en_dut.on()
        time.sleep(0.5)
        voe = get_v(adc)
        props_dict["psrr"] = G/(voe-voa)
        en_dut.off()
    if names_dict["cmrr"] in props:
        setup_test(Cmrr_c, Cmrr_p)
        en_dut.on()
        time.sleep(0.5)
        vof = get_v(adc)
        props_dict["cmrr"] = G/(vof-voa)
        en_dut.off()
    if names_dict["hilo"] in props:
        setup_test(Hi_c, Hi_p)
        en_dut.on()
        time.sleep(0.5)
        vo = get_v(adc)
        props_dict["hi"] = vo/G
        en_dut.off()
        setup_test(Lo_c, Lo_p)
        en_dut.on()
        time.sleep(0.5)
        vo = get_v(adc)
        props_dict["lo"] = vo/G
        en_dut.off()
        props_dict["hilo"] = props_dict["hi"] - props_dict["lo"]
    if names_dict["Isc"] in props:
        setup_test(Isc_c, Isc_p)
        en_dut.on()
        time.sleep(0.5)
        vo = get_v(adc)
        props_dict["isc"] = vo/rs
        en_dut.off()
    return props_dict
    
for i in range(len(cvs)):
  calibrate(i, adc)

props_dict = run_props(["Offset Voltage", "Negative Bias Current", "Positive Bias Current", "Offset Current", "Open Loop Gain", "Power Supply Rejection Ratio", "Common Mode Rejection Ratio", "Output Levek Hi/Lo", "Short Circuit Current"])
    
    
    
    
