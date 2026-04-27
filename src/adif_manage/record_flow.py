from __future__ import annotations

from datetime import datetime

from .adif_codec import DATE_PATTERN, TIME_PATTERN, missing_required_fields, validate_core_field_formats

ALL_QSO_FIELDS = [
    "ADDRESS","ADDRESS_INTL","AGE","ALTITUDE","ANT_AZ","ANT_EL","ANT_PATH","ARRL_SECT","AWARD_GRANTED","AWARD_SUBMITTED","A_INDEX",
    "BAND","BAND_RX","CALL","CHECK","CLASS","CLUBLOG_QSO_UPLOAD_DATE","CLUBLOG_QSO_UPLOAD_STATUS","CNTY","CNTY_ALT","COMMENT","COMMENT_INTL","CONT","CONTACTED_OP","CONTEST_ID","COUNTRY","COUNTRY_INTL","CQZ","CREDIT_SUBMITTED","CREDIT_GRANTED",
    "DARC_DOK","DCL_QSLRDATE","DCL_QSLSDATE","DCL_QSL_RCVD","DCL_QSL_SENT","DISTANCE","DXCC",
    "EMAIL","EQ_CALL","EQSL_AG","EQSL_QSLRDATE","EQSL_QSLSDATE","EQSL_QSL_RCVD","EQSL_QSL_SENT",
    "FISTS","FISTS_CC","FORCE_INIT","FREQ","FREQ_RX",
    "GRIDSQUARE","GRIDSQUARE_EXT","GUEST_OP",
    "HAMLOGEU_QSO_UPLOAD_DATE","HAMLOGEU_QSO_UPLOAD_STATUS","HAMQTH_QSO_UPLOAD_DATE","HAMQTH_QSO_UPLOAD_STATUS","HRDLOG_QSO_UPLOAD_DATE","HRDLOG_QSO_UPLOAD_STATUS",
    "IOTA","IOTA_ISLAND_ID","ITUZ",
    "K_INDEX",
    "LAT","LON","LOTW_QSLRDATE","LOTW_QSLSDATE","LOTW_QSL_RCVD","LOTW_QSL_SENT",
    "MAX_BURSTS","MODE","MORSE_KEY_INFO","MORSE_KEY_TYPE","MS_SHOWER",
    "MY_ALTITUDE","MY_ANTENNA","MY_ANTENNA_INTL","MY_ARRL_SECT","MY_CITY","MY_CITY_INTL","MY_CNTY","MY_CNTY_ALT","MY_COUNTRY","MY_COUNTRY_INTL","MY_CQ_ZONE","MY_DARC_DOK","MY_DXCC","MY_FISTS","MY_GRIDSQUARE","MY_GRIDSQUARE_EXT","MY_IOTA","MY_IOTA_ISLAND_ID","MY_ITU_ZONE","MY_LAT","MY_LON","MY_MORSE_KEY_INFO","MY_MORSE_KEY_TYPE","MY_NAME","MY_NAME_INTL","MY_POSTAL_CODE","MY_POSTAL_CODE_INTL","MY_POTA_REF","MY_RIG","MY_RIG_INTL","MY_SIG","MY_SIG_INTL","MY_SIG_INFO","MY_SIG_INFO_INTL","MY_SOTA_REF","MY_STATE","MY_STREET","MY_STREET_INTL","MY_USACA_COUNTIES","MY_VUCC_GRIDS","MY_WWFF_REF",
    "NAME","NAME_INTL","NOTES","NOTES_INTL","NR_BURSTS","NR_PINGS","OPERATOR","OWNER_CALLSIGN",
    "PFX","POTA_REF","PRECEDENCE","PROP_MODE","PUBLIC_KEY",
    "QRZCOM_QSO_DOWNLOAD_DATE","QRZCOM_QSO_DOWNLOAD_STATUS","QRZCOM_QSO_UPLOAD_DATE","QRZCOM_QSO_UPLOAD_STATUS","QSLMSG","QSLMSG_INTL","QSLMSG_RCVD","QSLRDATE","QSLSDATE","QSL_RCVD","QSL_RCVD_VIA","QSL_SENT","QSL_SENT_VIA","QSL_VIA","QSO_COMPLETE","QSO_DATE","QSO_DATE_OFF","QSO_RANDOM","QTH","QTH_INTL",
    "REGION","RIG","RIG_INTL","RST_RCVD","RST_SENT","RX_PWR",
    "SAT_MODE","SAT_NAME","SFI","SIG","SIG_INTL","SIG_INFO","SIG_INFO_INTL","SILENT_KEY","SKCC","SOTA_REF","SRX","SRX_STRING","STATE","STATION_CALLSIGN","STX","STX_STRING","SUBMODE","SWL",
    "TEN_TEN","TIME_OFF","TIME_ON","TX_PWR",
    "UKSMG","USACA_COUNTIES","VE_PROV","VUCC_GRIDS","WEB","WWFF_REF",
    "APP_ADIFMANAGE_WX",
]

