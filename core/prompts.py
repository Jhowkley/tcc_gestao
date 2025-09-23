def create_intention_prompt(question, chat_history_for_prompt=None):
    history_text = ""
    if chat_history_for_prompt:
        for msg in chat_history_for_prompt:
            if msg['role'] == 'user':
                history_text += f"Usuário: {msg['parts'][0]['text']}\n"
            elif msg['role'] == 'ai':
                history_text += f"Assistente: {msg['parts'][0]['text']}\n"
        history_text = "Histórico da conversa:\n" + history_text + "\n"

    prompt = f"""
    Com base na seguinte pergunta do usuário e no histórico da conversa, classifique a intenção principal do usuário em uma das seguintes categorias. Responda APENAS com o número da categoria.

    {history_text}
    Pergunta do Usuário: "{question}"

    Categorias de Intenção:
    1. Análise de dados simples (ex: "Qual o total de vendas?", "Número de clientes", "Valor das contas a pagar"). **Não pede diagnóstico, plano de ação ou insights aprofundados.**
    2. Análise de dados aprofundada/Estratégica (ex: "Me dê um plano de ação para aumentar as vendas", "Análise de lucratividade", "Por que as vendas caíram?", "Sugestões para o negócio"). **Exige diagnóstico, plano de ação e insights.**
    3. Conversa geral/saudação/ajuda não relacionada a análise de dados (ex: "Olá", "Tudo bem?", "Obrigado", "Me conte sobre você", "Quais suas funcionalidades?").
    Responda APENAS com o número da categoria (1, 2 ou 3).
    """
    return prompt