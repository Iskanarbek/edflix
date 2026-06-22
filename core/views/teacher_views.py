from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg
from ..models import (User, Course, Lesson, LessonFile, MultipleChoiceTest,
                      Question, Answer, LessonAccess, LessonRating,
                      TeacherWithdrawal, TOKEN_TO_USD)
from ..decorators import teacher_required


# ── Auth ──────────────────────────────────────────────────

def teacher_login(request):
    if request.session.get('user_id'):
        try:
            u = User.objects.get(id=request.session['user_id'])
            if u.is_teacher:
                return redirect('teacher_dashboard')
            if u.is_admin:
                return redirect('management_dashboard')
        except User.DoesNotExist:
            del request.session['user_id']

    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        try:
            user = User.objects.get(email=email, is_teacher=True)
            if user.check_password(password):
                user.expire_old_tokens()
                request.session['user_id'] = user.id
                return redirect('teacher_dashboard')
        except User.DoesNotExist:
            pass
        error = 'Invalid teacher credentials.'
    return render(request, 'teacher/login.html', {'error': error})


def teacher_register(request):
    if request.session.get('user_id'):
        try:
            u = User.objects.get(id=request.session['user_id'])
            if u.is_teacher:
                return redirect('teacher_dashboard')
        except User.DoesNotExist:
            del request.session['user_id']

    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')

        if not name or not email or not password:
            error = 'All fields are required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.objects.filter(email=email).exists():
            error = 'An account with this email already exists.'
        else:
            user = User(name=name, email=email, is_teacher=True)
            user.set_password(password)
            user.save()
            request.session['user_id'] = user.id
            messages.success(request, f'Welcome to Edflix, {user.name}!')
            return redirect('teacher_dashboard')
    return render(request, 'teacher/register.html', {'error': error})


@teacher_required
def teacher_logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    return redirect('teacher_login')


# ── Dashboard ─────────────────────────────────────────────

@teacher_required
def teacher_dashboard(request):
    teacher = User.objects.get(id=request.session['user_id'])
    teacher.expire_old_tokens()
    courses = Course.objects.filter(teacher=teacher).prefetch_related('lessons')
    total_courses = courses.count()
    total_lessons = Lesson.objects.filter(course__teacher=teacher).count()
    total_tokens = teacher.tokens_earned
    total_usd = teacher.earned_usd()
    return render(request, 'teacher/dashboard.html', {
        'teacher': teacher,
        'courses': courses,
        'total_courses': total_courses,
        'total_lessons': total_lessons,
        'total_tokens': total_tokens,
        'total_usd': total_usd,
    })


# ── Courses ───────────────────────────────────────────────

@teacher_required
def teacher_course_create(request):
    teacher = User.objects.get(id=request.session['user_id'])
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', '')
        if not title or not description or not category:
            return render(request, 'teacher/courses/form.html', {
                'action': 'Create',
                'category_choices': Course.CATEGORY_CHOICES,
                'error': 'Title, category and description are all required.',
            })
        course = Course(
            title=title,
            description=description,
            category=category,
            teacher=teacher,
        )
        if 'thumbnail' in request.FILES:
            course.thumbnail = request.FILES['thumbnail']
        if 'intro_video' in request.FILES:
            course.intro_video = request.FILES['intro_video']
        course.save()
        messages.success(request, f'Course "{course.title}" created. Now add lessons.')
        return redirect('teacher_lesson_create', course_id=course.id)
    return render(request, 'teacher/courses/form.html', {
        'action': 'Create',
        'category_choices': Course.CATEGORY_CHOICES,
    })


@teacher_required
def teacher_course_edit(request, course_id):
    teacher = User.objects.get(id=request.session['user_id'])
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    if request.method == 'POST':
        course.title = request.POST.get('title', '').strip()
        course.description = request.POST.get('description', '').strip()
        course.category = request.POST.get('category', '')
        if 'thumbnail' in request.FILES:
            course.thumbnail = request.FILES['thumbnail']
        if 'intro_video' in request.FILES:
            course.intro_video = request.FILES['intro_video']
        course.save()
        messages.success(request, f'Course "{course.title}" updated.')
        return redirect('teacher_dashboard')
    return render(request, 'teacher/courses/form.html', {
        'action': 'Edit',
        'course': course,
        'category_choices': Course.CATEGORY_CHOICES,
    })


@teacher_required
def teacher_course_delete(request, course_id):
    teacher = User.objects.get(id=request.session['user_id'])
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted.')
        return redirect('teacher_dashboard')
    return render(request, 'teacher/courses/confirm_delete.html', {'course': course})


