from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib import messages
from ..models import (Lesson, LessonAccess, LessonRating, CourseAgreement,
                      User, LessonFile, UserTestResult, Course)
from ..decorators import login_required
import os


@login_required
def course_intro(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = User.objects.get(id=request.session['user_id'])
    has_agreed = CourseAgreement.objects.filter(user=user, course=course).exists()

    if request.method == 'POST' and request.POST.get('agree'):
        ip = request.META.get('REMOTE_ADDR')
        CourseAgreement.objects.get_or_create(user=user, course=course, defaults={'ip_address': ip})
        first_lesson = course.lessons.first()
        if first_lesson:
            return redirect('lesson_detail', lesson_id=first_lesson.id)
        return redirect('section_list')

    return render(request, 'courses/intro.html', {
        'course': course,
        'has_agreed': has_agreed,
    })


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    user = User.objects.get(id=request.session['user_id'])
    user.expire_old_tokens()
    course = lesson.course
    has_agreed = CourseAgreement.objects.filter(user=user, course=course).exists()

    if not has_agreed:
        messages.warning(request, 'You must read and agree to the Course Agreement before accessing lessons.')
        return redirect('course_intro', course_id=course.id)

    access = LessonAccess.objects.filter(user=user, lesson=lesson).first()
    if not access:
        if user.tokens < lesson.token_cost:
            messages.warning(request, 'You need an active subscription to watch lessons. Choose a plan below.')
            return redirect('buy_tokens')
        user.tokens -= lesson.token_cost
        user.save(update_fields=['tokens'])
        LessonAccess.objects.create(user=user, lesson=lesson, tokens_spent=lesson.token_cost)
        teacher = course.teacher
        if teacher:
            teacher.tokens_earned += int(lesson.token_cost * 0.75)
            teacher.save(update_fields=['tokens_earned'])

    user_rating = LessonRating.objects.filter(user=user, lesson=lesson).first()
    test_result = None
    if hasattr(lesson, 'test'):
        test_result = UserTestResult.objects.filter(user=user, test=lesson.test).first()

    lessons = course.lessons.all()
    accessed_lesson_ids = list(
        LessonAccess.objects.filter(user=user, lesson__course=course)
        .values_list('lesson_id', flat=True)
    )
    test_results_map = {}
    for tr in UserTestResult.objects.filter(user=user, test__lesson__course=course):
        test_results_map[tr.test.lesson_id] = tr.score_percentage

    return render(request, 'lessons/detail.html', {
        'lesson': lesson,
        'course': course,
        'lessons': lessons,
        'accessed_lesson_ids': accessed_lesson_ids,
        'user_rating': user_rating.rating if user_rating else 0,
        'test_result': test_result,
        'user': user,
        'has_agreed': has_agreed,
        'test_results_map': test_results_map,
    })


@login_required
def rate_lesson(request, lesson_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    lesson = get_object_or_404(Lesson, id=lesson_id)
    user = User.objects.get(id=request.session['user_id'])

    if not LessonAccess.objects.filter(user=user, lesson=lesson).exists():
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        rating_val = int(request.POST.get('rating', 0))
        if not 1 <= rating_val <= 5:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid rating'}, status=400)

    LessonRating.objects.update_or_create(
        user=user, lesson=lesson, defaults={'rating': rating_val}
    )
    return JsonResponse({'success': True, 'avg_rating': lesson.average_rating()})


@login_required
def download_file(request, file_id):
    lesson_file = get_object_or_404(LessonFile, id=file_id)
    user = User.objects.get(id=request.session['user_id'])
    lesson = lesson_file.lesson
    if not LessonAccess.objects.filter(user=user, lesson=lesson).exists():
        messages.warning(request, 'Please unlock this lesson before downloading its materials.')
        return redirect('section_list')
    response = FileResponse(
        lesson_file.file.open('rb'),
        as_attachment=True,
        filename=os.path.basename(lesson_file.file.name)
    )
    return response
