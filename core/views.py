import json
import pandas as pd
import google.generativeai as genai
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .forms import ProdutoForm, ClienteForm, VendaForm, ContaReceberForm, ContaPagarForm, CategoriaForm, FornecedorForm 
from .models import Produto, Cliente, Venda, ContaReceber, ContaPagar, Categoria, Fornecedor
from datetime import date, timedelta
from decimal import Decimal


def dashboard_view(request):

    total_vendas = Venda.objects.all().count()

    receita_faturada = Venda.objects.filter(status='CONCLUIDA').aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    receita_recebida = ContaReceber.objects.filter(status='RECEBIDO').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    vendas_pendentes_count = Venda.objects.filter(status='PENDENTE').count()
    vendas_concluidas_count = Venda.objects.filter(status='CONCLUIDA').count()
    
    contas_receber_em_aberto_valor = ContaReceber.objects.filter(
        status__in=['ABERTO', 'ATRASADO']
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    contas_receber_em_aberto_count = ContaReceber.objects.filter(
        status__in=['ABERTO', 'ATRASADO']
    ).count()

    contas_pagar_em_aberto_valor = ContaPagar.objects.filter(
        status__in=['ABERTO', 'ATRASADO']
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    contas_pagar_em_aberto_count = ContaPagar.objects.filter(
        status__in=['ABERTO', 'ATRASADO']
    ).count()

    receita_por_mes = ContaReceber.objects.filter(
        status='RECEBIDO'
    ).annotate(
        mes_ano=TruncMonth('data_recebimento')
    ).values('mes_ano').annotate(
        total_recebido=Sum('valor')
    ).order_by('mes_ano')

    labels = [r['mes_ano'].strftime('%m/%Y') for r in receita_por_mes]
    data = [float(r['total_recebido']) for r in receita_por_mes]

    chart_data = {
        'labels': labels,
        'data': data,
    }

    produtos_mais_vendidos = Venda.objects.values('produto__nome').annotate(
        total_quantidade_vendida=Sum('quantidade')
    ).order_by('-total_quantidade_vendida')[:5]

    context = {
        'total_vendas': total_vendas,
        'receita_faturada': receita_faturada,
        'receita_recebida': receita_recebida,
        'vendas_pendentes_count': vendas_pendentes_count,
        'vendas_concluidas_count': vendas_concluidas_count,
        'contas_receber_em_aberto_valor': contas_receber_em_aberto_valor,
        'contas_receber_em_aberto_count': contas_receber_em_aberto_count,
        'contas_pagar_em_aberto_valor': contas_pagar_em_aberto_valor, 
        'contas_pagar_em_aberto_count': contas_pagar_em_aberto_count, 
        'chart_data_json': json.dumps(chart_data),
        'produtos_mais_vendidos': produtos_mais_vendidos,
    }
    return render(request, 'core/dashboard.html', context)


def lista_categorias_view(request): # Renomeado
    categorias = Categoria.objects.all()
    return render(request, 'core/lista_categorias.html', {'categorias': categorias})

def categoria_form_view(request, pk=None):
    if pk:
        instance = get_object_or_404(Categoria, pk=pk)
        titulo = "Editar Categoria"
    else:
        instance = None
        titulo = "Adicionar Categoria"

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('lista_categorias')
    else:
        form = CategoriaForm(instance=instance)

    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo})

def categoria_delete_view(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        return redirect('lista_categorias')
    return render(request, 'core/confirm_delete.html', {'instance': categoria, 'titulo': 'Deletar Categoria'})

# --- Views de CRUD para Fornecedor ---
def lista_fornecedores_view(request): # Renomeado
    fornecedores = Fornecedor.objects.all()
    return render(request, 'core/lista_fornecedores.html', {'fornecedores': fornecedores})

def fornecedor_form_view(request, pk=None):
    if pk:
        instance = get_object_or_404(Fornecedor, pk=pk)
        titulo = "Editar Fornecedor"
    else:
        instance = None
        titulo = "Adicionar Fornecedor"

    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('lista_fornecedores')
    else:
        form = FornecedorForm(instance=instance)

    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo})

