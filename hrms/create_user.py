import datetime
from .models import ShiftTiming,MartialStatus,Department,Designation
from .models import ReportingManager,Gender,HeadHr,Employee,CustomUser
import random
import string
from django.contrib.auth.hashers import make_password

def return_address(form):    
    return {
            'address_line_1': form.cleaned_data['address_line_1'],
            'address_line_2': form.cleaned_data['address_line_2'],
            'country': form.cleaned_data['country'],
            'district': form.cleaned_data['district'],
            'state': form.cleaned_data['state'],
            'zipcode': form.cleaned_data['zip_code'],
            }

def get_formatted_password():
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return 'Kashee' + random_suffix

def return_user(form):
        username = form.cleaned_data['first_name'] + str(form.cleaned_data['emp_code'])
        role= form.cleaned_data['role'].id
        user_data = {
                'email': form.cleaned_data['email'],
                'first_name': form.cleaned_data['first_name'],
                'last_name':form.cleaned_data['last_name'],
                'username' : username.lower(),
                'user_type':role

            }
        password = get_formatted_password()
        user = CustomUser.objects.create_user(**user_data)
        hashed_password = make_password(password)
        user.set_password(hashed_password)
        user.save() 
        return user

    
def formatted_joinig_date(obj):
            
    if obj is not None:
        formatted_j_date = obj.strftime('%Y-%m-%d')
    else:
        formatted_j_date = None  
    
    return formatted_j_date

def formatted_ann(obj):
    if obj is not None:
        formatted_ann_date = obj.strftime('%Y-%m-%d')
    else:
        formatted_ann_date = None 
    return formatted_ann_date

def setReportingManager(obj):    
    try:
        rm_ob = HeadHr.objects.get(emp_code=obj)
        rm_ob.is_reporting_manager = True
        rm_ob.save()
    except Exception as e:
        print(f"Error in setting HeadHr as reporting manager: {e}")
    
    try:
        rm_ob = Employee.objects.get(emp_code=obj)
        rm_ob.is_reporting_manager = True
        rm_ob.save()
    except Exception as e:
        print(f"Error in setting Employee as reporting manager: {e}")
    


def create_reporting_manager(reporting_manager_code,emp_code):
    repoting_m = ReportingManager.objects.create(rm_code=reporting_manager_code,emp_code=emp_code)
    repoting_m.save()
    return repoting_m 

def create_role_based_user(user,form,address_instance,reporting_m):
    ann_date = form.cleaned_data['anniversary']
    dob = form.cleaned_data['dob']
    today = datetime.date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    marital_status_instance = MartialStatus.objects.get(id=form.cleaned_data['martial_status'].id)
    dept_instance = Department.objects.get(id=form.cleaned_data['department'].id)
    gend_inst = Gender.objects.get(id=form.cleaned_data['gender'].id)
    shift_inst = ShiftTiming.objects.get(id=form.cleaned_data['shift'].id)
    desig_instance = Designation.objects.get(id=form.cleaned_data['designation'].id)
    date_of_joining = form.cleaned_data['date_of_joining']
    formatted_dob_date = dob.strftime('%Y-%m-%d')
    print(f"Selected Image : {form.cleaned_data['image']}")
    return {'admin': user,'martial_status':marital_status_instance ,
            'anniversary': formatted_ann(ann_date),'designation': desig_instance,'shift':shift_inst,
            'department':dept_instance, 'emp_code': form.cleaned_data['emp_code'],
            'phone_number': form.cleaned_data['phone_number'], 'date_of_joining': formatted_joinig_date(date_of_joining),
            'age':age, 'gender': gend_inst,'is_reporting_manager':False,
            'dob': formatted_dob_date, 'image': form.cleaned_data['image'],
            'reporting_manager':reporting_m,
            'address':address_instance 
        }
