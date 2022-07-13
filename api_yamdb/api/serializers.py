from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueValidator
from reviews.models import Category, Comment, Genre, Review, Title, User


class UserSerializer(serializers.ModelSerializer):
    """Сериалайзер модели User"""

    class Meta:
        model = User
        fields = (
            'username', 'email',
            'first_name', 'last_name',
            'bio', 'role'
        )


class EmailTokenSerializer(serializers.ModelSerializer):
    """Сериализатор модели User для получения кода"""
    class Meta:
        model = User
        fields = ('username', 'email')

    def validate_username(self, value):
        if value == 'me':
            raise ValidationError(message='Данное имя пользователя запрещено')
        return value


class TokenObtainPairSerializer(serializers.Serializer):
    """Сериализатор модели User для получения токена"""
    username = serializers.CharField(max_length=40, required=True)
    confirmation_code = serializers.CharField(max_length=10, required=True)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор модели Review"""
    author = SlugRelatedField(read_only=True, slug_field='username')
    title = SlugRelatedField(
        write_only=True, queryset=Title.objects.all(),
        slug_field='title', required=False
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date', 'title')

    def validate_score(self, value):
        if not (1 <= value <= 10) or value is None:
            raise serializers.ValidationError(
                'Возможная оценка: от 1 до 10'
            )
        return value

    def validate(self, attrs):
        title = get_object_or_404(
            Title, id=self.context['view'].kwargs.get('title_id')
        )
        user = self.context.get('request').user
        if Review.objects.filter(title=title, author=user).exists():
            if self.context['request'].method in ['POST']:
                raise serializers.ValidationError(
                    'Возможно оставить только 1 отзыв на произведение'
                )
        return super().validate(attrs)


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор модели Comment"""
    author = SlugRelatedField(read_only=True, slug_field='username')
    review = SlugRelatedField(
        write_only=True, queryset=Review.objects.all(),
        slug_field='review', required=False
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date', 'review')


class GenreSerializer(serializers.ModelSerializer):
    """Сериалайзер модели Genre"""
    slug = serializers.SlugField(
        max_length=100,
        validators=[
            UniqueValidator(
                queryset=Genre.objects.all(),
                message='Поле slug должно быть уникальным!'
            )
        ]
    )

    class Meta:
        model = Genre
        exclude = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    """Сериалайзер модели Category"""
    slug = serializers.SlugField(
        max_length=100,
        validators=[
            UniqueValidator(
                queryset=Category.objects.all(),
                message='Поле slug должно быть уникальным!'
            )
        ]
    )

    class Meta:
        model = Category
        exclude = ('id',)


class TitleSerializer(serializers.ModelSerializer):
    """Сериалайзер модели Title"""
    rating = serializers.IntegerField(
        source='reviews__score__avg', read_only=True
    )
    category = CategorySerializer()
    genre = GenreSerializer(many=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name',
            'year', 'rating',
            'description',
            'genre', 'category'
        )


class TitleCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер для модели Title для Post-запросов"""
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug', many=True, queryset=Genre.objects.all()
    )

    class Meta:
        model = Title
        fields = (
            'id', 'name',
            'year', 'description',
            'genre', 'category'
        )

    def validate_year(self, value):
        now = timezone.now()
        if value > now.year:
            raise ValidationError(message='Укажите корректный год выпуска')
        return value
