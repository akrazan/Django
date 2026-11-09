from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpRequest, HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, CreateView, FormView, ListView, DetailView, UpdateView

from myauth.forms import AvatarUploadForm, ProfileEditForm
from myauth.mixins import OwnerOrStaffMixin
from myauth.models import Profile



class AboutMeView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "myauth/about-me.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class ChangeMyAvatarView(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ("avatar",)
    template_name = "myauth/change-my-avatar.html"

    def get_success_url(self):
        return reverse_lazy("myauth:about-me")

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class RegisterView(CreateView):
    template_name = "myauth/register.html"
    form_class = UserCreationForm
    # success_url = None

    def form_valid(self, form: UserCreationForm):
        user = form.save()
        self.object = user
        Profile.objects.create(user=user)
        login(self.request, user)
        return redirect("myauth:about-me")

    def form_invalid(self, form):
        return super().form_invalid(form)


def set_cookie_view(request: HttpRequest) -> HttpResponse:
    response = HttpResponse("Cookie set")
    response.set_cookie("name", "Nazarenko", max_age=3600)
    return response


def get_cookie_view(request: HttpRequest) -> HttpResponse:
    value = request.COOKIES.get("name", "default value")
    return HttpResponse(f'Cookie value: {value!r}')


def set_session_view(request: HttpRequest) -> HttpResponse:
    request.session["foobar"] = "spameggs"
    return HttpResponse("Session set")


def get_session_view(request: HttpRequest) -> HttpResponse:
    value = request.session.get("foobar", "default value")
    return HttpResponse(f'Session value: {value!r}')


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "myauth/user-list.html"
    context_object_name = "users"


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "myauth/user-detail.html"
    context_object_name = "target_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.object)
        context["profile"] = profile
        return context


class ChangeAvatarView(LoginRequiredMixin, OwnerOrStaffMixin, FormView):
    form_class = AvatarUploadForm
    template_name = "myauth/change-avatar.html"

    # --- GET и POST: только проверка прав, остальное делегируем ---
    def get(self, request, *args, **kwargs):
        response = self.check_owner_or_staff()
        if response:
            return response
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.check_owner_or_staff()
        if response:
            return response
        return super().post(request, *args, **kwargs)

    # --- Подготовка формы: берём профиль у target_user ---
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        pk = self.kwargs.get("pk")
        target_user = get_object_or_404(User, pk=pk)
        profile, _ = Profile.objects.get_or_create(user=target_user)
        kwargs["instance"] = profile
        return kwargs

    # --- Сохранение и редирект ---
    def form_valid(self, form):
        form.save()
        pk = self.kwargs.get("pk")
        target_user = get_object_or_404(User, pk=pk)
        return redirect(
            reverse("myauth:user-detail", kwargs={"pk": target_user.pk})
        )

    # --- Контекст для шаблона ---
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pk = self.kwargs.get("pk")
        target_user = get_object_or_404(User, pk=pk)

        context["target_user"] = target_user
        return context


class ProfileEditView(LoginRequiredMixin, OwnerOrStaffMixin, UpdateView):
    model = Profile
    form_class = ProfileEditForm
    template_name = "myauth/profile-edit.html"

    # --- GET и POST: проверка прав через миксин ---
    def get(self, request, *args, **kwargs):
        response = self.check_owner_or_staff()
        if response:
            return response
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.check_owner_or_staff()
        if response:
            return response
        return super().post(request, *args, **kwargs)

    # --- получаем профиль ---
    def get_object(self, queryset=None):
        user_pk = self.kwargs.get("pk")
        user = get_object_or_404(User, pk=user_pk)
        # Получаем или создаём профиль для этого пользователя
        profile, _ = Profile.objects.get_or_create(user=user)
        return profile

    # --- После сохранения редиректим на страницу пользователя ---
    def get_success_url(self):
        return reverse("myauth:user-detail", kwargs={"pk": self.object.user.pk})

    # --- Контекст для заполнения формы ---
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_user"] = self.object.user
        context["profile"] = self.object
        return context
