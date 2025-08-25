from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from django.forms import Textarea
from .models import Voter, RegisteredVoter


class RegisteredVoterAdmin(admin.ModelAdmin):
    """
    Admin interface for managing the list of eligible voters
    """
    model = RegisteredVoter
    list_display = ['id', 'voter_count', 'preview_names']
    list_per_page = 20
    search_fields = ['names']
    
    fieldsets = (
        ('Eligible Voter Names', {
            'fields': ('names',),
            'description': 'Enter each eligible voter name on a separate line. These names will be validated against during voter registration.',
        }),
    )
    
    formfield_overrides = {
        models.TextField: {
            'widget': Textarea(attrs={
                'rows': 15,
                'cols': 60,
                'placeholder': 'Enter each eligible voter name on a separate line:\n\nJohn Smith\nJane Doe\nMichael Johnson\n...',
                'aria-label': 'List of eligible voter names',
                'aria-describedby': 'names-help-text'
            })
        },
    }
    
    def voter_count(self, obj):
        """Display count of eligible voters in this list"""
        if obj.names:
            count = len([name.strip() for name in obj.names.split('\n') if name.strip()])
            return format_html('<strong>{}</strong> eligible voters', count)
        return '0 eligible voters'
    voter_count.short_description = 'Total Eligible Voters'
    voter_count.admin_order_field = 'names'
    
    def preview_names(self, obj):
        """Show preview of first few names"""
        if obj.names:
            names = [name.strip() for name in obj.names.split('\n') if name.strip()]
            if names:
                preview = ', '.join(names[:3])
                if len(names) > 3:
                    preview += f' ... (+{len(names) - 3} more)'
                return preview
        return 'No names added'
    preview_names.short_description = 'Names Preview'
    
    def get_readonly_fields(self, request, obj=None):
        """Make ID readonly for existing objects"""
        if obj:  # editing an existing object
            return ['id'] + list(self.readonly_fields)
        return self.readonly_fields

    class Media:
        css = {
            'all': ('admin/css/enhanced-admin.css',)
        }
        js = ('admin/js/eligible-voters.js',)


class VoterAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for managing registered voters
    """
    model = Voter
    list_display = ['fullname', 'email', 'telephone_link', 'student_id', 'registration_status', 'eligible_list']
    list_filter = ['registered_list', 'email']
    search_fields = ['fullname', 'email', 'telephone', 'student_id']
    list_per_page = 25
    ordering = ['fullname']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('fullname', 'email', 'telephone', 'student_id'),
            'description': 'Basic voter information and contact details.',
        }),
        ('Registration Details', {
            'fields': ('registered_list',),
            'description': 'Select which eligible voter list this person should be validated against.',
            'classes': ('collapse',),  # Make this section collapsible
        }),
    )
    
    readonly_fields = ['registration_status']
    autocomplete_fields = ['registered_list']
    
    # Custom form field attributes for accessibility
    formfield_overrides = {
        models.CharField: {
            'widget': admin.widgets.AdminTextInputWidget(attrs={
                'aria-describedby': 'field-help',
                'autocomplete': 'off'
            })
        },
        models.EmailField: {
            'widget': admin.widgets.AdminEmailInputWidget(attrs={
                'aria-describedby': 'email-help',
                'autocomplete': 'email'
            })
        },
    }
    
    def telephone_link(self, obj):
        """Make phone number clickable"""
        if obj.telephone:
            return format_html(
                '<a href="tel:{}" aria-label="Call {}">{}</a>',
                obj.telephone,
                obj.fullname,
                obj.telephone
            )
        return '-'
    telephone_link.short_description = 'Phone Number'
    telephone_link.admin_order_field = 'telephone'
    
    def registration_status(self, obj):
        """Show registration validation status"""
        if not obj.registered_list or not obj.registered_list.names:
            return format_html('<span style="color: red;">⚠️ No eligible voter list assigned</span>')
        
        eligible_names = [name.strip().lower() for name in obj.registered_list.names.split('\n') if name.strip()]
        if obj.fullname.lower() in eligible_names:
            return format_html('<span style="color: green;">✅ Valid Registration</span>')
        else:
            return format_html('<span style="color: red;">❌ Name not in eligible list</span>')
    registration_status.short_description = 'Status'
    
    def eligible_list(self, obj):
        """Link to the associated eligible voter list"""
        if obj.registered_list:
            url = reverse('admin:app_registeredvoter_change', args=[obj.registered_list.pk])
            return format_html('<a href="{}" aria-label="View eligible voter list {}">List #{}</a>', 
                             url, obj.registered_list.pk, obj.registered_list.pk)
        return '-'
    eligible_list.short_description = 'Eligible List'
    
    actions = ['validate_all_registrations', 'export_voter_data']
    
    # In the validate_all_registrations method:
    def validate_all_registrations(self, request, queryset):
        """Custom admin action to validate selected voters"""
        valid_count = 0
        invalid_count = 0
    
        for voter in queryset:
            if voter.registered_list:
                eligible_names = voter.registered_list.get_eligible_names()
                if voter.fullname.lower() in eligible_names:
                    valid_count += 1
                else:
                    invalid_count += 1
            else:
                invalid_count += 1
    
        message = f"Validation complete: {valid_count} valid registrations, {invalid_count} invalid registrations."
        self.message_user(request, message)
    validate_all_registrations.short_description = "Validate selected voter registrations"

    # In the export_voter_data method:
    def export_voter_data(self, request, queryset):
        """Export voter data as CSV"""
        import csv
        from django.http import HttpResponse
    
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="voters.csv"'
    
        writer = csv.writer(response)
        writer.writerow(['Full Name', 'Email', 'Phone', 'Student ID', 'Status'])
    
        for voter in queryset:
            if voter.registered_list:
                eligible_names = voter.registered_list.get_eligible_names()
                status = 'Valid' if voter.fullname.lower() in eligible_names else 'Invalid'
            else:
                status = 'No List Assigned'
        
            writer.writerow([
                voter.fullname,
                voter.email,
                voter.telephone,
                voter.student_id,
                status
            ])
    
        return response
    export_voter_data.short_description = "Export selected voters as CSV"

    def get_queryset(self, request):
        """Optimize database queries"""
        return super().get_queryset(request).select_related('registered_list')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize foreign key field display"""
        if db_field.name == "registered_list":
            kwargs["queryset"] = RegisteredVoter.objects.all()
            kwargs["empty_label"] = "Select an eligible voter list..."
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {
            'all': ('admin/css/enhanced-admin.css',)
        }
        js = ('admin/js/voter-admin.js',)


# Register models with enhanced admin classes
admin.site.register(RegisteredVoter, RegisteredVoterAdmin)
admin.site.register(Voter, VoterAdmin)

# Customize admin site headers and titles
admin.site.site_header = "Voter Registration Administration"
admin.site.site_title = "Voter Registration Admin"
admin.site.index_title = "Welcome to Voter Registration Administration"