@teacher_required
def teacher_course_detail(request, course_id):
    teacher = User.objects.get(id=request.session['user_id'])
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    lessons = course.lessons.prefetch_related('files').all()
    return render(request, 'teacher/courses/detail.html', {
        'course': course,
        'lessons': lessons,
        'teacher': teacher,
    })


# ── Lessons ───────────────────────────────────────────────

@teacher_required
def teacher_lesson_create(request, course_id):
    teacher = User.objects.get(id=request.session['user_id'])
    course = get_object_or_404(Course, id=course_id, teacher=teacher)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return render(request, 'teacher/lessons/form.html', {
                'action': 'Create', 'course': course,
                'error': 'Lesson title is required.',
            })
        next_order = course.lessons.count()
        lesson = Lesson(
            course=course,
            title=title,
            description=request.POST.get('description', ''),
            order=next_order,
            token_cost=3,
        )
        lesson.video = request.FILES['video']
        lesson.save()
        for f in request.FILES.getlist('lesson_files'):
            LessonFile.objects.create(lesson=lesson, title=f.name, file=f)
        messages.success(request, f'Lesson "{lesson.title}" created.')
        return redirect('teacher_course_detail', course_id=course.id)
    return render(request, 'teacher/lessons/form.html', {
        'action': 'Create', 'course': course,
    })


@teacher_required
def teacher_lesson_edit(request, lesson_id):
    teacher = User.objects.get(id=request.session['user_id'])
    lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=teacher)
    if request.method == 'POST':
        lesson.title = request.POST.get('title', '').strip()
        lesson.description = request.POST.get('description', '')
        lesson.token_cost = 3
        if 'video' in request.FILES:
            lesson.video = request.FILES['video']
        lesson.save()
        for f in request.FILES.getlist('lesson_files'):
            LessonFile.objects.create(lesson=lesson, title=f.name, file=f)
        messages.success(request, f'Lesson "{lesson.title}" updated.')
        return redirect('teacher_course_detail', course_id=lesson.course.id)
    return render(request, 'teacher/lessons/form.html', {
        'action': 'Edit', 'lesson': lesson, 'course': lesson.course,
    })


@teacher_required
def teacher_lesson_delete(request, lesson_id):
    teacher = User.objects.get(id=request.session['user_id'])
    lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=teacher)
    course_id = lesson.course.id
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Lesson deleted.')
        return redirect('teacher_course_detail', course_id=course_id)
    return render(request, 'teacher/lessons/confirm_delete.html', {'lesson': lesson})


@teacher_required
def teacher_file_delete(request, file_id):
    teacher = User.objects.get(id=request.session['user_id'])
    f = get_object_or_404(LessonFile, id=file_id, lesson__course__teacher=teacher)
    course_id = f.lesson.course.id
    if request.method == 'POST':
        f.file.delete(save=False)
        f.delete()
        messages.success(request, 'File deleted.')
    return redirect('teacher_course_detail', course_id=course_id)


# ── Tests ─────────────────────────────────────────────────

