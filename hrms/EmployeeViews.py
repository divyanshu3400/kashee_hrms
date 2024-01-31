from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect,get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from .forms import LeaveEmpForm
from .models import Holiday,AttendanceEmployee
from .models import ReportingManager,LeaveType,EmpLeaveBalance,Employee
from django.db import transaction
from kashee import settings 
from .models import TourExpense
from django.utils import timezone as tz
from datetime import datetime,timezone 
from django.core.mail import EmailMessage
from .forms import ChangeUserPasswordForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .utility.calculation import (
    get_emp_leave_dates,
    get_holidays,
    get_start_end_dates,
    calculate_working_days,
    calculate_working_days,handle_multiple_records_case,handle_single_record_case,
    handle_attendance_conditions,calculate_working_hours,get_client_ip,get_total_absent,get_tour
)

from .utility.sending_email import (
    send_emp_leave_email,send_regularization_email_mngr_approval,send_regularization_email
)
from django.template.loader import render_to_string
from .utility.api import call_soap_api,process_attendance_data

attendance_list = call_soap_api()

def employee_home(request):
    emp = Employee.objects.get(admin=request.user)
    att = None
    try:
        current_date = datetime.now().date()
        att = AttendanceEmployee.objects.get(marked_by=emp,start_date=current_date)
    except:
        att = "None"
    today = datetime.now()
    formatted_date = today.strftime('%B, %Y')
    leave_dates = get_emp_leave_dates(emp)
    total_present = AttendanceEmployee.objects.filter(marked_by = emp,is_leave=False).count()
    leave_applied = AttendanceEmployee.objects.filter(marked_by = emp,is_leave=True).count()
    start_date, end_date = get_start_end_dates()
    
    holidays = get_holidays()
    todays = tz.now().date()
    tour_dates = get_tour(request.user, start_date,todays)
    total_absent = get_total_absent(start_date,todays ,holidays,leave_dates,tour_dates) 
    total_working_days = calculate_working_days(start_date, end_date, holidays, leave_dates)
    leave_balance1 = EmpLeaveBalance.objects.get(employee=emp,leave_type=1)
    leave_balance2 = EmpLeaveBalance.objects.get(employee=emp,leave_type=2)
    leave_balance3 = EmpLeaveBalance.objects.get(employee=emp,leave_type=3)
    context = {'leave_balance1':leave_balance1,'leave_balance2':leave_balance2,
               'leave_balance3':leave_balance3,'leave_applied':leave_applied,'emp':emp,
               'formatted_date': formatted_date,'total_working_days':total_working_days,
               'total_present':total_present,'total_absent':total_absent,'att':att}
    return render(request, "employee/dashboard.html",context=context)


def employee_profile(request):
    emp = Employee.objects.get(admin=request.user)
    print()
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceEmployee.objects.get(marked_by=emp,start_date=current_date)
    except:
        pass
    leave_balance1 = EmpLeaveBalance.objects.get(employee=emp,leave_type=1)
    leave_balance2 = EmpLeaveBalance.objects.get(employee=emp,leave_type=2)
    leave_balance3 = EmpLeaveBalance.objects.get(employee=emp,leave_type=3)
    leave_applied = AttendanceEmployee.objects.filter(marked_by = emp,is_leave=True).count()
    rm=None
    rm_emp = None
    try:
        rm = ReportingManager.objects.get(emp_code=emp.emp_code)
        rm_emp = Employee.objects.get(emp_code=rm.rm_code)
    except:
        pass
    form = UserProfileUpdateForm()
    context = {'form':form,'leave_balance1':leave_balance1,'leave_balance2':leave_balance2,
               'leave_balance3':leave_balance3,'leave_applied':leave_applied,'emp':emp,'rm_emp':rm_emp,'att':att}
    return render(request, "employee/profile.html",context=context)


def send_email_confirmation(first_name,email,password):
    to_email = [email]
    subject = 'Account Create At Kashee HRMS Credential'
    message = f'Hello {first_name},\n\nYour username: {email}\nYour password: {password}'
    email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, to_email)
    email.content_subtype = 'html'
    email.send()


