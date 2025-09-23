import json
import re 
import pandas as pd
import google.generativeai as genai
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from sqlglot import logger
from .forms import ProdutoForm, ClienteForm, VendaForm, ContaReceberForm, ContaPagarForm, CategoriaForm, FornecedorForm 
from .models import Produto, Cliente, Venda, ContaReceber, ContaPagar, Categoria, Fornecedor, ChatMessage
from datetime import date, timedelta
from decimal import Decimal
from string import Template
from .prompts import create_intention_prompt
import logging

logger = logging.getLogger(__name__)

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


def lista_categorias_view(request):
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

def lista_fornecedores_view(request): 
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
        titulo = "Adicionar Produto"

    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('lista_produtos')
    else:
        form = ProdutoForm(instance=instance)

    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo})

def produto_delete_view(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        produto.delete()
        return redirect('lista_produtos')
    return render(request, 'core/confirm_delete.html', {'instance': produto, 'titulo': 'Deletar Produto'})


def lista_clientes_view(request):
    clientes = Cliente.objects.all()
    return render(request, 'core/lista_clientes.html', {'clientes': clientes})

def cliente_form_view(request, pk=None):
    if pk:
        instance = get_object_or_404(Cliente, pk=pk)
        titulo = "Editar Cliente"
    else:
        instance = None
        titulo = "Adicionar Cliente" 

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=instance)

    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo})

def cliente_delete_view(request, pk): 
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'core/confirm_delete.html', {'instance': cliente, 'titulo': 'Deletar Cliente'})


def lista_vendas_view(request):
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

            if instance: 
                old_venda = Venda.objects.get(pk=instance.pk)
                if old_venda.produto == produto: 
                    if venda.quantidade > old_venda.quantidade:
                        if produto.quantidade_estoque < (venda.quantidade - old_venda.quantidade):
                            form.add_error('quantidade', f"Estoque insuficiente. Apenas {produto.quantidade_estoque} unidades disponíveis para adicionar.")
                            return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo, 'product_prices_json': json.dumps(product_prices)})
                    elif venda.quantidade < old_venda.quantidade:
                        produto.quantidade_estoque += (old_venda.quantidade - venda.quantidade) 
                else:
                    old_venda.produto.quantidade_estoque += old_venda.quantidade
                    old_venda.produto.save()
                    if produto.quantidade_estoque < venda.quantidade:
                        form.add_error('quantidade', f"Estoque insuficiente para o novo produto. Apenas {produto.quantidade_estoque} unidades disponíveis.")
                        return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo, 'product_prices_json': json.dumps(product_prices)})
                    produto.quantidade_estoque -= venda.quantidade
            else: 
                if produto.quantidade_estoque < venda.quantidade:
                    form.add_error('quantidade', f"Estoque insuficiente. Apenas {produto.quantidade_estoque} unidades disponíveis.")
                    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo, 'product_prices_json': json.dumps(product_prices)})
                produto.quantidade_estoque -= venda.quantidade


            produto.save()
            print(f"DEBUG: Estoque do produto {produto.nome} atualizado para {produto.quantidade_estoque}.")
            venda.save()
            print(f"DEBUG: Venda salva no banco de dados com PK: {venda.pk}")
            print(f"DEBUG: Status da venda APÓS save(): {venda.status}") 
            print(f"DEBUG: Forma de pagamento da venda: {venda.forma_pagamento}") 
            print(f"DEBUG: Condição de prazo da venda: {venda.condicao_prazo}")

            if venda.status == 'CONCLUIDA':
                print("DEBUG: Venda CONCLUIDA. Processando Conta a Receber.")
                
                data_vencimento = date.today()
                status_cr = 'ABERTO' 
                data_recebimento_cr = None
                if venda.forma_pagamento == 'AP' and venda.condicao_prazo:
                    print(f"DEBUG: Venda a Prazo ({venda.condicao_prazo}). Calculando data de vencimento.")
                    if venda.condicao_prazo == '7D':
                        data_vencimento += timedelta(days=7)
                    elif venda.condicao_prazo == '14D':
                        data_vencimento += timedelta(days=14)
                    elif venda.condicao_prazo == '28D':
                        data_vencimento += timedelta(days=28)
                
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
                    print(f"ERROR: Erro crítico ao criar/atualizar ContaReceber para venda PK {venda.pk}: {e}") 
            
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

