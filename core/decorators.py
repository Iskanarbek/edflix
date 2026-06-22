from django.shortcuts import redirect
from functools import wraps
from .models import User


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('signin')
        try:
            u = User.objects.get(id=user_id)
            if u.is_admin:
                return redirect('management_dashboard')
            if u.is_teacher:
                return redirect('teacher_dashboard')
        except User.DoesNotExist:
            del request.session['user_id']
            return redirect('signin')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('management_login')
        try:
            User.objects.get(id=user_id, is_admin=True)
        except User.DoesNotExist:
            return redirect('management_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('teacher_login')
        try:
            User.objects.get(id=user_id, is_teacher=True)
        except User.DoesNotExist:
            return redirect('teacher_login')
        return view_func(request, *args, **kwargs)
    return wrapper
