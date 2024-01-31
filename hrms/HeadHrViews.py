import datetime
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect,get_object_or_404, redirect, render
from django.urls import reverse
from .models import ShiftTiming,CustomUser,Address,EmpLeaveBalance,AttendanceHeadHr
from django.db import transaction
from kashee import settings 
from django.core.mail import EmailMessage
from .forms import ExcelUploadForm
from .forms import HrForm,ShiftTimingForm,LeaveHrForm,AddHolidaysForm, EditHrForm,EmployeeForm,Holiday
from .models import ShiftTiming,CustomUser,Address,MartialStatus,Department,Designation,Employee,AttendanceEmployee
from .models import ReportingManager,HeadHrLeaveBalance,Gender,LeaveType,AttendanceHeadHr,HeadHr
import random
from django.contrib.auth.hashers import make_password
import pandas as pd
from .create_user import (
    return_address,
    setReportingManager,
    create_reporting_manager,
    create_role_based_user,
    formatted_ann,
)
from .utility.sending_email import (
    send_emp_leave_email,send_regularization_email_mngr_approval,send_regularization_email
)
from .utility.calculation import (
    get_headhr_leave_dates,
    get_holidays,
    get_start_end_dates,
    calculate_working_days,handle_multiple_records_case,handle_single_record_case,handle_multiple_records_case_headhr,
    handle_attendance_conditions,calculate_working_hours,get_client_ip, get_tour, get_total_absent,handle_single_record_case_headhr
)

from .utility.api import call_soap_api,process_attendance_data

attendance_list = call_soap_api()
import json

