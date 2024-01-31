from django.urls import reverse
from datetime import datetime, timedelta, date
from ..models import Holiday,AttendanceEmployee, AttendanceHeadHr

def get_start_end_dates():
    today = datetime.now()
    start_date = date(today.year, today.month, 1)
    end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
    return start_date, end_date

def get_holidays():
    start_date, end_date = get_start_end_dates()
    holidays = Holiday.objects.filter(date__range=[start_date, end_date]).values_list('date', flat=True)
    return list(holidays)

def get_emp_leave_dates(user):
    start_date, end_date = get_start_end_dates()
    leave_dates = AttendanceEmployee.objects.filter(marked_by=user, date__range=[start_date, end_date]).values_list('date', flat=True)
    return list(leave_dates)

from hrms.models import Tour

def get_tour(user, start_date, end_date):
    tour_dates = Tour.objects.filter(applied_by=user, start_date__range=[start_date, end_date]).values_list('start_date', flat=True)
    return list(tour_dates)
  

def get_headhr_leave_dates(user):
    start_date, end_date = get_start_end_dates()
    leave_dates = AttendanceHeadHr.objects.filter(marked_by=user,date__range=[start_date, end_date]).values_list('date', flat=True)
    return list(leave_dates)

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def calculate_working_days(start_date, end_date, holidays, leave_dates):
    working_days = 0
    for single_date in daterange(start_date, end_date):
        if single_date.weekday() != 6 and single_date not in holidays:
            working_days += 1
    return working_days

def get_total_absent(start_date, end_date, holidays, leave_dates,tour_dates):
    total_absent = 0
    for single_date in daterange(start_date, end_date):
        if single_date.weekday() != 6 and single_date not in holidays and single_date not in leave_dates and single_date not in tour_dates:
            total_absent += 1
    return total_absent

def calculate_working_hours(check_in_timestamp, check_out_timestamp):  
    indian_timezone = timezone(timedelta(hours=5, minutes=30))
    check_in_datetime = datetime.fromtimestamp(check_in_timestamp, tz=indian_timezone)
    check_out_datetime = datetime.fromtimestamp(check_out_timestamp, tz=indian_timezone)   
    working_hours = check_out_datetime - check_in_datetime
    days, seconds = working_hours.days, working_hours.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return days,hours,minutes

from datetime import datetime, time, timezone, timedelta

def handle_attendance_conditions(attendance, shift):
    shift_start_time = shift.start_time
    indian_timezone = timezone(timedelta(hours=5, minutes=30))  # UTC+5:30
    human_readable_date = datetime.fromtimestamp(attendance.check_in, tz=indian_timezone)
    check_in_time = human_readable_date.time()
    grace_period = timedelta(minutes=15)
    shift_start_datetime = datetime.combine(datetime.now().date(), shift_start_time)

    shift_end_datetime = shift_start_datetime + grace_period

    if check_in_time == shift_start_time:
        attendance.status = 'Present'
        attendance.early_late_checks = 'On Time'

    elif shift_start_time < check_in_time < shift_end_datetime.time():
        attendance.status = 'Present'
        attendance.early_late_checks = 'Late'

    elif check_in_time >= shift_end_datetime.time():
        attendance.status = 'Present'
        attendance.early_late_checks = 'Half-Day'

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')

    ip = ip.split(":")[0]

    return ip


def handle_single_record_case_headhr(calendar_events, datetime_obj_checkin,custom_user):
    title = 'No Logout'
    color = '#FF4B4B'
    url = reverse('headhr_regularize', args=[datetime_obj_checkin.strftime('%Y-%m-%d'),datetime_obj_checkin.strftime('%Y-%m-%d'),"No Logout"])
    reg_data = RegularizationEmp.objects.filter(applied_by = custom_user,start_date = datetime_obj_checkin)
    if reg_data:
        for regu in reg_data:
            if regu.status =='Approved':
                title = 'Present'
                color = '#6AD02A'
                url = '#!'
            
    event_full_oneday = {
        'title': title,
        'start': datetime_obj_checkin.strftime('%Y-%m-%d'),
        'borderColor': color,
        'backgroundColor': color,
        'textColor': '#ffffff',
        'url' : url
    }
    event_checkin_oneday = {
        'title': 'Logged-in',
        'start': datetime_obj_checkin.isoformat(),
    }
    event_working_oneday = {
        'title': 'Working Hrs: 0:00:00',
        'start': datetime_obj_checkin.isoformat(),
    }
    dummy = {
        'title': '',
        'start': datetime_obj_checkin.isoformat(),
    }
    calendar_events.extend([event_full_oneday, event_checkin_oneday, event_working_oneday, dummy])

