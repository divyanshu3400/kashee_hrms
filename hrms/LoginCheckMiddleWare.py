from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class LoginCheckMiddleWare(MiddlewareMixin):
    def process_view(self,request,view_func,view_args,view_kwargs):
        modulename=view_func.__module__
        user=request.user
        if user.is_authenticated:
            if user.user_type == "2":
                if modulename == "hrms.HeadHrViews":
                    pass
                elif modulename == "hrms.views" or modulename == "django.views.static":
                    pass
                elif modulename == "django.contrib.auth.views" or modulename =="django.contrib.admin.sites":
                    pass
                else:
                    return HttpResponseRedirect(reverse("head_mark_attendance"))
                
            elif user.user_type == "3":
                if modulename == "hrms.EmployeeViews" or modulename == "django.views.static":
                    pass
                elif modulename == "hrms.views":
                    pass
                else:
                    return HttpResponseRedirect(reverse("employee_home"))
                
            elif user.user_type == "1":
                if modulename == "hrms.SuperAdminViews" or modulename == "django.views.static":
                    pass
                elif modulename == "hrms.views":
                    pass
                else:
                    return HttpResponseRedirect(reverse("super_admin_home"))


            else:
                return HttpResponseRedirect(reverse("show_login"))

        else:
            if request.path == reverse("show_login") or request.path == reverse("do_login") or modulename == "django.contrib.auth.views" or modulename =="django.contrib.admin.sites" or modulename=="hrms.views":
                pass
            else:
                return HttpResponseRedirect(reverse("show_login"))