REQUIRED_FIELD_SEQUENCE = [
    ("日期 DATE", "QSO_DATE", "YYYYMMDD", True),
    ("时间 TIME", "TIME_ON", "HHMM 或 HHMMSS", True),
    ("呼号 CALLSIGN", "CALL", "", True),
    ("频率 MHz", "FREQ", "如 14.250", True),
    ("模式 MODE", "MODE", "如 SSB,CW,FT8", True),
    ("信号 RST (己方发送)", "RST_SENT", "如 599", False),
    ("信号 RST (收到对方)", "RST_RCVD", "如 599", False),
    ("功率 PWR (己方发射)", "TX_PWR", "如 100W", False),
    ("功率 PWR (对方发射)", "RX_PWR", "如 100W", False),
    ("位置 QTH", "QTH", "", False),
    ("设备 RIG", "RIG", "如 IC-7300", False),
    ("天线 ANT", "MY_ANTENNA", "如 DP", False),
    ("天气 WX", "APP_ADIFMANAGE_WX", "", False),
]


def run_record_interaction(stdin_readline, stdout_write, last_fields=None):
    if last_fields is None:
        last_fields = {}

    fields: dict[str, str] = {}
    snapshot: dict[str, str] = dict(last_fields)

    stdout_write("\n=== 必填字段录入（请依次输入） ===\n")

    for label, field_name, hint, required in REQUIRED_FIELD_SEQUENCE:
        last_value = last_fields.get(field_name)

        while True:
            prompt_parts = [f"请输入 {label}"]
            if hint:
                prompt_parts.append(f" [{hint}]")

            if last_value:
                prompt_parts.append(f" (上次: {last_value})")
                if required:
                    prompt_parts.append(" [回车保留]")
                else:
                    prompt_parts.append(" [回车保留, - 跳过]")
            else:
                if not required:
                    prompt_parts.append(" [回车跳过]")

            prompt_parts.append(": ")
            stdout_write("".join(prompt_parts))

            value = stdin_readline().strip()

            if value == "":
                if last_value:
                    value = last_value
                elif required:
                    stdout_write("此字段为必填，不能跳过\n")
                    continue
                else:
                    break

            if value == "-":
                if required:
                    stdout_write("此字段为必填，不能跳过\n")
                    continue
                else:
                    break

            fields[field_name] = value
            snapshot[field_name] = value

            if field_name == "QSO_DATE":
                if not DATE_PATTERN.match(value):
                    stdout_write("日期格式错误，请输入 YYYYMMDD 格式\n")
                    fields.pop(field_name, None)
                    continue
                try:
                    datetime.strptime(value, "%Y%m%d")
                except ValueError:
                    stdout_write("日期无效，请输入有效的日期\n")
                    fields.pop(field_name, None)
                    continue

            if field_name == "TIME_ON":
                if not TIME_PATTERN.match(value):
                    stdout_write("时间格式错误，请输入 HHMM 或 HHMMSS 格式\n")
                    fields.pop(field_name, None)
                    continue
                if len(value) == 4:
                    hh = int(value[0:2])
                    mm = int(value[2:4])
                    if hh > 23 or mm > 59:
                        stdout_write("时间范围无效\n")
                        fields.pop(field_name, None)
                        continue
                else:
                    hh = int(value[0:2])
                    mm = int(value[2:4])
                    ss = int(value[4:6])
                    if hh > 23 or mm > 59 or ss > 59:
                        stdout_write("时间范围无效\n")
                        fields.pop(field_name, None)
                        continue

            break

    stdout_write("\n=== 选填字段 ===\n")
    already_filled = set(fields.keys())
    available = [f for f in ALL_QSO_FIELDS if f not in already_filled]

    while True:
        stdout_write("输入编号填写字段，0 完成，q 完成，qf 强制结束:\n")
        for i, name in enumerate(available, start=1):
            lv = last_fields.get(name)
            tag = f" (上次: {lv})" if lv else ""
            stdout_write(f"  {i:3d}: {name}{tag}\n")

        choice = stdin_readline().strip()

        if choice == "0":
            missing = missing_required_fields(fields)
            format_errors = validate_core_field_formats(fields)
            if missing:
                stdout_write("请填写所有必填字段再完成\n")
                continue
            if format_errors:
                stdout_write(f"字段格式错误: {', '.join(format_errors)}\n")
                continue
            return fields, snapshot

        if choice == "q":
            missing = missing_required_fields(fields)
            format_errors = validate_core_field_formats(fields)
            if missing:
                stdout_write("请填写所有必填字段再完成\n")
                continue
            if format_errors:
                stdout_write(f"字段格式错误: {', '.join(format_errors)}\n")
                continue
            return fields, snapshot

        if choice == "qf":
            missing = missing_required_fields(fields)
            format_errors = validate_core_field_formats(fields)
            if missing or format_errors:
                stdout_write("您未录入所有必填字段，QSO 记录失败\n")
                return None
            return fields, snapshot

        if not choice.isdigit():
            stdout_write("输入无效，请输入字段编号、0、q 或 qf\n")
            continue

        idx = int(choice)
        if idx < 1 or idx > len(available):
            stdout_write("编号超出范围\n")
            continue

        field_name = available[idx - 1]
        lv = last_fields.get(field_name, "")
        hint = f" (上次: {lv})" if lv else ""
        stdout_write(f"请输入 {field_name}{hint}: ")
        value = stdin_readline().strip()

        if value:
            fields[field_name] = value
            snapshot[field_name] = value
        elif field_name in fields:
            fields.pop(field_name)
