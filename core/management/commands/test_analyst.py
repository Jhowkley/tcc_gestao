# core/management/commands/test_analyst.py
from django.core.management.base import BaseCommand
from django.conf import settings
import google.generativeai as genai
import sys

class Command(BaseCommand):
    help = 'Testa a conexão direta com a API do Google Gemini'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("--- INICIANDO TESTE DIRETO COM API GEMINI ---"))

        # 1. Chave da API
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key == "SUA_CHAVE_API_VEM_AQUI":
            self.stdout.write(self.style.ERROR("ERRO: Chave GEMINI_API_KEY não configurada em config/settings.py"))
            return
        self.stdout.write("Passo 1: Chave de API encontrada.")

        try:
            # 2. Configurar a API do Google
            self.stdout.write("Passo 2: Configurando a API do Google...")
            sys.stdout.flush()
            genai.configure(api_key=api_key)
            self.stdout.write("Passo 2: API configurada com sucesso.")

            # 3. Criar o modelo
            self.stdout.write("\nPasso 3: Criando o modelo generativo...")
            sys.stdout.flush()
            model = genai.GenerativeModel('gemini-2.0-flash')
            self.stdout.write("Passo 3: Modelo criado com sucesso.")

            # 4. Fazer uma pergunta simples
            prompt = "Olá! Responda com 'API funcionando!' para confirmar."
            self.stdout.write(f"\nPasso 4: Enviando prompt: '{prompt}'")
            self.stdout.write("(Aguardando resposta da API...)")
            sys.stdout.flush()

            response = model.generate_content(prompt)

            self.stdout.write(self.style.SUCCESS(f"\n\n>>>> RESPOSTA DA API: {response.text}\n"))

        except Exception as e:
            self.stdout.write(self.style.ERROR("\n--- OCORREU UM ERRO DURANTE A EXECUÇÃO ---"))
            self.stdout.write(self.style.ERROR(f"Tipo do Erro: {type(e).__name__}"))
            self.stdout.write(self.style.ERROR(f"Mensagem: {e}"))

        self.stdout.write(self.style.SUCCESS("\n--- TESTE CONCLUÍDO ---"))