def employee_attend(request):
    emp = Employee.objects.get(admin=request.user)
    current_date = datetime.now().date()                    
    att =None
    try:
        att = AttendanceEmployee.objects.get(marked_by=emp,start_date=current_date)
    except:
        pass
    start_date, end_date = get_start_end_dates()
    print(f"start_date: {start_date}")
    return render(request, "employee/calendar.html", {'att':att,'emp':emp,'start_date':start_date})

from datetime import datetime

def leaves(request):
    emp = Employee.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceEmployee.objects.get(marked_by=emp,start_date=current_date)
    except:
        pass

    leaves = AttendanceEmployee.objects.filter(marked_by=emp,is_leave=True)
    context = {'leaves':leaves,'emp':emp,'att':att}
    return render(request, 'employee/leaves.html', context=context)


from datetime import datetime, timedelta

def calculate_working_hours_api(start_time_str, end_time_str):
    if start_time_str is None or end_time_str is None:
        # Handle the case where either start_time_str or end_time_str is None
        return None, None

    try:
        start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
        end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()

        start_datetime = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)

        if end_datetime < start_datetime:
            # If end time is on the next day, adjust the date
            end_datetime += timedelta(days=1)

        time_difference = end_datetime - start_datetime
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        return hours, minutes

    except ValueError as e:
        # Handle the case where there's an issue parsing the time strings
        print(f"Error calculating working hours: {e}")
        return None, None

from .models import RegularizationEmp

def get_events(request):
    calendar_events = []
    custom_user = request.user
    emp = Employee.objects.get(admin=custom_user)
    shift = emp.shift
    attendance = AttendanceEmployee.objects.filter(marked_by=emp)
    holidays = Holiday.objects.all()
    tours = Tour.objects.filter(applied_by=custom_user)
    reg_list = RegularizationEmp.objects.filter(applied_by =custom_user)
    
    if attendance_list:
        employee_dates = process_attendance_data(attendance_list)
        target_emp_code = str(emp.emp_code)
        processed_dates = set()

        if target_emp_code in employee_dates:
            attendance_logs = employee_dates[target_emp_code]
            i = 0

            while i < len(attendance_logs):
                data_checkin = attendance_logs[i]
                datetime_obj_checkin = data_checkin.get('date')

                if datetime_obj_checkin.date() in processed_dates:
                    i += 1
                    continue

                previous_day_records = [record for record in attendance_logs if record['date'].date() == (datetime_obj_checkin.date() - timedelta(days=1))]
                datetime_obj_checkout_previous_day = previous_day_records[-1]['date'] if previous_day_records else None

                if len(previous_day_records) == 1 and datetime_obj_checkout_previous_day > datetime_obj_checkin:
                    working_hours = datetime_obj_checkin - datetime_obj_checkout_previous_day
                else:
                    working_hours = None

                same_date_records = [record for record in attendance_logs if record['date'].date() == datetime_obj_checkin.date()]

                if len(same_date_records) == 1:
                    handle_single_record_case(calendar_events, datetime_obj_checkin,custom_user)

                elif len(same_date_records) >= 2:
                    datetime_obj_checkout = same_date_records[-1]['date']
                    working_hours = datetime_obj_checkout - datetime_obj_checkin
                    handle_multiple_records_case(calendar_events, datetime_obj_checkin, shift, working_hours, same_date_records,custom_user)
                    i += 1  # Skip the next record as it is used for check-out

                processed_dates.add(datetime_obj_checkin.date())
                i += 1
                
    for entry in attendance:
        if entry.is_leave and entry.is_approved:
            if entry.status == 'SL (Sick Leave)':
                title = entry.status
                color = '#da00e6'
            elif entry.status == 'EL (Earned Leave)':
                color = '#9500ff'
                title = entry.status
            elif entry.status == 'CL (Casual Leave)':
                color = '#ffa500'
                title = entry.status
                
            event = {
                    'title': title,
                    'start': entry.start_date,
                    'end': entry.end_date + timedelta(days=1),
                    'borderColor': color,
                    'backgroundColor': color,
                    'textColor': '#000000',
            }
            calendar_events.append(event)
            
                
        if not entry.is_leave :
            if entry.status == 'Present' or entry.early_late_checks == 'Half-Day':
                color = '#ff8080'
                text_color ='#000000'
                title = entry.early_late_checks
                               
            elif entry.status == 'Present' and entry.early_late_checks == 'Late':
                color = '#02b802'
                text_color ='#000000'
                title = entry.early_late_checks
                
            elif entry.status == 'Present' and entry.early_late_checks == 'On Time':
                color = '#91fa91'
                text_color ='#000000'
                title = entry.early_late_checks

            else:
                color = '#000012'
                text_color ='#000000'
                
            if entry.end_date:
               end =  entry.end_date + timedelta(days=1)
            else:
                end = entry.start_date 
            event = {
                    'title': title,
                    'start': entry.start_date,
                    'end': end,
                    'borderColor': color,
                    'backgroundColor': color,
                    'textColor': text_color,
                 }
            calendar_events.append(event)
        
    for holiday in holidays:
        event = {
            'title': holiday.name,
            'start': holiday.date.isoformat(),
            'end': holiday.date.isoformat(),
            'borderColor': "#9ba9bf",
            'backgroundColor': "#9ba9bf",
            'textColor': '#fff',
        }
        calendar_events.append(event)
    
    for tour in tours:
        
        if tour.is_approved:
            event = {
                'title': tour.title,
                'start': tour.start_date.isoformat(),
                'end': tour.end_date + timedelta(days=1),
                'borderColor': "#a9a9a9",
                'backgroundColor': "#a9a9a9",
                'textColor': '#fff',
            }
            calendar_events.append(event)
    
    
    if reg_list:
            for reg in reg_list:
                if reg.status == 'Approved':       
                    event = {
                            'title': "Regularised",
                            'start': reg.start_date,
                            'borderColor': "#a9a9a9",
                            'backgroundColor': "#a9a9a9",
                            'textColor': '#fff',
                        }
                calendar_events.append(event)

    return JsonResponse(calendar_events, safe=False)


