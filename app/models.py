from django.db import models
from django.core.exceptions import ValidationError


class RegisteredVoter(models.Model):
    names = models.TextField(
        help_text="Enter each eligible voter name on a separate line"
    )
    
    def __str__(self):
        return f"Eligible Voters List #{self.pk}"
    
    def get_eligible_names(self):
        """Return a list of eligible voter names (lowercase for comparison)"""
        if self.names:
            return [name.strip().lower() for name in self.names.split('\n') if name.strip()]
        return []


class Voter(models.Model):
    fullname = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=14, unique=True)
    student_id = models.CharField(max_length=10, unique=True)
    registered_list = models.ForeignKey(
        RegisteredVoter, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The eligible voter list this person was validated against"
    )
    
    def __str__(self):
        return self.fullname
    
    @classmethod
    def is_eligible_voter(cls, fullname):
        """Check if a name exists in any registered voter list"""
        registered_lists = RegisteredVoter.objects.all()
        for voter_list in registered_lists:
            eligible_names = voter_list.get_eligible_names()
            if fullname.lower().strip() in eligible_names:
                return voter_list
        return None
        
    def clean(self):
        """Validate that the voter's name is in the eligible lists"""
        eligible_list = self.is_eligible_voter(self.fullname)
        if not eligible_list:
            raise ValidationError(
                "The name you provided is not found in our registered voter list. "
                "Please contact the administrator if you believe this is an error."
            )
        # Automatically assign the registered list
        self.registered_list = eligible_list
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)