from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

app_name = "myauth"

urlpatterns = [
    path(
        'login/',
        LoginView.as_view(
            template_name="myauth/login.html",
            redirect_authenticated_user=True,
        ),
        name='login'
    ),

    path(
        'logout/',
        LogoutView.as_view(
            next_page='myauth:login'
        ),
        name='logout'
    ),

    path("about-me/", views.AboutMeView.as_view(), name="about-me"),
    path("about-me/avatar/", views.ChangeMyAvatarView.as_view(), name="change-my-avatar"),

    path("register/", views.RegisterView.as_view(), name="register"),

    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/avatar/", views.ChangeAvatarView.as_view(), name="change-avatar"),
    path("users/<int:pk>/edit/", views.ProfileEditView.as_view(), name="profile-edit"),

    path('cookie/get', views.get_cookie_view, name='cookie-get'),
    path('cookie/set', views.set_cookie_view, name='cookie-set'),

    path('session/get', views.get_session_view, name='session-get'),
    path('session/set', views.set_session_view, name='session-set'),
]