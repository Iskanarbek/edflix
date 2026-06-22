import json
import base64
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from ..models import TokenPlan, TokenPurchase, PaymeTransaction, User
from ..decorators import login_required


PAYME_KEY = getattr(settings, 'PAYME_KEY', 'PAYME_SECRET_KEY_HERE')
PAYME_ID = getattr(settings, 'PAYME_ID', 'PAYME_MERCHANT_ID_HERE')
UZS_TO_TIYIN = 100
USD_TO_UZS = 12500  # approximate rate, update as needed


@login_required
def buy_tokens(request):
    plans = TokenPlan.objects.filter(is_active=True).order_by('price_usd')
    user = User.objects.get(id=request.session['user_id'])
    return render(request, 'tokens/buy.html', {'plans': plans, 'user': user})


@login_required
def initiate_purchase(request, plan_id):
    plan = get_object_or_404(TokenPlan, id=plan_id, is_active=True)
    user = User.objects.get(id=request.session['user_id'])

    # Create a pending purchase record
    purchase = TokenPurchase.objects.create(
        user=user,
        plan=plan,
        tokens_added=plan.tokens,
        tokens_remaining=plan.tokens,
        amount_paid=plan.price_usd,
        is_confirmed=False,
    )

    # Payme checkout URL: amount in tiyin (UZS * 100)
    amount_tiyin = int(float(plan.price_usd) * USD_TO_UZS * UZS_TO_TIYIN)
    merchant_id = PAYME_ID

    # Encode params for Payme
    params = f"m={merchant_id};ac.purchase_id={purchase.id};a={amount_tiyin}"
    encoded = base64.b64encode(params.encode()).decode()
    checkout_url = f"https://checkout.paycom.uz/{encoded}"

    return render(request, 'tokens/payme_redirect.html', {
        'plan': plan,
        'user': user,
        'purchase': purchase,
        'checkout_url': checkout_url,
        'amount_tiyin': amount_tiyin,
    })


@csrf_exempt
def payme_callback(request):
    """Handle Payme merchant API callbacks."""
    if request.method != 'POST':
        return JsonResponse({'error': {'code': -32600, 'message': 'Invalid request'}}, status=400)

    # Verify Basic Auth
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Basic '):
        return _payme_error(-32504, 'Insufficient privilege')
    try:
        decoded = base64.b64decode(auth_header[6:]).decode()
        _, key = decoded.split(':', 1)
        if key != PAYME_KEY:
            return _payme_error(-32504, 'Insufficient privilege')
    except Exception:
        return _payme_error(-32504, 'Insufficient privilege')

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _payme_error(-32700, 'Parse error')

    method = body.get('method')
    params = body.get('params', {})
    req_id = body.get('id')

    if method == 'CheckPerformTransaction':
        return _check_perform_transaction(params, req_id)
    elif method == 'CreateTransaction':
        return _create_transaction(params, req_id)
    elif method == 'PerformTransaction':
        return _perform_transaction(params, req_id)
    elif method == 'CancelTransaction':
        return _cancel_transaction(params, req_id)
    elif method == 'CheckTransaction':
        return _check_transaction(params, req_id)
    elif method == 'GetStatement':
        return _get_statement(params, req_id)
    else:
        return _payme_error(-32601, 'Method not found', req_id)


def _check_perform_transaction(params, req_id):
    purchase_id = params.get('account', {}).get('purchase_id')
    try:
        purchase = TokenPurchase.objects.get(id=purchase_id, is_confirmed=False)
        amount = int(float(purchase.amount_paid) * USD_TO_UZS * UZS_TO_TIYIN)
        if params.get('amount') != amount:
            return _payme_error(-31001, 'Wrong amount', req_id)
        return JsonResponse({'result': {'allow': True}, 'id': req_id})
    except TokenPurchase.DoesNotExist:
        return _payme_error(-31050, 'Order not found', req_id)