def apply_leaves(request):
    employee= Employee.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceEmployee.objects.get(marked_by=employee,start_date=current_date)
    except:
        pass

    if request.method == 'POST':
        form = LeaveEmpForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            current_date = datetime.today()
            if start_date is not None:
                formatted_start_date = start_date.strftime('%Y-%m-%d')
            else:
                formatted_start_date = None  
            if end_date is not None:
                formatted_end_date = end_date.strftime('%Y-%m-%d')
            else:
                formatted_end_date = None 
                
            formatted_current_date = current_date.strftime('%Y-%m-%d')
            start_date1 = datetime.strptime(formatted_start_date, '%Y-%m-%d')
            end_date1 = datetime.strptime(formatted_end_date, '%Y-%m-%d')
            days = ((end_date1 - start_date1).days)+1
            leave_type = LeaveType.objects.get(id=form.cleaned_data['leave_type'].id)
            
            if leave_type.leave_type == "EL (Earned Leave)" and days < 4:
                messages.error(request, "The earned leave should be for 4 or more days.")
                return redirect('emp_apply_leaves')
                        
            if leave_type.leave_type == "CL (Casual Leave)" and (start_date1 - current_date).days+1 < 3:
                messages.error(request, "You must apply for casual leave at least 3 days in advance.")
                return redirect('emp_apply_leaves')
            
            if leave_type.leave_type == "SL (Sick Leave)" and days > 3 and not form.cleaned_data['medical_certificate']:
                messages.error(request, "Medical Certificate required for Sick Leave more than 3 days.")
                return redirect('emp_apply_leaves')
            try:
                if AttendanceEmployee.objects.get(marked_by=employee, start_date=formatted_start_date , is_leave=True):
                    messages.error(request, "Your already have event on this date. Please Check")
                    return redirect('emp_apply_leaves')
            except:
                pass
                
            leaves_data = {
                    'start_date': formatted_start_date,
                    'end_date': formatted_end_date,
                    'reason': form.cleaned_data['reason'],
                    'status':leave_type.leave_type ,
                    'is_leave':True,
                    'is_approved':False,
                    'is_rejected':False,
                    'leave_type':leave_type,
                    'marked_by':employee,
                    'date':formatted_current_date
                    }
            try:
                with transaction.atomic():                    
                    leave = AttendanceEmployee.objects.create(**leaves_data)                    
                    messages.success(request,"Your leave request has been sent to your manager. Wait for approval. Thanks!!")
                    send_emp_leave_email(employee,leave)
                return redirect('emp_apply_leaves')
            except Exception as e:
                print("Exception")
                print(e)
                messages.error(request,"Leave application failed")        
                
                return redirect('emp_apply_leaves')
    else:
        form = LeaveEmpForm()
    return render(request, 'employee/apply_leaves.html',{'form':form,'emp':employee,'att':att})

    