def venda_delete_view(request, pk):
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
    print("\nDEBUG: Acessando lista_contas_receber_view.") 
    
    contas = ContaReceber.objects.all().select_related('venda__produto', 'cliente', 'venda').order_by('-data_vencimento')
    
    print(f"DEBUG: Total de Contas a Receber carregadas: {contas.count()}") 
    
    if contas.exists():
        print("DEBUG: Detalhes das Contas a Receber carregadas:")
        for conta in contas:
            print(f"DEBUG: CR ID: {conta.pk}, Venda PK: {conta.venda.pk if conta.venda else 'N/A'}, Cliente: {conta.cliente.nome if conta.cliente else 'N/A'}, Valor: {conta.valor}, Status: {conta.status}, Vencimento: {conta.data_vencimento}") # Debug point 3
    else:
        print("DEBUG: Nenhuma Conta a Receber encontrada no banco de dados.")

    context = {
        'contas': contas,
        'titulo': 'Contas a Receber',
        'ativo_cr': 'active', 
    }
    print("DEBUG: Contexto para template de Contas a Receber preparado.") 
    return render(request, 'core/lista_contas_receber.html', context)

def conta_receber_form_view(request, pk=None):
    if pk:
        instance = get_object_or_404(ContaReceber, pk=pk)
        titulo = "Editar Conta a Receber"
    else:
        instance = None
        titulo = "Adicionar Conta a Receber" 

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

@csrf_exempt
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



def lista_contas_pagar_view(request): 
    contas = ContaPagar.objects.all().select_related('fornecedor').order_by('-data_vencimento')
    context ={
        'contas_pagar': contas,
        'titulo': 'Contas a Pagar',
        'ativo_cp': 'active', 
    }
    return render(request, 'core/lista_contas_pagar.html', context)

def conta_pagar_form_view(request, pk=None):
    if pk:
        instance = get_object_or_404(ContaPagar, pk=pk)
        titulo = "Editar Conta a Pagar"
    else:
        instance = None
        titulo = "Adicionar Conta a Pagar" 

    if request.method == 'POST':
        form = ContaPagarForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('lista_contas_pagar')
    else:
        form = ContaPagarForm(instance=instance)

    return render(request, 'core/form_generico.html', {'form': form, 'titulo': titulo})

