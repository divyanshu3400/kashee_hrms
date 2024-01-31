from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    role = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.role}"

class ShiftTiming(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_time = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"
    
    class Meta:
        db_table = 'tbl_shift_timing'
        managed = True
        verbose_name = 'ShiftTiming'
        verbose_name_plural = 'ShiftTimings'    

class Logo(models.Model):
    logo = models.CharField(max_length=100)
    logo_image = models.ImageField(upload_to='logos/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.logo} - {self.logo_image}"
    
    class Meta:
        db_table = 'tbl_logo'
        managed = True
        verbose_name = 'Logo'
        verbose_name_plural = 'Logos'    

class Designation(models.Model):
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.designation}"

class Gender(models.Model):
    gender = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.gender}"

class MartialStatus(models.Model):
    marital_status = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.marital_status}"


class Address(models.Model):
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=10)
    def __str__(self):
        return f"{self.address_line_1}, {self.state}, {self.zipcode}"


class Department(models.Model):
    dept = models.CharField(max_length=100)
    class Meta:
        db_table = 'tbl_department'
        managed = True
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return self.dept


class CustomUser(AbstractUser):
    is_password_changed = models.BooleanField(default=False)
    user_type_data=((1,"SuperAdmin"),(2,"HeadHr"),(3,"Employee"))
    user_type=models.CharField(default=1,choices=user_type_data,max_length=10)

    class Meta:
        db_table = 'tbl_user'
        managed = True
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class ReportingManager(models.Model):
    rm_code = models.CharField(max_length=100, default="")
    emp_code = models.CharField(max_length= 100, default="")

    class Meta:
        db_table = 'tbl_reporting_m'
        managed = True
        verbose_name = 'ReportingManager'
        verbose_name_plural = 'ReportingManagers'
        
    def __str__(self):
        return f"{self.rm_code}"

class BaseModel(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, blank=True, null=True)
    shift = models.ForeignKey(ShiftTiming, on_delete=models.CASCADE, blank=True, null=True)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, blank=True, null=True)
    martial_status = models.ForeignKey(MartialStatus, on_delete=models.CASCADE, blank=True, null=True)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, blank=True, null=True)
    anniversary = models.DateField(blank=True, null=True)
    date_of_joining = models.DateField(blank=True, null=True)
    emp_code = models.CharField(max_length=20, blank=True, null=True)
    is_reporting_manager = models.BooleanField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='profile_pic/', blank=True, null=True)
    objects = models.Manager()
    created_at = models.DateTimeField(auto_now_add=True)
    age = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class HeadHr(BaseModel):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, blank=True, null=True)
    reporting_manager = models.OneToOneField(ReportingManager, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.admin.first_name}-{self.admin.last_name}"

class Employee(BaseModel):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, blank=True, null=True)
    reporting_manager = models.OneToOneField(ReportingManager, null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return f"{self.admin.first_name}-{self.admin.last_name}"
    
    class Meta:
        db_table = 'tbl_employee'
        managed = True
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'



class LeaveType(models.Model):
    leave_type = models.CharField(max_length=100, unique=True)
    days = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.leave_type
    
    class Meta:
        db_table = 'tbl_leave_type'
        managed = True
        verbose_name = 'LeaveType'
        verbose_name_plural = 'LeaveTypes'

class BaseAttendance(models.Model):
    check_in = models.FloatField(default=0)
    check_out = models.FloatField(default=0) 
    is_leave = models.BooleanField()
    date = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    latitude = models.FloatField(default=0)
    ip = models.CharField(max_length=200, default="")
    longitude = models.FloatField(default=0)
    is_approved= models.BooleanField(blank=True, null=True)
    is_rejected= models.BooleanField(blank=True, null=True)
    reason = models.TextField(blank=True)
    attend_image = models.ImageField(upload_to='attend_img/', blank=True, null=True)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, blank=True, null=True)
    early_late_checks = models.CharField(max_length=100,default="NA",blank=True,null=True)
    hrs_worked = models.CharField(max_length=200,default="NA",blank=True,null=True)
    regularisation_count = models.IntegerField(default=0,blank=True,null=True)
    status = models.CharField(max_length=20)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.status}-({self.early_late_checks})"


class AttendanceEmployee(BaseAttendance):
    marked_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='marked_attendance_by')

    class Meta:
        db_table = 'tbl_attendance_employee'
        managed = True
        verbose_name = 'AttendanceEmployee'
        verbose_name_plural = 'AttendanceEmployees'
        
    def get_employee(self):
        return self.marked_by



class AttendanceHeadHr(BaseAttendance):
    marked_by = models.ForeignKey(HeadHr, on_delete=models.SET_NULL, null=True, related_name='marked_attendance_by')
    class Meta:
        db_table = 'tbl_attendance_headhr'
        managed = True
        verbose_name = 'AttendanceHr'
        verbose_name_plural = 'AttendanceHr'
        
    def get_employee(self):
        return self.marked_by



class BaseLeaveBalance(models.Model):
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    balance = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.get_employee()} - {self.leave_type}: {self.balance}"

    def get_employee(self):
        raise NotImplementedError("Subclasses of BaseLeaveBalance must implement get_employee method.")


class EmpLeaveBalance(BaseLeaveBalance):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tbl_employee_leave_balance'
        managed = True
        verbose_name = 'EmpLeaveBalance'
        verbose_name_plural = 'EmpLeaveBalances'

    def get_employee(self):
        return self.employee


class HeadHrLeaveBalance(BaseLeaveBalance):
    headhr = models.ForeignKey(HeadHr, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tbl_head_hr_leave_balance'
        managed = True
        verbose_name = 'HeadHrLeaveBalance'
        verbose_name_plural = 'HeadHrLeaveBalances'

    def get_employee(self):
        return self.headhr


class RegularizationEmp(models.Model):
    
    REGULARIZATION_TYPES = [
        ('Late Coming', 'Late Coming'),
        ('Early Going', 'Early Going'),
        ('Mis Punching', 'Mis Punching'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    applied_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='regularizations')
    regularization_type = models.CharField(max_length=20, choices=REGULARIZATION_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    hrs_worked = models.CharField(max_length=10, default='0')
    count = models.BigIntegerField(default=0, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    admin_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.applied_by.username} - {self.regularization_type} - {self.status}"
    
    def get_employee(self):
        return self.applied_by
    

class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()

    def __str__(self):
        return f"{self.name} - {self.date}"
    
from django.utils import timezone

class Tour(models.Model):
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    destination = models.CharField(max_length=200,default="")
    message = models.TextField(default="")
    applied_on = models.DateField(default=timezone.now)
    applied_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False, blank=True, null=True)
    is_rejected = models.BooleanField(default=False, blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'tbl_users_tour'
        managed = True
        verbose_name = 'UserTour'
        verbose_name_plural = 'UserTours'

    def __str__(self):
        return f"{self.applied_by.first_name} | {self.title}"


class TourExpense(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    bill = models.FileField(upload_to='expense_bills/')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'tbl_tour_expanse'
        verbose_name = 'Tour Expense'
        verbose_name_plural = 'Tour Expenses'

    def __str__(self):
        return f"{self.tour.title} - {self.expense_date}"