from datetime import datetime, timezone, timedelta

def mark_attendance(request):
    
    head_hr = Employee.objects.get(admin=request.user)
    if has_checked_in(head_hr):
        return redirect('employee_home')
    else:
        return redirect('emp_mark_checkin')

def has_checked_in(user):
    current_date = datetime.now().date()
    latest_attendance = AttendanceEmployee.objects.filter(marked_by=user, start_date=current_date).order_by('-check_in').first()
    if latest_attendance:
        return False
    else:
        return True


def mark_check_out(request):
    emp = Employee.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceEmployee.objects.get(marked_by=emp,start_date=current_date)
    except:
        pass

    msg="Check-Out"
    ip_address = get_client_ip(request)
    current_date = datetime.now().date()
    att = AttendanceEmployee.objects.get(marked_by=emp,start_date=current_date)
    indian_timezone = timezone(timedelta(hours=5, minutes=30)) 
    human_readable_date = datetime.fromtimestamp(att.check_in, tz=indian_timezone)
    formatted_date = human_readable_date.strftime("%b-%d-%Y")
    formatted_time = human_readable_date.strftime("%I:%M %p")
    context =  {'ip_address': ip_address,'msg':msg,'emp':emp ,'formatted_date':formatted_date,'formatted_time':formatted_time, 'att':att}
    return render(request, 'employee/mark_attendance.html',context=context)


def mark_check_in(request):
    emp = Employee.objects.get(admin=request.user)
    msg="Check-In"
    att=None
    ip_address = get_client_ip(request)
    return render(request, 'employee/mark_attendance.html', {'emp':emp,'ip_address': ip_address,'msg':msg,'att':att})

import os
import base64
from django.core.files.base import ContentFile

def save_headhr_attend(request):
    if request.method == 'POST':
        user = Employee.objects.get(admin=request.user) 
        ip = request.POST.get('ip')
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        imagebase64 = request.POST.get('imagebase64')
        format, imgstr = imagebase64.split(';base64,') 
        current_timestamp = datetime.timestamp(datetime.now())
        ext = format.split('/')[-1]
        image_dir = 'images'
        image_path = os.path.join(image_dir, f"user_{request.user.username}_image.{ext}")
        
        image_content = ContentFile(base64.b64decode(imgstr), name=image_path)
        current_date = datetime.now().date()
        existing_attendance = AttendanceEmployee.objects.filter(marked_by=user, start_date=current_date).first()

        if existing_attendance:
            messages.success(request, f"Hello! {request.user.first_name}. Checked-Out Successfully")        
            if existing_attendance.attend_image:
                existing_photo_path = existing_attendance.attend_image.path
                if os.path.exists(existing_photo_path):
                    os.remove(existing_photo_path)

            existing_attendance.check_out = current_timestamp
            existing_attendance.end_date = current_date
            existing_attendance.attend_image = image_content
            day,hours,minutes = calculate_working_hours(check_in_timestamp=existing_attendance.check_in, check_out_timestamp=current_timestamp)
            if hours < 4:
                existing_attendance.early_late_checks = "Absent"
            if hours < 8:
                existing_attendance.early_late_checks = "Half-Day"
                
            existing_attendance.hrs_worked=f"{day}-Day, {hours}-Hrs, {minutes}-Min"
            handle_attendance_conditions(existing_attendance, user.shift)
            existing_attendance.save()
        
        else:              
            messages.success(request, f"Hello! {request.user.first_name}. Checked-In Successfully")
            new_attendance = AttendanceEmployee(
                marked_by=user,
                check_in=current_timestamp,
                date=current_date,
                start_date = current_date,
                is_leave = False,
                latitude = float(lat),
                ip = ip,
                longitude = float(lon),
                attend_image = image_content
            )
            handle_attendance_conditions(new_attendance, user.shift)
            new_attendance.save()
        return JsonResponse({"sucess":True,'message':"Attendance Marked Successfully"})



