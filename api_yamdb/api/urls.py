from django.urls import include, path
from rest_framework import routers

from .views import (APISendCode, APISendToken, CategoryViewSet, CommentViewSet,
                    GenreViewSet, ReviewSet, TitleViewSet, UserViewSet)

app_name = 'api'


router = routers.DefaultRouter()
r = router.register(
    r'titles/(?P<title_id>\d+)/reviews', ReviewSet, basename='reviews'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet, basename='comments'
)
router.register(r'users', UserViewSet, basename='user')
router.register(r'titles', TitleViewSet, basename='titles')
router.register(r'genres', GenreViewSet, basename='genres')
router.register(r'categories', CategoryViewSet, basename='categories')

urlpatterns = [
    path('v1/auth/signup/', APISendCode.as_view(), name='signup'),
    path('v1/auth/token/', APISendToken.as_view(), name='get_token'),
    path('v1/', include(router.urls)),
]
