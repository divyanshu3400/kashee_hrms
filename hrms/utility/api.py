import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def call_soap_api():
    url = "http://10.10.10.63:99/iclock/WebAPIService.asmx"
    # url = "http://192.168.108.81:99/iclock/WebAPIService.asmx"
    headers = {'Content-Type': 'text/xml'}
    params = {'op': 'GetTransactionsLog'}
    body = """<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetTransactionsLog xmlns="http://tempuri.org/">
                    <FromDateTime>2023-01-01 00:01</FromDateTime>
                    <ToDateTime>2024-12-22 23:59</ToDateTime>
                    <SerialNumber>CEXJ222261829</SerialNumber>
                    <UserName>ApiUser</UserName>
                    <UserPassword>@Essl#123</UserPassword>
                    <strDataList>string</strDataList>
                </GetTransactionsLog>
            </soap:Body>
        </soap:Envelope>
    """
    response = requests.post(url, params=params, data=body, headers=headers)

    if response.status_code == 200:
        root = ET.fromstring(response.content) 
        log_result = root.find(".//{http://tempuri.org/}GetTransactionsLogResult").text
        str_data_list = root.find(".//{http://tempuri.org/}strDataList").text

        return str_data_list
from datetime import datetime

def process_attendance_data(attendance_list):
    employee_dates = {}
    lines = attendance_list.split('\n')
    for line in lines:
        columns = line.strip().split('\t')
        if len(columns) >= 2:
            emp_code = columns[0].strip()
            date_str = columns[1].strip()
            datetime_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

            # Check if emp_code exists in the dictionary, and initialize it if not
            if emp_code not in employee_dates:
                employee_dates[emp_code] = []

            employee_dates[emp_code].append({'date': datetime_obj})

    return employee_dates
