from kashee import settings 
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from hrms.models import HeadHr, EmpLeaveBalance, Employee, CustomUser, ReportingManager

def send_emp_leave_email(employee, leave):
    try:
        reporting_m = ReportingManager.objects.get(emp_code=employee.emp_code)
        remp_obj = Employee.objects.get(emp_code=reporting_m.rm_code)
    except (ReportingManager.DoesNotExist, Employee.DoesNotExist):
       pass

    admin = CustomUser.objects.filter(is_superuser=True).first()
    hr = HeadHr.objects.all()

    cc_email_list = []

    if hr:
        for h in hr:
            cc_email_list.append(h.admin.email)
    
    if admin:
        cc_email_list.append(admin.email)
    
    sl = EmpLeaveBalance.objects.get(employee=employee,leave_type=1)
    el = EmpLeaveBalance.objects.get(employee=employee,leave_type=2)
    cl = EmpLeaveBalance.objects.get(employee=employee,leave_type=3)
    subject = 'Leave Application'
    context = {
        'subject': subject,
        'emp': employee,
        'leave': leave,
        'cl':cl,
        'sl':sl,
        'el':el,
        'mngr':remp_obj,
    }
    
    email_html_message = render_to_string('email_templates/leave_application.txt', context)
    
    email = EmailMessage(
        subject,
        email_html_message,
        settings.EMAIL_HOST_USER,
        [remp_obj.admin.email,employee.admin.email], 
        cc=cc_email_list,
    )
    email.send()

def send_leave_status_email(emp,approver,leave):
    admin = CustomUser.objects.filter(is_superuser=True)
    hr = HeadHr.objects.all()

    cc_email_list = []
    try:
        reporting_m = ReportingManager.objects.get(emp_code=emp.emp_code)
        remp_obj = Employee.objects.get(emp_code=reporting_m.rm_code)
    except (ReportingManager.DoesNotExist, Employee.DoesNotExist):
       pass

    if hr:
        for h in hr:
            cc_email_list.append(h.admin.email)
    
    if admin:
        for ad in admin:
            cc_email_list.append(ad.email)

    subject = 'Leave Application'
    status = ""
    if leave.is_approved:
        status = "Approved"
    if leave.is_rejected:
        status = "Not Approved"
        
    sl = EmpLeaveBalance.objects.get(employee=emp,leave_type=1)
    el = EmpLeaveBalance.objects.get(employee=emp,leave_type=2)
    cl = EmpLeaveBalance.objects.get(employee=emp,leave_type=3)
    subject = 'Leave Application'
    context = {
        'subject': subject,
        'emp': emp,
        'leave': leave,
        'cl':cl,
        'sl':sl,
        'el':el,
        'mngr':remp_obj,
        'amngr':approver,
        'status':status
        
    }
  
   
    email_html_message = render_to_string('email_templates/leave_application.txt', context)
    
    email = EmailMessage(
        subject,
        email_html_message,
        settings.EMAIL_HOST_USER,
        [emp.admin.email], 
        cc=cc_email_list,
    )
    # email.content_subtype = 'html'
    
    email.send()

def send_regularization_email(emp,reg):
    admin = CustomUser.objects.filter(is_superuser=True)
    hr = HeadHr.objects.all()
    
    cc_email_list = []
    try:
        reporting_m = ReportingManager.objects.get(emp_code=emp.emp_code)
        remp_obj = Employee.objects.get(emp_code=reporting_m.rm_code)
    except (ReportingManager.DoesNotExist, Employee.DoesNotExist):
       pass

    if hr:
        for h in hr:
            cc_email_list.append(h.admin.email)
    
    if admin:
        for ad in admin:
            cc_email_list.append(ad.email)

    subject = 'Regularization Request Application'
    flag = ""
    if reg.regularization_type =="Late Coming":
        flag = "came at"
    elif reg.regularization_type =="Early Going":
        flag = 'went at'
    else:
        flag = 'mispunched'
    context = {
        'subject': subject,
        'emp': emp,
        'reg': reg,
        'mngr':remp_obj,
        'flag':flag,
    }
   
    email_html_message = render_to_string('email_templates/regularization_mail.txt', context)
    
    email = EmailMessage(
        subject,
        email_html_message,
        settings.EMAIL_HOST_USER,
        [emp.admin.email], 
        cc=cc_email_list,
    )
    # email.content_subtype = 'html'
    
    email.send()

def send_regularization_email_mngr_approval(emp,approver,reg):
    admin = CustomUser.objects.filter(is_superuser=True)
    hr = HeadHr.objects.all()

    cc_email_list = []
    try:
        reporting_m = ReportingManager.objects.get(emp_code=emp.emp_code)
        remp_obj = Employee.objects.get(emp_code=reporting_m.rm_code)
    except (ReportingManager.DoesNotExist, Employee.DoesNotExist):
       pass

    if hr:
        for h in hr:
            cc_email_list.append(h.admin.email)
    
    if admin:
        for ad in admin:
            cc_email_list.append(ad.email)

    subject = 'Regularization approval for {{reg.start_date}}'

    context = {
        'subject': subject,
        'emp': emp,
        'reg': reg,
        'mngr':remp_obj,
        'amngr':approver,        
    }
   
    email_html_message = render_to_string('email_templates/leave_application.txt', context)
    
    email = EmailMessage(
        subject,
        email_html_message,
        settings.EMAIL_HOST_USER,
        [emp.admin.email], 
        cc=cc_email_list,
    )
    # email.content_subtype = 'html'
    
    email.send()

