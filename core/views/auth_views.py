from django.shortcuts import render, redirect
from django.contrib import messages
from ..forms import SignUpForm, SignInForm
from ..models import User
from ..decorators import login_required


def landing(request):
    if request.session.get('user_id'):
        return redirect('section_list')
    return render(request, 'landing.html')


def signup(request):
    if request.session.get('user_id'):
        user_id = request.session['user_id']
        try:
            u = User.objects.get(id=user_id)
            if u.is_admin:
                return redirect('management_dashboard')
            if u.is_teacher:
                return redirect('teacher_dashboard')
        except User.DoesNotExist:
            del request.session['user_id']
        return redirect('section_list')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User(
            name=form.cleaned_data['name'],
            email=form.cleaned_data['email'].lower(),
        )
        user.set_password(form.cleaned_data['password'])
        user.save()
        request.session['user_id'] = user.id
        messages.success(request, f"Welcome to Edflix, {user.name}!")
        return redirect('section_list')
    return render(request, 'auth/signup.html', {'form': form})


def signin(request):
    if request.session.get('user_id'):
        user_id = request.session['user_id']
        try:
            u = User.objects.get(id=user_id)
            if u.is_admin:
                return redirect('management_dashboard')
            if u.is_teacher:
                return redirect('teacher_dashboard')
            return redirect('section_list')
        except User.DoesNotExist:
            del request.session['user_id']
    form = SignInForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].lower()
        password = form.cleaned_data['password']
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                request.session['user_id'] = user.id
                messages.success(request, f"Welcome back, {user.name}!")
                if user.is_admin:
                    return redirect('management_dashboard')
                return redirect('section_list')
            else:
                form.add_error('password', 'Incorrect password.')
        except User.DoesNotExist:
            form.add_error('email', 'No account found with this email.')
    return render(request, 'auth/signin.html', {'form': form})


@login_required
def logout_confirm(request):
    if request.method == 'POST':
        if 'user_id' in request.session:
            del request.session['user_id']
        messages.success(request, 'You have been signed out successfully.')
        return redirect('landing')
    return render(request, 'auth/logout_confirm.html')