def fornecedor_delete_view(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        fornecedor.delete()
        return redirect('lista_fornecedores')
    return render(request, 'core/confirm_delete.html', {'instance': fornecedor, 'titulo': 'Deletar Fornecedor'})


def lista_produtos_view(request):
    produtos = Produto.objects.all().select_related('categoria', 'fornecedor')
    return render(request, 'core/lista_produtos.html', {'produtos': produtos})

def produto_form_view(request, pk=None):
    if pk:
        instance = get_object_or_404(Produto, pk=pk)
        titulo = "Editar Produto"
    else:
        instance = None
        titulo = "Adicionar Produto" # Mudado de 'produto_novo' para 'Adicionar Produto' para a UI

    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('lista_produtos')
    else:
        form = ProdutoForm(instance=instance)

    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo})

def produto_delete_view(request, pk): # Adicionado
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        produto.delete()
        return redirect('lista_produtos')
    return render(request, 'core/confirm_delete.html', {'instance': produto, 'titulo': 'Deletar Produto'})


# --- Views de CRUD para Cliente ---
def lista_clientes_view(request): # Renomeado
    clientes = Cliente.objects.all()
    return render(request, 'core/lista_clientes.html', {'clientes': clientes})

def cliente_form_view(request, pk=None):
    if pk:
        instance = get_object_or_404(Cliente, pk=pk)
        titulo = "Editar Cliente"
    else:
        instance = None
        titulo = "Adicionar Cliente" # Mudado de 'cliente_novo' para 'Adicionar Cliente' para a UI

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=instance)

    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo})

def cliente_delete_view(request, pk): # Adicionado
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'core/confirm_delete.html', {'instance': cliente, 'titulo': 'Deletar Cliente'})


# --- Views de CRUD para Venda ---
def lista_vendas_view(request): # Renomeado
    vendas = Venda.objects.all().select_related('produto', 'cliente').order_by('-data_venda')
    return render(request, 'core/lista_vendas.html', {'vendas': vendas})

