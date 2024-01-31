from django import forms
from .models import ShiftTiming,Role,Gender,MartialStatus,Department,Designation,AttendanceHeadHr,LeaveType
from .models import HeadHr,Employee,Holiday,AttendanceEmployee,ReportingManager
from itertools import chain

class HrForm(forms.ModelForm):
    reporting_manager = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    martial_status = forms.ModelChoiceField(queryset=MartialStatus.objects.all(), 
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    gender = forms.ModelChoiceField(queryset=Gender.objects.all(),
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    role = forms.ModelChoiceField(queryset=Role.objects.all(),
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    designation = forms.ModelChoiceField(queryset=Designation.objects.all(),
                    widget=forms.Select(attrs={'class': ' js-example-data-array select2-hidden-accessible'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control form-control-primary'}
    ))
    shift = forms.ModelChoiceField(queryset=ShiftTiming.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control form-control-primary'}
    ))

    image = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False)
    address_line_1 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'House No/Street'}))
    address_line_2 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control','placeholder':'Landmark'}))
    district = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'},))
    zip_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = HeadHr
        fields = ['anniversary', 'date_of_joining', 'emp_code', 'dob']

        widgets = {
            'emp_code': forms.TextInput(attrs={'class': 'form-control'}),
            'anniversary': forms.TextInput(attrs={'id': 'dropper-animation', 'class': 'form-control'}),
            'dob': forms.TextInput(attrs={'id': 'dropper-default', 'class': 'form-control'}),
            'date_of_joining': forms.TextInput(attrs={'id': 'dropper-max-year', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        head_hr_objects = HeadHr.objects.all()
        # employee_objects = Employee.objects.all()
        reporting_manager_choices = list(chain(head_hr_objects))
        choices = [("", "------")]
        choices.extend([(obj.emp_code, obj.admin.first_name) for obj in reporting_manager_choices])
        
        self.fields['reporting_manager'].choices = choices


class HeadHrForm(forms.ModelForm):
    reporting_manager = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    martial_status = forms.ModelChoiceField(queryset=MartialStatus.objects.all(), 
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    gender = forms.ModelChoiceField(queryset=Gender.objects.all(),
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    role = forms.ModelChoiceField(queryset=Role.objects.filter(id=2),
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    designation = forms.ModelChoiceField(queryset=Designation.objects.all(),
                    widget=forms.Select(attrs={'class': ' js-example-data-array select2-hidden-accessible'}))
    department = forms.ModelChoiceField(queryset=Department.objects.filter(id=4), 
        widget=forms.Select(attrs={'class': 'form-control form-control-primary'}
    ))
    shift = forms.ModelChoiceField(queryset=ShiftTiming.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control form-control-primary'}
    ))

    image = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False)
    address_line_1 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'House No/Street'}))
    address_line_2 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control','placeholder':'Landmark'}))
    district = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'},))
    zip_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = HeadHr
        fields = ['anniversary', 'date_of_joining', 'emp_code', 'dob']

        widgets = {
            'emp_code': forms.TextInput(attrs={'class': 'form-control'}),
            'anniversary': forms.TextInput(attrs={'id': 'dropper-animation', 'class': 'form-control'}),
            'dob': forms.TextInput(attrs={'id': 'dropper-default', 'class': 'form-control'}),
            'date_of_joining': forms.TextInput(attrs={'id': 'dropper-max-year', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        head_hr_objects = HeadHr.objects.all()
        employee_objects = Employee.objects.all()
        reporting_manager_choices = list(chain(head_hr_objects, employee_objects))
        choices = [("", "------")]
        choices.extend([(obj.emp_code, obj.admin.first_name) for obj in reporting_manager_choices])
        
        self.fields['reporting_manager'].choices = choices

class EmployeeForm(forms.ModelForm):
    reporting_manager = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    martial_status = forms.ModelChoiceField(queryset=MartialStatus.objects.all(), 
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    gender = forms.ModelChoiceField(queryset=Gender.objects.all(),
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    role = forms.ModelChoiceField(queryset=Role.objects.filter(id=3),
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    designation = forms.ModelChoiceField(queryset=Designation.objects.all(),
                    widget=forms.Select(attrs={'class': ' js-example-data-array select2-hidden-accessible'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control form-control-primary'}
    ))
    shift = forms.ModelChoiceField(queryset=ShiftTiming.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control form-control-primary'}
    ))

    image = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False)

    address_line_1 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'House No/Street'}))
    address_line_2 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control','placeholder':'Landmark'}))
    district = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'},))
    zip_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = HeadHr
        fields = ['anniversary', 'date_of_joining', 'emp_code', 'dob']

        widgets = {
            'emp_code': forms.TextInput(attrs={'class': 'form-control'}),
            'anniversary': forms.TextInput(attrs={'id': 'dropper-animation', 'class': 'form-control'}),
            'dob': forms.TextInput(attrs={'id': 'dropper-default', 'class': 'form-control'}),
            'date_of_joining': forms.TextInput(attrs={'id': 'dropper-max-year', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # head_hr_objects = HeadHr.objects.all()
        # hr_objects = HeadHr.objects.all()
        employee_objects = Employee.objects.all()
        reporting_manager_choices = list(chain(employee_objects))
        choices = [("", "------")]
        choices.extend([(obj.emp_code, obj.admin.first_name) for obj in reporting_manager_choices])
        
        self.fields['reporting_manager'].choices = choices


class EditHrForm(forms.ModelForm):
    reporting_manager = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    
    martial_status = forms.ModelChoiceField(queryset=MartialStatus.objects.all(), 
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    gender = forms.ModelChoiceField(queryset=Gender.objects.all(),
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    role = forms.ModelChoiceField(queryset=Role.objects.all(),
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    designation = forms.ModelChoiceField(queryset=Designation.objects.all(),
                    widget=forms.Select(attrs={'class': ' js-example-data-array select2-hidden-accessible'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control form-control-primary'}
    ))
    shift = forms.ModelChoiceField(queryset=ShiftTiming.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control form-control-primary'}
    ))

    image = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False)
    address_line_1 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'House No/Street'}))
    address_line_2 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control','placeholder':'Landmark'}))
    district = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control','required':'required'},))
    zip_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = HeadHr
        fields = ['anniversary','image', 'date_of_joining', 'emp_code', 'dob', 'department', 'shift', 'designation', 'phone_number',
                  'martial_status', 'gender', 'admin', 'address']

        widgets = {
            'emp_code': forms.TextInput(attrs={'class': 'form-control'}),
            'anniversary': forms.TextInput(attrs={'id': 'dropper-animation', 'class': 'form-control'}),
            'dob': forms.TextInput(attrs={'id': 'dropper-default', 'class': 'form-control'}),
            'date_of_joining': forms.TextInput(attrs={'id': 'dropper-max-year', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        head_hr_objects = HeadHr.objects.all()
        employee_objects = Employee.objects.all()
        reporting_manager_choices = list(chain(head_hr_objects, employee_objects))
        choices = [("", "------")]
        choices.extend([(obj.emp_code, obj.admin.first_name) for obj in reporting_manager_choices])
        
        self.fields['reporting_manager'].choices = choices
        
        if 'instance' in kwargs:
            instance = kwargs['instance']
            self.fields['admin'].initial = instance.admin if instance.admin else None
            self.fields['address'].initial = instance.address if instance.address else None

            self.fields['role'].initial = instance.admin.user_type
            if (instance and instance.reporting_manager):
                reportin_m = ReportingManager.objects.get(emp_code = instance.reporting_manager.emp_code )      
                self.fields['reporting_manager'].initial = reportin_m.rm_code 
            self.fields['email'] = forms.EmailField(
                label='Email',
                widget=forms.EmailInput(attrs={'class': 'form-control'}),
                initial=instance.admin.email if (instance and instance.admin) else None,
                required=False
            )

            self.fields['first_name'] = forms.CharField(
                label='First Name',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                initial=instance.admin.first_name if (instance and instance.admin) else None,
                required=False
            )

            self.fields['last_name'] = forms.CharField(
                label='Last Name',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                initial=instance.admin.last_name if (instance and instance.admin) else None,
                required=False
            )

            self.fields['address_line_1'] = forms.CharField(
                label='Address Line 1',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                initial=instance.address.address_line_1 if (instance and instance.address) else None,
                required=False
            )
            self.fields['address_line_2'] = forms.CharField(
                label='Address Line 2',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                initial=instance.address.address_line_2 if (instance and instance.address) else None,
                required=False
            )
            self.fields['state'] = forms.CharField(
                label='State',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                initial=instance.address.state if (instance and instance.address) else None,
                required=False
            )
            self.fields['country'] = forms.CharField(
                label='Country',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                initial=instance.address.country if (instance and instance.address) else None,
                required=False
            )
            self.fields['district'] = forms.CharField(
                label='District',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                initial=instance.address.district if (instance and instance.address) else None,
                required=False
            )
            self.fields['zip_code'] = forms.CharField(
                label='Zip Code',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                initial=instance.address.zipcode if (instance and instance.address) else None,
                required=False
            )
        self.fields['admin'].required = False
        self.fields['address'].required = False


class ShiftTimingForm(forms.ModelForm):
    class Meta:
        model = ShiftTiming
        fields = ['start_time', 'end_time', 'grace_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'placeholder': 'Select time', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'placeholder': 'Select time', 'type': 'time'}),
            'grace_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Grace Timing','type': 'number'}),
        }


class LeaveHrForm(forms.ModelForm):
    leave_type = forms.ModelChoiceField(queryset=LeaveType.objects.all(), 
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    medical_certificate = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False)

    half_day = forms.BooleanField(required=False, label='Half Day', widget=forms.CheckboxInput(attrs={'class': 'form-control'}))

    class Meta:
        model = AttendanceHeadHr
        fields = ['start_date', 'end_date', 'reason']

        widgets = {
            'start_date': forms.TextInput(attrs={'id': 'dropper-default', 'class': 'form-control'}),
            'end_date': forms.TextInput(attrs={'id': 'dropper-max-year', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter reason', 'rows': 3}),
        }


class LeaveEmpForm(forms.ModelForm):
    leave_type = forms.ModelChoiceField(queryset=LeaveType.objects.all(), 
                    widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))
    medical_certificate = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False)

    half_day = forms.BooleanField(required=False, label='Half Day', widget=forms.CheckboxInput(attrs={'class': 'form-control'}))

    class Meta:
        model = AttendanceEmployee
        fields = ['start_date', 'end_date', 'reason']

        widgets = {
            'start_date': forms.TextInput(attrs={'id': 'dropper-default', 'class': 'form-control'}),
            'end_date': forms.TextInput(attrs={'id': 'dropper-max-year', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter reason','rows': 3}),
        }


class AddHolidaysForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['name','date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.TextInput(attrs={'id': 'dropper-animation', 'class': 'form-control'}),
        }


class ExcelUploadForm(forms.Form):
    file = forms.FileField()

class DemoForm(forms.Form):
    reporting_manager = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-control form-control-primary'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        head_hr_objects = HeadHr.objects.all()
        hr_objects = HeadHr.objects.all()
        employee_objects = Employee.objects.all()
        reporting_manager_choices = list(chain(head_hr_objects, hr_objects, employee_objects))
        
        choices = [("", "------")]
        choices.extend([(obj.admin.email, obj.admin.first_name) for obj in reporting_manager_choices])
        
        self.fields['reporting_manager'].choices = choices



from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SetPasswordForm(forms.Form):
    """
    A form that lets a user set their password without entering the old
    password
    """

    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
    }
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password",'class': 'form-control form-control-lg'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password",'class': 'form-control form-control-lg'}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        password_validation.validate_password(password2, self.user)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class ChangeUserPasswordForm(SetPasswordForm):
    """
    A form that lets a user change their password by entering their old
    password.
    """

    error_messages = {
        **SetPasswordForm.error_messages,
        "password_incorrect": _(
            "Your old password was entered incorrectly. Please enter it again."
        ),
    }
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True,'class': 'form-control form-control-lg'}
        ),
    )

    field_order = ["old_password", "new_password1", "new_password2"]

    def clean_old_password(self):
        """
        Validate that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise ValidationError(
                self.error_messages["password_incorrect"],
                code="password_incorrect",
            )
        return old_password

from .models import Tour,TourExpense


class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = ['title', 'start_date', 'end_date', 'destination', 'message']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows':3}),
            'start_date': forms.DateInput(attrs={'id': 'dropper-animation', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'id': 'dropper-default', 'class': 'form-control'}),
        }



from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class FileFieldForm(forms.Form):
    file_field = MultipleFileField()



from multiupload.fields import MultiFileField

class TourExpenseForm(forms.ModelForm):
    class Meta:
        model = TourExpense
        fields = ['bill']

class MultiFileForm(forms.Form):
    files = MultiFileField(min_num=1, max_num=20, max_file_size=1024*1024*5)


from .models import RegularizationEmp

class RegularizationForm(forms.ModelForm):
    class Meta:
        model = RegularizationEmp
        fields = ['regularization_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'regularization_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.TextInput(attrs={'id': 'dropper-default', 'class': 'form-control'}),
            'end_date': forms.TextInput(attrs={'id': 'dropper-max-year', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    def __init__(self, *args, **kwargs):
        start_date = kwargs.pop('start_date', None)
        end_date = kwargs.pop('end_date', None)
        super(RegularizationForm, self).__init__(*args, **kwargs)

        if end_date:
            self.fields['end_date'].initial = end_date

        if start_date:
            self.fields['start_date'].initial = start_date


class AdminRegularizationForm(forms.ModelForm):
    class Meta:
        model = RegularizationEmp
        fields = '__all__'
        exclude = ['count']
        widgets = {
            'applied_by': forms.Select(attrs={'class': 'form-control readonly-select'}),
            'regularization_type': forms.Select(attrs={'class': 'form-control readonly-select'}),
            'start_date': forms.TextInput(attrs={'id': 'dropper-default', 'class': 'form-control', 'readonly':'readonly'}),
            'end_date': forms.TextInput(attrs={'id': 'dropper-max-year', 'class': 'form-control', 'readonly':'readonly'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,'readonly':'readonly'}),
            'status': forms.Select(attrs={'class': 'form-control readonly-select'}),
            'admin_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hrs_worked': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'created_at': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }


from .models import HeadHr,Logo  # Import your UserProfile model

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = HeadHr
        fields = ['image']

    def __init__(self, *args, **kwargs):
        super(UserProfileUpdateForm, self).__init__(*args, **kwargs)


class LogoForm(forms.ModelForm):
    class Meta:
        model = Logo
        fields = ['logo_image']

    def __init__(self, *args, **kwargs):
        super(LogoForm, self).__init__(*args, **kwargs)



from django.contrib.auth.forms import PasswordResetForm,SetPasswordForm

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'})
    )
  
class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        help_text="Your password must contain at least 8 characters.",
    )

    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )

