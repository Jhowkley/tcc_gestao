import json
import os
import dotenv
import re 
import pandas as pd
import google.generativeai as genai
import logging
import calendar
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from sqlglot import logger
from .forms import ProdutoForm, ClienteForm, VendaForm, ContaReceberForm, ContaPagarForm, CategoriaForm, FornecedorForm 
from .models import Produto, Cliente, Venda, ContaReceber, ContaPagar, Categoria, Fornecedor, ChatMessage
from datetime import date, timedelta
from decimal import Decimal
from string import Template
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout
from django.utils import timezone


logger = logging.getLogger(__name__)

@login_required
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

@login_required
def lista_categorias_view(request):
    categorias = Categoria.objects.all()
    return render(request, 'core/lista_categorias.html', {'categorias': categorias})

@login_required
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

@login_required
def lista_fornecedores_view(request): 
    fornecedores = Fornecedor.objects.all()
    return render(request, 'core/lista_fornecedores.html', {'fornecedores': fornecedores})

@login_required
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

@login_required
def fornecedor_delete_view(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        fornecedor.delete()
        return redirect('lista_fornecedores')
    return render(request, 'core/confirm_delete.html', {'instance': fornecedor, 'titulo': 'Deletar Fornecedor'})

@login_required
def lista_produtos_view(request):
    produtos = Produto.objects.all().select_related('categoria', 'fornecedor')
    return render(request, 'core/lista_produtos.html', {'produtos': produtos})

@login_required
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

@login_required
def produto_delete_view(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        produto.delete()
        return redirect('lista_produtos')
    return render(request, 'core/confirm_delete.html', {'instance': produto, 'titulo': 'Deletar Produto'})

@login_required
def lista_clientes_view(request):
    clientes = Cliente.objects.all()
    return render(request, 'core/lista_clientes.html', {'clientes': clientes})

@login_required
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

@login_required
def cliente_delete_view(request, pk): 
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'core/confirm_delete.html', {'instance': cliente, 'titulo': 'Deletar Cliente'})

@login_required
def lista_vendas_view(request):
    vendas = Venda.objects.all().select_related('produto', 'cliente').order_by('-data_venda')
    return render(request, 'core/lista_vendas.html', {'vendas': vendas})

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
def conta_receber_delete_view(request, pk): 
    conta = get_object_or_404(ContaReceber, pk=pk)
    if request.method == 'POST':
        conta.delete()
        return redirect('lista_contas_receber')
    return render(request, 'core/confirm_delete.html', {'instance': conta, 'titulo': 'Deletar Conta a Receber'})

@login_required
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


@login_required
def lista_contas_pagar_view(request): 
    contas = ContaPagar.objects.all().select_related('fornecedor').order_by('-data_vencimento')
    context ={
        'contas_pagar': contas,
        'titulo': 'Contas a Pagar',
        'ativo_cp': 'active', 
    }
    return render(request, 'core/lista_contas_pagar.html', context)

@login_required
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

@login_required
def conta_pagar_delete_view(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    if request.method == 'POST':
        conta.delete()
        return redirect('lista_contas_pagar')
    return render(request, 'core/confirm_delete.html', {'instance': conta, 'titulo': 'Deletar Conta a Pagar'})

@login_required
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


print(f"DEBUG VIEWS.PY: os.environ.get('GEMINI_API_KEY') -> {os.environ.get('GEMINI_API_KEY')}")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.0-flash')

@csrf_exempt
def ask_api_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip()
            session_id = data.get('session_id') 

            if not question:
                return JsonResponse({'answer': 'Por favor, faça uma pergunta.'}, status=400)
            
            if not session_id:
                return JsonResponse({'answer': 'Erro: ID de sessão não fornecido.'}, status=400)

            ChatMessage.objects.create(session_id=session_id, role='user', content=question)

            history_messages = ChatMessage.objects.filter(session_id=session_id).order_by('timestamp')
            
            
            gemini_history = []
            for msg in history_messages:
                gemini_history.append({
                    'role': 'user' if msg.role == 'user' else 'model', 
                    'parts': [msg.content]
                })

            print(f"DEBUG: Histórico de chat para session_id {session_id}:")
            for h_msg in gemini_history:
                print(f"  - {h_msg['role']}: {h_msg['parts'][0][:100]}...") 
                
            df = get_dataframe_from_db()
            agreggated_metrics = get_aggregated_metrics(df) 

            df_for_gemini_str = ""
            if not df.empty:
                relevant_cols = [
                    'tipo_registro', 'id_origem', 'produto_nome', 'cliente_nome',
                    'quantidade_vendida', 'valor_total_venda', 'data_transacao', 'status_venda_code',
                    'valor_conta_receber', 'valor_conta_pagar', 'data_vencimento_pagar', 
                    'status_conta_receber', 'data_vencimento_receber', 'data_recebimento'
                ]
                df_relevant = df[relevant_cols].head(50)
                
                for col in ['data_transacao', 'data_vencimento_receber', 'data_recebimento', 'data_vencimento_pagar', 'data_lancamento_pagar', 'data_pagamento_pagar']: 
                    if col in df_relevant.columns:
                        df_relevant[col] = df_relevant[col].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('N/A')

                df_for_gemini_str = df_relevant.to_json(orient="records", date_format="iso")
                print(f"DEBUG: DataFrame para Gemini (primeiras 50 linhas): {df_for_gemini_str[:500]}...")

            
            agent_prompt = create_unified_agent_prompt(question, df_for_gemini_str, agreggated_metrics)
            print(f"DEBUG: Prompt Único para Gemini: \n{agent_prompt[:2000]}...")

            # start the chat with the history
            chat = model.start_chat(history=gemini_history) 
            
            response = chat.send_message(
                agent_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0, 
                    max_output_tokens=1000,
                )
            )
            
            gemini_raw_response = response.text
            print(f"DEBUG: Resposta bruta do Gemini (Único Prompt): {gemini_raw_response[:1000]}...")

            try:
                cleaned_response = gemini_raw_response.strip()

                json_start_index = cleaned_response.find('```json')
                json_end_index = cleaned_response.rfind('```')

                if json_start_index != -1 and json_end_index != -1 and json_end_index > json_start_index:
                    cleaned_response = cleaned_response[json_start_index + len('```json'):json_end_index]
                elif cleaned_response.startswith('{') and cleaned_response.endswith('}'):
                    pass
                else:
                    print(f"WARNING: Não foi possível encontrar os delimitadores '```json' e '```' na resposta do Gemini. Tentando parsear a resposta bruta. Resposta: {cleaned_response[:200]}")
                    pass

                cleaned_response = cleaned_response.strip()

                if not cleaned_response:
                    raise ValueError("Resposta do Gemini limpa resultou em string vazia ou inválida.")
                
                print(f"DEBUG: Resposta limpa para JSON.loads: {cleaned_response[:1000]}...")

                parsed_response = json.loads(cleaned_response)

                final_answer_text = parsed_response.get('resposta_final', 'Não foi possível gerar uma resposta.')
                diagnostico_text = parsed_response.get('diagnostico', '').strip()
                plano_de_acao_text = parsed_response.get('plano_de_acao', '').strip()
                dados_analisados_json = parsed_response.get('dados_analisados', {})

                full_response_for_user = final_answer_text
                if diagnostico_text and diagnostico_text.lower() not in ['Não aplicável', 'não aplicavel', 'n/a', 'na']:
                    full_response_for_user += f"\n\nDiagnóstico:\n{diagnostico_text}"
                    
                if plano_de_acao_text and plano_de_acao_text.lower() not in ['Não aplicável', 'não aplicavel', 'n/a', 'na']:
                    full_response_for_user += f"\n\nPlano de Ação:\n{plano_de_acao_text}"
                
                # 3. Session ChatMessage
                ChatMessage.objects.create(session_id=session_id, role='assistant', content=full_response_for_user)

                return JsonResponse({
                    'answer': full_response_for_user,
                    'diagnostico': diagnostico_text,
                    'plano_de_acao': plano_de_acao_text,
                    'dados_analisados': dados_analisados_json
                }, status=200)

            except json.JSONDecodeError:
                print(f"ERROR: Gemini não retornou um JSON válido. Resposta bruta: {gemini_raw_response}")
                # History session Error message
                ChatMessage.objects.create(session_id=session_id, role='assistant', content='Erro: Resposta inválida do servidor de IA.')
                return JsonResponse({'answer': 'Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente.'}, status=500)
            except ValueError as ve:
                print(f"ERROR: Erro de processamento da resposta do Gemini: {ve}. Resposta original: {gemini_raw_response}")
                ChatMessage.objects.create(session_id=session_id, role='assistant', content='Erro: A resposta da IA não pôde ser interpretada.')
                return JsonResponse({'answer': 'Desculpe, a resposta da inteligência artificial não pôde ser processada. Por favor, tente novamente.'}, status=500)
            except Exception as e:
                print(f"ERROR: Erro inesperado ao processar resposta do Gemini: {e}. Resposta original: {gemini_raw_response}")
                ChatMessage.objects.create(session_id=session_id, role='assistant', content=f'Erro inesperado: {str(e)}.')
                return JsonResponse({'answer': 'Ocorreu um erro inesperado ao interpretar a resposta. Por favor, tente novamente.'}, status=500)

        except Exception as e:
            print(f"ERROR: Erro na ask_api_view: {e}")
            return JsonResponse({'answer': f'Ocorreu um erro inesperado no servidor: {str(e)}'}, status=500)
    
    return JsonResponse({'answer': 'Método não permitido.'}, status=405)

def get_aggregated_metrics(df):
    metrics = {}
    
    if df.empty:
        metrics['total_vendas_concluidas'] = 0.0
        metrics['total_vendas_pendentes'] = 0.0
        metrics['total_contas_recebidas'] = 0.0
        metrics['total_contas_receber_aberto_atrasado'] = 0.0
        metrics['total_contas_pagar_aberto_atrasado'] = 0.0
        metrics['quantidade_vendas_concluidas'] = 0
        metrics['quantidade_vendas_pendentes'] = 0
        metrics['total_estoque_geral'] = 0
        metrics['quantidade_total_produtos_cadastrados'] = 0
        return metrics

    vendas_df = df[df['tipo_registro'] == 'Venda']
    
    metrics['total_vendas_concluidas'] = vendas_df[vendas_df['status_venda_code'] == 'CONCLUIDA']['valor_total_venda'].sum()
    metrics['total_vendas_concluidas'] = round(float(metrics['total_vendas_concluidas']), 2) 

    metrics['total_vendas_pendentes'] = vendas_df[vendas_df['status_venda_code'] == 'PENDENTE']['valor_total_venda'].sum()
    metrics['total_vendas_pendentes'] = round(float(metrics['total_vendas_pendentes']), 2)

    metrics['quantidade_vendas_concluidas'] = vendas_df[vendas_df['status_venda_code'] == 'CONCLUIDA'].shape[0]
    
    metrics['quantidade_vendas_pendentes'] = vendas_df[vendas_df['status_venda_code'] == 'PENDENTE'].shape[0]

    contas_receber_df = df[df['tipo_registro'] == 'ContaReceber']
    
    metrics['total_contas_recebidas'] = contas_receber_df[contas_receber_df['status_conta_receber'] == 'RECEBIDO']['valor_conta_receber'].sum()
    metrics['total_contas_recebidas'] = round(float(metrics['total_contas_recebidas']), 2)

    metrics['total_contas_receber_aberto_atrasado'] = contas_receber_df[
        (contas_receber_df['status_conta_receber'] == 'ABERTO') | 
        (contas_receber_df['status_conta_receber'] == 'ATRASADO')
    ]['valor_conta_receber'].sum()
    metrics['total_contas_receber_aberto_atrasado'] = round(float(metrics['total_contas_receber_aberto_atrasado']), 2)

    contas_pagar_df = df[df['tipo_registro'] == 'ContaPagar']
    
    metrics['total_contas_pagar_aberto_atrasado'] = contas_pagar_df[
        (contas_pagar_df['status_conta_pagar'] == 'ABERTO') | 
        (contas_pagar_df['status_conta_pagar'] == 'ATRASADO')
    ]['valor_conta_pagar'].sum()
    metrics['total_contas_pagar_aberto_atrasado'] = round(float(metrics['total_contas_pagar_aberto_atrasado']), 2)
    
    produtos_df = df[df['tipo_registro'] == 'Produto']
    
    metrics['total_estoque_geral'] = produtos_df['estoque_atual'].sum()
    metrics['total_estoque_geral'] = round(float(metrics['total_estoque_geral']), 2)
    
    metrics['quantidade_total_produtos_cadastrados'] = produtos_df.shape[0]
    
    return metrics

def get_dataframe_from_db():
    vendas_queryset = Venda.objects.select_related('produto', 'cliente')
    contas_receber_queryset = ContaReceber.objects.select_related('venda__produto', 'cliente', 'venda')
    contas_pagar_queryset = ContaPagar.objects.select_related('fornecedor')
    produtos_queryset = Produto.objects.select_related('fornecedor', 'categoria')
    

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
            # outers camps for consistency
            "valor_conta_receber": None, "status_conta_receber": None, "data_vencimento_receber": None, "data_recebimento": None,
            "fornecedor_nome": None, "valor_conta_pagar": None, "status_conta_pagar": None, "data_vencimento_pagar": None, "data_pagamento": None,
            "estoque_atual": None, "preco_compra": None, "preco_venda_unitario": None, "categoria_nome": None
        })

    dados_contas_receber = []
    for cr in contas_receber_queryset:
        produto_nome_venda = cr.venda.produto.nome if cr.venda and cr.venda.produto else "N/A"
        cliente_nome_cr = cr.cliente.nome if cr.cliente else (cr.venda.cliente.nome if cr.venda and cr.venda.cliente else "Consumidor Final")

        dados_contas_receber.append({
            "tipo_registro": "ContaReceber", "id_origem": cr.pk,
            "produto_nome": produto_nome_venda, "cliente_nome": cliente_nome_cr,
            "quantidade_vendida": cr.venda.quantidade if cr.venda else None, 
            "valor_total_venda": float(cr.venda.valor_total) if cr.venda and cr.venda.valor_total is not None else None, 
            "data_transacao": cr.venda.data_venda.strftime('%Y-%m-%d') if cr.venda else None, # Data base
            "status_venda_code": cr.venda.status if cr.venda else None, # Status venda 
            "status_venda_display": cr.venda.get_status_display() if cr.venda else None,
            "forma_pagamento": cr.venda.get_forma_pagamento_display() if cr.venda else None,
            "condicao_prazo": cr.venda.get_condicao_prazo_display() if cr.venda and cr.venda.condicao_prazo else "À Vista",
            "valor_conta_receber": float(cr.valor), "status_conta_receber": cr.status,
            "data_vencimento_receber": cr.data_vencimento.strftime('%Y-%m-%d'),
            "data_recebimento": cr.data_recebimento.strftime('%Y-%m-%d') if cr.data_recebimento else None,
            "fornecedor_nome": None, "valor_conta_pagar": None, "status_conta_pagar": None, "data_vencimento_pagar": None, "data_pagamento": None,
            "estoque_atual": None, "preco_compra": None, "preco_venda_unitario": None, "categoria_nome": None
        })
    
    dados_contas_pagar = []
    for cp in contas_pagar_queryset:
        fornecedor_nome_cp = cp.fornecedor.nome_empresa if cp.fornecedor else "N/A"
        dados_contas_pagar.append({
            "tipo_registro": "ContaPagar", "id_origem": cp.pk,
            "fornecedor_nome": fornecedor_nome_cp,
            "valor_conta_pagar": float(cp.valor),
            "status_conta_pagar": cp.status,
            "status_conta_pagar_code": cp.status,
            "status_conta_pagar_display": cp.get_status_display(),
            "data_vencimento_pagar": cp.data_vencimento.strftime('%Y-%m-%d'),
            "data_pagamento": cp.data_pagamento.strftime('%Y-%m-%d') if cp.data_pagamento else None,
            "produto_nome": None, "cliente_nome": None, "quantidade_vendida": None, "valor_total_venda": None,
            "data_transacao": None, "status_venda_code": None, "status_venda_display": None, "forma_pagamento": None, "condicao_prazo": None,
            "valor_conta_receber": None, "status_conta_receber": None, "data_vencimento_receber": None, "data_recebimento": None,
            "estoque_atual": None, "preco_compra": None, "preco_venda_unitario": None, "categoria_nome": None
        })
    
    dados_produtos = []
    for p in produtos_queryset:
        dados_produtos.append({
            "tipo_registro": "Produto",
            "id_origem": p.pk,
            "produto_nome": p.nome,
            "descricao_produto": p.descricao,
            "fornecedor_nome": p.fornecedor.nome_empresa if p.fornecedor else "N/A",
            "categoria_nome": p.categoria.nome if p.categoria else "N/A",
            "preco_compra": float(p.preco_compra),
            "preco_venda_unitario": float(p.preco_venda),
            "estoque_atual": p.quantidade_estoque,
            "data_cadastro_produto": p.data_cadastro.strftime('%Y-%m-%d %H:%M:%S'),
            # other fields set to None for consistency
            "cliente_nome": None, "quantidade_vendida": None, "valor_total_venda": None,
            "data_transacao": None, "status_venda_code": None, "status_venda_display": None, "forma_pagamento": None, "condicao_prazo": None,
            "valor_conta_receber": None, "status_conta_receber": None, "data_vencimento_receber": None, "data_recebimento": None,
            "valor_conta_pagar": None, "status_conta_pagar": None, "data_vencimento_pagar": None, "data_pagamento": None,
        })

    df_list = dados_vendas + dados_contas_receber + dados_contas_pagar + dados_produtos
    df = pd.DataFrame(df_list)

    if not df.empty:
        # convert typings for pandas
        for col in ['data_transacao', 'data_vencimento_receber', 'data_recebimento', 'data_vencimento_pagar', 'data_pagamento', 'data_cadastro_produto']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        for col in ['quantidade_vendida', 'valor_total_venda', 'valor_conta_receber', 'valor_conta_pagar', 'estoque_atual', 'preco_compra', 'preco_venda_unitario']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

