# core/admin.py
from django.contrib import admin
from .models import Produto, Venda, Cliente, Fornecedor, ContaPagar, ContaReceber

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'fornecedor', 'preco_venda', 'quantidade_estoque')
    search_fields = ('nome', 'fornecedor__nome_empresa')

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'valor_total', 'data_venda')
    list_filter = ('data_venda', 'produto', 'cliente')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'email')
    search_fields = ('nome', 'email')

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome_empresa', 'contato_nome', 'telefone')
    search_fields = ('nome_empresa', 'contato_nome')

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ('descricao','fornecedor','valor', 'data_vencimento', 'status', 'data_pagamento')
    list_filter = ('status','fornecedor', 'data_vencimento')
    search_fields = ('descricao', 'fornecedor__nome_empresa')
    date_hierarchy = 'data_vencimento'

@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = ('descricao','cliente','valor', 'data_vencimento', 'status', 'data_recebimento')
    list_filter = ('status','cliente', 'venda', 'data_vencimento')
    search_fields = ('descricao', 'cliente__nome', 'venda__produto__nome')
    date_hierarchy = 'data_vencimento'