# forms.py
from django import forms
from .models import Account, Transaction, TradeEntry, TradeExit
from django.core.exceptions import ValidationError

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'type', 'currency', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['id'] = f'id_account_{name}'

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['account', 'type', 'amount', 'fee', 'tax', 'date', 'description']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['id'] = f'id_transaction_{name}'
        if user is not None:
            self.fields['account'].queryset = Account.objects.filter(user=user)


class EntryForm(forms.ModelForm):
    gross_amount = forms.DecimalField(required=False, disabled=True, label='Gross Amount')
    net_amount = forms.DecimalField(required=False, disabled=True, label='Net Amount')

    class Meta:
        model = TradeEntry
        fields = ['security', 'account', 'quantity', 'price', 'fee', 'tax','date', 'note']
        widgets = {
            'security': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'step': '0.0001', 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'fee': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'tax': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        #custom fields id
        for name, field in self.fields.items():
            field.widget.attrs['id'] = f'id_entry_{name}'

class ExitForm(forms.ModelForm):
    class Meta:
        model = TradeExit
        fields = ['entry', 'price', 'quantity', 'fee', 'tax', 'date']
        widgets = {
            'entry': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs['id'] = f'id_exit_{name}'

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        entry = self.cleaned_data.get('entry')
        if entry is None:
            raise ValidationError("Entry is required")
        elif entry.remaining_quantity is None:
            raise ValidationError("remaining_quantity is required")
        if entry and quantity > entry.remaining_quantity:
            raise ValidationError("Exit quantity cannot exceed remaining entry quantity.")
        return quantity
