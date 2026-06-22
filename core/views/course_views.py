from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Course, CourseAgreement, LessonAccess, User
from ..decorators import login_required

SECTIONS = [
    {
        'key': 'general_english',
        'label': 'General English',
        'short': 'ENG',
        'description': 'Build a solid foundation in grammar, vocabulary, and communication — the bedrock of every English exam and real-world use.',
        'color_class': 'section-eng',
    },
    {
        'key': 'ielts',
        'label': 'IELTS',
        'short': 'IELTS',
        'description': 'Structured preparation for all four IELTS components — Listening, Reading, Writing, Speaking — designed for Band 7 and above.',
        'color_class': 'section-ielts',
    },
    {
        'key': 'sat',
        'label': 'SAT',
        'short': 'SAT',
        'description': 'Evidence-based strategies for SAT Math and Evidence-Based Reading & Writing. Focus on what the exam actually tests.',
        'color_class': 'section-sat',
    },
]


@login_required
def section_list(request):
    user = User.objects.get(id=request.session['user_id'])
    return render(request, 'courses/sections.html', {'sections': SECTIONS, 'user': user})


@login_required
def section_courses(request, category):
    valid = [s['key'] for s in SECTIONS]
    if category not in valid:
        return redirect('section_list')
    section = next(s for s in SECTIONS if s['key'] == category)
    courses = Course.objects.filter(category=category)
    user = User.objects.get(id=request.session['user_id'])
    return render(request, 'courses/list.html', {
        'section': section,
        'courses': courses,
        'user': user,
    })


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    first_lesson = course.lessons.first()
    if first_lesson:
        return redirect('lesson_detail', lesson_id=first_lesson.id)
    # No lessons yet — show empty course page
    user = User.objects.get(id=request.session['user_id'])
    has_agreed = CourseAgreement.objects.filter(user=user, course=course).exists()
    return render(request, 'courses/detail.html', {
        'course': course,
        'lessons': [],
        'accessed_lesson_ids': [],
        'user': user,
        'has_agreed': has_agreed,
    })
