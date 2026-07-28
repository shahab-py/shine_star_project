from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_verified = True
            user.save()
            login(request, user)
            messages.success(request, "ثبت‌نام با موفقیت انجام شد!")
            return redirect('shop:home')
        else:
            messages.error(request, "خطا در ثبت‌نام. لطفاً فرم را چک کنید.")
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "پروفایل با موفقیت بروزرسانی شد.")
            return redirect('profile')
        else:
            messages.error(request, "خطا در ذخیره اطلاعات.")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})