def handle_multiple_records_case_headhr(calendar_events, datetime_obj_checkin, shift, working_hours, same_date_records,custom_user):
    color, text_color, title = '', '', ''
    datetime_obj_checkout = same_date_records[-1]['date']
    url = '#!'
    if 4 < (working_hours.total_seconds() / 3600) < 8 or \
            (datetime_obj_checkin.time() > (datetime.combine(datetime.min, shift.start_time) + timedelta(minutes=shift.grace_time)).time()):
        title = 'Half-Day'
        color = '#FF4B4B'
        text_color = '#ffffff'
        reg_data = RegularizationEmp.objects.filter(applied_by = custom_user,start_date = datetime_obj_checkin)
        if reg_data:
            for regu in reg_data:
                if regu.status == 'Approved':
                    title = 'Present'
                    color = '#6AD02A'

        title = title
        color = color
        text_color = '#ffffff'
        url = reverse('headhr_regularize', args=[datetime_obj_checkin.strftime('%Y-%m-%d'),datetime_obj_checkout.strftime('%Y-%m-%d'),working_hours ])
        
    elif (working_hours.total_seconds() / 3600) < 4:
        url = reverse('headhr_regularize', args=[datetime_obj_checkin.strftime('%Y-%m-%d'),datetime_obj_checkout.strftime('%Y-%m-%d'),working_hours ])      
        title = 'Absent'
        color = '#F90707'
        text_color = '#ffffff'       

    elif datetime_obj_checkin.time() > shift.start_time:
        title = 'Present (Late)'
        color = '#50B611'
        text_color = '#ffffff'
    else:
        title = 'Present (On Time)'
        color = '#6AD02A'
        text_color = '#ffffff'

    event_full_oneday = {
        'title': title,
        'start': datetime_obj_checkin.strftime('%Y-%m-%d'),
        'end': datetime_obj_checkout.strftime('%Y-%m-%d'),
        'borderColor': color,
        'backgroundColor': color,
        'textColor': text_color,
        'url':url
        
    }
    event_checkin_oneday = {
        'title': 'Logged-in',
        'start': datetime_obj_checkin.isoformat(),
    }
    event_wrh_oneday = {
        'title': f'Working Hrs: {working_hours}',
        'start': datetime_obj_checkout.isoformat(),
    }

    calendar_events.extend([event_full_oneday, event_checkin_oneday, event_wrh_oneday])

    if datetime_obj_checkout and datetime_obj_checkout != datetime_obj_checkin:
        event_checkout = {
            'title': 'Logged Out',
            'start': datetime_obj_checkout.isoformat(),
        }
        calendar_events.append(event_checkout)


def handle_single_record_case(calendar_events, datetime_obj_checkin,custom_user):
    title = 'No Logout'
    color = '#FF4B4B'
    url = reverse('emp_regularize', args=[datetime_obj_checkin.strftime('%Y-%m-%d'),datetime_obj_checkin.strftime('%Y-%m-%d'),"No Logout"])
    reg_data = RegularizationEmp.objects.filter(applied_by = custom_user,start_date = datetime_obj_checkin)
    if reg_data:
        for regu in reg_data:
            if regu.status=='Approved':
                title = 'Present'
                color = '#6AD02A'
                url = '#!'
                       
    event_full_oneday = {
        'title': title,
        'start': datetime_obj_checkin.strftime('%Y-%m-%d'),
        'borderColor': color,
        'backgroundColor': color,
        'textColor': '#ffffff',
        'url' : url
    }
    event_checkin_oneday = {
        'title': 'Logged-in',
        'start': datetime_obj_checkin.isoformat(),
    }
    event_working_oneday = {
        'title': 'Working Hrs: 0:00:00',
        'start': datetime_obj_checkin.isoformat(),
    }
    dummy = {
        'title': '',
        'start': datetime_obj_checkin.isoformat(),
    }
    calendar_events.extend([event_full_oneday, event_checkin_oneday, event_working_oneday, dummy])


from hrms.models import RegularizationEmp

def handle_multiple_records_case(calendar_events, datetime_obj_checkin, shift, working_hours, same_date_records,custom_user):
    color, text_color, title = '', '', ''
    datetime_obj_checkout = same_date_records[-1]['date']
    url = '#!'
    if 4 < (working_hours.total_seconds() / 3600) < 8 or \
            (datetime_obj_checkin.time() > (datetime.combine(datetime.min, shift.start_time) + timedelta(minutes=shift.grace_time)).time()):
        title = 'Half-Day'
        color = '#FF4B4B'
        text_color = '#ffffff'
        url = reverse('emp_regularize', args=[datetime_obj_checkin.strftime('%Y-%m-%d'),datetime_obj_checkout.strftime('%Y-%m-%d'),working_hours ])
        reg_data = RegularizationEmp.objects.filter(applied_by = custom_user,start_date = datetime_obj_checkin)
        if reg_data:
            for regu in reg_data:
                if regu.status=='Approved':
                    title = 'Present'
                    color = '#6AD02A'
                    url = '#!'
        title = title
        color = color
        text_color = '#ffffff'
        url = url
        
    elif (working_hours.total_seconds() / 3600) < 4:
        title = 'Absent'
        color = '#F90707'
        text_color = '#ffffff'     
        url = reverse('emp_regularize', args=[datetime_obj_checkin.strftime('%Y-%m-%d'),datetime_obj_checkout.strftime('%Y-%m-%d'),working_hours ])
          

    elif datetime_obj_checkin.time() > shift.start_time:
        title = 'Present (Late)'
        color = '#50B611'
        text_color = '#ffffff'
    else:
        title = 'Present (On Time)'
        color = '#6AD02A'
        text_color = '#ffffff'

    event_full_oneday = {
        'title': title,
        'start': datetime_obj_checkin.strftime('%Y-%m-%d'),
        'end': datetime_obj_checkout.strftime('%Y-%m-%d'),
        'borderColor': color,
        'backgroundColor': color,
        'textColor': text_color,
        'url':url
        
    }
    event_checkin_oneday = {
        'title': 'Logged-in',
        'start': datetime_obj_checkin.isoformat(),
    }
    event_wrh_oneday = {
        'title': f'Working Hrs: {working_hours}',
        'start': datetime_obj_checkout.isoformat(),
    }

    calendar_events.extend([event_full_oneday, event_checkin_oneday, event_wrh_oneday])

    if datetime_obj_checkout and datetime_obj_checkout != datetime_obj_checkin:
        event_checkout = {
            'title': 'Logged Out',
            'start': datetime_obj_checkout.isoformat(),
        }
        calendar_events.append(event_checkout)
