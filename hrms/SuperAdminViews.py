import datetime
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect,get_object_or_404, redirect, render
from django.urls import reverse
from .forms import ShiftTimingForm,AddHolidaysForm, EditHrForm,HeadHrForm,EmployeeForm
from .models import ShiftTiming,CustomUser,Address,MartialStatus,Department,Designation
from .models import ReportingManager,HeadHrLeaveBalance,Gender,LeaveType,AttendanceHeadHr
import random
from django.contrib.auth.hashers import make_password
from django.db import transaction
import string
from kashee import settings 
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.shortcuts import render
from .forms import ExcelUploadForm,LogoForm
from .models import Holiday,HeadHr,HeadHrLeaveBalance,EmpLeaveBalance,Employee
import pandas as pd
import json
from .utility.sending_email import (
    send_leave_status_email,send_regularization_email_ce_approval,send_tour_email_ce_approval
)

from .create_user import (
    return_address,
    setReportingManager,
    create_reporting_manager,
    create_role_based_user,
    formatted_ann)

from .utility.calculation import (
    get_holidays,
    get_start_end_dates,
    calculate_working_days,
    calculate_working_days,handle_multiple_records_case,handle_single_record_case)

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def super_admin_home(request):
    logo = Logo.objects.all().first()
    start_date, end_date = get_start_end_dates()
    holidays = get_holidays()
    leave_dates = []
    total_working_days = calculate_working_days(start_date, end_date, holidays, leave_dates)
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count
    leave_emp = AttendanceEmployee.objects.filter(is_leave=True).count()
    leave_hhr = AttendanceHeadHr.objects.filter(is_leave=True).count()
    total_leave = leave_hhr+leave_emp
    form = LogoForm()
    admin = CustomUser.objects.filter(is_superuser=True)
    for name in admin:
        print(name.username)
        
    print(admin)
    context = {'shift_count':shift_count,'total_count':total_count,
               'total_working_days':total_working_days,'logo':logo,'total_leave': total_leave,'logo_form':form}
    return render(request, "superadmin/home_content.html", context=context)


def super_admin_profile(request):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count  
    context = {'shift_count':shift_count,'total_count':total_count}
    return render(request, "superadmin/profile.html",context=context)


def enroll_head_hr(request):
    message = "Head HR"
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count  
    leave_types = LeaveType.objects.all()
    if request.method == 'POST':
        form = HeadHrForm(request.POST)
        if form.is_valid():           
            emp_code = form.cleaned_data.get('emp_code')
            if not emp_code:
                emp_code = f"{random.randint(100, 999)}"
                form.cleaned_data['emp_code'] = emp_code
            username = form.cleaned_data['first_name'] + str(form.cleaned_data['emp_code'])
            reporting_manager_code =  form.cleaned_data['reporting_manager']
            repoting_m = None
            if reporting_manager_code !="":
                repoting_m = create_reporting_manager(reporting_manager_code, emp_code)
            try:
                with transaction.atomic():
                    if CustomUser.objects.filter(email=form.cleaned_data['email']).exists() or CustomUser.objects.filter(username=username).exists():
                        messages.error(request,"This email / username already taken")
                        return redirect('enroll_hr')
                    if HeadHr.objects.filter(emp_code=form.cleaned_data['emp_code']).exists():
                        messages.error(request,"Sorry! This Emp Code Already Exists. Try again")
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
                    headhr = HeadHr.objects.create(**create_role_based_user(user=user,form=form,address_instance=address_instance,reporting_m=repoting_m))
                    headhr.save()
                    for leave in leave_types:
                        HeadHrLeaveBalance.objects.create(headhr=headhr,leave_type=leave,balance=leave.days).save()
                    if reporting_manager_code:
                        setReportingManager(reporting_manager_code)
                    send_email_confirmation(form.cleaned_data['first_name'], form.cleaned_data['email'], password)
                    messages.success(request, "Head HR registered successfully!!")
                    return HttpResponseRedirect(reverse("admin_hr_list"))
            except Exception as e:
                print("Excecption")
                print(e)
                messages.error(request, "Failed to create the HR")
                if 'address_instance' in locals() and address_instance:
                    address_instance.delete()
                if 'user' in locals() and user:
                    user.delete()
                if 'repoting_m' in locals() and repoting_m:
                    repoting_m.delete()
                return redirect('admin_enroll_head_hr')
        else:
            messages.error(request,"Form is not valid")
            return redirect('admin_enroll_head_hr')
    else:
        form = HeadHrForm()
    return render(request, 'superadmin/enroll_hr.html', {'form': form,'total_count':total_count, 'shift_count':shift_count,'msg':message})