@teacher_required
def teacher_test_create(request, lesson_id):
    teacher = User.objects.get(id=request.session['user_id'])
    lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=teacher)
    if hasattr(lesson, 'test'):
        return redirect('teacher_test_edit', test_id=lesson.test.id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        test = MultipleChoiceTest.objects.create(lesson=lesson, title=title)
        _save_questions(request, test)
        messages.success(request, 'Test created.')
        return redirect('teacher_course_detail', course_id=lesson.course.id)
    return render(request, 'teacher/tests/form.html', {'lesson': lesson, 'action': 'Create'})


@teacher_required
def teacher_test_edit(request, test_id):
    teacher = User.objects.get(id=request.session['user_id'])
    test = get_object_or_404(MultipleChoiceTest, id=test_id, lesson__course__teacher=teacher)
    lesson = test.lesson
    if request.method == 'POST':
        test.title = request.POST.get('title', '').strip()
        test.save()
        test.questions.all().delete()
        _save_questions(request, test)
        messages.success(request, 'Test updated.')
        return redirect('teacher_course_detail', course_id=lesson.course.id)
    return render(request, 'teacher/tests/form.html', {
        'lesson': lesson, 'test': test, 'action': 'Edit',
    })


@teacher_required
def teacher_test_delete(request, test_id):
    teacher = User.objects.get(id=request.session['user_id'])
    test = get_object_or_404(MultipleChoiceTest, id=test_id, lesson__course__teacher=teacher)
    lesson = test.lesson
    if request.method == 'POST':
        test.delete()
        messages.success(request, 'Test deleted.')
    return redirect('teacher_course_detail', course_id=lesson.course.id)


def _save_questions(request, test):
    q_texts = request.POST.getlist('question_text')
    for idx, q_text in enumerate(q_texts):
        if not q_text.strip():
            continue
        q = Question.objects.create(test=test, question_text=q_text, order=idx)
        answers = request.POST.getlist(f'answer_{idx}')
        try:
            correct_idx = int(request.POST.get(f'correct_{idx}', 0))
        except (ValueError, TypeError):
            correct_idx = 0
        for a_idx, a_text in enumerate(answers):
            if a_text.strip():
                Answer.objects.create(
                    question=q,
                    answer_text=a_text,
                    is_correct=(a_idx == correct_idx)
                )


# ── Analytics ─────────────────────────────────────────────

@teacher_required
def teacher_analytics(request):
    teacher = User.objects.get(id=request.session['user_id'])
    courses = Course.objects.filter(teacher=teacher).prefetch_related('lessons')

    course_data = []
    for course in courses:
        lessons_data = []
        for lesson in course.lessons.all():
            accesses = LessonAccess.objects.filter(lesson=lesson)
            tokens = accesses.aggregate(t=Sum('tokens_spent'))['t'] or 0
            teacher_tokens = int(tokens * 0.75)
            avg_rating = lesson.average_rating()
            lessons_data.append({
                'lesson': lesson,
                'views': accesses.count(),
                'tokens': teacher_tokens,
                'usd': round(teacher_tokens * TOKEN_TO_USD, 2),
                'avg_rating': avg_rating,
            })
        course_tokens = sum(d['tokens'] for d in lessons_data)
        course_usd = round(course_tokens * TOKEN_TO_USD, 2)
        avg_r = course.average_rating()
        course_data.append({
            'course': course,
            'lessons': lessons_data,
            'total_tokens': course_tokens,
            'total_usd': course_usd,
            'avg_rating': avg_r,
        })

    return render(request, 'teacher/analytics.html', {
        'teacher': teacher,
        'course_data': course_data,
        'total_tokens': teacher.tokens_earned,
        'total_usd': teacher.earned_usd(),
    })


# ── Card & Withdrawal ────────────────────────────────────

@teacher_required
def teacher_connect_card(request):
    teacher = User.objects.get(id=request.session['user_id'])
    if request.method == 'POST':
        card_number = request.POST.get('card_number', '').replace(' ', '')
        card_expiry = request.POST.get('card_expiry', '').strip()
        if len(card_number) not in (16, 18):
            messages.error(request, 'Please enter a valid card number (16–18 digits).')
        elif len(card_expiry) != 5 or '/' not in card_expiry:
            messages.error(request, 'Please enter expiry as MM/YY.')
        else:
            teacher.card_number = card_number
            teacher.card_expiry = card_expiry
            teacher.save(update_fields=['card_number', 'card_expiry'])
            messages.success(request, 'Card connected successfully.')
            return redirect('teacher_dashboard')
    return render(request, 'teacher/connect_card.html', {'teacher': teacher})


@teacher_required
def teacher_withdraw(request):
    teacher = User.objects.get(id=request.session['user_id'])
    if request.method == 'POST':
        if not teacher.has_card():
            messages.error(request, 'Please connect your card first.')
            return redirect('teacher_connect_card')
        try:
            amount_usd = float(request.POST.get('amount_usd', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount.')
            return redirect('teacher_dashboard')

        tokens_needed = int(amount_usd / TOKEN_TO_USD)
        if amount_usd < 10:
            messages.error(request, 'Minimum withdrawal amount is $10.')
            return redirect('teacher_dashboard')
        if tokens_needed > teacher.tokens_earned:
            messages.error(
                request,
                f'Insufficient balance. You have ${teacher.earned_usd()} available.'
            )
            return redirect('teacher_dashboard')

        teacher.tokens_earned -= tokens_needed
        teacher.save(update_fields=['tokens_earned'])
        TeacherWithdrawal.objects.create(
            teacher=teacher,
            tokens_withdrawn=tokens_needed,
            amount_usd=amount_usd,
            card_number=teacher.card_number,
            status='pending',
        )
        messages.success(
            request,
            f'Withdrawal of ${amount_usd:.2f} initiated. Funds will arrive in 1–3 business days.'
        )
    return redirect('teacher_dashboard')