def venda_form_view(request, pk=None):
    product_prices = {str(p.id): float(p.preco_venda) for p in Produto.objects.all()}

    if pk:
        instance = get_object_or_404(Venda, pk=pk)
        titulo = "Editar Venda"
    else:
        instance = None
        titulo = "Registrar Nova Venda"

    print(f"\nDEBUG: Método da requisição: {request.method}")
    if request.method == 'POST':
        print("Dados POST recebidos:", request.POST)
        form = VendaForm(request.POST, instance=instance)

        if form.is_valid():
            print("DEBUG: Formulário de Venda é válido.")
            venda = form.save(commit=False)
            produto = venda.produto 

            # Lógica de controle de estoque (sem alterações aqui, parece ok)
            if instance: # Se for uma edição
                old_venda = Venda.objects.get(pk=instance.pk)
                if old_venda.produto == produto: # Mesmo produto
                    if venda.quantidade > old_venda.quantidade: # Aumentou a quantidade
                        if produto.quantidade_estoque < (venda.quantidade - old_venda.quantidade):
                            form.add_error('quantidade', f"Estoque insuficiente. Apenas {produto.quantidade_estoque} unidades disponíveis para adicionar.")
                            return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo, 'product_prices_json': json.dumps(product_prices)})
                    elif venda.quantidade < old_venda.quantidade: # Diminuiu a quantidade
                        produto.quantidade_estoque += (old_venda.quantidade - venda.quantidade) # Ajuste de estoque se a quantidade DIMINUIU
                else: # Produto foi alterado
                    # Devolve estoque do produto antigo
                    old_venda.produto.quantidade_estoque += old_venda.quantidade
                    old_venda.produto.save()
                    # Retira estoque do novo produto
                    if produto.quantidade_estoque < venda.quantidade:
                        form.add_error('quantidade', f"Estoque insuficiente para o novo produto. Apenas {produto.quantidade_estoque} unidades disponíveis.")
                        return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo, 'product_prices_json': json.dumps(product_prices)})
                    produto.quantidade_estoque -= venda.quantidade
            else: # Nova venda
                if produto.quantidade_estoque < venda.quantidade:
                    form.add_error('quantidade', f"Estoque insuficiente. Apenas {produto.quantidade_estoque} unidades disponíveis.")
                    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo, 'product_prices_json': json.dumps(product_prices)})
                produto.quantidade_estoque -= venda.quantidade

            # Salvar o produto e a venda DEPOIS de toda a lógica de estoque
            produto.save()
            print(f"DEBUG: Estoque do produto {produto.nome} atualizado para {produto.quantidade_estoque}.")
            venda.save() # Salva a venda no banco de dados
            print(f"DEBUG: Venda salva no banco de dados com PK: {venda.pk}")
            print(f"DEBUG: Status da venda APÓS save(): {venda.status}") # <-- NOVO PRINT IMPORTANTÍSSIMO
            print(f"DEBUG: Forma de pagamento da venda: {venda.forma_pagamento}") # <-- NOVO PRINT
            print(f"DEBUG: Condição de prazo da venda: {venda.condicao_prazo}") # <-- NOVO PRINT

            # --- LÓGICA DE CRIAÇÃO/ATUALIZAÇÃO DE CONTA A RECEBER ---
            if venda.status == 'CONCLUIDA':
                print("DEBUG: Venda CONCLUIDA. Processando Conta a Receber.")
                
                # Definições padrão para CR
                data_vencimento = date.today()
                status_cr = 'ABERTO' 
                data_recebimento_cr = None

                # Ajusta data de vencimento se for a prazo
                if venda.forma_pagamento == 'AP' and venda.condicao_prazo:
                    print(f"DEBUG: Venda a Prazo ({venda.condicao_prazo}). Calculando data de vencimento.")
                    if venda.condicao_prazo == '7D':
                        data_vencimento += timedelta(days=7)
                    elif venda.condicao_prazo == '14D':
                        data_vencimento += timedelta(days=14)
                    elif venda.condicao_prazo == '28D':
                        data_vencimento += timedelta(days=28)
                
                # Se for à vista, muda status e data de recebimento
                if venda.forma_pagamento == 'AV':
                    print("DEBUG: Venda à Vista. Definindo Conta a Receber como RECEBIDO.")
                    status_cr = 'RECEBIDO' 
                    data_recebimento_cr = date.today() 

                try:
                    print(f"DEBUG: Tentando obter ou criar Conta a Receber para venda PK: {venda.pk}.")
                    conta_receber, created = ContaReceber.objects.get_or_create(
                        venda=venda,
                        defaults={
                            'cliente': venda.cliente,
                            'descricao': f"Recebimento de Venda #{venda.pk} - {venda.produto.nome}",
                            'valor': venda.valor_total,
                            'data_vencimento': data_vencimento,
                            'status': status_cr,
                            'data_recebimento': data_recebimento_cr
                        }
                    )
                    if not created:
                        # Se não foi criada (já existia), atualiza os campos
                        conta_receber.cliente = venda.cliente
                        conta_receber.descricao = f"Recebimento de Venda #{venda.pk} - {venda.produto.nome}"
                        conta_receber.valor = venda.valor_total
                        conta_receber.data_vencimento = data_vencimento
                        conta_receber.status = status_cr
                        conta_receber.data_recebimento = data_recebimento_cr
                        conta_receber.save()
                        print(f"DEBUG: Conta a Receber existente ATUALIZADA para venda PK: {venda.pk}.")
                    else:
                        print(f"DEBUG: Nova Conta a Receber CRIADA para venda PK: {venda.pk}.")
                except Exception as e:
                    print(f"ERROR: Erro crítico ao criar/atualizar ContaReceber para venda PK {venda.pk}: {e}") # <-- Capture qualquer erro aqui
            
            # Lógica para DELETAR ContaReceber se a venda era CONCLUIDA e foi para PENDENTE
            elif instance and instance.status == 'CONCLUIDA' and venda.status == 'PENDENTE':
                print("DEBUG: Venda alterada de CONCLUIDA para PENDENTE. Excluindo Conta a Receber existente.")
                try:
                    conta_receber = ContaReceber.objects.get(venda=venda)
                    conta_receber.delete()
                    print(f"DEBUG: Conta a Receber excluída para venda PK: {venda.pk}.")
                except ContaReceber.DoesNotExist:
                    print(f"DEBUG: Nenhuma Conta a Receber encontrada para exclusão para venda PK: {venda.pk}.")
            else:
                print(f"DEBUG: Venda com status '{venda.status}' não acionou a lógica de Conta a Receber (ou já foi processada/excluída).")

            print("DEBUG: Redirecionando para lista_vendas.")
            return redirect('lista_vendas') 
        else:
            print("DEBUG: Formulário de Venda NÃO é válido. Erros:", form.errors)
            print("DEBUG: Dados POST que causaram o erro:", request.POST)
            return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo, 'product_prices_json': json.dumps(product_prices)})
    else:
        form = VendaForm(instance=instance)

    context = {
        'form': form,
        'titulo': titulo,
        'product_prices_json': json.dumps(product_prices)
    }
    return render(request, 'core/form_generico.html', context)