def create_unified_agent_prompt(question, df_json_str, aggregated_metrics): 
    aggregated_metrics_str = json.dumps(aggregated_metrics, indent=2)

    return f"""
    Você é um assistente de negócios especializado em analisar dados de Vendas, Contas a Receber e Contas a Pagar e Produtos de uma empresa.
    Seu objetivo é responder às perguntas do usuário de forma precisa, com insights relevantes, diagnósticos e, quando apropriado, planos de ação.
    Você tem acesso a dados detalhados no formato JSON, representando um DataFrame pandas.

    **REGRAS CRÍTICAS (LEIA ATENTAMENTE E SIGA RIGOROSAMENTE):**
    1.  **FOCO RESTRITO:** Sua análise deve se concentrar **EXCLUSIVAMENTE em Vendas, Contas a Receber e Contas a Pagar e Produtos**.
    2.  **DADOS REAIS:** Use **SOMENTE** os dados fornecidos no JSON. **NÃO INVENTE, ADIVINHE OU FABRIQUE DADOS, NOMES (clientes, produtos, fornecedores), VALORES, OU CENÁRIOS QUE NÃO ESTEJAM NO JSON OU IMPLÍCITOS NELE.**
    3.  **FORMULAÇÃO DA RESPOSTA:** Sempre retorne sua resposta como um objeto JSON. Este JSON DEVE ter as seguintes chaves:
        -   `resposta_final`: (String) Uma resposta direta e conversacional à pergunta do usuário. Inclua números formatados (R$ X,XX, Y unidades).
        -   `diagnostico`: (String) Um diagnóstico conciso e factual baseado nos dados analisados, identificando pontos fortes, fracos, ou tendências. **Preencha este campo APENAS se a pergunta do usuário solicitar explicitamente uma análise, diagnóstico, ou insights aprofundados.** Caso contrário, deve ser uma string vazia ("").
        -   `plano_de_acao`: (String) Sugestões de ações práticas e acionáveis que o gestor pode tomar com base na análise. Seja específico e use os dados (nomes de produtos, clientes, fornecedores) do `dados_analisados` se relevante. Se o resultado indicar falta de dados para uma ação, mencione isso. **Preencha este campo APENAS se a pergunta do usuário solicitar explicitamente um plano de ação, recomendações, ou "o que devo fazer?".** Caso contrário, deve ser uma string vazia ("").
        -   `dados_analisados`: (Objeto JSON) Um resumo dos cálculos e métricas chave que você usou na sua análise. **Se a pergunta for de natureza conversacional ou não exigir análise de dados, este campo deve ser um objeto JSON vazio ({{}}).**
    4.  **CONDICIONALIDADE DE ANÁLISE/AÇÃO:** `diagnostico` e `plano_de_acao` SÃO OPCIONAIS e devem ser preenchidos APENAS quando a INTENÇÃO do usuário indicar uma solicitação de análise profunda ou recomendação de ação. Para perguntas simples de dados (ex: "Quantas vendas tivemos?", "Qual o valor da Conta a Pagar X?", "Quantos produtos temos em estoque?"), deixe `diagnostico` e `plano_de_acao` vazios.
    5.  **SEMPRE UM JSON VÁLIDO:** O retorno DEVE ser um JSON válido.
    6. **PRIORIZE FATOS AGREGADOS:** Para perguntas sobre **valores totais, quantidades totais ou somas de categorias específicas**, você **DEVE** utilizar os `Fatos Agregados` fornecidos abaixo. **NÃO tente somar os dados brutos do `DataFrame JSON` para essas perguntas, pois os `Fatos Agregados` já são os valores precisos e finais.**
    ---

    **Fatos Agregados Pré-Calculados (Sempre use para perguntas de totalização):**
    ```json
    {aggregated_metrics_str}
    ```

    ---

    **Dados Detalhados Disponíveis (DataFrame JSON - para análises mais profundas, se os fatos agregados não forem suficientes):**
    ```json
    {df_json_str}
    ```

    **Colunas Disponíveis no DataFrame e Seus Tipos/Valores Importantes (para referência em análises detalhadas):**
    -   `tipo_registro`: "Venda", "ContaReceber", "ContaPagar", **"Produto"** (use capitalização exata)
    -   `id_origem`: ID único do registro (Venda, Conta, Produto).
    -   `produto_nome`: Nome do produto. (Presente em Venda, ContaReceber, Produto)
    -   `cliente_nome`: Nome do cliente. (Presente em Venda, ContaReceber)
    -   `fornecedor_nome`: Nome do fornecedor. (Presente em ContaPagar, Produto)
    -   `categoria_nome`: Nome da categoria do produto. (Presente em Produto)
    -   `descricao_produto`: Descrição detalhada do produto. (Presente em Produto)
    -   `quantidade_vendida`: Quantidade de itens em uma venda. (Presente em Venda, ContaReceber)
    -   `valor_total_venda`: Valor monetário total de uma venda. (Presente em Venda, ContaReceber)
    -   `data_transacao`: Data da venda ou transação. (Presente em Venda, ContaReceber)
    -   `status_venda_code`: Status da venda (e.g., "CONCLUIDA", "PENDENTE" - use capitalização exata). (Presente em Venda, ContaReceber)
    -   `status_conta_receber`: Status da conta a receber (e.g., "ABERTO", "RECEBIDO", "ATRASADO" - use capitalização exata). (Presente em ContaReceber)
    -   `valor_conta_receber`: Valor monetário de uma conta a receber. (Presente em ContaReceber)
    -   `data_vencimento_receber`: Data de vencimento da conta a receber. (Presente em ContaReceber)
    -   `data_recebimento`: Data de recebimento da conta a receber. (Presente em ContaReceber)
    -   `valor_conta_pagar`: Valor monetário de uma conta a pagar. (Presente em ContaPagar)
    -   `status_conta_pagar`: Status da conta a pagar (e.g., "ABERTO", "PAGO", "ATRASADO" - use capitalização exata). (Presente em ContaPagar)
    -   `data_vencimento_pagar`: Data de vencimento da conta a pagar. (Presente em ContaPagar) 
    -   `data_pagamento`: Data de pagamento da conta a pagar. (Presente em ContaPagar)
    -   `estoque_atual`: Quantidade de unidades em estoque do produto. (Presente em Produto)
    -   `preco_compra`: Preço de custo unitário do produto. (Presente em Produto)
    -   `preco_venda_unitario`: Preço de venda unitário do produto. (Presente em Produto)
    -   `data_cadastro_produto`: Data de cadastro do produto. (Presente em Produto)

    ---

    **Pergunta do Usuário:** "{question}"

    ---

    **Seu retorno JSON:**
    ```json
    {{
        "resposta_final": "[Resposta direta para o usuário]",
        "diagnostico": "[Diagnóstico com base nos dados]",
        "plano_de_acao": "[Plano de ação específico]",
        "dados_analisados": {{
            "metrica_1": "valor",
            "metrica_2": "valor"
        }}
    }}
    ```
    """
    
def logout_view(request):
    logout(request)
    return redirect('login')
