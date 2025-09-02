from django import forms
from .utils import get_files, get_column_names

class UploadFileForm(forms.Form):
    file = forms.FileField(label='CSV File')
    filename = forms.CharField(label='Filename', max_length=100, initial='DataFrame')
    header = forms.IntegerField(label='Column names (1, 2, 3...)', required=False, initial=-1)
    delimiter = forms.ChoiceField(
        label="Separator",
        choices=[
            (',', 'Comma (,)'),
            (';', 'Semicolon (;)'),
            ('\t', 'Tab (\\t)'),
        ],
        initial=',',
    )
    skip_rows = forms.IntegerField(label='Number of rows to skip', required=False, initial=0)
    custom_columns = forms.CharField(label='Custom column names seperated by ","', required=False)


class EditChooseForm(forms.Form):
    files = forms.ChoiceField(choices=[], label="Choose File", required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["files"].choices = ((f, f) for f in get_files())
        


class EditActionsForm(forms.Form):
    """
    Remember to update list on the bottom of this file
    """
    new_name = forms.CharField(initial=None, required=False, max_length=100)
    drops = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Choose columns to drop"
    )
    target = forms.ChoiceField(choices=[], label="Choose target column", required=True)
    delete_old = forms.BooleanField(initial=False, required=False, widget=forms.CheckboxInput)

    TYPES = [
        ('', 'Do not change'),
        ('int', 'Integer'),
        ('float', 'Float'),
        ('str', 'String'),
        ('bool', 'Boolean'),
        ('category', 'Category'),
        ('datetime', 'Date'),
    ]
        
    def __init__(self, filename=None, *args, **kwawrgs):
        super().__init__(*args, **kwawrgs)
        if filename:
            columns = [(c, c) for c in get_column_names(filename)]
            self.fields["target"].choices = columns
            # Drops
            self.fields["drops"].choices = columns
            
            # Change Types
            for col, _ in columns:
                self.fields[col] = forms.ChoiceField(
                    choices = self.TYPES,
                    label = f"New type - {col}",
                    required=False,
                    initial=self.TYPES[0][0]
                )
            

EXCLUDED_FIELDS = ["new_name", "drops", "delete_old", "target"]