def enroll_employee(request):
    message = "Employee"
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count 
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
                    if Employee.objects.filter(emp_code=form.cleaned_data['emp_code']).exists():
                        messages.error(request,"Sorry! This Emp Code Already Exists. Try again")
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
    return render(request, 'superadmin/enroll_hr.html', {'form': form, 'total_count':total_count,'shift_count':shift_count,'msg':message})

from django.shortcuts import get_object_or_404

def get_role(role_id,hr_id):
    if role_id==2:
        return get_object_or_404(HeadHr, id=hr_id) 
    elif role_id==3:
        return get_object_or_404(Employee, id=hr_id)
    

def edit_hr(request, hr_id,role_id):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count 
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
                        return HttpResponseRedirect(reverse("admin_hr_list"))

                    else:
                        update_employee(form,role_instance)
                        messages.success(request, "Data updated successfully!!")
                        return HttpResponseRedirect(reverse("admin_hr_list"))

            except Exception as e:
                print("Exception")
                print(e)
                messages.error(request, "Failed to update the HR details")
                return redirect('admin_edit_hr', hr_id=hr_id,role_id=role_id)
        else:
            print(form.errors)
            messages.error(request, "Form is not valid")
            return redirect('admin_edit_hr', hr_id=hr_id,role_id=role_id)
    else:
        form = EditHrForm(instance=get_role(role_id=role_id,hr_id=hr_id))
    return render(request, 'superadmin/enroll_hr.html', {'form': form,'total_count':total_count,'shift_count':shift_count ,'msg': message, 'hr': get_role(role_id=role_id,hr_id=hr_id)})

from datetime import datetime, timezone, timedelta

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
    
    reporting_m = None
    try:        
        reporting_m = ReportingManager.objects.get(rm_code = reporting_manager_code ,emp_code = emp_code)
        reporting_m.delete()
    except:
        pass
    if reporting_manager_code !="":
        reporting_m = create_reporting_manager(reporting_manager_code=reporting_manager_code,emp_code=emp_code)
        head_rm = HeadHr.objects.get(emp_code = reporting_m.rm_code)
        head_rm.is_reporting_manager = True


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
    reporting_m = None
    if reporting_manager_code !="":
        try: 
            reporting_m = ReportingManager.objects.get(rm_code = reporting_manager_code ,emp_code = emp_code)
            reporting_m.delete()
        except:
            pass
        reporting_m = create_reporting_manager(reporting_manager_code=reporting_manager_code,emp_code=emp_code)
        employee_rm = Employee.objects.get(emp_code = reporting_m.rm_code)
        employee_rm.is_reporting_manager = True
        

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

def view_attendance(request,hr_id, role_id):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    shift_count = ShiftTiming.objects.all().count()
    total_count = head_hr_count+emp_count 
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
        
    url = reverse('sadmin_ind_emp_events', args=[emp.admin.user_type , emp.id])
        
    return render(request, 'superadmin/emp_atten.html', {'emp':emp,'url':str(url),'remp':remp,'total_count':total_count,'shift_count':shift_count})