def venda_delete_view(request, pk): # Adicionado
    venda = get_object_or_404(Venda, pk=pk)
    if request.method == 'POST':
        produto = venda.produto
        produto.quantidade_estoque += venda.quantidade
        produto.save()
        
        try:
            conta_receber = ContaReceber.objects.get(venda=venda)
            conta_receber.delete()
        except ContaReceber.DoesNotExist:
            pass
            
        venda.delete()
        return redirect('lista_vendas')
    return render(request, 'core/confirm_delete.html', {'instance': venda, 'titulo': 'Deletar Venda'})


def lista_contas_receber_view(request):
    print("\nDEBUG: Acessando lista_contas_receber_view.") # Debug point 1
    
    contas = ContaReceber.objects.all().select_related('venda__produto', 'cliente', 'venda').order_by('-data_vencimento')
    
    print(f"DEBUG: Total de Contas a Receber carregadas: {contas.count()}") # Debug point 2
    
    if contas.exists():
        print("DEBUG: Detalhes das Contas a Receber carregadas:")
        for conta in contas:
            # Note o uso de .pk para IDs e .valor para o campo Decimal
            print(f"DEBUG: CR ID: {conta.pk}, Venda PK: {conta.venda.pk if conta.venda else 'N/A'}, Cliente: {conta.cliente.nome if conta.cliente else 'N/A'}, Valor: {conta.valor}, Status: {conta.status}, Vencimento: {conta.data_vencimento}") # Debug point 3
    else:
        print("DEBUG: Nenhuma Conta a Receber encontrada no banco de dados.") # Debug point 4

    context = {
        'contas': contas, # Usando 'contas' como o nome da variável no template
        'titulo': 'Contas a Receber',
        'ativo_cr': 'active', # Adicione se estiver usando para realçar o link no menu
    }
    print("DEBUG: Contexto para template de Contas a Receber preparado.") # Debug point 5
    return render(request, 'core/lista_contas_receber.html', context)

def conta_receber_form_view(request, pk=None):
    if pk:
        instance = get_object_or_404(ContaReceber, pk=pk)
        titulo = "Editar Conta a Receber"
    else:
        instance = None
        titulo = "Adicionar Conta a Receber" # Mudado de 'conta_receber_nova' para 'Adicionar Conta a Receber' para a UI

    if request.method == 'POST':
        form = ContaReceberForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('lista_contas_receber')
    else:
        form = ContaReceberForm(instance=instance)

    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo})

def conta_receber_delete_view(request, pk): # Adicionado
    conta = get_object_or_404(ContaReceber, pk=pk)
    if request.method == 'POST':
        conta.delete()
        return redirect('lista_contas_receber')
    return render(request, 'core/confirm_delete.html', {'instance': conta, 'titulo': 'Deletar Conta a Receber'})

@csrf_exempt # Para permitir POST sem token CSRF para esta função simples de marcar
def marcar_conta_receber_recebida(request, pk):
    if request.method == 'GET':
        conta = get_object_or_404(ContaReceber, pk=pk)
        if conta.status == 'ABERTO' or conta.status == 'ATRASADO':
            conta.status = 'RECEBIDO'
            conta.data_recebimento = date.today()
            conta.save()
            return JsonResponse({'status': 'success', 'message': 'Conta marcada como recebida.'})
        return JsonResponse({'status': 'info', 'message': 'A conta já foi recebida ou cancelada.'})
    return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)



def lista_contas_pagar_view(request): # Renomeado
    contas = ContaPagar.objects.all().select_related('fornecedor').order_by('-data_vencimento')
    context ={
        'contas_pagar': contas,
        'titulo': 'Contas a Pagar',
        'ativo_cp': 'active', # Adicione se estiver usando para realçar o link no menu
    }
    return render(request, 'core/lista_contas_pagar.html', context)

