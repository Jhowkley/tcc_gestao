# core/forms.py
from django import forms
from .models import Produto, Cliente, Venda, ContaReceber, ContaPagar, Categoria, Fornecedor

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = '__all__'

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = '__all__'

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = '__all__'
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'endereco': forms.Textarea(attrs={'rows': 3}),
        }

class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ['produto', 'cliente', 'quantidade', 'status', 'forma_pagamento', 'condicao_prazo']

class ContaReceberForm(forms.ModelForm):
    class Meta:
        model = ContaReceber
        fields = '__all__'
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date'}),
            'data_recebimento': forms.DateInput(attrs={'type': 'date'}),
        }

class ContaPagarForm(forms.ModelForm):
    class Meta:
        model = ContaPagar
        fields = '__all__'
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
        }