def send_regularization_email_ce_approval(reg,approver):
    admin = CustomUser.objects.filter(is_superuser=True)
    hr = HeadHr.objects.all()
    emp = None
    if reg.applied_by.user_type == 2:
        emp = HeadHr.objects.get(admin=reg.applied_by)
    else:
        emp = Employee.objects.get(admin=reg.applied_by)        
    cc_email_list = []
    try:
        reporting_m = ReportingManager.objects.get(emp_code=emp.emp_code)
        remp_obj = Employee.objects.get(emp_code=reporting_m.rm_code)
    except (ReportingManager.DoesNotExist, Employee.DoesNotExist):
       pass
   
    if hr:
        for h in hr:
            cc_email_list.append(h.admin.email)
    
    if admin:
        for ad in admin:
            cc_email_list.append(ad.email)

    subject = 'Regularization approval for {{reg.start_date}}'
    context = {'subject': subject,'emp': emp,'reg': reg,'mngr':remp_obj,'ce':approver,}    
    email_html_message = render_to_string('email_templates/leave_application.txt', context)
    email = EmailMessage(subject,email_html_message,settings.EMAIL_HOST_USER,[emp.admin.email], cc=cc_email_list)
    email.content_subtype = 'html'
    email.send()
    
    
def send_emp_tour_email(employee, tour):
    try:
        reporting_m = ReportingManager.objects.get(emp_code=employee.emp_code)
        remp_obj = Employee.objects.get(emp_code=reporting_m.rm_code)
    except (ReportingManager.DoesNotExist, Employee.DoesNotExist):
       pass

    admin = CustomUser.objects.filter(is_superuser=True).first()
    hr = HeadHr.objects.all()

    cc_email_list = []

    if hr:
        for h in hr:
            cc_email_list.append(h.admin.email)
    
    if admin:
        cc_email_list.append(admin.email)
        
    subject = 'Leave Application'
    context = {
        'subject': subject,
        'emp': employee,
        'tour': tour,
        'mngr':remp_obj,
    }
    
    email_html_message = render_to_string('email_templates/tour_application_mail.txt', context)
    
    email = EmailMessage(
        subject,
        email_html_message,
        settings.EMAIL_HOST_USER,
        [remp_obj.admin.email,employee.admin.email], 
        cc=cc_email_list,
    )
    email.send()


def send_tour_email_mngr_approval(emp,approver,tour,status):
    admin = CustomUser.objects.filter(is_superuser=True)
    hr = HeadHr.objects.all()

    cc_email_list = []
    try:
        reporting_m = ReportingManager.objects.get(emp_code=emp.emp_code)
        remp_obj = Employee.objects.get(emp_code=reporting_m.rm_code)
    except (ReportingManager.DoesNotExist, Employee.DoesNotExist):
       pass

    if hr:
        for h in hr:
            cc_email_list.append(h.admin.email)
    
    if admin:
        for ad in admin:
            cc_email_list.append(ad.email)

    subject = f'Tour approval for {{destination}}'

    subject = 'Leave Application'
    context = {
        'subject': subject,
        'emp': emp,
        'tour': tour,
        'amngr':approver,
        'status':status,        
    }
   
    email_html_message = render_to_string('email_templates/tour_approval.txt', context)
    
    email = EmailMessage(
        subject,
        email_html_message,
        settings.EMAIL_HOST_USER,
        [emp.admin.email], 
        cc=cc_email_list,
    )
    
    email.send()

def send_tour_email_ce_approval(tour,approver,status):
    admin = CustomUser.objects.filter(is_superuser=True)
    hr = HeadHr.objects.all()
    emp = None
    if tour.applied_by.user_type == 2:
        emp = HeadHr.objects.get(admin=tour.applied_by)
    else:
        emp = Employee.objects.get(admin=tour.applied_by)        
    cc_email_list = []
    try:
        reporting_m = ReportingManager.objects.get(emp_code=emp.emp_code)
        remp_obj = Employee.objects.get(emp_code=reporting_m.rm_code)
    except (ReportingManager.DoesNotExist, Employee.DoesNotExist):
       pass
   
    if hr:
        for h in hr:
            cc_email_list.append(h.admin.email)
    
    if admin:
        for ad in admin:
            cc_email_list.append(ad.email)

    subject = f'Tour approval for {{destination}}'
    context = {'subject': subject,'emp': emp,'tour': tour,'status':status,'mngr':remp_obj,'ce':approver,}    
    email_html_message = render_to_string('email_templates/leave_application.txt', context)
    email = EmailMessage(subject,email_html_message,settings.EMAIL_HOST_USER,[emp.admin.email], cc=cc_email_list)
    email.content_subtype = 'html'
    email.send()
    