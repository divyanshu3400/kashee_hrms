from django.core.management.base import BaseCommand
from hrms.models import LeaveType

class Command(BaseCommand):
    help = 'Populate LeaveType model with initial data'

    def handle(self, *args, **kwargs):
        # Clear existing data (optional, use if needed)
        LeaveType.objects.all().delete()

        leave_types = [
            
            {'leave_type': 'SL (Sick Leave)', 'days': '10'},
            {'leave_type': 'EL (Earned Leave)', 'days': '30'},
            {'leave_type': 'CL (Casual Leave)', 'days': '10'},
        ]

        for leave_type_data in leave_types:
            LeaveType.objects.create(**leave_type_data)

        self.stdout.write(self.style.SUCCESS('Leave types created successfully'))
