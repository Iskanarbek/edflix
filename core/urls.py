from django.urls import path
from .views.auth_views import landing, signup, signin, logout_confirm
from .views.course_views import section_list, section_courses, course_detail
from .views.lesson_views import course_intro, lesson_detail, rate_lesson, download_file
from .views.token_views import buy_tokens, initiate_purchase, payme_callback
from .views.test_views import take_test
from .views.management_views import (
    management_login, management_logout, management_dashboard,
    admin_teacher_detail, admin_delete_course, admin_delete_lesson,
)
from .views.teacher_views import (
    teacher_login, teacher_register, teacher_logout, teacher_dashboard,
    teacher_course_create, teacher_course_edit, teacher_course_delete, teacher_course_detail,
    teacher_lesson_create, teacher_lesson_edit, teacher_lesson_delete, teacher_file_delete,
    teacher_test_create, teacher_test_edit, teacher_test_delete,
    teacher_analytics, teacher_connect_card, teacher_withdraw,
)

urlpatterns = [
    # ── Public ──────────────────────────────────────
    path('', landing, name='landing'),
    path('signup/', signup, name='signup'),
    path('signin/', signin, name='signin'),
    path('logout/', logout_confirm, name='logout'),

    # ── Student ─────────────────────────────────────
    path('courses/', section_list, name='section_list'),
    path('courses/<slug:category>/', section_courses, name='section_courses'),
    path('course/<int:course_id>/', course_detail, name='course_detail'),
    path('course/<int:course_id>/intro/', course_intro, name='course_intro'),
    path('lessons/<int:lesson_id>/', lesson_detail, name='lesson_detail'),
    path('lessons/<int:lesson_id>/rate/', rate_lesson, name='rate_lesson'),
    path('files/<int:file_id>/download/', download_file, name='download_file'),
    path('tokens/', buy_tokens, name='buy_tokens'),
    path('tokens/buy/<int:plan_id>/', initiate_purchase, name='initiate_purchase'),
    path('tests/<int:test_id>/', take_test, name='take_test'),

    # ── Payme ───────────────────────────────────────
    path('payme/callback/', payme_callback, name='payme_callback'),

    # ── Teacher ─────────────────────────────────────
    path('teacher/', teacher_login, name='teacher_login'),
    path('teacher/register/', teacher_register, name='teacher_register'),
    path('teacher/logout/', teacher_logout, name='teacher_logout'),
    path('teacher/dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/analytics/', teacher_analytics, name='teacher_analytics'),
    path('teacher/card/', teacher_connect_card, name='teacher_connect_card'),
    path('teacher/withdraw/', teacher_withdraw, name='teacher_withdraw'),
    path('teacher/courses/create/', teacher_course_create, name='teacher_course_create'),
    path('teacher/courses/<int:course_id>/', teacher_course_detail, name='teacher_course_detail'),
    path('teacher/courses/<int:course_id>/edit/', teacher_course_edit, name='teacher_course_edit'),
    path('teacher/courses/<int:course_id>/delete/', teacher_course_delete, name='teacher_course_delete'),
    path('teacher/courses/<int:course_id>/lessons/create/', teacher_lesson_create, name='teacher_lesson_create'),
    path('teacher/lessons/<int:lesson_id>/edit/', teacher_lesson_edit, name='teacher_lesson_edit'),
    path('teacher/lessons/<int:lesson_id>/delete/', teacher_lesson_delete, name='teacher_lesson_delete'),
    path('teacher/files/<int:file_id>/delete/', teacher_file_delete, name='teacher_file_delete'),
    path('teacher/lessons/<int:lesson_id>/test/create/', teacher_test_create, name='teacher_test_create'),
    path('teacher/tests/<int:test_id>/edit/', teacher_test_edit, name='teacher_test_edit'),
    path('teacher/tests/<int:test_id>/delete/', teacher_test_delete, name='teacher_test_delete'),

    # ── Admin ───────────────────────────────────────
    path('management/login/', management_login, name='management_login'),
    path('management/logout/', management_logout, name='management_logout'),
    path('management/', management_dashboard, name='management_dashboard'),
    path('management/teachers/<int:teacher_id>/', admin_teacher_detail, name='admin_teacher_detail'),
    path('management/courses/<int:course_id>/delete/', admin_delete_course, name='admin_delete_course'),
    path('management/lessons/<int:lesson_id>/delete/', admin_delete_lesson, name='admin_delete_lesson'),
]
