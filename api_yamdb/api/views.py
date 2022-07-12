import secrets
import string

from django.core.mail import EmailMessage
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.models import Category, Genre, Review, Title, User, USER
from .filters import TitleFilter
from .mixins import ListCreateDestroyMixin
from .permissions import IsAdmin, IsAdminOrReadOnly, IsAuthorOrStaffOrReadOnly
from .serializers import (CategorySerializer, CommentSerializer,
                          EmailTokenSerializer, GenreSerializer,
                          ReviewSerializer, TitleCreateSerializer,
                          TitleSerializer, TokenObtainPairSerializer,
                          UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет сериалайзера UserSerializer"""
    permission_classes = (IsAuthenticated, IsAdmin)
    pagination_class = PageNumberPagination
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ('username',)
    search_fields = ['username']

    @action(methods=['get', 'patch'],
            detail=False,
            permission_classes=(IsAuthenticated,),
            url_path='me',)
    def user_data(self, request):
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'PATCH':
            serializer = UserSerializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            if request.user.is_user:
                serializer.save(role=USER)
            else:
                serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)


class APISendCode(APIView):
    """Вьюкласс сериалайзера EmailTokenSerializer"""
    permission_classes = (AllowAny,)

    def post(self, request):
        confirmation_code = ''.join(
            secrets.choice(
                string.ascii_uppercase + string.digits) for _ in range(9))
        serializer = EmailTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            username=serializer.validated_data['username'],
            confirmation_code=confirmation_code
        )
        email = EmailMessage('Регистрация YAMDB',
                             f'используйте код подвтерждения:'
                             f'{confirmation_code}',
                             to=[serializer.validated_data['email']],
                             )
        email.send()
        return Response(serializer.data,
                        status=status.HTTP_200_OK)


class APISendToken(APIView):
    """Вьюкласс сериалайзера TokenObtainPairSerializer"""
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, username=serializer.validated_data['username']
        )

        if serializer.validated_data['confirmation_code'] == (
                user.confirmation_code):
            token = RefreshToken.for_user(user).access_token
            return Response({'token': str(token)}, status=status.HTTP_200_OK)
        return Response(
            {'ошибка авторизации': 'Код подтверждения некорректен'},
            status=status.HTTP_400_BAD_REQUEST)


class ReviewSet(viewsets.ModelViewSet):
    """Вьюсет сериалайзера ReviewSerializer"""
    serializer_class = ReviewSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly & IsAuthorOrStaffOrReadOnly
    ]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ('title_id', 'id')

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        return title.reviews.all()

    def perform_create(self, serializer):
        serializer.save(
            title_id=self.kwargs.get('title_id'),
            author=self.request.user
        )


class CommentViewSet(viewsets.ModelViewSet):
    """Вьюсет сериалайзера CommentSerializer"""
    serializer_class = CommentSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly & IsAuthorOrStaffOrReadOnly
    ]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ('review_id', 'id',)

    def get_queryset(self):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        serializer.save(
            author=self.request.user, review=review
        )


class TitleViewSet(viewsets.ModelViewSet):
    """Вьюсет сериалайзера TitleSerializer"""
    queryset = Title.objects.all().annotate(
        Avg('reviews__score')).order_by('name')
    serializer_class = TitleSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TitleSerializer
        return TitleCreateSerializer


class CategoryViewSet(ListCreateDestroyMixin):
    """Вьюсет сериалайзера CategorySerializer"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (filters.SearchFilter,)


class GenreViewSet(ListCreateDestroyMixin):
    """Вьюсет сериалайзера GenreSerializer"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (filters.SearchFilter,)
