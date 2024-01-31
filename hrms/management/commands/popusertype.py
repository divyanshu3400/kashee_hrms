from django.core.management.base import BaseCommand
from hrms.models import Role,Gender,Designation,Department,MartialStatus

class Command(BaseCommand):
    help = 'Populate UserType data'

    def handle(self, *args, **options):
        roles = ['','HR', 'EMPLOYEE']
        for role in roles:
            Role.objects.get_or_create(role=role)

        genders = ['Male', 'Female','Trans', 'Others']
        for gender in genders:
            Gender.objects.get_or_create(gender=gender)

        designations = [
            'Assistant Manager-F&A',
            'Assistant Manager-F&A',
            'Assistant Manager-PES',
            'Assistant Manager-PIB',
            'Assistant Manager-Purchase',
            'Assistant Manager-Quality',
            'Assistant Manager-Sales',
            'Assistant Store Keeper',
            'Asst- PES',
            'Chemist',
            'Facilitator',
            'Chief Executive',
            'Dy. Manager - Quality',
            'Executive - MCC Incharge (Trainee)',
            'Executive- MCC Incharge',
            'Executive-BMC Incharge',
            'Executive- Logistics',
            'Executive- Logistics (Trainee)',
            'Executive- Sales',
            'Executive-Area Operation',
            'Executive-ERP (IT)',
            'Executive-F&A',
            'Executive-FES',
            'Executive-HR',
            'Executive-HR (Trainee)',
            'Executive-IT',
            'Executive-MIS',
            'Sr. Executive-P.I.B',
            'Executive-P.I.B',
            'Executive-PES',
            'Executive-Quality',
            'Executive-Store Incharge',
            'Head - Field Operations',
            'Head-Cluster Operations',
            'Manager- Finance & Accounts',
            'Manager- HR',
            'Manager-Cluster Operations',
            'Manager-CS & Legal',
            'Manager-Field Operations',
            'Manager-IT & MIS',
            'Manager-Legal & CS',
            'Manager-Quality ',
            ]
        for designation in designations:
            Designation.objects.get_or_create(designation=designation)

        departments = ['IT', 'Finance', 'Sale', 'HR']
        for dept in departments:
            Department.objects.get_or_create(dept=dept)

        marital_status = ['Single', 'Married','Divorced','Widow','Widower']
        for status in  marital_status:
            MartialStatus.objects.get_or_create(marital_status = status)

        self.stdout.write(self.style.SUCCESS('Data populated successfully'))