def hr_list(request):
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
            rm_emp = Employee.objects.get(emp_code = rmp.rm_code)
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
                'view_url': reverse('admin_view_emp_profile', args=[obj.id, obj.admin.user_type]),
                'delete_url': reverse('admin_delete_hr', args=[obj.id, obj.admin.user_type]),
                'edit_url': reverse('admin_edit_hr', args=[obj.id , obj.admin.user_type]),
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
        if obj.admin.user_type == '2':
            role = "HR"

        employees_dict = {
                'name': f"{obj.admin.first_name} {obj.admin.last_name}",
                'email': obj.admin.email,
                'department': obj.department,
                'age': obj.age,
                'designation': obj.designation,
                'rm':rm_emp,
                'role': role,
                'view_url': reverse('admin_view_emp_profile', args=[obj.id , obj.admin.user_type]),
                'delete_url': reverse('admin_delete_hr', args=[obj.id, obj.admin.user_type]),
                'edit_url': reverse('admin_edit_hr', args=[obj.id , obj.admin.user_type]),
            }
        employees.append(employees_dict)
        
        
    context = {
        'total_count': total_count,
        'shift_count': shift_count,
        'hr_objects': employees,
    }
    return render(request, 'superadmin/hr_list.html', context)

from django.db import transaction
from django.http import Http404

def delete_hr(request, hr_id, role_id):
    try:
        with transaction.atomic():
            role = get_role(hr_id=hr_id, role_id=role_id)
            if isinstance(role, HeadHr):
                leave_balance = HeadHrLeaveBalance.objects.filter(headhr=role)
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
            try:
                reporting_manager = ReportingManager.objects.get(emp_code=role.emp_code)
                reporting_manager.delete()
            except:
                pass
            user = get_object_or_404(CustomUser, id=role.admin.id)
            user.delete()
            
            messages.success(request, "User data has been deleted successfully")
            return redirect('admin_hr_list')

    except Http404:
        raise Http404("Rolling back changes due to an error")

    except Exception as e:
        messages.error(request, f"An error occurred:")
        raise e
    
from .utility.api import call_soap_api,process_attendance_data
attendance_list = call_soap_api()


def get_emp_events(request,role_id,employee_id):
    calendar_events = []
    role_instance = get_role(role_id, employee_id)
    if isinstance(role_instance, HeadHr):
        emp = HeadHr.objects.get(id = employee_id)
        attendance = AttendanceHeadHr.objects.filter(marked_by=emp)
        
    else:
        emp = Employee.objects.get(id=employee_id)
        attendance = AttendanceEmployee.objects.filter(marked_by=emp)
        
    shift = emp.shift
    holidays = Holiday.objects.all()
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
    reg_list = RegularizationEmp.objects.filter(applied_by =emp.admin)
            
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


def shift_timing(request):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    total_count = head_hr_count+emp_count

    shift_timings = ShiftTiming.objects.all()
    shift_count = ShiftTiming.objects.all().count()
    context = {'shift_count':shift_count,'shift_timings': shift_timings,'total_count':total_count}
    return render(request, "superadmin/shift_timing.html", context)


def add_shift_timing(request):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    total_count = head_hr_count+emp_count

    shift_count = ShiftTiming.objects.all().count()
    if request.method == 'POST':
        form = ShiftTimingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_shift_timing')
    else:
        form = ShiftTimingForm()

    return render(request, "superadmin/add_shift_timing.html", {'form': form,'total_count':total_count ,'shift_count':shift_count})

def edit_shift_timing(request, pk=None):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    total_count = head_hr_count+emp_count
    shift = None
    if pk:
        shift = get_object_or_404(ShiftTiming, id=pk)
    if request.method == 'POST':
        form = ShiftTimingForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            return redirect('admin_shift_timing')
    else:
        form = ShiftTimingForm(instance=shift)

    return render(request, "superadmin/add_shift_timing.html", {'form': form,'total_count':total_count})


def delete_shift(request, pk):
    shift = get_object_or_404(ShiftTiming, id=pk)
    if request.method == 'POST':
        shift.delete()
        return redirect('admin_shift_timing')
    
def send_email_confirmation(first_name,email,password):
    logo = Logo.objects.all().first()
    to_email = [email]
    subject = 'Your account has been created at Kashee HRMS.'
    context = {
        'name':first_name,
        'email':email,
        'password':password,
        'logo':logo
    }
    email_html_message = render_to_string('email_templates/login_email_temp.html', context)
    email = EmailMessage(subject, email_html_message, settings.EMAIL_HOST_USER, to_email)
    email.content_subtype = 'html'
    email.send()


def my_attend(request):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    total_count = head_hr_count+emp_count
    shift_count = ShiftTiming.objects.all().count()
    context = {'shift_count':shift_count,'total_count':total_count}
    return render(request, "superadmin/my_attend.html", context)



