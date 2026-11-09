from django import forms
from .models import Profile

class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["avatar"]


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }
