from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import MultipleChoiceTest, UserTestResult, LessonAccess, User
from ..decorators import login_required


@login_required
def take_test(request, test_id):
    test = get_object_or_404(MultipleChoiceTest, id=test_id)
    lesson = test.lesson
    user = User.objects.get(id=request.session['user_id'])

    if not LessonAccess.objects.filter(user=user, lesson=lesson).exists():
        messages.error(request, 'You need to unlock this lesson first.')
        return redirect('lesson_detail', lesson_id=lesson.id)

    if request.method == 'POST':
        questions = test.questions.prefetch_related('answers').all()
        total = questions.count()
        correct = 0
        for question in questions:
            selected_id = request.POST.get(f'question_{question.id}')
            if selected_id:
                try:
                    answer = question.answers.get(id=int(selected_id))
                    if answer.is_correct:
                        correct += 1
                except Exception:
                    pass
        score = round((correct / total * 100) if total > 0 else 0, 1)
        UserTestResult.objects.update_or_create(
            user=user, test=test,
            defaults={'score_percentage': score}
        )
        messages.success(request, f'Test completed! Your score: {score}%')
        return redirect('lesson_detail', lesson_id=lesson.id)

    questions = test.questions.prefetch_related('answers').all()
    existing_result = UserTestResult.objects.filter(user=user, test=test).first()
    return render(request, 'lessons/test.html', {
        'test': test,
        'lesson': lesson,
        'questions': questions,
        'existing_result': existing_result,
        'user': user,
    })