def edit_holidays(request, holiday_id=None):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    total_count = head_hr_count+emp_count
    shift = None
    if holiday_id:
        shift = get_object_or_404(Holiday, id=holiday_id)
    if request.method == 'POST':
        form = AddHolidaysForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, "Holiday Updated Successfully")
            return redirect('admin_add_holidays')
    else:
        form = AddHolidaysForm(instance=shift)
    return render(request, "superadmin/add_holidays.html", {'form': form,'total_count':total_count})


def delete_holidays(request, pk):
    shift = get_object_or_404(ShiftTiming, id=pk)
    if request.method == 'POST':
        shift.delete()
        return redirect('admin_add_holidays')

from dateutil import parser as date_parser

def add_holidays(request):
    head_hr_count = HeadHr.objects.all().count()
    emp_count = Employee.objects.all().count()
    total_count = head_hr_count+emp_count
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
                        formatted_start_date = date_str.strftime('%Y-%m-%d')
                    except ValueError as e:
                        error_message = f"Error converting date: {e}"
                        return render(request, 'headhr/holidays.html', {'form': form, 'shift_count': shift_count, 'error_message': error_message})
                    holiday = Holiday.objects.create(
                        name=row['Holiday Name'],
                        date=formatted_start_date,
                    )
                    holiday.save()
                messages.success(request, "Holidays uploaded successfully")
                return redirect('admin_add_holidays')

            except Exception as e:
                error_message = f"Error: {e}"
                print(error_message)
                messages.error(request, "Error Occurred. Please try again later.")
                form = ExcelUploadForm()
                return render(request, 'headhr/holidays.html', {'form': form, 'shift_count': shift_count})
        else:
            messages.error(request, "Error Occurred. Please try again later.")
            print(form.errors)  # Access form errors without calling it as a function
            return redirect('admin_add_holidays')
      
    else:
        form = ExcelUploadForm()
        
    return render(request, 'superadmin/holidays.html', {'form': form,'total_count':total_count ,'shift_count': shift_count,'holidays':holidays})


from .models import AttendanceEmployee

def admin_requested_leaves(request):
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
            employee_rm = None
            try:
                reporting_manager_emp_code = leave.marked_by.reporting_manager.rm_code
                employee_rm = Employee.objects.get(emp_code=reporting_manager_emp_code)
            except:
                pass
            status = ""
            if leave.is_approved:
                status = 'Approved'
            elif leave.is_rejected:
                status = 'Rejected'
            else:
                status = 'Pending'
            leave_dict = {
                'requested_by': f"{leave.marked_by.admin.first_name} {leave.marked_by.admin.last_name}",
                'reporting_manager': employee_rm,
                'department': leave.marked_by.department.dept,
                'leave_type': leave.status,
                'applied_on': leave.date,
                'start_date': leave.start_date,
                'end_date': leave.end_date,
                'reason': leave.reason,
                'status': status,
                'checks':leave.early_late_checks,
                'approve_url': reverse('admin_approve_leaves', args=[leave.id, leave.marked_by.id,leave.marked_by.admin.user_type]),
                'reject_url': reverse('admin_reject_leaves', args=[leave.id, leave.marked_by.id,leave.marked_by.admin.user_type]),
            }
            leaves_list.append(leave_dict)
    context = {'leaves': leaves_list,'hr_count':total_count, 'shift_count':shift_count,'total_count':total_count}
    
    return render(request, 'superadmin/leave_req.html', context=context)

from datetime import timedelta