def requested_leaves(request):
    emp = Employee.objects.get(admin=request.user)
    rms = ReportingManager.objects.filter(rm_code=emp.emp_code)
    emp_codes = [rm.emp_code for rm in rms]
    leaves = AttendanceEmployee.objects.filter(marked_by__emp_code__in=emp_codes, is_leave=True)
    context = {'leaves': leaves, 'emp': emp}
    return render(request, 'employee/leave_req.html', context=context)



def approves_leaves(request, leave_id, marked_by):
    leave = AttendanceEmployee.objects.get(id=leave_id)
    leave.is_approved = True
    leave.is_rejected = False
    days = (leave.end_date - leave.start_date).days + 1
    employee = Employee.objects.get(id=marked_by)

    overlapping_tour = Tour.objects.filter(
        applied_by=employee.admin,
        start_date__lte=leave.end_date, 
        end_date__gte=leave.start_date,
    ).first()

    if overlapping_tour:
        overlapping_tour.start_date = leave.end_date - timedelta(days=1)
        overlapping_tour.save()

    leave_type = LeaveType.objects.get(leave_type=leave.status)
    leave_balance = EmpLeaveBalance.objects.get(employee=employee, leave_type=leave_type)

    if leave_balance.balance > 0:
        leave_balance.balance -= days

    leave_balance.save()
    leave.save()
    messages.success(request, 'Leave Approved')
    return redirect('requested_leaves')

def delete(request,leave_id):
    leave = AttendanceEmployee.objects.get(id=leave_id)
    leave.delete()
    messages.error(request, 'Leave Cancelled')
    return redirect('emp_leaves')

def cancel_leave(request,leave_id):
   pass


def edit_leave(request, leave_id=None):
    emp = Employee.objects.get(admin=request.user)
    leave = None
    if leave_id:
        leave = get_object_or_404(AttendanceEmployee, id=leave_id)
    if request.method == 'POST':
        form = LeaveEmpForm(request.POST, instance=leave)
        if form.is_valid():
            form.save()
            return redirect('emp_leaves')
    else:
        form = LeaveEmpForm(instance=leave)

    return render(request, "employee/apply_leaves.html", {'form': form,'emp':emp})

def reject_leaves(request, leave_id,marked_by):
    leave = AttendanceEmployee.objects.get(id=leave_id)
    leave.is_approved = False
    leave.is_rejected = True
    days = ((leave.end_date - leave.start_date).days)+1
    employee= Employee.objects.get(id=marked_by)
    leave_type = LeaveType.objects.get(leave_type=leave.status)
    leave_balance = EmpLeaveBalance.objects.get(employee=employee,leave_type=leave_type)
    if leave_balance.balance < int(leave_type.days):
        leave_balance.balance =leave_balance.balance + days 
    leave_balance.save()
    leave.save()
    messages.error(request, 'Leave Rejected')
    return redirect('requested_leaves')


@login_required(login_url='/')
def change_password(request):
    emp = Employee.objects.get(admin=request.user)
    if request.method == 'POST':
        form_data = ChangeUserPasswordForm(request.user, request.POST)
        if form_data.is_valid():
            form_data.save()
            logout(request)
            messages.success(request, "Your password was changed successfully. Please Login again to continue...")
            return redirect("show_login")
        else:
            messages.error(request, "Error while changing the password. Please try again")
            return redirect("emp_change_password")
    
    else:
        form  = ChangeUserPasswordForm(request.user)
        return render(request, 'employee/change_password.html', {'form':form,'emp':emp})


from .models import Tour
from .forms import TourForm


def add_tour(request):
    emp = Employee.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceEmployee.objects.get(marked_by=emp,start_date=current_date)
    except:
        pass

    if request.method == 'POST':
        form = TourForm(request.POST)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.applied_by = request.user 
            tour.save()
            messages.success(request, "Your Tour has beent sent for approval to your manager. Wait for approval")
            return redirect('emp_tours')
        else:
            return redirect('emp_apply_tour')
    else:
        form = TourForm()
    return render(request, 'employee/apply_tour.html', {'form': form,'att':att,'emp':emp})

