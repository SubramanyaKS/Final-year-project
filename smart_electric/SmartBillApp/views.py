from django.shortcuts import render
from django.shortcuts import  render, redirect
from SmartBillApp.forms import NewUserForm
from django.contrib.auth import login
from django.contrib import messages
# Create your views here.
def home(request):
    return render(request,"index.html")

def login(request):
    return render(request,"login.html")

def main(request):
    return render(request,"main.html")
def contact(request):
    return render(request,"contact.html")

def register_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Registration successful." )
			return redirect("main.html")
		messages.error(request, "Unsuccessful registration. Invalid information.")
	form = NewUserForm()
	return render (request=request, template_name="register.html", context={"register_form":form})