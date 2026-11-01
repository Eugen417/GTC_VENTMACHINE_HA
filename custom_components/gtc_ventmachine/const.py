"""Константы интеграции GTC Ventmachine (автоматика Оазис v.5 / Syberia 5)."""

DOMAIN = "gtc_ventmachine"

PLATFORMS = ["sensor", "fan", "number", "binary_sensor", "climate", "select"]

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_POLL_INTERVAL = 5

# ---------------------------------------------------------------------------
# Адресация регистров Modbus (0-based на шине = адрес из PDF "Оазис v.5" - 1)
# ---------------------------------------------------------------------------

# Input Registers (Функция 0x04)
IR_FIRMWARE_VERS = 0       # PDF 0x01 (01): Firmware_Vers
IR_FIRMWARE_SUBVERS = 1    # PDF 0x02 (02): Firmware_SubVers
IR_STATE_0 = 2             # PDF 0x03 (03): State_0 (битовое поле состояния)
IR_STATE_1 = 3             # PDF 0x04 (04): State_1 (этап работы 0..12)
IR_ERROR_CODE = 4          # PDF 0x05 (05): Error_Code (основные ошибки)
IR_ERROR_CODE_1 = 5        # PDF 0x06 (06): Error_Code_1 (доп. поле ошибок)
IR_LAST_TIME = 6           # PDF 0x07 (07): Last_Time (ст. байт мин, мл. байт сек)
IR_TKAN_X10 = 7            # PDF 0x08 (08): Tkan_x10 (T1 приточный воздух, °C x 10)
IR_TOBR_X10 = 8            # PDF 0x09 (09): Tobr_x10 (T2 обратная вода, °C x 10)
IR_TKANK_X10 = 9           # PDF 0x0A (10): TkanK_x10 (T1 скоррект., °C x 10)
IR_TOBRK_X10 = 10          # PDF 0x0B (11): TobrK_x10 (T2 скоррект., °C x 10)
IR_TNAR_X10 = 11           # PDF 0x0C (12): TNar_x10 (T3 наружный воздух, °C x 10)
IR_TNARK_X10 = 12          # PDF 0x0D (13): TNarK_x10 (T3 скоррект., °C x 10)
IR_PSENS_PA = 13           # PDF 0x0E (14): PSens_Pa (перепад давления, Па)
IR_ZAGR_FILTR_1 = 14       # PDF 0x0F (15): ZagrFiltr1 (загрязнение фильтра 1, %)

IR_FAN_STATE_1 = 25        # PDF 0x1A (26): Fan_State_1 (текущая скорость вент. 1)
IR_NEXT_TIMER_TIME = 26    # PDF 0x1B (27): Next_Timer_Hour (ст.) / Min (мл.)
IR_NEXT_TIMER_TEMP = 27    # PDF 0x1C (28): Next_Timer_Temp_Target (°C x 10)
IR_NEXT_TIMER_FAN = 28     # PDF 0x1D (29): Next_Timer_Fan_Target
IR_MAX_HOLDING = 29        # PDF 0x1E (30): Max_Holding
IR_FAN_STATE_2 = 30        # PDF 0x1F (31): Fan_State_2 (текущая скорость вент. 2)

IR_TKOMN_X10_P = 57        # PDF 0x3A (58): TKomn_x10_P (темп. в помещении, °C x 10)
IR_ROOM_HUM_P = 58         # PDF 0x3B (59): Room_Hum_P (влажность в помещении, %)
IR_ROOM_CO2 = 60           # PDF 0x3D (61): Room_CO2 (CO2 в помещении, ppm)

IR_ERROR_CODE_2 = 69       # PDF 0x46 (70): Error_Code_2
IR_ERROR_CODE_3 = 70       # PDF 0x47 (71): Error_Code_3

IR_TKOMN_X10 = 74          # PDF 0x4B (75): TKomn_x10 (T4 в помещении, °C x 10)
IR_TRECP_X10 = 76          # PDF 0x4D (77): Trecp_x10 (T5 выход рекуператора, °C x 10)

IR_FAN1_RPM = 81           # PDF 0x52 (82): Fan1_RPM (обороты двигателя 1)
IR_FAN2_RPM = 82           # PDF 0x53 (83): Fan2_RPM (обороты двигателя 2)
IR_ZAGR_FILTR_2 = 84       # PDF 0x55 (85): ZagrFiltr2 (загрязнение фильтра 2, %)

# Holding Registers (Функции 0x03 / 0x06)
HR_TYPE_DEV = 0            # PDF 0x01 (01): Type_Dev (конфигурация оборудования)
HR_POWER_DEV = 2           # PDF 0x03 (03): Power_Dev (Bit 0: 1 - вкл, 0 - выкл)
HR_TEMP_TARGET = 31        # PDF 0x20 (32): Temp_Target (уставка темп., °C x 10)
HR_FAN_TARGET_1 = 32       # PDF 0x21 (33): Fan_Target_1 (уставка скорости 1..10)
HR_FAN_TARGET_2 = 33       # PDF 0x22 (34): Fan_Target_2 (уставка скорости вент. 2)
HR_MAC_START = 353         # PDF 0x162..0x164 (354..356): MAC[0..5] (3 регистра)