def view_tour(request,tour_id):
    emp = Employee.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceEmployee.objects.get(marked_by=emp,start_date=current_date)
    except:
        pass

    tour_details = Tour.objects.get(id=tour_id,applied_by=request.user)
    tour_expanse = TourExpense.objects.filter(tour=tour_details)
    return render(request, 'employee/tour_details.html', {'emp':emp,'att':att,'tour_details': tour_details,'tour_expanse':tour_expanse})

from django.http import JsonResponse
from .forms import TourExpenseForm


def edit_tour(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id, applied_by=request.user)

    if request.method == 'POST':
        form = TourForm(request.POST, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, "Tour Updated Successfully!!")
            return redirect('emp_tours')
    else:
        form = TourForm(instance=tour)

    return render(request, 'employee/apply_tour.html', {'form': form, 'tour': tour})

def delete_tour(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id, applied_by=request.user)
    tour.delete()
    messages.error(request, "Tour Deleted Successfully!!")
    return redirect('emp_tours')

def mark_complete(request,tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    tour.is_completed = True
    today = datetime.today()
    formatted_tour_date = today.strftime('%Y-%m-%d')
    tour.completion_date = formatted_tour_date
    tour.save()
    return redirect('emp_tours')

def tours(request):
    emp = Employee.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceEmployee.objects.get(marked_by=emp,start_date=current_date)
    except:
        pass

    user_tours = Tour.objects.filter(applied_by=request.user)            
    return render(request, 'employee/tour.html', {'emp':emp,'att':att,'tours': user_tours})   


def upload_bill(request):
    if request.method == 'POST':
        # Get tour_id from POST data
        tour_id = request.POST.get('tour_id')
        tour = Tour.objects.get(id=tour_id)
        print(f"Tour id: {tour_id}")
        uploaded_files = request.FILES.getlist('bills')

        for uploaded_file in uploaded_files:
            print(f"File name: {uploaded_file.name}")
            print(f"File size: {uploaded_file.size} bytes")
            tour_expense = TourExpense.objects.create(tour=tour, bill=uploaded_file)
            tour_expense.save()
        messages.success(request, "Files uploaded successfully.")
        return redirect('emp_tours')
    else:
        messages.error(request, "Error occurred! Try again.")
        return redirect('emp_tours')


# Example in a Django view
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

def send_notification(user_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {"type": "send.notification", "message": message},
    )


def approves_tour(request, tour_id, applied_by):
    tour = Tour.objects.get(id=tour_id)
    tour.is_approved = True
    tour.is_rejected = False
    tour.save()
    messages.success(request, 'Tour Approved')
    return redirect('admin_requested_tour')


def reject_tour(request, tour_id, applied_by):
    tour = Tour.objects.get(id=tour_id)
    tour.is_approved = False
    tour.is_rejected = True
    tour.save()
    messages.error(request, 'Tour Rejected')
    return redirect('admin_requested_tour')


def view_tour(request,tour_id):
    tour_details = get_object_or_404(Tour, id=tour_id)
    emp_object = None
    rm_manager = None
    emp_object = Employee.objects.get(admin=tour_details.applied_by)
    rm_obj = ReportingManager.objects.get(emp_code=emp_object.emp_code)
    rm_manager = Employee.objects.get(emp_code=rm_obj.rm_code)
    return render(request, 'superadmin/tour_details.html', {'tour_details': tour_details,'emp':emp_object,'rm':rm_manager})


# views.py
from django.shortcuts import render, redirect
from .forms import RegularizationForm
from .models import RegularizationEmp,CustomUser

def req_regularization(request):
    emp = Employee.objects.get(admin=request.user)
    rms = ReportingManager.objects.filter(rm_code=emp.emp_code)
    emp_codes = [rm.emp_code for rm in rms]
    employees = Employee.objects.filter(emp_code__in=emp_codes)
    custom_users = [custom_user.admin for custom_user in employees]
    regs = RegularizationEmp.objects.filter(applied_by__in=custom_users)
    context = {'regularization_list':regs, 'emp': emp}
    return render(request, 'employee/regularization_req.html',context)

def regularization_list(request):
    emp = Employee.objects.get(admin = request.user)
    remp = 'NA'
    try:
        rm = ReportingManager.objects.get(emp_code = emp.emp_code)
        remp = Employee.objects.get(emp_code = rm.rm_code)
    except:
        pass
    regularizations = RegularizationEmp.objects.filter(applied_by = request.user)
    return render(request, 'employee/regularization_list.html', {'regularizations':regularizations,'remp':remp})


def regularization_create(request, start_date=None, end_date =None,working_hrs=None):
    
    if request.method == 'POST':
        form = RegularizationForm(request.POST)
        if form.is_valid():
            regularization = form.save(commit=False)
            regularization.applied_by = request.user
            start_date = form.cleaned_data['start_date']
            if RegularizationEmp.objects.filter(applied_by=request.user, start_date=start_date).exists():
                messages.error(request, 'You already have applied for the regularization on the selected date')
                return render('emp_attendance')
            regularization.created_at = datetime.today()  
            regularization.hrs_worked = working_hrs  
            regularization.save()
            messages.success(request, 'Your Regularization request has been sent to you reporting manager for approval.')
            emp = Employee.objects.get(admin=request.user)
            send_regularization_email(emp,regularization)
            return redirect('emp_regularization_list')
    else:
        form = RegularizationForm(start_date=start_date,end_date =end_date)

    return render(request, 'employee/regularization.html', {'form': form})


from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegularizationForm
from .models import RegularizationEmp

def regularization_view(request, pk):
    regularization = get_object_or_404(RegularizationEmp, pk=pk)
    form = RegularizationForm(instance=regularization)
    return render(request, 'employee/regularization_view.html', {'form': form, 'regularization': regularization})

def regularization_edit(request, pk):
    regularization = get_object_or_404(RegularizationEmp, pk=pk)

    if request.method == 'POST':
        form = RegularizationForm(request.POST, instance=regularization)
        if form.is_valid():
            form.instance.applied_by = request.user
            form.save()
            messages.success(request, 'Regularization Updated Successfully')
            
            return redirect('emp_regularization_list')
    else:
        form = RegularizationForm(instance=regularization)

    return render(request, 'employee/regularization.html', {'form': form, 'regularization': regularization})

def regularization_delete(request, pk):
    regularization = get_object_or_404(RegularizationEmp, applied_by=request.user, pk=pk)
    regularization.delete()
    messages.error(request, 'Regularization Deleted Successfully')
    return redirect('emp_regularization_list')

from django.contrib import messages
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .models import RegularizationEmp
from .forms import AdminRegularizationForm


class EmployeeRegularizationView(FormView):
    template_name = 'employee/regularization_form.html'
    form_class = AdminRegularizationForm
    success_url = reverse_lazy('remp_req_regularization')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        regularization_id = self.kwargs.get('regularization_id')
        regularization_instance = get_object_or_404(RegularizationEmp, pk=regularization_id)
        kwargs['instance'] = regularization_instance
        return kwargs

    def form_valid(self, form):
        action = self.request.POST.get('action')
        regularization_instance = form.save(commit=False)

        if action == 'approve':
            regularization_instance.status = "Approved"
            regularization_instance.admin_comments = form.cleaned_data['admin_comments']
            messages.success(self.request, 'Regularization request approved successfully.')
            send_regularization_email_mngr_approval(regularization_instance,self.request.user)
        elif action == 'reject':
            regularization_instance.status = "Rejected"
            regularization_instance.admin_comments = form.cleaned_data['admin_comments']
            send_regularization_email_mngr_approval(regularization_instance,self.request.user)
            messages.success(self.request, 'Regularization request rejected successfully.')

        regularization_instance.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error processing the regularization request.')
        return super().form_invalid(form)

from .forms import UserProfileUpdateForm

import os
from PIL import Image
from django.shortcuts import render, redirect
from .forms import UserProfileUpdateForm

def update_profile(request):
    emp = Employee.objects.get(admin=request.user)

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES)
        
        if form.is_valid():
            if emp.image:
                old_image_path = emp.image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
                    emp.image = None

            emp.image = form.cleaned_data['image']
            emp.save()
            img = Image.open(emp.image.path)

            if img.width != 150 or img.height != 150:
                img = img.resize((150, 150), resample=Image.BICUBIC)
                # img = img.resize((150, 150), Image.ANTIALIAS)
                img.save(emp.image.path)

            emp.save()

            return redirect('employee_profile')