def conta_pagar_form_view(request, pk=None):
    if pk:
        instance = get_object_or_404(ContaPagar, pk=pk)
        titulo = "Editar Conta a Pagar"
    else:
        instance = None
        titulo = "Adicionar Conta a Pagar" # Mudado de 'conta_pagar_nova' para 'Adicionar Conta a Pagar' para a UI

    if request.method == 'POST':
        form = ContaPagarForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('lista_contas_pagar')
    else:
        form = ContaPagarForm(instance=instance)

    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo})

def conta_pagar_delete_view(request, pk): # Adicionado
    conta = get_object_or_404(ContaPagar, pk=pk)
    if request.method == 'POST':
        conta.delete()
        return redirect('lista_contas_pagar')
    return render(request, 'core/confirm_delete.html', {'instance': conta, 'titulo': 'Deletar Conta a Pagar'})

@csrf_exempt # Para permitir POST sem token CSRF para esta função simples de marcar
def marcar_conta_pagar_paga(request, pk):
    if request.method == 'POST':
        conta = get_object_or_404(ContaPagar, pk=pk)
        if conta.status == 'ABERTO' or conta.status == 'ATRASADO':
            conta.status = 'PAGO'
            conta.data_pagamento = date.today()
            conta.save()
            return JsonResponse({'status': 'success', 'message': 'Conta marcada como paga.'})
        return JsonResponse({'status': 'info', 'message': 'A conta já foi paga ou cancelada.'})
    return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)