def conta_pagar_delete_view(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    if request.method == 'POST':
        conta.delete()
        return redirect('lista_contas_pagar')
    return render(request, 'core/confirm_delete.html', {'instance': conta, 'titulo': 'Deletar Conta a Pagar'})

@csrf_exempt 
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
            raw_body = request.body.decode('utf-8')
            logger.info(f"Raw Request Body: {raw_body}")
            data = json.loads(request.body)
            question = data.get('question')
            session_id = data.get('session_id')
            logger.info(f"Parsed Question: '{question}', Parsed Session ID: '{session_id}'")
            print(f"DEBUG: Pergunta recebida: '{question}' para sessão: '{session_id}'")

            if not question or not session_id:
                print("ERROR: Nenhuma pergunta ou session_id fornecido.")
                return JsonResponse({'error': 'Nenhuma pergunta ou ID de sessão fornecido.'}, status=400)

            db_history = ChatMessage.objects.filter(session_id=session_id).order_by('timestamp')
            chat_history_gemini_format = []
            chat_history_for_prompt = []

            for msg in db_history:
                gemini_role = 'user' if msg.role == 'user' else 'model'
                chat_history_gemini_format.append({'role': gemini_role, 'parts': [{'text': msg.content}]})
                chat_history_for_prompt.append({'role': msg.role, 'parts': [{'text': msg.content}]})
            
            print(f"DEBUG: Histórico de chat recuperado ({len(db_history)} mensagens).")

            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            intention_prompt_content = create_intention_prompt(question, chat_history_for_prompt)
            print(f"DEBUG: Prompt de intenção para Gemini: \n{intention_prompt_content[:500]}...")
            
            chat_for_intention = genai.GenerativeModel('gemini-2.0-flash').start_chat(history=chat_history_gemini_format)
            intention_response = chat_for_intention.send_message(intention_prompt_content)
            
            try:
                intention_category_str = re.search(r'\d', intention_response.text.strip())
                if intention_category_str:
                    intention_category = int(intention_category_str.group(0))
                else:
                    raise ValueError("Nenhum número de categoria encontrado na resposta.")
            except ValueError:
                print(f"WARNING: Não foi possível classificar a intenção, resposta bruta: '{intention_response.text}'. Assumindo análise de dados aprofundada (categoria 2).")
                intention_category = 2 

            print(f"DEBUG: Intenção detectada: {intention_category}")

            final_answer = "" 
            
            if intention_category == 3: 
                print("DEBUG: Intenção: Conversa Geral. Respondendo diretamente.")
                chat_for_general = genai.GenerativeModel('gemini-2.0-flash').start_chat(history=chat_history_gemini_format)
                general_response = chat_for_general.send_message(f"Responda à pergunta do usuário: '{question}'. Seja conciso, amigável e direto. Não gere código Python ou planos de ação. Foco em responder a perguntas gerais, saudações ou pedidos de ajuda.")
                final_answer = general_response.text.strip()
                
            elif intention_category == 1: 
                print("DEBUG: Intenção: Análise de Dados Simples. Gerando código e apenas o resultado.")
                
                try:
                    vendas_queryset = Venda.objects.select_related('produto', 'cliente')
                    contas_receber_queryset = ContaReceber.objects.select_related('venda__produto', 'cliente', 'venda')
                    contas_pagar_queryset = ContaPagar.objects.select_related('fornecedor')

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
                            "status_venda_code": v.status,
                            "status_venda_display": v.get_status_display(),
                            "forma_pagamento": v.get_forma_pagamento_display(),
                            "condicao_prazo": v.get_condicao_prazo_display() if v.condicao_prazo else "À Vista",
                            "valor_conta_receber": None, "status_conta_receber": None, "data_vencimento_receber": None, "data_recebimento": None,
                            "fornecedor_nome": None, "valor_conta_pagar": None, "status_conta_pagar": None, "data_vencimento_pagar": None, "data_pagamento": None,
                        })

                    dados_contas_receber = []
                    for cr in contas_receber_queryset:
                        produto_nome_venda = cr.venda.produto.nome if cr.venda and cr.venda.produto else "N/A"
                        cliente_nome_cr = cr.cliente.nome if cr.cliente else (cr.venda.cliente.nome if cr.venda and cr.venda.cliente else "Consumidor Final")

                        dados_contas_receber.append({
                            "tipo_registro": "ContaReceber", "id_origem": cr.pk,
                            "produto_nome": produto_nome_venda, "cliente_nome": cliente_nome_cr,
                            "quantidade_vendida_receber": cr.venda.quantidade if cr.venda else None,
                            "valor_total_venda_receber": float(cr.venda.valor_total) if cr.venda and cr.venda.valor_total is not None else None,
                            "data_transacao": cr.venda.data_venda.strftime('%Y-%m-%d') if cr.venda else None,
                            "status_venda_code": v.status,
                            "status_venda_display": v.get_status_display(),
                            "forma_pagamento": cr.venda.get_forma_pagamento_display() if cr.venda else None,
                            "condicao_prazo": cr.venda.get_condicao_prazo_display() if cr.venda and cr.venda.condicao_prazo else "À Vista",
                            "valor_conta_receber": float(cr.valor), "status_conta_receber": cr.status,
                            "data_vencimento_receber": cr.data_vencimento.strftime('%Y-%m-%d'),
                            "data_recebimento": cr.data_recebimento.strftime('%Y-%m-%d') if cr.data_recebimento else None,
                            "fornecedor_nome": None, "valor_conta_pagar": None, "status_conta_pagar": None, "data_vencimento_pagar": None, "data_pagamento": None,
                        })

                    dados_contas_pagar = []
                    for cp in contas_pagar_queryset:
                        fornecedor_nome_cp = cp.fornecedor.nome_empresa if cp.fornecedor else "N/A"

                        dados_contas_pagar.append({
                            "tipo_registro": "ContaPagar", "id_origem": cp.pk,
                            "produto_nome": None, "cliente_nome": None, "quantidade_vendida": None, "valor_total_venda": None,
                            "data_transacao": None, "status_venda": None, "forma_pagamento": None, "condicao_prazo": None,
                            "valor_conta_receber": None, "status_conta_receber": None, "data_vencimento_receber": None, "data_recebimento": None,
                            "fornecedor_nome": fornecedor_nome_cp,
                            "valor_conta_pagar": float(cp.valor), "status_conta_pagar": cp.status,
                            "status_conta_pagar_code": cp.status,
                            "status_conta_pagar_display": cp.get_status_display(),
                            "data_vencimento_pagar": cp.data_vencimento.strftime('%Y-%m-%d'),
                            "data_pagamento": cp.data_pagamento.strftime('%Y-%m-%d') if cp.data_pagamento else None,
                        })

                    df = pd.DataFrame(dados_vendas + dados_contas_receber + dados_contas_pagar)
                    print(f"DEBUG: DataFrame criado com {len(df)} linhas.")

                    if df.empty:
                        print("DEBUG: DataFrame vazio, retornando mensagem sem dados.")
                        final_answer = 'Não há dados de vendas ou contas para analisar. Por favor, adicione alguns registros para que eu possa gerar insights.'
                    else:
                        simple_analysis_prompt = f"""
                        Você é um assistente especialista em Python e Pandas. Quando receber uma pergunta, responda o usuário em linguagem natural e seja educado, interativo e conversacional.
                        O usuário fez a seguinte pergunta: "{question}".
                        Você tem acesso a um DataFrame pandas chamado `df` com as colunas: {df.columns.to_list()}.
                        Gere APENAS o código Python que calcula o `result` para responder à pergunta. Responda o `result` de forma gentil e educada.
                        Formato:
                        Claro, aqui está a resposta: {{result}}
                        Use o seguinte código como base:
                        ```python
                        # Seu código aqui, exemplo: result = df['valor_total_venda'].sum()
                        ```
                        """
                        print(f"DEBUG: Prompt para Análise Simples: \n{simple_analysis_prompt[:500]}...")
                        
                        chat_for_simple_analysis = genai.GenerativeModel('gemini-2.0-flash').start_chat(history=chat_history_gemini_format)
                        simple_response = chat_for_simple_analysis.send_message(simple_analysis_prompt)
                        
                        generated_code_simple = simple_response.text.strip().replace("```python", "").replace("```", "").strip()
                        
                        execution_globals = {"pd": pd, "df": df}
                        execution_locals = {'result': None}
                        calculated_result_simple = "Resultado não gerado."

                        try:
                            exec(generated_code_simple, execution_globals, execution_locals)
                            calculated_result_simple = execution_locals.get('result', "Resultado não gerado pela IA") 
                            print(f"DEBUG: Resultado do código executado (simples): {calculated_result_simple}")
                        except Exception as e_exec:
                            error_message_exec = f"Erro na execução do código (simples): {type(e_exec).__name__}: {e_exec}"
                            print(f"ERROR: {error_message_exec}")
                            calculated_result_simple = f"Desculpe, houve um erro ao calcular o resultado: {error_message_exec}"
                        
                        if isinstance(calculated_result_simple, (int, float, Decimal)):
                            if "R$" in question or "valor" in question.lower() or "receita" in question.lower() or "custo" in question.lower() or "montante" in question.lower():
                                final_answer = f"R$ {float(calculated_result_simple):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            else:
                                final_answer = f"{int(calculated_result_simple):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        elif isinstance(calculated_result_simple, dict):
                            final_answer = "\n" + "\n".join([f"- {k}: {v}" for k, v in calculated_result_simple.items()])
                        elif calculated_result_simple is None or (isinstance(calculated_result_simple, pd.Series) and calculated_result_simple.empty) or (isinstance(calculated_result_simple, str) and calculated_result_simple == "Resultado não gerado pela IA"):
                            final_answer = "0" if ("R$" in question or "valor" in question.lower() or "custo" in question.lower() or "montante" in question.lower()) else "N/A"
                        else:
                            final_answer = str(calculated_result_simple) 
                    
                except Exception as e_df_or_gemini_call:
                    error_message_df = f'Ocorreu um erro ao criar DataFrame ou chamar Gemini para análise simples: {type(e_df_or_gemini_call).__name__}: {e_df_or_gemini_call}'
                    print(f"ERROR (e_df_or_gemini_call): {error_message_df}")
                    final_answer = f"Desculpe, houve um erro interno ao processar sua solicitação de dados simples: {error_message_df}"

            else:
                print("DEBUG: Intenção: Análise Estratégica. Gerando código com diagnóstico e plano de ação.")
                
                try:
                    vendas_queryset = Venda.objects.select_related('produto', 'cliente')
                    contas_receber_queryset = ContaReceber.objects.select_related('venda__produto', 'cliente', 'venda')
                    contas_pagar_queryset = ContaPagar.objects.select_related('fornecedor')

                    dados_vendas = []
                    for v in vendas_queryset:
                        dados_vendas.append({
                            "tipo_registro": "Venda", "id_origem": v.pk,
                            "produto_nome": v.produto.nome if v.produto else "N/A", "cliente_nome": v.cliente.nome if v.cliente else "Consumidor Final",
                            "quantidade_vendida": v.quantidade,
                            "valor_total_venda": float(v.valor_total),
                            "data_transacao": v.data_venda.strftime('%Y-%m-%d'),
                            "status_venda": v.get_status_display(),
                            "forma_pagamento": v.get_forma_pagamento_display(),
                            "condicao_prazo": v.get_condicao_prazo_display() if v.condicao_prazo else "À Vista",
                            "valor_conta_receber": None, "status_conta_receber": None, "data_vencimento_receber": None, "data_recebimento": None,
                            "fornecedor_nome": None, "valor_conta_pagar": None, "status_conta_pagar": None, "data_vencimento_pagar": None, "data_pagamento": None,
                        })

                    dados_contas_receber = []
                    for cr in contas_receber_queryset:
                        produto_nome_venda = cr.venda.produto.nome if cr.venda and cr.venda.produto else "N/A"
                        cliente_nome_cr = cr.cliente.nome if cr.cliente else (cr.venda.cliente.nome if cr.venda and cr.venda.cliente else "Consumidor Final")

                        dados_contas_receber.append({
                            "tipo_registro": "ContaReceber", "id_origem": cr.pk,
                            "produto_nome": produto_nome_venda, "cliente_nome": cliente_nome_cr,
                            "quantidade_vendida_receber": cr.venda.quantidade if cr.venda else None,
                            "valor_total_venda_receber": float(cr.venda.valor_total) if cr.venda and cr.venda.valor_total is not None else None,
                            "data_transacao": cr.venda.data_venda.strftime('%Y-%m-%d') if cr.venda else None,
                            "status_venda": cr.venda.get_status_display() if cr.venda else None,
                            "forma_pagamento": cr.venda.get_forma_pagamento_display() if cr.venda else None,
                            "condicao_prazo": cr.venda.get_condicao_prazo_display() if cr.venda and cr.venda.condicao_prazo else "À Vista",
                            "valor_conta_receber": float(cr.valor), "status_conta_receber": cr.status,
                            "data_vencimento_receber": cr.data_vencimento.strftime('%Y-%m-%d'),
                            "data_recebimento": cr.data_recebimento.strftime('%Y-%m-%d') if cr.data_recebimento else None,
                            "fornecedor_nome": None, "valor_conta_pagar": None, "status_conta_pagar": None, "data_vencimento_pagar": None, "data_pagamento": None,
                        })

                    dados_contas_pagar = []
                    for cp in contas_pagar_queryset:
                        fornecedor_nome_cp = cp.fornecedor.nome_empresa if cp.fornecedor else "N/A"

                        dados_contas_pagar.append({
                            "tipo_registro": "ContaPagar", "id_origem": cp.pk,
                            "produto_nome": None, "cliente_nome": None, "quantidade_vendida": None, "valor_total_venda": None,
                            "data_transacao": None, "status_venda": None, "forma_pagamento": None, "condicao_prazo": None,
                            "valor_conta_receber": None, "status_conta_receber": None, "data_vencimento_receber": None, "data_recebimento": None,
                            "fornecedor_nome": fornecedor_nome_cp,
                            "valor_conta_pagar": float(cp.valor), "status_conta_pagar": cp.status,
                            "data_vencimento_pagar": cp.data_vencimento.strftime('%Y-%m-%d'),
                            "data_pagamento": cp.data_pagamento.strftime('%Y-%m-%d') if cp.data_pagamento else None,
                        })

                    df = pd.DataFrame(dados_vendas + dados_contas_receber + dados_contas_pagar)
                    print(f"DEBUG: DataFrame criado com {len(df)} linhas.")
                    
                    if df.empty:
                        print("DEBUG: DataFrame vazio, retornando mensagem sem dados.")
                        final_answer = 'Não há dados de vendas ou contas para analisar. Por favor, adicione alguns registros para que eu possa gerar insights.'
                    else:
                        prompt_content = create_code_generation_prompt(question, df.columns.to_list(), chat_history_for_prompt)
                        
                        print(f"DEBUG: Prompt final para Gemini (Análise de Dados Estratégica): \n{prompt_content[:1000]}...")

                        response_content = chat_for_intention.send_message(prompt_content)
                        print(f"DEBUG: Resposta bruta do Gemini: {response_content.text}")

                        parts = response_content.text.strip().split('---RESPOSTA---')

                        if len(parts) != 2:
                            error_message = f"Formato de resposta inesperado do modelo de IA (Análise de Dados Estratégica). Resposta bruta: {response_content.text}"
                            print(f"ERROR: {error_message}")
                            final_answer = error_message
                        else:
                            generated_code = parts[0].strip().replace("```python", "").replace("```", "").strip()
                            response_template = parts[1].strip()

                            print(f"DEBUG: Código gerado pela IA: ```python\n{generated_code}\n```")
                            print(f"DEBUG: Template de resposta da IA: '{response_template}'")

                            execution_globals = {"pd": pd, "df": df}
                            execution_locals = {'result': None}
                            calculated_result = "Valor não definido pelo código gerado."

                            try:
                                exec(generated_code, execution_globals, execution_locals)
                                calculated_result = execution_locals.get('result', "Resultado não gerado pela IA") 
                                print(f"DEBUG: Resultado do código executado: {calculated_result}")
                            except Exception as e_exec:
                                error_message_exec = f"Erro na execução do código gerado pela IA: {type(e_exec).__name__}: {e_exec}"
                                print(f"ERROR: {error_message_exec}")
                                calculated_result = f"Desculpe, houve um erro ao processar sua solicitação: {error_message_exec}"
                            
                            formatted_result = str(calculated_result)
                            
                            if isinstance(calculated_result, (int, float, Decimal)):
                                if "R$" in response_template or "valor" in question.lower() or "receita" in question.lower() or "custo" in question.lower() or "montante" in question.lower():
                                    formatted_result = f"R$ {float(calculated_result):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                else:
                                    formatted_result = f"{int(calculated_result):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            elif isinstance(calculated_result, dict):
                                formatted_result = "\n" + "\n".join([f"- {k}: {v}" for k, v in calculated_result.items()])
                            elif calculated_result is None or (isinstance(calculated_result, pd.Series) and calculated_result.empty) or (isinstance(calculated_result, str) and calculated_result == "Resultado não gerado pela IA"):
                                formatted_result = "0" if ("R$" in response_template or "valor" in question.lower() or "custo" in question.lower() or "montante" in question.lower()) else "N/A"
                            else:
                                formatted_result = str(calculated_result)
                            
                            print(f"DEBUG: Resultado formatado (Estratégico): '{formatted_result}'")

                            final_answer = response_template 
                            
                            match_analysis_content = re.search(
                                r"Aqui está a sua análise:\n(.*?)(?=\n+Diagnóstico:|\n+Plano de Ação:|$)", 
                                response_template, 
                                re.DOTALL
                            )

                            if match_analysis_content:
                                llm_inserted_analysis_content = match_analysis_content.group(1).strip()
                                print(f"DEBUG: Conteúdo da análise detectado pelo LLM no template para substituição (Estratégico): '{llm_inserted_analysis_content}'")
                                final_answer = final_answer.replace(llm_inserted_analysis_content, formatted_result, 1)
                            elif '{{result}}' in response_template:
                                print("DEBUG: O {{result}} placeholder foi encontrado (Estratégico). Realizando substituição direta.")
                                final_answer = final_answer.replace('{{result}}', formatted_result)
                            else:
                                print("DEBUG: Nenhum padrão de análise nem {{result}} encontrado (Estratégico). Usando template original do LLM.")
                                final_answer = response_template 
                                
                        print(f"DEBUG: Resposta final formatada e substituída (Estratégica): '{final_answer}'")
                
                except Exception as e_df_or_gemini_call:
                    error_message_df = f'Ocorreu um erro ao criar DataFrame ou chamar Gemini para análise estratégica: {type(e_df_or_gemini_call).__name__}: {e_df_or_gemini_call}'
                    print(f"ERROR (e_df_or_gemini_call): {error_message_df}")
                    final_answer = f"Desculpe, houve um erro interno ao processar sua solicitação estratégica: {error_message_df}"

            ChatMessage.objects.create(session_id=session_id, role='user', content=question)
            ChatMessage.objects.create(session_id=session_id, role='ai', content=final_answer)

            return JsonResponse({'answer': final_answer})

        except json.JSONDecodeError as e_json:
            error_message_json = f'Erro ao decodificar JSON na requisição: {e_json}'
            print(f"ERROR (e_json): {error_message_json}")
            return JsonResponse({'error': error_message_json}, status=400)
        except Exception as e_outer:
            error_message_outer = f'Ocorreu um erro no servidor antes do processamento da pergunta: {type(e_outer).__name__}: {e_outer}'
            print(f"CRITICAL ERROR (e_outer): {error_message_outer}")
            return JsonResponse({'error': error_message_outer}, status=500)

    print("DEBUG: Método não permitido.")
    return JsonResponse({'error': 'Método não permitido.'}, status=405)


