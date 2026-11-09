# permissions.py
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404


class OwnerOrStaffMixin:
    """
    Проверяет: request.user владелец профиля или пользователь с правами is_staff или superuser.
    Возвращает HttpResponseForbidden, если прав нет. Иначе возвращает None.
    """

    def get_target_user(self):
        pk = self.kwargs.get("pk")
        return get_object_or_404(User, pk=pk)

    def check_owner_or_staff(self):
        target_user = self.get_target_user()

        if not hasattr(self, "target_user"):
            self.target_user = target_user

        user = self.request.user

        # Проверка прав: владелец ИЛИ стафф ИЛИ суперпользователь
        if not (user == target_user or user.is_staff or user.is_superuser):
            return HttpResponseForbidden("У вас нет прав менять аватар этого пользователя.")

        return None
