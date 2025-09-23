# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    

    path('categorias/', views.lista_categorias_view, name='lista_categorias'), 
    path('categorias/novo/', views.categoria_form_view, name='categoria_novo'), 
    path('categorias/<int:pk>/editar/', views.categoria_form_view, name='categoria_editar'),
    path('categorias/<int:pk>/deletar/', views.categoria_delete_view, name='categoria_deletar'), 
    
    # URLs de Produto
    path('produtos/', views.lista_produtos_view, name='lista_produtos'),
    path('produtos/novo/', views.produto_form_view, name='produto_novo'),
    path('produtos/<int:pk>/editar/', views.produto_form_view, name='produto_editar'),
    path('produtos/<int:pk>/deletar/', views.produto_delete_view, name='produto_deletar'), 
    
    # URLs de Venda
    path('vendas/', views.lista_vendas_view, name='lista_vendas'),
    path('vendas/nova/', views.venda_form_view, name='venda_nova'),
    path('vendas/<int:pk>/editar/', views.venda_form_view, name='venda_editar'), 
    path('vendas/<int:pk>/deletar/', views.venda_delete_view, name='venda_deletar'), 

    # URLs de Cliente
    path('clientes/', views.lista_clientes_view, name='lista_clientes'),
    path('clientes/novo/', views.cliente_form_view, name='cliente_novo'),
    path('clientes/<int:pk>/editar/', views.cliente_form_view, name='cliente_editar'),
    path('clientes/<int:pk>/deletar/', views.cliente_delete_view, name='cliente_deletar'), 

    # URLs de Fornecedor
    path('fornecedores/', views.lista_fornecedores_view, name='lista_fornecedores'),
    path('fornecedores/novo/', views.fornecedor_form_view, name='fornecedor_novo'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_form_view, name='fornecedor_editar'),
    path('fornecedores/<int:pk>/deletar/', views.fornecedor_delete_view, name='fornecedor_deletar'),
    
    # URLs de Conta a Pagar
    path('contas-a-pagar/', views.lista_contas_pagar_view, name='lista_contas_pagar'),
    path('contas-a-pagar/nova/', views.conta_pagar_form_view, name='conta_pagar_nova'),
    path('contas-a-pagar/<int:pk>/editar/', views.conta_pagar_form_view, name='conta_pagar_editar'),
    path('contas-a-pagar/<int:pk>/pagar/', views.marcar_conta_pagar_paga, name='marcar_conta_pagar_paga'),
    path('contas-a-pagar/<int:pk>/deletar/', views.conta_pagar_delete_view, name='conta_pagar_deletar'), 
    
    # URLs de Conta a Receber
    path('contas-a-receber/', views.lista_contas_receber_view, name='lista_contas_receber'),
    path('contas-a-receber/nova/', views.conta_receber_form_view, name='conta_receber_nova'),
    path('contas-a-receber/<int:pk>/editar/', views.conta_receber_form_view, name='conta_receber_editar'),
    path('contas-a-receber/<int:pk>/receber/', views.marcar_conta_receber_recebida, name='marcar_conta_receber_recebida'),
    path('contas-a-receber/<int:pk>/deletar/', views.conta_receber_delete_view, name='conta_receber_deletar'), 
    
    # URL da API do Chatbot
    path('api/ask/', views.ask_api_view, name='ask_api'),
]