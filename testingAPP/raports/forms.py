from django import forms
from .utils import get_files

class StandardReportForm(forms.Form):
    files = forms.ChoiceField(choices=[], label="Choose File", required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["files"].choices = ((f, f) for f in get_files())