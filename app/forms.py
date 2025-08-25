from django import forms
from .models import Voter


class VoterRegistrationForm(forms.ModelForm):
    class Meta:
        model = Voter
        fields = ['fullname', 'email', 'telephone', 'student_id']  # No registered_list here
        widgets = {
            "fullname": forms.TextInput(attrs={
                "autofocus": True,
                "aria-describedby": "fullname-help",
                "required": True,
                "class": "form-control",
                "placeholder": "Enter your full name exactly as registered"
            }),
            "email": forms.EmailInput(attrs={
                "aria-describedby": "email-help",
                "required": True,
                "class": "form-control",
                "placeholder": "your.email@example.com"
            }),
            "telephone": forms.TextInput(attrs={
                "aria-describedby": "telephone-help",
                "required": True,
                "class": "form-control",
                "type": "tel",
                "placeholder": "+1234567890"
            }),
            "student_id": forms.TextInput(attrs={
                "aria-describedby": "student-id-help",
                "required": True,
                "class": "form-control",
                "placeholder": "Your student ID"
            }),
        }
        labels = {
            'fullname': 'Full Name *',
            'email': 'Email Address *',
            'telephone': 'Phone Number *',
            'student_id': 'Student ID *',
        }
        help_texts = {
            'fullname': 'Enter your full name exactly as it appears in our registered voter list',
            'email': 'We will use this email to send you voting information',
            'telephone': 'Include country code if outside your local area',
            'student_id': 'Your official student identification number',
        }
    
    def clean_fullname(self):
        """Additional validation for fullname"""
        fullname = self.cleaned_data.get('fullname')
        if fullname:
            # Check if name is eligible before saving
            if not Voter.is_eligible_voter(fullname):
                raise forms.ValidationError(
                    "The name you provided is not found in our registered voter list. "
                    "Please ensure you enter your name exactly as registered, or contact "
                    "the administrator for assistance."
                )
        return fullname