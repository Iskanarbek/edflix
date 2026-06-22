from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Avg
from ..models import User, Course, Lesson, LessonFile, LessonAccess, TokenPurchase, TOKEN_TO_USD
from ..decorators import admin_required


def management_login(request):
    if request.session.get('user_id'):
        try:
            u = User.objects.get(id=request.session['user_id'])
            if u.is_admin:
                return redirect('management_dashboard')
            if u.is_teacher:
                return redirect('teacher_dashboard')
        except User.DoesNotExist:
            del request.session['user_id']

    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').lower()
        password = request.POST.get('password', '')
        try:
            user = User.objects.get(email=email, is_admin=True)
            if user.check_password(password):
                request.session['user_id'] = user.id
                return redirect('management_dashboard')
        except User.DoesNotExist:
            pass
        error = 'Invalid admin credentials.'
    return render(request, 'management/login.html', {'error': error})


@admin_required
def management_logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    return redirect('management_login')


@admin_required
def management_dashboard(request):
    total_users = User.objects.filter(is_admin=False, is_teacher=False).count()
    total_courses = Course.objects.count()
    total_lessons = Lesson.objects.count()
    total_revenue = TokenPurchase.objects.filter(is_confirmed=True).aggregate(
        total=Sum('amount_paid')
    )['total'] or 0

    teachers = User.objects.filter(is_teacher=True).order_by('name')
    teacher_data = []
    for t in teachers:
        earned = round(t.tokens_earned * TOKEN_TO_USD, 2)
        teacher_data.append({'teacher': t, 'earned_usd': earned})

    return render(request, 'management/dashboard.html', {
        'total_users': total_users,
        'total_courses': total_courses,
        'total_lessons': total_lessons,
        'total_revenue': total_revenue,
        'teacher_data': teacher_data,
    })


@admin_required
def admin_teacher_detail(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, is_teacher=True)
    courses = Course.objects.filter(teacher=teacher).prefetch_related('lessons__files')
    return render(request, 'management/teacher_detail.html', {
        'teacher': teacher,
        'courses': courses,
    })


@admin_required
def admin_delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    teacher_id = course.teacher.id if course.teacher else None
    if request.method == 'POST':
        course.delete()
        messages.success(request, f'Course "{course.title}" deleted.')
        if teacher_id:
            return redirect('admin_teacher_detail', teacher_id=teacher_id)
        return redirect('management_dashboard')
    return render(request, 'management/confirm_delete.html', {
        'object': course,
        'object_type': 'Course',
        'back_url': f'/management/teachers/{teacher_id}/' if teacher_id else '/management/',
    })


@admin_required
def admin_delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    teacher_id = lesson.course.teacher.id if lesson.course.teacher else None
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, f'Lesson "{lesson.title}" deleted.')
        if teacher_id:
            return redirect('admin_teacher_detail', teacher_id=teacher_id)
        return redirect('management_dashboard')
    return render(request, 'management/confirm_delete.html', {
        'object': lesson,
        'object_type': 'Lesson',
        'back_url': f'/management/teachers/{teacher_id}/' if teacher_id else '/management/',
    })
