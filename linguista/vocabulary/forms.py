from django import forms


class BulkAddWordsForm(forms.Form):
    words_input = forms.CharField(
        label='Enter words (separated by spaces)',
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 50})
    )