def create_code_generation_prompt(question, available_columns, chat_history_for_prompt=None):

    column_list = "\n".join([f"- {col}" for col in available_columns])

    history_text = ""
    if chat_history_for_prompt:
        for msg in chat_history_for_prompt:
            if msg['role'] == 'user':
                history_text += f"Usuário: {msg['parts'][0]['text']}\n"
            elif msg['role'] == 'ai':
                analysis_match = re.search(r"Aqui está a sua análise:\n(.*?)(?=\n+Diagnóstico:|\n+Plano de Ação:|$)", msg['parts'][0]['text'], re.DOTALL)
                
                if analysis_match:
                    history_text += f"Assistente (Análise): {analysis_match.group(1).strip()}\n"
                else:
                    first_line_of_ai_response = msg['parts'][0]['text'].split('\n')[0]
                    history_text += f"Assistente: {first_line_of_ai_response}\n" # first line input
            
        history_text = "Histórico da conversa:\n" + history_text + "\n"

    prompt = f"""
    Você é um consultor financeiro e estratégico experiente, com acesso completo aos dados de vendas e contas de uma empresa no formato de um DataFrame pandas chamado `df`.
    Seu objetivo é ajudar o gestor a tomar decisões informadas e proativas, indo além de simples cálculos para fornecer insights acionáveis e planos de ação.

    O DataFrame `df` consolidado contém as seguintes colunas disponíveis:
    {column_list}

    Detalhes das colunas importantes:
    - 'tipo_registro': Indica o tipo de registro ('Venda', 'ContaReceber', 'ContaPagar').
    - 'status_venda_code': Código interno do status da venda (e.g., 'P', 'C').
    - 'status_venda_display': Representação legível do status da venda (e.g., 'PENDENTE', 'CONCLUIDO').
    - 'status_conta_receber_code': Código interno do status da conta a receber (e.g., 'ABERTO', 'RECEBIDO', 'ATRASADO').
    - 'status_conta_receber_display': Representação legível do status da conta a receber (e.g., 'Aberto', 'Recebido', 'Atrasado').
    - 'status_conta_pagar_code': Código interno do status da conta a pagar (e.g., 'ABERTO', 'PAGO', 'ATRASADO').
    - 'status_conta_pagar_display': Representação legível do status da conta a pagar (e.g., 'Aberto', 'Pago', 'Atrasado').
    - 'valor_conta_receber': Valor monetário da conta a receber.
    - 'valor_conta_pagar': Valor monetário da conta a pagar.
    - 'valor_total_venda': Valor total da venda.
    - 'valor_total_venda_receber': Valor total da venda a receber.
    - 'quantidade_vendida': Quantidade de itens vendidos na venda.
    - 'quantidade_vendida_receber': Quantidade de itens vendidos na venda associada à conta a receber.
    - 'data_transacao': Data da venda ou data base para o registro.
    - 'data_recebimento': Data em que a conta a receber foi efetivamente recebida.
    - 'data_pagamento': Data em que a conta a pagar foi efetivamente paga.
    - 'cliente_nome': Nome do cliente.
    - 'produto_nome': Nome do produto.
    - 'fornecedor_nome': Nome do fornecedor.

    {history_text}
    O usuário fez a seguinte pergunta: {question}

    Com base nesta pergunta e no histórico (se houver), você deve:
    1. Gerar um fragmento de código Python (usando pandas) para analisar o `df` e obter o `result` solicitado. O código deve ser conciso e focar em gerar um único resultado final (número, string, dicionário, lista). **O `result` deve ser o dado puro, sem formatação de texto explicativo.**
    2. Elaborar um texto de resposta que não apenas apresente o resultado (onde `{{result}}` será substituído pelo valor calculado), mas também:
        - Um breve diagnóstico ou contextualização do resultado.
        - Sugestões de 'Plano de Ação' concreto e acionável para o gestor.
        - Possíveis impactos ou próximas etapas para essas ações.
        - Não suponha, use somente as colunas como base para o diagnóstico e plano de ação.
        - Use somente os nomes reais das colunas do DataFrame para referenciar os dados.

    **IMPORTANTE:**
    - Se a pergunta não puder ser respondida com os dados disponíveis ou exigir mais detalhes, o `result` deve ser uma string explicando isso.
    - O formato `{{result}}` é um placeholder. Não o substitua com o valor real; seu código Python fará isso.

    Formato da sua resposta:
    ```python
    # Seu código Python aqui. Exemplo: result = df['valor_total_venda'].sum()
    ```
    ---RESPOSTA---
    Aqui está a sua análise:
    {{result}}

    Diagnóstico: [Seu diagnóstico baseado no resultado. Foco em fatos e implicações diretas. Se o `result` for uma string explicativa, baseie o diagnóstico nela.]

    Plano de Ação:
    1. **Ação 1:** [Descrição da ação] - *Justificativa e Impacto. Se a análise não for possível, sugira ações para obter mais dados ou refinar a pergunta.*
    2. **Ação 2:** [Descrição da ação] - *Justificativa e Impacto.*
    [Adicione mais ações conforme necessário]

    Procurando por mais insights? Pergunte-me sobre...
    """
    return prompt