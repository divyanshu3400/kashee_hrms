from django.shortcuts import render
import requests
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from itertools import chain
from hrms.EmailBackEnd import EmailBackEnd
from hrms.models import *
from datetime import datetime
from .models import ShiftTiming



def ShowLoginPage(request):
    return render(request,"registration/auth_login.html")

from django.contrib.auth.decorators import login_required
from .forms import ChangeUserPasswordForm

@login_required(login_url='/')
def change_password(request):
    if request.method == 'POST':
        form_data = ChangeUserPasswordForm(request.user, request.POST)
        if form_data.is_valid():
            custom_user = request.user
            custom_user.is_password_changed = True
            custom_user.save()
            form_data.save()
            logout(request)
            messages.success(request, "Your password was changed successfully. Please Login again to continue...")
            return redirect("show_login")
        else:
            messages.error(request, "Error while changing the password. Please try again")
            return redirect("change_password")    
    else:
        form  = ChangeUserPasswordForm(request.user)
        return render(request, 'registration/change_password.html', {'form':form})


def doLogin(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        # captcha_token=request.POST.get("g-recaptcha-response")
        # cap_url="https://www.google.com/recaptcha/api/siteverify"
        # cap_secret="6LfqmUcpAAAAAAVEYe58RikxdtmGbUa4rF_fkoHm"
        # cap_data={"secret":cap_secret,"response":captcha_token}
        # cap_server_response=requests.post(url=cap_url,data=cap_data)
        # cap_json=json.loads(cap_server_response.text)

        # if cap_json['success']==False:
        #     messages.error(request,"Invalid Captcha Try Again")
        #     return HttpResponseRedirect("/")
        user = EmailBackEnd.authenticate(
        request,
        username=request.POST.get("email").strip(),
        password=request.POST.get("password").strip()
    )
        if user!=None:
            login(request,user)
            if user.user_type=="2":
                messages.success(request, f"Welcome! {user} Logged In Successfully.")
                if not request.user.is_password_changed:
                    return redirect('change_password')
                    
                return redirect('hrhead_home')
            elif user.user_type=="1":
                if not request.user.is_password_changed:
                    return redirect('change_password')

                messages.success(request, f"Welcome! {user} Logged In Successfully.")
                return redirect(reverse("super_admin_home"))
            elif user.user_type=="3":
                if not request.user.is_password_changed:
                    return redirect('change_password')

                messages.success(request, f"Welcome! {user} Logged In Successfully.")
                return redirect(reverse("employee_home"))            
         
        else:
            messages.error(request,"Invalid Login Details")
            return HttpResponseRedirect("/")


def GetUserDetails(request):
    if request.user!=None:
        return HttpResponse("User : "+request.user.email+" usertype : "+str(request.user.user_type))
    else:
        return HttpResponse("Please Login First")

def forgot_password(request):
    return render(request,"registration/auth_reset_pass.html")

def logout_user(request):
    logout(request)
    messages.success(request, "Logged Out Successfully")
    return redirect("show_login")

def showFirebaseJS(request):
    data='importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-app.js");' \
         'importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-messaging.js"); ' \
         'var firebaseConfig = {' \
         '        apiKey: "YOUR_API_KEY",' \
         '        authDomain: "FIREBASE_AUTH_URL",' \
         '        databaseURL: "FIREBASE_DATABASE_URL",' \
         '        projectId: "FIREBASE_PROJECT_ID",' \
         '        storageBucket: "FIREBASE_STORAGE_BUCKET_URL",' \
         '        messagingSenderId: "FIREBASE_SENDER_ID",' \
         '        appId: "FIREBASE_APP_ID",' \
         '        measurementId: "FIREBASE_MEASUREMENT_ID"' \
         ' };' \
         'firebase.initializeApp(firebaseConfig);' \
         'const messaging=firebase.messaging();' \
         'messaging.setBackgroundMessageHandler(function (payload) {' \
         '    console.log(payload);' \
         '    const notification=JSON.parse(payload);' \
         '    const notificationOption={' \
         '        body:notification.body,' \
         '        icon:notification.icon' \
         '    };' \
         '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
         '});'

    return HttpResponse(data,content_type="text/javascript")


def get_users_transactions_logs(request):
    soap_api_url = 'http://10.10.10.63/iclock/WebAPIService.asmx'
    soap_request_payload = '''
    <?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <GetTransactionsLog xmlns="http://tempuri.org/">
          <FromDateTime>2023/05/22</FromDateTime>
          <ToDateTime>2023/12/27</ToDateTime>
          <SerialNumber>CEXJ222261829</SerialNumber>
          <UserName>esslapi</UserName>
          <UserPassword>Api@12345</UserPassword>
          <strDataList></strDataList>
        </GetTransactionsLog>
      </soap:Body>
    </soap:Envelope>
    '''
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': '"http://tempuri.org/GetTransactionsLog"'
    }

    response = requests.post(soap_api_url, data=soap_request_payload, headers=headers)

    return HttpResponse(response.content, content_type='text/xml')


def loader(request):
    return render(request, "loader.html")

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def home(request):
    return render(request, 'index.html')


def notification_test_page(request):
    current_user = request.user
    channel_layer = get_channel_layer()
    data = "notification"+ "...." + str(datetime.now())
    print(f'user-{current_user.id}')
    async_to_sync(channel_layer.group_send)(str(current_user.id),
        {
            "type": "notify",
            "text": data,
            'rejected_by': request.user
        },
    )
    return render(request, 'notify.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth import login
from django.http import HttpResponseRedirect

from .forms import CustomPasswordResetForm,CustomSetPasswordForm
# Custom Password Reset View
class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/auth_reset_pass.html'
    email_template_name = 'registration/reset_pass.txt'
    success_url = reverse_lazy('password_reset_done')
    form_class = CustomPasswordResetForm

class CustomPasswordResetDoneView(TemplateView):
    template_name = 'registration/password_reset_done.html'

# Password Reset Confirm View
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'  # Customize this template
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('password_reset_complete')  # URL to redirect to after the password is successfully reset

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your password has been successfully reset.')
        return response

# Password Reset Complete View
class CustomPasswordResetCompleteView(TemplateView):
    template_name = 'registration/password_reset_complete.html'  # Customize this template

def redirect_to_login(request):
    return HttpResponseRedirect(reverse_lazy('show_login'))