@csrf_exempt
def ask_api_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question')

            print(f"DEBUG: Pergunta recebida: '{question}'") # Debug point 1

            if not question:
                print("ERROR: Nenhuma pergunta fornecida.") # Debug point 2
                return JsonResponse({'error': 'Nenhuma pergunta fornecida.'}, status=400)

            # --- Início do bloco principal de lógica ---
            try:
                vendas_queryset = Venda.objects.select_related('produto', 'cliente')
                contas_receber_queryset = ContaReceber.objects.select_related('venda__produto', 'cliente', 'venda')
                contas_pagar_queryset = ContaPagar.objects.select_related('fornecedor')

                print("DEBUG: Querysets de dados obtidos.") # Debug point 3

                dados_vendas = []
                for v in vendas_queryset:
                    dados_vendas.append({
                        "tipo_registro": "Venda",
                        "id_origem": v.pk,
                        "produto_nome": v.produto.nome if v.produto else "N/A",
                        "cliente_nome": v.cliente.nome if v.cliente else "Consumidor Final",
                        "quantidade_vendida": v.quantidade,
                        "valor_total_venda": float(v.valor_total),
                        "data_transacao": v.data_venda.strftime('%Y-%m-%d'),
                        "status_venda": v.get_status_display(),
                        "forma_pagamento": v.get_forma_pagamento_display(),
                        "condicao_prazo": v.get_condicao_prazo_display() if v.condicao_prazo else "À Vista",
                        "valor_conta_receber": None,
                        "status_conta_receber": None,
                        "data_vencimento_receber": None,
                        "data_recebimento": None,
                        "fornecedor_nome": None,
                        "valor_conta_pagar": None,
                        "status_conta_pagar": None,
                        "data_vencimento_pagar": None,
                        "data_pagamento": None,
                    })

                dados_contas_receber = []
                for cr in contas_receber_queryset:
                    produto_nome_venda = cr.venda.produto.nome if cr.venda and cr.venda.produto else "N/A"
                    cliente_nome_cr = cr.cliente.nome if cr.cliente else (cr.venda.cliente.nome if cr.venda and cr.venda.cliente else "Consumidor Final")

                    dados_contas_receber.append({
                        "tipo_registro": "ContaReceber",
                        "id_origem": cr.pk,
                        "produto_nome": produto_nome_venda,
                        "cliente_nome": cliente_nome_cr,
                        "quantidade_vendida": cr.venda.quantidade if cr.venda else None,
                        "valor_total_venda": float(cr.venda.valor_total) if cr.venda and cr.venda.valor_total is not None else None, # Ajuste para Decimal
                        "data_transacao": cr.venda.data_venda.strftime('%Y-%m-%d') if cr.venda else None,
                        "status_venda": cr.venda.get_status_display() if cr.venda else None,
                        "forma_pagamento": cr.venda.get_forma_pagamento_display() if cr.venda else None,
                        "condicao_prazo": cr.venda.get_condicao_prazo_display() if cr.venda and cr.venda.condicao_prazo else "À Vista",
                        "valor_conta_receber": float(cr.valor),
                        "status_conta_receber": cr.get_status_display(),
                        "data_vencimento_receber": cr.data_vencimento.strftime('%Y-%m-%d'),
                        "data_recebimento": cr.data_recebimento.strftime('%Y-%m-%d') if cr.data_recebimento else None,
                        "fornecedor_nome": None,
                        "valor_conta_pagar": None,
                        "status_conta_pagar": None,
                        "data_vencimento_pagar": None,
                        "data_pagamento": None,
                    })

                dados_contas_pagar = []
                for cp in contas_pagar_queryset:
                    fornecedor_nome_cp = cp.fornecedor.nome_empresa if cp.fornecedor else "N/A"

                    dados_contas_pagar.append({
                        "tipo_registro": "ContaPagar",
                        "id_origem": cp.pk,
                        "produto_nome": None,
                        "cliente_nome": None,
                        "quantidade_vendida": None,
                        "valor_total_venda": None,
                        "data_transacao": None,
                        "status_venda": None,
                        "forma_pagamento": None,
                        "condicao_prazo": None,
                        "valor_conta_receber": None,
                        "status_conta_receber": None,
                        "data_vencimento_receber": None,
                        "data_recebimento": None,
                        "fornecedor_nome": fornecedor_nome_cp,
                        "valor_conta_pagar": float(cp.valor),
                        "status_conta_pagar": cp.get_status_display(),
                        "data_vencimento_pagar": cp.data_vencimento.strftime('%Y-%m-%d'),
                        "data_pagamento": cp.data_pagamento.strftime('%Y-%m-%d') if cp.data_pagamento else None,
                    })

                df = pd.DataFrame(dados_vendas + dados_contas_receber + dados_contas_pagar)
                print(f"DEBUG: DataFrame criado com {len(df)} linhas.") # Debug point 4

                if df.empty:
                    print("DEBUG: DataFrame vazio, retornando mensagem sem dados.") # Debug point 5
                    return JsonResponse({'answer': 'Não há dados de vendas ou contas para analisar.'})

                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-2.0-flash')
                print("DEBUG: Modelo Gemini configurado.") # Debug point 6

                prompt_content = create_code_generation_prompt(question, df.columns.to_list())
                print(f"DEBUG: Prompt gerado para Gemini: \n{prompt_content[:500]}...") # Debug point 7 (primeiros 500 chars)

                response_content = model.generate_content(prompt_content)
                print(f"DEBUG: Resposta bruta do Gemini: {response_content.text}") # Debug point 8

                parts = response_content.text.strip().split('---RESPOSTA---')

                if len(parts) != 2:
                    error_message = f"Formato de resposta inesperado do modelo de IA. Resposta bruta: {response_content.text}"
                    print(f"ERROR: {error_message}") # Debug point 9
                    return JsonResponse({'error': error_message}, status=500)

                generated_code = parts[0].strip().replace("```python", "").replace("```", "").strip()
                response_template = parts[1].strip()

                print(f"DEBUG: Código gerado pela IA: ```python\n{generated_code}\n```") # Debug point 10
                print(f"DEBUG: Template de resposta da IA: '{response_template}'") # Debug point 11

                execution_globals = {"pd": pd, "df": df}
                execution_locals = {'result': None} # Inicialize 'result' para garantir que sempre exista
                
                calculated_result = "Valor não definido pelo código gerado." # Inicializa antes do try/except do exec

                exec(generated_code, execution_globals, execution_locals)
                calculated_result = execution_locals['result'] # Agora sabemos que 'result' existe
                
                print(f"DEBUG: Resultado do código executado: {calculated_result}") # Debug point 12

                formatted_result = str(calculated_result)
                if isinstance(calculated_result, (int, float, Decimal)):
                    # A condição foi ajustada para ser mais específica para valores monetários.
                    # Removido 'total' da verificação aqui.
                    if "R$" in response_template or "valor" in question.lower() or "receita" in question.lower() or "custo" in question.lower() or "montante" in question.lower():
                        formatted_result = f"R$ {float(calculated_result):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    else:
                        # Para contagens ou outros números não monetários, formata como número inteiro
                        formatted_result = f"{int(calculated_result):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                elif isinstance(calculated_result, dict):
                    formatted_result = "\n" + "\n".join([f"- {k}: {v}" for k, v in calculated_result.items()])
                elif calculated_result is None or (isinstance(calculated_result, pd.Series) and calculated_result.empty):
                    formatted_result = "0" if ("R$" in response_template or "valor" in question.lower() or "custo" in question.lower() or "montante" in question.lower()) else "N/A"
                
                print(f"DEBUG: Resultado formatado: '{formatted_result}'") # Debug point 13

                final_answer = response_template.format(result=formatted_result)
                print(f"DEBUG: Resposta final: '{final_answer}'") # Debug point 14
                
                return JsonResponse({'answer': final_answer})

            except Exception as e_main_logic:
                # Este é o catch para qualquer erro dentro do bloco principal de lógica antes do JSON final
                error_message_main = f'Ocorreu um erro inesperado na lógica principal do chatbot: {type(e_main_logic).__name__}: {e_main_logic}'
                print(f"CRITICAL ERROR (e_main_logic): {error_message_main}") # Debug point 16
                return JsonResponse({'error': error_message_main}, status=500)
            # --- Fim do bloco principal de lógica ---

        except json.JSONDecodeError as e_json:
            error_message_json = f'Erro ao decodificar JSON na requisição: {e_json}'
            print(f"ERROR (e_json): {error_message_json}") # Debug point 17
            return JsonResponse({'error': error_message_json}, status=400)
        except Exception as e_outer:
            # Este é o catch para erros muito iniciais (ex: request.body)
            error_message_outer = f'Ocorreu um erro no servidor antes do processamento da pergunta: {type(e_outer).__name__}: {e_outer}'
            print(f"CRITICAL ERROR (e_outer): {error_message_outer}") # Debug point 18
            return JsonResponse({'error': error_message_outer}, status=500)

    print("DEBUG: Método não permitido.") # Debug point 19
    return JsonResponse({'error': 'Método não permitido.'}, status=405)