def _create_transaction(params, req_id):
    purchase_id = params.get('account', {}).get('purchase_id')
    transaction_id = params.get('id')
    amount = params.get('amount')
    create_time = params.get('time')

    try:
        purchase = TokenPurchase.objects.get(id=purchase_id, is_confirmed=False)
    except TokenPurchase.DoesNotExist:
        return _payme_error(-31050, 'Order not found', req_id)

    expected_amount = int(float(purchase.amount_paid) * USD_TO_UZS * UZS_TO_TIYIN)
    if amount != expected_amount:
        return _payme_error(-31001, 'Wrong amount', req_id)

    txn, created = PaymeTransaction.objects.get_or_create(
        transaction_id=transaction_id,
        defaults={
            'purchase': purchase,
            'amount': amount,
            'state': 1,
            'create_time': create_time,
        }
    )
    if not created and txn.state != 1:
        return _payme_error(-31008, 'Transaction state error', req_id)

    return JsonResponse({'result': {
        'create_time': txn.create_time,
        'transaction': str(txn.id),
        'state': txn.state,
    }, 'id': req_id})


def _perform_transaction(params, req_id):
    transaction_id = params.get('id')
    perform_time = params.get('time', 0)

    try:
        txn = PaymeTransaction.objects.get(transaction_id=transaction_id)
    except PaymeTransaction.DoesNotExist:
        return _payme_error(-31003, 'Transaction not found', req_id)

    if txn.state == 2:
        return JsonResponse({'result': {
            'transaction': str(txn.id),
            'perform_time': txn.perform_time,
            'state': txn.state,
        }, 'id': req_id})

    if txn.state != 1:
        return _payme_error(-31008, 'Transaction state error', req_id)

    txn.state = 2
    txn.perform_time = perform_time
    txn.save()

    # Credit tokens to student
    purchase = txn.purchase
    if purchase and not purchase.is_confirmed:
        purchase.is_confirmed = True
        purchase.save(update_fields=['is_confirmed'])
        user = purchase.user
        user.tokens += purchase.tokens_added
        user.save(update_fields=['tokens'])

    return JsonResponse({'result': {
        'transaction': str(txn.id),
        'perform_time': txn.perform_time,
        'state': txn.state,
    }, 'id': req_id})


def _cancel_transaction(params, req_id):
    transaction_id = params.get('id')
    cancel_time = params.get('time', 0)
    reason = params.get('reason')

    try:
        txn = PaymeTransaction.objects.get(transaction_id=transaction_id)
    except PaymeTransaction.DoesNotExist:
        return _payme_error(-31003, 'Transaction not found', req_id)

    if txn.state == 2:
        return _payme_error(-31007, 'Cannot cancel completed transaction', req_id)

    txn.state = -1
    txn.cancel_time = cancel_time
    txn.reason = reason
    txn.save()

    # If already credited, remove tokens
    if txn.purchase and txn.purchase.is_confirmed:
        user = txn.purchase.user
        user.tokens = max(0, user.tokens - txn.purchase.tokens_added)
        user.save(update_fields=['tokens'])
        txn.purchase.is_confirmed = False
        txn.purchase.save(update_fields=['is_confirmed'])

    return JsonResponse({'result': {
        'transaction': str(txn.id),
        'cancel_time': txn.cancel_time,
        'state': txn.state,
    }, 'id': req_id})


def _check_transaction(params, req_id):
    transaction_id = params.get('id')
    try:
        txn = PaymeTransaction.objects.get(transaction_id=transaction_id)
    except PaymeTransaction.DoesNotExist:
        return _payme_error(-31003, 'Transaction not found', req_id)
    return JsonResponse({'result': {
        'create_time': txn.create_time,
        'perform_time': txn.perform_time,
        'cancel_time': txn.cancel_time,
        'transaction': str(txn.id),
        'state': txn.state,
        'reason': txn.reason,
    }, 'id': req_id})


def _get_statement(params, req_id):
    from_time = params.get('from', 0)
    to_time = params.get('to', 0)
    txns = PaymeTransaction.objects.filter(
        create_time__gte=from_time,
        create_time__lte=to_time,
    )
    transactions = []
    for txn in txns:
        transactions.append({
            'id': txn.transaction_id,
            'time': txn.create_time,
            'amount': txn.amount,
            'account': {'purchase_id': txn.purchase_id},
            'create_time': txn.create_time,
            'perform_time': txn.perform_time,
            'cancel_time': txn.cancel_time,
            'transaction': str(txn.id),
            'state': txn.state,
            'reason': txn.reason,
        })
    return JsonResponse({'result': {'transactions': transactions}, 'id': req_id})


def _payme_error(code, message, req_id=None):
    return JsonResponse({
        'error': {'code': code, 'message': {'ru': message, 'uz': message, 'en': message}},
        'id': req_id,
    })
