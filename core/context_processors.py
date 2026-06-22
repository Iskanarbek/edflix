from .models import User


def user_context(request):
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            if 'user_id' in request.session:
                del request.session['user_id']
    return {'current_user': user}