def create_code_generation_prompt(question, columns):
    column_list = ", ".join([f"'{col}'" for col in columns])
    prompt = f"""
    Você é um assistente de programação analítica que converte perguntas em código Python Pandas e, em seguida, gera uma frase de resposta amigável que incorpora o resultado.
    
    O DataFrame disponível se chama `df` e possui as seguintes colunas: [{column_list}].
    Este DataFrame pode conter três tipos de registros, identificados pela coluna 'tipo_registro': 'Venda', 'ContaReceber' ou 'ContaPagar'.
    
    **Colunas e Suas Definições Cruciais:**
    - 'tipo_registro': Indica se a linha é uma 'Venda', 'ContaReceber' ou 'ContaPagar'. Use para filtrar.
    - 'produto_nome': Nome do produto (para 'Venda' e 'ContaReceber' associada a venda).
    - 'cliente_nome': Nome do cliente (para 'Venda' e 'ContaReceber').
    - 'fornecedor_nome': Nome do fornecedor (para 'ContaPagar').
    - 'quantidade_vendida': Quantidade de itens em uma transação de 'Venda'.
    - 'valor_total_venda': Valor total monetário de uma 'Venda' (Receita Faturada).
    - 'status_venda': Status da 'Venda' ('Pendente', 'Concluída').
    - 'forma_pagamento': Forma de pagamento da 'Venda' ('À Vista', 'A Prazo').
    - 'condicao_prazo': Condição de prazo da 'Venda' ('7 Dias', '14 Dias', '28 Dias', 'À Vista').
    - 'valor_conta_receber': Valor monetário de uma 'ContaReceber'.
    - 'status_conta_receber': Status da 'ContaReceber' ('ABERTO', 'RECEBIDO', 'ATRASADO', 'CANCELADO'). 
    - 'data_transacao': Data da 'Venda' (YYYY-MM-DD).
    - 'data_vencimento_receber': Data de vencimento da 'ContaReceber' (YYYY-MM-DD).
    - 'data_recebimento': Data em que a 'ContaReceber' foi recebida (YYYY-MM-DD ou None).
    - 'valor_conta_pagar': Valor monetário de uma 'ContaPagar'.
    - 'status_conta_pagar': Status da 'ContaPagar' ('ABERTO', 'PAGO', 'ATRASADO', 'CANCELADO'). 
    - 'data_vencimento_pagar': Data de vencimento da 'ContaPagar' (YYYY-MM-DD).
    - 'data_pagamento': Data em que a 'ContaPagar' foi paga (YYYY-MM-DD ou None).

    **Instruções Cruciais para o CÓDIGO:**
    - O código deve ser UMA ÚNICA LINHA Python.
    - O resultado do cálculo deve ser armazenado na variável `result`.
    - Use `df` como seu DataFrame.
    - NÃO inclua imports (ex: `import pandas`).
    - Converta colunas de data (ex: 'data_transacao', 'data_recebimento', 'data_vencimento_receber', 'data_pagamento', 'data_vencimento_pagar') para datetime usando `pd.to_datetime()` se precisar de operações de data ou filtragem por período. Lembre-se de lidar com valores `None` ou `NaT` após a conversão, usando `.dropna()` ou verificações `notna()`.
    - Para contar itens, use `len()`. Para somar valores, use `.sum()`.
    
    **Instruções Cruciais para a RESPOSTA:**
    - A resposta deve ser uma frase amigável e direta.
    - **IMPERATIVO: Use o placeholder EXATAMENTE `{{result}}` (minúsculo) onde o valor calculado será inserido.**
    - Após o código, adicione a string `---RESPOSTA---` e, em seguida, a sua frase de resposta.

    **Exemplos:**

    Pergunta: "Qual a receita recebida total?"
    Código: result = df[(df['tipo_registro'] == 'ContaReceber') & (df['status_conta_receber'] == 'RECEBIDO')]['valor_conta_receber'].sum()
    ---RESPOSTA---A receita total que já foi recebida é de {{result}}.

    Pergunta: "Quantas vendas a prazo foram feitas?"
    Código: result = len(df[(df['tipo_registro'] == 'Venda') & (df['forma_pagamento'] == 'AP')])
    ---RESPOSTA---Foram realizadas {{result}} vendas a prazo.

    Pergunta: "Qual o valor das contas a receber que estão em aberto?"
    Código: result = df[(df['tipo_registro'] == 'ContaReceber') & df['status_conta_receber'].isin(['ABERTO', 'ATRASADO'])]['valor_conta_receber'].sum()
    ---RESPOSTA---O valor total das contas a receber em aberto é de {{result}}.

    Pergunta: "Quais os 3 produtos mais vendidos?"
    Código: result = df[df['tipo_registro'] == 'Venda'].groupby('produto_nome')['quantidade_vendida'].sum().nlargest(3).to_dict()
    ---RESPOSTA---Os 3 produtos mais vendidos foram: {{result}}.

    Pergunta: "Quantas vendas concluídas?"
    Código: result = len(df[(df['tipo_registro'] == 'Venda') & (df['status_venda'] == 'CONCLUIDA')])
    ---RESPOSTA---O número de vendas concluídas é de {{result}}.

    Pergunta: "Qual o valor das vendas feitas à vista?"
    Código: result = df[(df['tipo_registro'] == 'Venda') & (df['forma_pagamento'] == 'AV')]['valor_total_venda'].sum()
    ---RESPOSTA---O valor total das vendas feitas à vista foi de {{result}}.

    Pergunta: "Qual o total de contas a pagar em aberto?"
    Código: result = df[(df['tipo_registro'] == 'ContaPagar') & df['status_conta_pagar'].isin(['ABERTO', 'ATRASADO'])]['valor_conta_pagar'].sum()
    ---RESPOSTA---O total de contas a pagar em aberto é de {{result}}.

    Pergunta: "Qual o número de clientes cadastrados?"
    Código: result = len(df[df['tipo_registro'] == 'Venda']['cliente_nome'].unique())
    ---RESPOSTA---Existem {{result}} clientes únicos registrados através das vendas.

    **Pergunta do Usuário:**
    {question}

    **Seu Código (apenas uma linha), seguido por ---RESPOSTA--- e a frase:**
    """
    return prompt