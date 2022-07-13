from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import year_validator

USER = 'user'
ADMIN = 'admin'
MODERATOR = 'moderator'
CHOICES = (
    (USER, 'user'),
    (ADMIN, 'admin'),
    (MODERATOR, 'moderator'),
)


class User(AbstractUser):
    """Модель User"""
    bio = models.TextField(
        blank=True,
        verbose_name='Биография',
        help_text='Здесь вы можете ввести информацию о себе'
    )
    role = models.CharField(
        max_length=20,
        choices=CHOICES,
        default=USER,
        verbose_name='Роль пользователя'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Адрес электронной почты',
        help_text='Это поле должно быть уникальным'
    )
    username = models.CharField(
        max_length=40,
        unique=True,
        verbose_name='Имя пользователя',
        help_text='Это поле должно быть уникальным'
    )
    confirmation_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Код подтверждения',
        help_text='Необходим для получения токена'
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    REQUIRED_FIELD = ['username', 'email']

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_staff or self.is_superuser

    @property
    def is_user(self):
        return self.role == USER

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email', 'username'],
                                    name='unique_user')
        ]
        ordering = ['username']
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.username


class Category(models.Model):
    """Модель Category"""
    name = models.CharField(max_length=256, verbose_name='Название категории')
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Slug категории',
        help_text='Это поле должно быть уникальным'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Модель Genre"""
    name = models.CharField(max_length=256, verbose_name='Название жанра')
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Slug жанра',
        help_text='Это поле должно быть уникальным'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'genre'
        verbose_name_plural = 'genres'

    def __str__(self):
        return self.name


class Title(models.Model):
    """Модель Title"""
    name = models.CharField(
        max_length=200,
        verbose_name='Название произведения'
    )
    genre = models.ManyToManyField(
        Genre,
        blank=True,
        verbose_name='Жанр произведения'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        related_name='titles', null=True,
        verbose_name='Категория произведения'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание произведения'
    )
    year = models.PositiveSmallIntegerField(
        validators=[year_validator],
        verbose_name='Год публикации произведения'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'title'
        verbose_name_plural = 'titles'

    def __str__(self):
        return self.name


class Review(models.Model):
    """Модель Review"""
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение'
    )
    text = models.TextField(
        verbose_name='Текст отзыва',
        help_text='Введите текст отзыва'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор',
    )
    score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Минимальная оценка - 1'),
            MaxValueValidator(10, 'Максимальная оценка - 10')
        ],
        verbose_name='Оценка произведения',
        help_text='Введите значение от 1 до 10'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата добавления отзыва',
        auto_now_add=True, db_index=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['title', 'author'],
                                    name='unique_review')
        ]
        ordering = ['-pub_date']
        verbose_name = 'review'
        verbose_name_plural = 'reviews'

    def __str__(self):
        return self.text


class Comment(models.Model):
    """Модель Comment"""
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв на произведение'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата добавления комментария',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'comment'
        verbose_name_plural = 'comments'

    def __str__(self):
        return self.text
