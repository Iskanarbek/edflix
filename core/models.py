from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password
from django.utils import timezone
from datetime import timedelta


TOKEN_TO_USD = 0.50  # 1 token = $0.50


class User(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    # Student token balance (from plan purchases, expires monthly)
    tokens = models.IntegerField(default=0)
    # Teacher earned tokens (from students, 75% of lesson cost, never expire)
    tokens_earned = models.IntegerField(default=0)
    # Visa card for teacher withdrawals
    card_number = models.CharField(max_length=19, blank=True)
    card_expiry = models.CharField(max_length=5, blank=True)  # MM/YY
    date_joined = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)

    def has_card(self):
        return bool(self.card_number and self.card_expiry)

    def earned_usd(self):
        return round(self.tokens_earned * TOKEN_TO_USD, 2)

    def expire_old_tokens(self):
        """Zero out tokens from expired purchases. Call on login and page load."""
        now = timezone.now()
        expired = self.purchases.filter(expires_at__lt=now, processed_expiry=False)
        if not expired.exists():
            return
        # For each expired purchase, subtract tokens_remaining from user balance
        for purchase in expired:
            self.tokens = max(0, self.tokens - purchase.tokens_remaining)
            purchase.tokens_remaining = 0
            purchase.processed_expiry = True
            purchase.save(update_fields=['tokens_remaining', 'processed_expiry'])
        self.save(update_fields=['tokens'])

    def __str__(self):
        return self.email


class Course(models.Model):
    CATEGORY_CHOICES = [
        ('general_english', 'General English'),
        ('ielts', 'IELTS'),
        ('sat', 'SAT'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courses', limit_choices_to={'is_teacher': True}
    )
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    intro_video = models.FileField(upload_to='videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def average_rating(self):
        ratings = LessonRating.objects.filter(lesson__course=self)
        if ratings.exists():
            return round(ratings.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return None

    def lesson_count(self):
        return self.lessons.count()

    def tokens_earned(self):
        total = LessonAccess.objects.filter(lesson__course=self).aggregate(
            total=models.Sum('tokens_spent')
        )['total'] or 0
        return int(total * 0.75)

    def usd_earned(self):
        return round(self.tokens_earned() * TOKEN_TO_USD, 2)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video = models.FileField(upload_to='videos/', blank=True, null=True)
    order = models.IntegerField(default=0)
    token_cost = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def average_rating(self):
        ratings = LessonRating.objects.filter(lesson=self)
        if ratings.exists():
            return round(ratings.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return None

    def view_count(self):
        return self.accesses.count()

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class LessonFile(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='files')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MultipleChoiceTest(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='test')
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(MultipleChoiceTest, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question_text[:60]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.answer_text


class UserTestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(MultipleChoiceTest, on_delete=models.CASCADE, related_name='results')
    score_percentage = models.FloatField(default=0)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'test']

    def __str__(self):
        return f"{self.user.email} — {self.test.title}: {self.score_percentage}%"


class LessonRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    rated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'lesson']

    def __str__(self):
        return f"{self.user.email} rated {self.lesson.title}: {self.rating}/5"


class LessonAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accessed_lessons')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='accesses')
    tokens_spent = models.IntegerField(default=10)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'lesson']

    def __str__(self):
        return f"{self.user.email} accessed {self.lesson.title}"


class CourseAgreement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agreements')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='agreements')
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.email} agreed to {self.course.title}"


class TokenPlan(models.Model):
    name = models.CharField(max_length=100)
    price_usd = models.DecimalField(max_digits=8, decimal_places=2)
    tokens = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} — ${self.price_usd} / {self.tokens} tokens"


class TokenPurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    plan = models.ForeignKey(TokenPlan, on_delete=models.SET_NULL, null=True)
    tokens_added = models.IntegerField()
    tokens_remaining = models.IntegerField(default=0)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    processed_expiry = models.BooleanField(default=False)
    payme_transaction_id = models.CharField(max_length=255, blank=True)
    is_confirmed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at and not self.pk:
            self.expires_at = timezone.now() + timedelta(days=30)
        if self.tokens_remaining == 0 and not self.pk:
            self.tokens_remaining = self.tokens_added
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} bought {self.tokens_added} tokens"


class TeacherWithdrawal(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    tokens_withdrawn = models.IntegerField()
    amount_usd = models.DecimalField(max_digits=8, decimal_places=2)
    card_number = models.CharField(max_length=19)
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending'
    )

    def __str__(self):
        return f"{self.teacher.email} withdrew ${self.amount_usd}"


class PaymeTransaction(models.Model):
    transaction_id = models.CharField(max_length=255, unique=True)
    purchase = models.ForeignKey(TokenPurchase, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.BigIntegerField()  # in tiyin (1 UZS = 100 tiyin)
    state = models.IntegerField(default=1)
    create_time = models.BigIntegerField(default=0)
    perform_time = models.BigIntegerField(default=0)
    cancel_time = models.BigIntegerField(default=0)
    reason = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.transaction_id