def hrhead_home(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count
    user_activity = None
    current_date = datetime.now().date()
    head_hr_attend = AttendanceHeadHr.objects.filter(start_date=current_date, is_leave=True)
    employee_attend = AttendanceEmployee.objects.filter(start_date=current_date, is_leave = True)
    gender_male = Gender.objects.get(gender='Male')
    gender_female = Gender.objects.get(gender='Female')
    user_activity = list(chain(head_hr_attend, employee_attend))    
    head_hr_user_fem  = HeadHr.objects.filter(gender = gender_female).count()
    head_hr_usee_male  = HeadHr.objects.filter(gender = gender_male).count()
    emp_user_fem  = Employee.objects.filter(gender = gender_female).count()
    emp_user_male  = Employee.objects.filter(gender = gender_male).count()
    male = head_hr_usee_male+emp_user_male
    female = head_hr_user_fem+emp_user_fem
    gender = Gender.objects.all()
    gender_list = []
    
    for g in gender:
        gender_list.append(g.gender)
    context = {'total_count':total_count,'emp':head_hr, 'shift_count':shift_count,'att':att,'user_activity':user_activity,'gender_list':json.dumps(gender_list),'male':male,'female':female}
    return render(request, "headhr/home_content.html", context=context)

def dashboard(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass

    from datetime import datetime
    from django.utils import timezone    
    today = datetime.now()
    formatted_date = today.strftime('%B, %Y')
    headhr = HeadHr.objects.get(admin=request.user)
    total_present = AttendanceHeadHr.objects.filter(marked_by = headhr,is_leave=False).count()
    leave_applied = AttendanceHeadHr.objects.filter(marked_by = headhr,is_leave=True).count()
    start_date, end_date = get_start_end_dates()
    holidays = get_holidays()
    leave_dates = get_headhr_leave_dates(headhr)
    todays = timezone.now().date()
    tour_dates = get_tour(request.user, start_date,todays)
    total_absent = get_total_absent(start_date,todays ,holidays,leave_dates,tour_dates) 
    total_working_days = calculate_working_days(start_date, end_date, holidays, leave_dates)
    leave_balance1 = HeadHrLeaveBalance.objects.get(headhr=headhr,leave_type=1)
    leave_balance2 = HeadHrLeaveBalance.objects.get(headhr=headhr,leave_type=2)
    leave_balance3 = HeadHrLeaveBalance.objects.get(headhr=headhr,leave_type=3)

    context = {'leave_balance1':leave_balance1,'leave_balance2':leave_balance2,
               'leave_balance3':leave_balance3,'leave_applied':leave_applied,'emp':headhr,
               'formatted_date': formatted_date,'total_working_days':total_working_days,
               'total_present':total_present,'total_absent':total_absent,'att':att}
    return render(request, "headhr/dashboard.html",context=context)


def hrhead_profile(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass

    shift_count = ShiftTiming.objects.all().count()    
    leave_balance1 = HeadHrLeaveBalance.objects.get(headhr=head_hr,leave_type=1)
    leave_balance2 = HeadHrLeaveBalance.objects.get(headhr=head_hr,leave_type=2)
    leave_balance3 = HeadHrLeaveBalance.objects.get(headhr=head_hr,leave_type=3)
    leave_applied = AttendanceHeadHr.objects.filter(marked_by= head_hr,is_leave=True).count()
    rm=None
    rm_emp = None
    try:
        rm = ReportingManager.objects.get(emp_code=head_hr.emp_code)
        rm_emp = HeadHr.objects.get(emp_code=rm.rm_code)
    except:
        pass
    context = {'shift_count':shift_count,'leave_balance1':leave_balance1,'leave_balance2':leave_balance2,
               'leave_balance3':leave_balance3,'leave_applied':leave_applied, 'att':att,'emp':head_hr,'rm_emp':rm_emp}
    return render(request, "headhr/profile.html",context=context)

def mark_attendance(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    if has_checked_in(head_hr):
        return redirect('hrhead_home')
    else:
        return redirect('head_mark_checkin')
    
from datetime import datetime, timezone, timedelta

def mark_check_out(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    msg="Check-Out"
    ip_address = get_client_ip(request)
    current_date = datetime.now().date()
    att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    indian_timezone = timezone(timedelta(hours=5, minutes=30)) 
    human_readable_date = datetime.fromtimestamp(att.check_in, tz=indian_timezone)
    formatted_date = human_readable_date.strftime("%b-%d-%Y")
    formatted_time = human_readable_date.strftime("%I:%M %p")

    return render(request, 'headhr/mark_attendance.html', {'ip_address': ip_address,'msg':msg, 'formatted_date':formatted_date,'formatted_time':formatted_time, 'att':att})


def mark_check_in(request):
    msg="Check-In"
    att=None
    ip_address = get_client_ip(request)
    return render(request, 'headhr/mark_attendance.html', {'ip_address': ip_address,'msg':msg,'att':att})


def has_checked_in(user):
    current_date = datetime.now().date()
    latest_attendance = AttendanceHeadHr.objects.filter(marked_by=user, start_date=current_date).order_by('-check_in').first()
    if latest_attendance:
        return False
    else:
        return True

import base64
from django.core.files.base import ContentFile

import os

def save_headhr_attend(request):
    if request.method == 'POST':
        user = HeadHr.objects.get(admin=request.user) 
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
        existing_attendance = AttendanceHeadHr.objects.filter(marked_by=user, start_date=current_date).first()

        if existing_attendance:
            messages.success(request, f"Hello! {request.user.first_name}. Checked-Out Successfully")        
            if existing_attendance.attend_image:
                existing_photo_path = existing_attendance.attend_image.path
                if os.path.exists(existing_photo_path):
                    os.remove(existing_photo_path)

            existing_attendance.check_out = current_timestamp
            existing_attendance.end_date = current_date
            existing_attendance.attend_image = image_content
            day,hours, minutes = calculate_working_hours(check_in_timestamp=existing_attendance.check_in, check_out_timestamp=current_timestamp)
            
            if hours < 4:
                existing_attendance.early_late_checks = "Absent"
            if hours < 8:
                existing_attendance.early_late_checks = "Half-Day"
                                
            existing_attendance.hrs_worked=f"{day}-Day, {hours}-Hrs, {minutes}-Min"
            handle_attendance_conditions(existing_attendance, user.shift)
            existing_attendance.save()
        
        else:              
            messages.success(request, f"Hello! {request.user.first_name}.Checked-In Successfully")
            new_attendance = AttendanceHeadHr(
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

import string

def enroll_hr(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass

    message = "HR"
    hr_count = HeadHr.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    leave_types = LeaveType.objects.all()
    if request.method == 'POST':
        form = HrForm(request.POST)
        if form.is_valid():            
            emp_code = form.cleaned_data.get('emp_code')
            if not emp_code:
                emp_code = f"{random.randint(100, 999)}"
                form.cleaned_data['emp_code'] = emp_code
            username = form.cleaned_data['first_name'] + str(form.cleaned_data['emp_code'])
            reporting_manager_code =  form.cleaned_data['reporting_manager']
            reporting_m = None
            if reporting_manager_code !="":
                create_reporting_manager(reporting_manager_code,emp_code)
            try:
                with transaction.atomic():
                    if CustomUser.objects.filter(email=form.cleaned_data['email']).exists() or CustomUser.objects.filter(username=username).exists():
                        messages.error(request,"This email / username already taken")
                        return redirect('enroll_hr')
                    address_instance = Address.objects.create(**return_address(form))
                    username = form.cleaned_data['first_name'] + str(form.cleaned_data['emp_code'])
                    role= form.cleaned_data['role'].id
                    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    password = 'Kashee' + random_suffix
                    email = form.cleaned_data['email']
                    last_name = form.cleaned_data['last_name']
                    first_name = form.cleaned_data['first_name']
                    email = form.cleaned_data['email']
                    hashed_password = make_password(password)
                    user = CustomUser.objects.create(username=username,first_name=first_name,last_name=last_name,email=email,password=hashed_password,user_type=role)
                    hr = HeadHr.objects.create(**create_role_based_user(user,form,address_instance,reporting_m))               
                    hr.save()
                    for leave in leave_types:
                        HeadHr.objects.create(hr=hr,leave_type=leave,balance=leave.days).save()
                    send_email_confirmation(form.cleaned_data['first_name'], form.cleaned_data['email'], password)
                    if reporting_manager_code:
                        setReportingManager(reporting_manager_code)
                    messages.success(request, "HR registered successfully!!")
                    return HttpResponseRedirect(reverse("admin_hr_list"))
            except Exception as e:
                print("Excecption")
                print(e)
                messages.error(request, "Failed to create the HR")
                if 'address_instance' in locals() and address_instance:
                    address_instance.delete()
                if 'user' in locals() and user:
                    user.delete()
                if 'repoting_m' in locals() and reporting_m:
                    reporting_m.delete()
                
                return redirect('admin_enroll_hr')
        else:
            messages.error(request,"Form is not valid")
            return redirect('admin_enroll_hr')
    else:
        form = HrForm()
    return render(request, 'headhr/enroll_hr.html', {'att':att,'form': form,'emp':head_hr,'hr_count':hr_count, 'shift_count':shift_count,'msg':message})


def enroll_employee(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass

    message = "Employee"
    shift_count = ShiftTiming.objects.all().count()
    leave_types = LeaveType.objects.all()
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('first_name') + str(form.cleaned_data.get('emp_code'))
            reporting_manager_code =  form.cleaned_data['reporting_manager']
            emp_code = form.cleaned_data['emp_code']
            reporting_m = None
            if reporting_manager_code !="":
                reporting_m = create_reporting_manager(reporting_manager_code=reporting_manager_code,emp_code=emp_code)
            try:
                with transaction.atomic():
                    if CustomUser.objects.filter(email=form.cleaned_data['email']).exists() or CustomUser.objects.filter(username=username).exists():
                        messages.error(request,"This email / username already taken")
                        return redirect('enroll_hr')
                    address_instance = Address.objects.create(**return_address(form=form))
                    username = form.cleaned_data['first_name'] + str(form.cleaned_data['emp_code'])
                    role= form.cleaned_data['role'].id
                    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    password = 'Kashee' + random_suffix
                    email = form.cleaned_data['email']
                    last_name = form.cleaned_data['last_name']
                    first_name = form.cleaned_data['first_name']
                    email = form.cleaned_data['email']
                    hashed_password = make_password(password)
                    user = CustomUser.objects.create(username=username,first_name=first_name,last_name=last_name,email=email,password=hashed_password,user_type=role)
                    employee = Employee.objects.create(**create_role_based_user(user=user,form=form,address_instance=address_instance,reporting_m=reporting_m))
                    employee.save()
                    for leave in leave_types:
                        EmpLeaveBalance.objects.create(employee=employee,leave_type=leave,balance=leave.days).save()
                    if reporting_manager_code !="":
                        setReportingManager(reporting_manager_code)
                    send_email_confirmation(form.cleaned_data['first_name'], form.cleaned_data['email'],password)
                    messages.success(request, "Employee registered successfully!!")
                    return HttpResponseRedirect(reverse("admin_hr_list"))
            except Exception as e:
                print("Excecption")
                print(e)
                messages.error(request, "Failed to create the Employee")
                if 'address_instance' in locals() and address_instance:
                    address_instance.delete()
                if 'user' in locals() and user:
                    user.delete()
                return redirect('admin_enroll_rm')
        else:
            messages.error(request,"Form is not valid")
            return redirect('admin_enroll_rm')
    else:
        form = EmployeeForm()
    return render(request, 'headhr/enroll_hr.html', {'att':att,'form': form,'emp':head_hr, 'shift_count':shift_count,'msg':message})

from django.shortcuts import get_object_or_404

def get_role(role_id,hr_id):
    if role_id==1:
        return get_object_or_404(HeadHr, id=hr_id)
    else:
        return get_object_or_404(Employee, id=hr_id)
    

def edit_hr(request, hr_id,role_id):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass
    
    message = f"Edit Employee, {get_role(role_id=role_id,hr_id=hr_id).admin.first_name} {get_role(role_id=role_id,hr_id=hr_id).admin.last_name}"
    
    if request.method == 'POST':
        form = EditHrForm(request.POST, instance=get_role(role_id=role_id,hr_id=hr_id))
        if form.is_valid():
            try:
                with transaction.atomic():
                    role_instance = get_role(role_id, hr_id)
                    if isinstance(role_instance, HeadHr):
                        update_head_hr(form,role_instance)
                        messages.success(request, "Data updated successfully!!")
                        return HttpResponseRedirect(reverse("head_hr_list"))

                    else:
                        update_employee(form,role_instance)
                        messages.success(request, "Data updated successfully!!")
                        return HttpResponseRedirect(reverse("head_hr_list"))

            except Exception as e:
                print("Exception")
                print(e)
                messages.error(request, "Failed to update the details")
                return redirect('head_edit_hr', hr_id=hr_id,role_id=role_id)
        else:
            print(form.errors)
            messages.error(request, "Form is not valid")
            return redirect('head_edit_hr', hr_id=hr_id,role_id=role_id)
    else:
        form = EditHrForm(instance=get_role(role_id=role_id,hr_id=hr_id))
    return render(request, 'headhr/enroll_hr.html', {'att':att,'form': form, 'emp':head_hr,'msg': message, 'hr': get_role(role_id=role_id,hr_id=hr_id)})

from itertools import chain

def hr_list(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass

    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    total_count = head_hr_count+emp_count

    head_hr_objects = HeadHr.objects.select_related(
        'admin', 'department', 'designation', 'martial_status', 'gender','reporting_manager'
    ).all()

    employee_objects = Employee.objects.select_related(
        'admin', 'department', 'designation', 'martial_status', 'gender','reporting_manager'
    ).all()
    # all_hr_objects = list(chain(hr_objects, head_hr_objects, employee_objects))
    shift_count = ShiftTiming.objects.all().count()
    employees = []
    for obj in employee_objects:
        rm_emp = None
        try:        
            rmp = ReportingManager.objects.get(emp_code = obj.emp_code)
            print(rmp)
            rm_emp = Employee.objects.get(emp_code = rmp.rm_code)
            print(rm_emp)
        except:
            pass
        role = ""
        if obj.admin.user_type == '3':
            role = "Employee"

        employees_dict = {
                'name': f"{obj.admin.first_name} {obj.admin.last_name}",
                'email': obj.admin.email,
                'department': obj.department,
                'age': obj.age,
                'designation': obj.designation,
                'rm':rm_emp,
                'role': role,
                'view_url': reverse('head_view_emp_profile', args=[obj.id, obj.admin.user_type]),
                'delete_url': reverse('head_delete_hr', args=[obj.id, obj.admin.user_type]),
                'edit_url': reverse('head_edit_hr', args=[obj.id , obj.admin.user_type]),
            }
        employees.append(employees_dict)

    for obj in head_hr_objects:
        rm_emp = None
        try:        
            rmp = ReportingManager.objects.get(emp_code = obj.emp_code)
            rm_emp = HeadHr.objects.get(emp_code = rmp.rm_code)
        except:
            pass
        role = ""
        if obj.admin.user_type == '1':
            role = "HR"

        employees_dict = {
                'name': f"{obj.admin.first_name} {obj.admin.last_name}",
                'email': obj.admin.email,
                'department': obj.department,
                'age': obj.age,
                'designation': obj.designation,
                'rm':rm_emp,
                'role': role,
                'view_url': reverse('head_view_emp_profile', args=[obj.id , obj.admin.user_type]),
                'delete_url': reverse('head_delete_hr', args=[obj.id, obj.admin.user_type]),
                'edit_url': reverse('head_edit_hr', args=[obj.id , obj.admin.user_type]),
            }
        employees.append(employees_dict)
        
        
    context = {
        'total_count': total_count,
        'shift_count': shift_count,
        'hr_objects': employees,
        'emp':head_hr
    }
    return render(request, 'headhr/hr_list.html', context)


def update_head_hr(form,role_instance):
    username = form.cleaned_data.get('first_name') + str(form.cleaned_data.get('emp_code'))
    reporting_manager_code =  form.cleaned_data['reporting_manager']
    emp_code = form.cleaned_data['emp_code']
    ann_date = form.cleaned_data['anniversary']
    dob = form.cleaned_data['dob']
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    marital_status_instance = MartialStatus.objects.get(id=form.cleaned_data['martial_status'].id)
    dept_instance = Department.objects.get(id=form.cleaned_data['department'].id)
    gend_inst = Gender.objects.get(id=form.cleaned_data['gender'].id)
    shift_inst = ShiftTiming.objects.get(id=form.cleaned_data['shift'].id)
    desig_instance = Designation.objects.get(id=form.cleaned_data['designation'].id)
    print(desig_instance)
    print(marital_status_instance)
    
    reporting_m = None
    try:        
        reporting_m = ReportingManager.objects.get(rm_code = reporting_manager_code ,emp_code = emp_code)
        reporting_m.delete()
    except:
        pass
    if reporting_manager_code !="":
        reporting_m = create_reporting_manager(reporting_manager_code=reporting_manager_code,emp_code=emp_code)

    try:
        address_instance = Address.objects.get(id = role_instance.address.id)
        address_instance.address_line_1  = form.cleaned_data.get('address_line_1')
        address_instance.address_line_2  = form.cleaned_data.get('address_line_2')
        address_instance.district  = form.cleaned_data.get('district')
        address_instance.state  = form.cleaned_data.get('state')
        address_instance.country  = form.cleaned_data.get('country')
        address_instance.zipcode  = form.cleaned_data.get('zip_code')
        address_instance.save()
        user=CustomUser.objects.get(id=role_instance.admin.id)
        user.first_name = form.cleaned_data.get('first_name')
        user.last_name = form.cleaned_data.get('last_name')
        user.email = form.cleaned_data.get('email')         
        user.username = username           
        user.save()
        employee = HeadHr.objects.get(id=role_instance.id)
        date_of_joining = form.cleaned_data['date_of_joining']
        formatted_dob_date = dob.strftime('%Y-%m-%d')
        employee.anniversary = formatted_ann(ann_date)
        employee.department = dept_instance
        employee.address = address_instance
        employee.martial_status = marital_status_instance
        employee.age = age
        employee.gender = gend_inst
        employee.shift = shift_inst
        employee.emp_code = emp_code
        employee.designation = desig_instance
        employee.date_of_joining = date_of_joining
        employee.dob = formatted_dob_date
        employee.reporting_manager = reporting_m
        employee.save()
        return True
    except Exception as e:
        return False

def view_attendance(request,hr_id, role_id):
    role_instance = get_role(role_id, hr_id)
    remp = None
    if isinstance(role_instance, HeadHr):
        emp = HeadHr.objects.get(id = hr_id)
        try:
            rm = ReportingManager.objects.get(emp_code = emp.emp_code)
        except:
            rm = None
        if rm is not None:
            remp = HeadHr.objects.get(emp_code = rm.rm_code)
    else:
        emp = Employee.objects.get(id=hr_id)
        try:
            rm = ReportingManager.objects.get(emp_code = emp.emp_code)
        except:
            rm=None
            
        if rm is not None:
            remp = Employee.objects.get(emp_code = rm.rm_code)
        
    url = reverse('ind_emp_events', args=[emp.admin.user_type , emp.id])
        
    return render(request, 'headhr/emp_atten.html', {'emp':emp,'url':str(url),'remp':remp})

def update_employee(form,role_instance):
    username = form.cleaned_data.get('first_name') + str(form.cleaned_data.get('emp_code'))
    reporting_manager_code =  form.cleaned_data['reporting_manager']
    emp_code = form.cleaned_data['emp_code']
    ann_date = form.cleaned_data['anniversary']
    dob = form.cleaned_data['dob']
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    marital_status_instance = MartialStatus.objects.get(id=form.cleaned_data['martial_status'].id)
    dept_instance = Department.objects.get(id=form.cleaned_data['department'].id)
    gend_inst = Gender.objects.get(id=form.cleaned_data['gender'].id)
    shift_inst = ShiftTiming.objects.get(id=form.cleaned_data['shift'].id)
    desig_instance = Designation.objects.get(id=form.cleaned_data['designation'].id)
    print(f"reporting_manager_code: {reporting_manager_code}")
    reporting_m = None
    if reporting_manager_code !="":
        print('Inside If block')
        try:        
            reporting_m = ReportingManager.objects.get(rm_code = reporting_manager_code ,emp_code = emp_code)
            reporting_m.delete()
        except:
            pass
        reporting_m = create_reporting_manager(reporting_manager_code=reporting_manager_code,emp_code=emp_code)

    try:
        address_instance = Address.objects.get(id = role_instance.address.id)
        address_instance.address_line_1  = form.cleaned_data.get('address_line_1')
        address_instance.address_line_2  = form.cleaned_data.get('address_line_2')
        address_instance.district  = form.cleaned_data.get('district')
        address_instance.state  = form.cleaned_data.get('state')
        address_instance.country  = form.cleaned_data.get('country')
        address_instance.zipcode  = form.cleaned_data.get('zip_code')
        address_instance.save()
        user=CustomUser.objects.get(id=role_instance.admin.id)
        user.first_name = form.cleaned_data.get('first_name')
        user.last_name = form.cleaned_data.get('last_name')
        user.email = form.cleaned_data.get('email')         
        user.username = username           
        user.save()
        employee = Employee.objects.get(id=role_instance.id)
        date_of_joining = form.cleaned_data['date_of_joining']
        formatted_dob_date = dob.strftime('%Y-%m-%d')
        employee.anniversary = formatted_ann(ann_date)
        employee.department = dept_instance
        employee.address = address_instance
        employee.martial_status = marital_status_instance
        employee.age = age
        employee.gender = gend_inst
        employee.shift = shift_inst
        employee.emp_code = emp_code
        employee.designation = desig_instance
        employee.date_of_joining = date_of_joining
        employee.dob = formatted_dob_date
        employee.reporting_manager = reporting_m
        employee.save()
        return True
    except Exception as e:
        return False

from django.db import transaction
from django.http import Http404

def delete_hr(request, hr_id, role_id):
    try:
        with transaction.atomic():
            role = get_role(hr_id=hr_id, role_id=role_id)
            if isinstance(role, HeadHr):
                leave_balance = HeadHrLeaveBalance.objects.filter(head_hr=role)
                attendances = AttendanceHeadHr.objects.filter(marked_by=hr_id)
                for leave in leave_balance:
                    leave.delete()
                for attendance in attendances:
                    attendance.delete()

            elif isinstance(role, Employee):
                leave_balance = EmpLeaveBalance.objects.filter(employee=role)
                attendances = AttendanceHeadHr.objects.filter(marked_by=hr_id)
                for leave in leave_balance:
                    leave.delete()
                for attendance in attendances:
                    attendance.delete()

            address = Address.objects.get(id=role.address.id)
            address.delete()
            
            reporting_manager = ReportingManager.objects.get(emp_code=role.emp_code)
            reporting_manager.delete()
            
            user = get_object_or_404(CustomUser, id=role.admin.id)
            user.delete()
            
            messages.success(request, "User data has been deleted successfully")
            return redirect('admin_hr_list')

    except Http404:
        # Re-raising Http404 if needed with custom message or perform additional handling
        raise Http404("Rolling back changes due to an error")

    except Exception as e:
        # Log the exception or perform error handling as required
        # Avoid using generic 'Exception' for handling unless necessary
        # This block is to catch any other unexpected exceptions
        # Rollback will be handled automatically by 'transaction.atomic()'
        messages.error(request, f"An error occurred: {str(e)}")
        # Optionally, you might want to log the exception for debugging
        # logger.error(f"An error occurred: {str(e)}")
        # Then re-raise the exception to let Django handle it
        raise e


def shift_timing(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count
    context = {'total_count':total_count, 'shift_count':shift_count,'att':att}
    shift_timings = ShiftTiming.objects.all()
    shift_count = ShiftTiming.objects.all().count()
    context = {'total_count':total_count, 'shift_count':shift_count,'shift_timings': shift_timings}
    return render(request, "headhr/shift_timing.html", context)


def add_shift_timing(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass

    shift_count = ShiftTiming.objects.all().count()
    if request.method == 'POST':
        form = ShiftTimingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shift_timing')
    else:
        form = ShiftTimingForm()
    return render(request, "headhr/add_shift_timing.html", {'att':att,'form': form, 'shift_count':shift_count})

def edit_shift_timing(request, pk=None):
    shift = None
    if pk:
        shift = get_object_or_404(ShiftTiming, id=pk)
    if request.method == 'POST':
        form = ShiftTimingForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            return redirect('shift_timing')
    else:
        form = ShiftTimingForm(instance=shift)

    return render(request, "headhr/add_shift_timing.html", {'form': form})


def delete_shift(request, pk):
    shift = get_object_or_404(ShiftTiming, id=pk)
    if request.method == 'POST':
        shift.delete()
        return redirect('success_delete')
    
def send_email_confirmation(first_name,email,password):
    to_email = [email]
    subject = 'Account Create At Kashee HRMS Credential'
    message = f'Hello {first_name},\n\nYour username: {email}\nYour password: {password}'
    email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, to_email)
    email.content_subtype = 'html'
    email.send()

def admin_requested_tours(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count
    tours = Tour.objects.all()
    tours_list = []
    if tours:
        for tour in tours:
            custom_user = tour.applied_by
            emp_object = None
            reporting_manager = None    
            try:
                emp_object = HeadHr.objects.get(admin=custom_user)
                rm_obj = ReportingManager.objects.get(emp_code=emp_object.emp_code)
                reporting_manager = HeadHr.objects.get(emp_code=rm_obj.rm_code)
            except Exception as e:
                print(f"Error while getting Department: {e}")
                
            try:
                emp_object = Employee.objects.get(admin=custom_user)
                rm_obj = ReportingManager.objects.get(emp_code=emp_object.emp_code)
                reporting_manager = Employee.objects.get(emp_code=rm_obj.rm_code)
            except Exception as e:
                print(f"Error while getting Department: {e}")

            status = ""
            if tour.is_approved:
                status = 'Approved'
            elif tour.is_rejected:
                status = 'Rejected'
            else:
                status = 'Pending'
            tour_dict = {
                'requested_by': f"{tour.applied_by.first_name} {tour.applied_by.last_name}",
                'reporting_manager': reporting_manager,
                'department': emp_object.department,
                'applied_on': tour.applied_on,
                'start_date': tour.start_date,
                'end_date': tour.end_date,
                'reason': tour.message,
                'status': status,
                'is_completed':tour.is_completed,
                'view_url': reverse('admin_view_tour', args=[tour.id]),
                'approve_url': reverse('admin_approve_tour', args=[tour.id]),
                'reject_url': reverse('admin_reject_tour', args=[tour.id]),
            }
            tours_list.append(tour_dict)

    context = {'att':att,'tours': tours_list,'hr_count':total_count, 'shift_count':shift_count,'total_count':total_count}
    
    return render(request, 'headhr/tour_req.html', context=context)

def admin_requested_leaves(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass

    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count
    all_leaves = []
    employee_leaves = AttendanceEmployee.objects.filter(is_leave=True)
    head_leaves = AttendanceHeadHr.objects.filter(is_leave=True)
    all_leaves.extend(employee_leaves)
    all_leaves.extend(head_leaves)
    leaves_list = []
    if all_leaves:
        for leave in all_leaves:
            rm = None
            if leave.marked_by.reporting_manager is not  None:                
                reporting_manager_emp_code = leave.marked_by.reporting_manager.rm_code
                employee_rm = Employee.objects.get(emp_code=reporting_manager_emp_code)
                rm = f"{employee_rm.admin.first_name} {employee_rm.admin.last_name}"
            status = ""
            if leave.is_approved:
                status = 'Approved'
            elif leave.is_rejected:
                status = 'Rejected'
            else:
                status = 'Pending'
            leave_dict = {
                'requested_by': f"{leave.marked_by.admin.first_name} {leave.marked_by.admin.last_name}",
                'reporting_manager': rm ,
                'department': leave.marked_by.department.dept,
                'leave_type': leave.status,
                'applied_on': leave.date,
                'start_date': leave.start_date,
                'end_date': leave.end_date,
                'reason': leave.reason,
                'checks':leave.early_late_checks,
                'status': status,
                'view_url': reverse('admin_reject_leaves', args=[leave.id, leave.marked_by.id]),
                'approve_url': reverse('admin_approve_leaves', args=[leave.id, leave.marked_by.id]),
                'reject_url': reverse('admin_reject_leaves', args=[leave.id, leave.marked_by.id]),
            }
            leaves_list.append(leave_dict)
            print(leaves_list)
    context = {'att':att,'leaves': leaves_list,'hr_count':total_count, 'shift_count':shift_count,'total_count':total_count}
    
    return render(request, 'headhr/leave_req.html', context=context)

def my_attend(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count
    shift_count = ShiftTiming.objects.all().count()
    context = {'att':att,'total_count':total_count,'shift_count':shift_count}
    return render(request, "headhr/my_attend.html", context)



def add_holidays(request):
    head_hr = HeadHr.objects.get(admin=request.user)
    att =None
    try:
        current_date = datetime.now().date()
        att = AttendanceHeadHr.objects.get(marked_by=head_hr,start_date=current_date)
    except:
        pass
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count
    shift_count = ShiftTiming.objects.all().count()
    if request.method == 'POST':
        form = AddHolidaysForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shift_timing')
    else:
        form = AddHolidaysForm()

    return render(request, "headhr/holidays.html", {'total_count':total_count,'att':att,'form': form, 'shift_count':shift_count})

def edit_holidays(request, pk=None):
    shift = None
    if pk:
        shift = get_object_or_404(ShiftTiming, id=pk)
    if request.method == 'POST':
        form = AddHolidaysForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            return redirect('shift_timing')
    else:
        form = AddHolidaysForm(instance=shift)

    return render(request, "headhr/holidays.html", {'form': form})


def delete_holidays(request, pk):
    shift = get_object_or_404(ShiftTiming, id=pk)
    if request.method == 'POST':
        shift.delete()
        return redirect('success_delete')

def add_holidays(request):
    shift_count = ShiftTiming.objects.all().count()
    holidays = Holiday.objects.all()
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        print(f"Forms validation is : {form.is_valid()}")
        if form.is_valid():
            excel_file = request.FILES['file']
            Holiday.objects.all().delete()
            try:
                df = pd.read_excel(excel_file)
                for index, row in df.iterrows():
                    try:
                        date_str = row['Date']
                        print(f"date_str: {date_str}")
                        formatted_start_date = date_str.strftime('%Y-%m-%d')
                        print(f"date_obj: {formatted_start_date}")
                    except ValueError as e:
                        error_message = f"Error converting date: {e}"
                        return render(request, 'headhr/holidays.html', {'form': form, 'shift_count': shift_count, 'error_message': error_message})
                    holiday = Holiday.objects.create(
                        name=row['Holiday Name'],
                        date=formatted_start_date,
                    )
                    holiday.save()
                messages.success(request, "Holidays uploaded successfully")
                return redirect('add_holidays')

            except Exception as e:
                error_message = f"Error: {e}"
                print(error_message)
                messages.error(request, "Error Occurred. Please try again later.")
                form = ExcelUploadForm()
                return render(request, 'headhr/holidays.html', {'form': form, 'shift_count': shift_count})
        else:
            messages.error(request, "Error Occurred. Please try again later.")
            print(form.errors)  # Access form errors without calling it as a function
            return redirect('add_holidays')
      
    else:
        form = ExcelUploadForm()
        
    return render(request, 'headhr/holidays.html', {'form': form, 'shift_count': shift_count,'holidays':holidays})

from datetime import timedelta


def get_events(request):
    calendar_events = []
    custom_user = request.user
    emp = HeadHr.objects.get(admin=custom_user)
    shift = emp.shift
    attendance = AttendanceHeadHr.objects.filter(marked_by=emp)
    holidays = Holiday.objects.all()
    tours = Tour.objects.filter(applied_by=custom_user)
    
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
                    handle_single_record_case_headhr(calendar_events, datetime_obj_checkin,emp.admin)

                elif len(same_date_records) >= 2:
                    datetime_obj_checkout = same_date_records[-1]['date']
                    working_hours = datetime_obj_checkout - datetime_obj_checkin
                    handle_multiple_records_case_headhr(calendar_events, datetime_obj_checkin, shift, working_hours, same_date_records,emp.admin)
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
    reg_list = RegularizationEmp.objects.filter(applied_by =custom_user)
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
                if reg.status == 'Rejected':       
                    event = {
                            'title': "Reg Rejected",
                            'start': reg.start_date,
                            'borderColor': "#a9a9a9",
                            'backgroundColor': "#a9a9a9",
                            'textColor': '#fff',
                        }
                calendar_events.append(event)

 
    return JsonResponse(calendar_events, safe=False)

def get_emp_events(request,role_id,employee_id):
    calendar_events = []
    role_instance = get_role(role_id, employee_id)
    if isinstance(role_instance, HeadHr):
        emp = HeadHr.objects.get(id = employee_id)
    else:
        emp = Employee.objects.get(id=employee_id)
    shift = emp.shift
    attendance = AttendanceEmployee.objects.filter(marked_by=emp)
    holidays = Holiday.objects.all()
    reg_list = RegularizationEmp.objects.filter(applied_by =emp.admin)
    tours = Tour.objects.filter(applied_by=emp.admin)
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
                    handle_single_record_case(calendar_events, datetime_obj_checkin,emp.admin)

                elif len(same_date_records) >= 2:
                    datetime_obj_checkout = same_date_records[-1]['date']
                    working_hours = datetime_obj_checkout - datetime_obj_checkin
                    handle_multiple_records_case(calendar_events, datetime_obj_checkin, shift, working_hours, same_date_records,emp.admin)
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
    if request.method == 'POST':
        form = LeaveHrForm(request.POST)
        if form.is_valid():
            headhr = HeadHr.objects.get(admin=request.user)
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            current_date = datetime.today()
            
            # Calculate formatted dates
            formatted_start_date = start_date.strftime('%Y-%m-%d') if start_date else None
            formatted_end_date = end_date.strftime('%Y-%m-%d') if end_date else None
            formatted_current_date = current_date.strftime('%Y-%m-%d')
            
            # Check the difference between start and end dates
            days = (end_date - start_date).days + 1
            
            leave_type = LeaveType.objects.get(id=form.cleaned_data['leave_type'].id)
            
            if leave_type.leave_type == "EL (Earned Leave)" and days < 4:
                messages.error(request, "The earned leave should be for 4 or more days.")
                return redirect('head_apply_leaves')
            
            if leave_type.leave_type == "CL (Casual Leave)" and (start_date - current_date).days < 3:
                messages.error(request, "You must apply for casual leave at least 3 days in advance.")
                return redirect('head_apply_leaves')
            
            if leave_type.leave_type == "SL (Sick Leave)" and days > 3 and not form.cleaned_data['medical_certificate']:
                messages.error(request, "Medical Certificate required for Sick Leave more than 3 days.")
                return redirect('head_apply_leaves')

            leaves_data = {
                'start_date': formatted_start_date,
                'end_date': formatted_end_date,
                'reason': form.cleaned_data['reason'],
                'status': leave_type.leave_type,
                'is_leave': True,
                'is_approved': False,
                'is_rejected': False,
                'leave_type':leave_type,
                'marked_by': headhr,
                'date': formatted_current_date
            }
            
            try:
                with transaction.atomic():                    
                    AttendanceHeadHr.objects.create(**leaves_data)
                    messages.success(request, "Your leave request has been sent to your manager. Wait for approval. Thanks!!")
                return redirect('head_apply_leaves')
            except Exception as e:
                print("Exception")
                print(e)
                messages.error(request, "Leave application failed")        
                return redirect('head_apply_leaves')
    else:
        form = LeaveHrForm()
    
    return render(request, 'headhr/apply_leaves.html', {'form': form})
def leaves(request):
    custom_user = request.user
    emp = HeadHr.objects.get(admin = custom_user)
    leaves = AttendanceHeadHr.objects.filter(marked_by=emp,is_leave=True)
    context = {'leaves':leaves,'emp':emp}
    return render(request, 'headhr/leaves.html', context=context)

from .forms import ChangeUserPasswordForm
from django.contrib.auth import login,logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required(login_url='/')
def change_password(request):
    if request.method == 'POST':
        form_data = ChangeUserPasswordForm(request.user, request.POST)
        if form_data.is_valid():
            form_data.save()
            logout(request)
            messages.success(request, "Your password was changed successfully. Please Login again to continue...")
            return redirect("show_login")
        else:
            messages.error(request, "Error while changing the password. Please try again")
            return redirect("headhr_change_password")
    
    else:
        form  = ChangeUserPasswordForm(request.user)
        return render(request, 'hearhr/change_password.html', {'form':form})


from datetime import datetime, timedelta, date
from .models import Holiday
from .models import Tour,TourExpense
from .forms import TourForm

def add_tour(request):
    if request.method == 'POST':
        form = TourForm(request.POST)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.applied_by = request.user 
            tour.save()
            messages.success(request, "Your Tour has beent sent for approval to your manager. Wait for approval")
            
            return redirect('head_tours')
        else:
            return redirect('headhr_apply_tour')
    else:
        form = TourForm()
    return render(request, 'headhr/apply_tour.html', {'form': form})

def view_tour(request,tour_id):
    tour_details = Tour.objects.get(id=tour_id,applied_by=request.user)
    tour_expanse = TourExpense.objects.filter(tour=tour_details)
    return render(request, 'headhr/tour_details.html', {'tour_details': tour_details,'tour_expanse':tour_expanse})

from django.http import JsonResponse
from .forms import TourExpenseForm

def edit_tour(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id, applied_by=request.user)

    if request.method == 'POST':
        form = TourForm(request.POST, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, "Tour Updated Successfully!!")
            return redirect('head_tours')
    else:
        form = TourForm(instance=tour)

    return render(request, 'headhr/apply_tour.html', {'form': form, 'tour': tour})

def delete_tour(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id, applied_by=request.user)
    tour.delete()
    messages.error(request, "Tour Deleted Successfully!!")
    return redirect('head_tours')

def mark_complete(request,tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    tour.is_completed = True
    today = datetime.today()
    formatted_tour_date = today.strftime('%Y-%m-%d')
    tour.completion_date = formatted_tour_date
    tour.save()
    return redirect('head_tours')

def tours(request):
    user_tours = Tour.objects.filter(applied_by=request.user)            
    return render(request, 'headhr/tour.html', {'tours': user_tours})   


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
        return redirect('head_tours')
    else:
        messages.error(request, "Error occurred! Try again.")
        return redirect('head_tours')
    
def emp_attendance_list(request):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    total_count = head_hr_count+emp_count
    head_hr_objects = AttendanceHeadHr.objects.filter(is_leave=False)
    employee_objects = AttendanceEmployee.objects.filter(is_leave=False)
    all_hr_objects = list(chain(head_hr_objects, employee_objects))
    shift_count = ShiftTiming.objects.all().count()
    context = {
        'total_count': total_count,
        'shift_count': shift_count,
        'hr_objects': all_hr_objects
    }
    
    return render(request, "headhr/employee_attendance_list.html", context=context)

from django.shortcuts import render, redirect
from .forms import RegularizationForm

def regularization_list(request):    
    regularizations = RegularizationEmp.objects.filter(applied_by = request.user)
    return render(request, 'headhr/regularization_list.html', {'regularizations':regularizations})

def regularization_create(request, start_date=None, end_date =None,working_hrs=None):
    if request.method == 'POST':
        form = RegularizationForm(request.POST)
        if form.is_valid():
            regularization = form.save(commit=False)
            regularization.applied_by = request.user
            start_date = form.cleaned_data['start_date']
            if RegularizationEmp.objects.filter(applied_by=request.user, start_date=start_date).exists():
                messages.error(request, 'You already have applied for the regularization on the selected date')
                return render('headhr_attendance')
            regularization.created_at = datetime.today()
            regularization.count = regularization.count+1
            regularization.hrs_worked = working_hrs
            regularization.save()
            messages.success(request, 'Your Regularization request has been sent to you reporting manager for approval.')
            return redirect('headhr_regularization_list')
    else:
        form = RegularizationForm(start_date=start_date,end_date =end_date)

    return render(request, 'headhr/regularization.html', {'form': form})



def regularization_view(request, pk):
    regularization = get_object_or_404(RegularizationEmp, pk=pk)
    form = RegularizationForm(instance=regularization)
    return render(request, 'headhr/regularization_view.html', {'form': form, 'regularization': regularization})

def regularization_edit(request, pk):
    regularization = get_object_or_404(RegularizationEmp, pk=pk)

    if request.method == 'POST':
        form = RegularizationForm(request.POST, instance=regularization)
        if form.is_valid():
            form.instance.applied_by = request.user
            form.save()
            messages.success(request, 'Regularization Updated Successfully')
            
            return redirect('headhr_regularization_list')
    else:
        form = RegularizationForm(instance=regularization)

    return render(request, 'headhr/regularization.html', {'form': form, 'regularization': regularization})

def regularization_delete(request, pk):
    regularization = get_object_or_404(RegularizationEmp, applied_by=request.user, pk=pk)
    regularization.delete()
    messages.error(request, 'Regularization Deleted Successfully')
    return redirect('headhr_regularization_list')

from django.contrib import messages
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .models import RegularizationEmp
from .forms import AdminRegularizationForm

class HeadRegularizationView(FormView):
    template_name = 'headhr/regularization_form.html'
    form_class = AdminRegularizationForm
    success_url = reverse_lazy('rmhead_requested_regs')

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
        elif action == 'reject':
            regularization_instance.status = "Rejected"
            regularization_instance.admin_comments = form.cleaned_data['admin_comments']
            messages.success(self.request, 'Regularization request rejected successfully.')

        regularization_instance.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error processing the regularization request.')
        return super().form_invalid(form)

def req_regularization(request):
    emp = HeadHr.objects.get(admin=request.user)    
    rms = ReportingManager.objects.filter(rm_code=emp.emp_code)
    emp_codes = [rm.emp_code for rm in rms]
    employees = HeadHr.objects.filter(emp_code__in=emp_codes)
    custom_users = [custom_user.admin for custom_user in employees]
    regs = RegularizationEmp.objects.filter(applied_by__in=custom_users)
    context = {'regularization_list':regs, 'emp': emp}
    return render(request, 'headhr/regularization_req.html',context)


def requested_leaves(request):
    emp = HeadHr.objects.get(admin=request.user)
    rms = ReportingManager.objects.filter(rm_code=emp.emp_code)
    emp_codes = [rm.emp_code for rm in rms]
    leaves = AttendanceHeadHr.objects.filter(marked_by__emp_code__in=emp_codes, is_leave=True)
    context = {'leaves': leaves, 'emp': emp}
    return render(request, 'headhr/leave_req.html', context=context)


def requested_tours(request):
    emp = HeadHr.objects.get(admin=request.user)    
    rms = ReportingManager.objects.filter(rm_code=emp.emp_code)
    emp_codes = [rm.emp_code for rm in rms]
    employees = HeadHr.objects.filter(emp_code__in=emp_codes)
    custom_users = [custom_user.admin for custom_user in employees]
    regs = Tour.objects.filter(applied_by__in=custom_users)
    context = {'tours':regs, 'emp': emp}
    return render(request, 'headhr/tour_req.html',context)

from .forms import UserProfileUpdateForm

import os
from PIL import Image
from django.shortcuts import render, redirect
from .forms import UserProfileUpdateForm

def update_profile(request):
    emp = HeadHr.objects.get(admin=request.user)

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
        
def approves_leaves(request, leave_id, marked_by):
    leave = AttendanceHeadHr.objects.get(id=leave_id)
    leave.is_approved = True
    leave.is_rejected = False
    days = (leave.end_date - leave.start_date).days + 1
    employee = HeadHr.objects.get(id=marked_by)

    overlapping_tour = Tour.objects.filter(
        applied_by=employee.admin,
        start_date__lte=leave.end_date, 
        end_date__gte=leave.start_date,
    ).first()

    if overlapping_tour:
        overlapping_tour.start_date = leave.end_date - timedelta(days=1)
        overlapping_tour.save()

    leave_type = LeaveType.objects.get(leave_type=leave.status)
    leave_balance = HeadHrLeaveBalance.objects.get(employee=employee, leave_type=leave_type)

    if leave_balance.balance > 0:
        leave_balance.balance -= days

    leave_balance.save()
    leave.save()
    messages.success(request, 'Leave Approved')
    return redirect('requested_leaves')

def delete(request,leave_id):
    leave = AttendanceHeadHr.objects.get(id=leave_id)
    leave.delete()
    messages.error(request, 'Leave Cancelled')
    return redirect('emp_leaves')

def cancel_leave(request,leave_id):
   pass

from .forms import LeaveHrForm

def edit_leave(request, leave_id=None):
    emp = HeadHr.objects.get(admin=request.user)
    leave = None
    if leave_id:
        leave = get_object_or_404(AttendanceHeadHr, id=leave_id)
    if request.method == 'POST':
        form = LeaveHrForm(request.POST, instance=leave)
        if form.is_valid():
            form.save()
            return redirect('emp_leaves')
    else:
        form = LeaveHrForm(instance=leave)

    return render(request, "employee/apply_leaves.html", {'form': form,'emp':emp})

def reject_leaves(request, leave_id,marked_by):
    leave = AttendanceHeadHr.objects.get(id=leave_id)
    leave.is_approved = False
    leave.is_rejected = True
    days = ((leave.end_date - leave.start_date).days)+1
    employee= HeadHr.objects.get(id=marked_by)
    leave_type = LeaveType.objects.get(leave_type=leave.status)
    leave_balance = HeadHrLeaveBalance.objects.get(employee=employee,leave_type=leave_type)
    if leave_balance.balance < int(leave_type.days):
        leave_balance.balance =leave_balance.balance + days 
    leave_balance.save()
    leave.save()
    messages.error(request, 'Leave Rejected')
    return redirect('requested_leaves')
