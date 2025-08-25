from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Voter, RegisteredVoter
from .forms import VoterRegistrationForm


def voters(request):
    voters = Voter.objects.all().select_related('registered_list')
    return render(request, "app/voters.html", {"voters": voters})


def voter(request, voter_id):
    voter = get_object_or_404(Voter, id=voter_id)
    return render(request, "app/voter.html", {"voter": voter})


def voter_forms(request):
    if request.method == 'POST':
        form = VoterRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # The model's save method will automatically validate and assign registered_list
                voter = form.save()
                messages.success(
                    request, 
                    f"Registration completed successfully! Welcome, {voter.fullname}."
                )
                return redirect("voter", voter_id=voter.id)
            except ValidationError as e:
                messages.error(request, str(e))
                return render(request, "app/voter_forms.html", {"forms": form})
            except Exception as e:
                messages.error(
                    request, 
                    "An error occurred during registration. Please try again or contact support."
                )
                return render(request, "app/voter_forms.html", {"forms": form})
        else:
            messages.error(request, "Please correct the errors below.")
            return render(request, "app/voter_forms.html", {"forms": form})
    
    # GET request - show empty form
    form = VoterRegistrationForm()
    context = {
        'forms': form,
        'instructions': {
            'title': 'Voter Registration',
            'description': 'Please provide your details below. Your name will be verified against our registered voter list.',
        }
    }
    return render(request, "app/voter_forms.html", context)