def approves_leaves(request, leave_id, marked_by,role_id):
    role_instance = get_role(role_id,marked_by)
    leave = None
    employee = None
    leave_balance = None
    
    if isinstance(role_instance, HeadHr):
        leave =  AttendanceHeadHr.objects.get(id=leave_id)
        employee = HeadHr.objects.get(id=marked_by)
        leave_balance = HeadHrLeaveBalance.objects.get(employee=employee, leave_type=leave_type)        
        leave.is_approved = True
        leave.is_rejected = False
        days = (leave.end_date - leave.start_date).days + 1
                        
    else:
        leave = AttendanceEmployee.objects.get(id=leave_id)
        employee = Employee.objects.get(id=marked_by)
        leave_balance = EmpLeaveBalance.objects.get(employee=employee, leave_type=leave_type)        
        leave.is_approved = True
        leave.is_rejected = False
        days = (leave.end_date - leave.start_date).days + 1

    overlapping_tour = Tour.objects.filter(
        applied_by=employee.admin,
        start_date__lte=leave.end_date, 
        end_date__gte=leave.start_date,
    ).first()

    if overlapping_tour:
        if leave.start_date < overlapping_tour.start_date:
            print("Leave start date is less than tour start date")
            overlapping_tour.start_date = leave.end_date + timedelta(days=1)
            overlapping_tour.save()
            
            
        else:
            print("Leave dates in between the tour dates")
            overlapping_tour.end_date = leave.start_date - timedelta(days=1)
            overlapping_tour.save()
            

    leave_type = LeaveType.objects.get(leave_type=leave.status)

    if leave_balance.balance > 0:
        leave_balance.balance -= days

    leave_balance.save()
    leave.save()
    messages.success(request, 'Leave Approved')
    
    send_leave_status_email(employee,request.user,leave)
    return redirect('admin_requested_leaves')


def reject_leaves(request, leave_id,marked_by,role_id):
    role_instance = get_role(role_id,marked_by)
    leave = None
    employee = None
    leave_balance = None
    
    if isinstance(role_instance, HeadHr):
        leave =  AttendanceHeadHr.objects.get(id=leave_id)
        employee = HeadHr.objects.get(id=marked_by)
        leave_balance = HeadHrLeaveBalance.objects.get(employee=employee, leave_type=leave_type)        
        leave.is_approved = True
        leave.is_rejected = False
        days = (leave.end_date - leave.start_date).days + 1
                        
    else:
        leave = AttendanceEmployee.objects.get(id=leave_id)
        employee = Employee.objects.get(id=marked_by)
        leave_balance = EmpLeaveBalance.objects.get(employee=employee, leave_type=leave_type)        
        leave.is_approved = True
        leave.is_rejected = False
        days = (leave.end_date - leave.start_date).days + 1

    leave_type = LeaveType.objects.get(leave_type=leave.status)
    if leave_balance.balance < int(leave_type.days):
        leave_balance.balance = leave_balance.balance + days 
    leave_balance.save()
    leave.save()
    messages.error(request, 'Leave Rejected')
    send_leave_status_email(employee,request.user,leave)

    return redirect('admin_requested_leaves')

from .forms import ChangeUserPasswordForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

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
            return redirect("admin_change_password")
    
    else:
        form  = ChangeUserPasswordForm(request.user)
        return render(request, 'superadmin/change_password.html', {'form':form})

from .models import Tour

def admin_requested_tours(request):
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

    context = {'tours': tours_list,'hr_count':total_count, 'shift_count':shift_count,'total_count':total_count}
    
    return render(request, 'superadmin/tour_req.html', context=context)


def approves_tour(request, tour_id):
    tour = Tour.objects.get(id=tour_id)
    tour.is_approved = True
    tour.is_rejected = False
    tour.save()
    send_tour_email_ce_approval(tour,request.user,"approved")
    messages.success(request, 'Tour Approved')
    return redirect('admin_requested_tour')


def reject_tour(request, tour_id):
    tour = Tour.objects.get(id=tour_id)
    tour.is_approved = False
    tour.is_rejected = True
    tour.save()
    send_tour_email_ce_approval(tour,request.user,"rejected")
    messages.error(request, 'Tour Rejected')
    return redirect('admin_requested_tour')


def admin_view_tour(request,tour_id):
    tour_details = get_object_or_404(Tour, id=tour_id)
    emp_object = None
    rm_manager = None
    try:
        emp_object = HeadHr.objects.get(admin=tour_details.applied_by)
        rm_obj = ReportingManager.objects.get(emp_code=emp_object.emp_code)
        rm_manager = HeadHr.objects.get(emp_code=rm_obj.rm_code)
    except Exception as e:
        print(f"Error while getting Department: {e}")
        
    try:
        emp_object = Employee.objects.get(admin=tour_details.applied_by)
        rm_obj = ReportingManager.objects.get(emp_code=emp_object.emp_code)
        rm_manager = Employee.objects.get(emp_code=rm_obj.rm_code)
    except Exception as e:
        print(f"Error while getting Department: {e}")
    return render(request, 'superadmin/tour_details.html', {'tour_details': tour_details,'emp':emp_object,'rm':rm_manager})


from .models import RegularizationEmp

def req_regularization(request):
    regs = RegularizationEmp.objects.all()
    regularization_list = []
    rm = None
    remp = "NA"
    emp = None
    for reg in regs:
        try:   
            emp = Employee.objects.get(admin = reg.applied_by)
            rm = ReportingManager.objects.get(emp_code = emp.emp_code)
            remp = Employee.objects.get(emp_code = rm.rm_code)
        except:
            pass
        
        reg_dict = {
            'reg':reg,
            'emp':emp,
            'remp':remp   
        }
        regularization_list.append(reg_dict)
    return render(request, 'superadmin/regularization_req.html',{'regularization_list':regularization_list})


from django.urls import reverse_lazy
from .forms import AdminRegularizationForm
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, render

class AdminRegularizationView(FormView):
    template_name = 'superadmin/admin_regularization_form.html'
    form_class = AdminRegularizationForm
    success_url = reverse_lazy('admin_requested_regs')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        regularization_id = self.kwargs.get('regularization_id')
        regularization_instance = get_object_or_404(RegularizationEmp, pk=regularization_id)
        kwargs['instance'] = regularization_instance
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        head_hr_count = HeadHr.objects.all().count()
        emp_count = Employee.objects.all().count()
        shift_count = ShiftTiming.objects.all().count()
        context['shift_count'] = shift_count
        context['total_count'] = emp_count+ head_hr_count
        return context

    def form_valid(self, form):
        action = self.request.POST.get('action')
        regularization_instance = form.save(commit=False)

        if action == 'approve':
            regularization_instance.status = "Approved"
            regularization_instance.admin_comments = form.cleaned_data['admin_comments']
            
            send_regularization_email_ce_approval(regularization_instance,self.request.user)
            messages.success(self.request, 'Regularization request approved successfully.')
        elif action == 'reject':
            regularization_instance.status = "Rejected"
            send_regularization_email_ce_approval(regularization_instance,self.request.user)
            regularization_instance.admin_comments = form.cleaned_data['admin_comments']
            messages.error(self.request, 'Regularization request rejected successfully.')

        regularization_instance.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error processing the regularization request.')
        return super().form_invalid(form)


def send_status_email(first_name,email,password):
    to_email = [email]
    subject = 'Account Create At Kashee HRMS Credential'
    context = {
        'name':first_name,
        'email':email,
        'password':password
    }
    email_html_message = render_to_string('email_templates/login_email_temp.html', context)
    email = EmailMessage(subject, email_html_message, settings.EMAIL_HOST_USER, to_email)
    email.content_subtype = 'html'
    email.send()

import os
from PIL import Image
from django.shortcuts import render, redirect
from .forms import Logo

def update_logo(request):
    logo = Logo.objects.all().first()
    if request.method == 'POST':
        form = LogoForm(request.POST, request.FILES)
        
        if form.is_valid():
            if logo is not None:               
                if logo.logo_image:
                    old_image_path = logo.logo_image.path
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                        logo.logo_image= None

                logo.logo_image = form.cleaned_data['logo_image']
                logo.save()
                img = Image.open(logo.logo_image.path)

                if img.width != 50 or img.height != 50:
                    img = img.resize((50, 50), resample=Image.BICUBIC)
                    img.save(logo.logo_image.path)

                logo.save()
            else:
                logo = Logo.objects.create()                 
                logo.logo_image = form.cleaned_data['logo_image']
                logo.save()
                img = Image.open(logo.logo_image.path)

                if img.width != 50 or img.height != 50:
                    img = img.resize((50, 50), resample=Image.BICUBIC)
                    img.save(logo.logo_image.path)
                logo.save()
        return redirect('super_admin_home')
    

def create_admin(request):
    pass