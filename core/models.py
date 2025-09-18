# core/models.py
from django.db import models
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal

class Fornecedor(models.Model):
    nome_empresa = models.CharField(max_length=255)
    contato_nome = models.CharField(max_length=255, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['nome_empresa']

    def __str__(self):
        return self.nome_empresa

    def get_absolute_url(self):
        return reverse('fornecedor_editar', kwargs={'pk': self.pk}) # ALTERADO AQUI

class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.TextField(blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']

    def __str__(self):
        return self.nome
    
    def get_absolute_url(self):
        return reverse('cliente_editar', kwargs={'pk': self.pk}) # ALTERADO AQUI

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['nome']

    def __str__(self):
        return self.nome
    
    def get_absolute_url(self):
        return reverse('categoria_editar', kwargs={'pk': self.pk}) # ALTERADO AQUI

class Produto(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos_da_categoria')
    preco_compra = models.DecimalField(max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_estoque = models.IntegerField(default=0)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['nome']

    def __str__(self):
        return self.nome
    
    def get_absolute_url(self):
        return reverse('produto_editar', kwargs={'pk': self.pk}) # ALTERADO AQUI

class Venda(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONCLUIDA', 'Concluída'),
    ]
    FORMAS_PAGAMENTO = [
        ('AV', 'À Vista'),
        ('AP', 'A Prazo'),   
    ]
    CONDICOES_PRAZO =[
        ('7D', '7 Dias'),
        ('14D', '14 Dias'),
        ('28D', '28 Dias'),
    ]
    forma_pagamento = models.CharField(max_length=2, choices=FORMAS_PAGAMENTO, default='AV')
    condicao_prazo = models.CharField(max_length=3, choices=CONDICOES_PRAZO, blank=True, null=True)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='vendas_produto')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendas_cliente')
    quantidade = models.PositiveIntegerField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    data_venda = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDENTE')

    def __str__(self):
        return f"Venda de {self.quantidade}x {self.produto.nome} para {self.cliente.nome if self.cliente else 'N/A'} (R${self.valor_total})"

    def save(self, *args, **kwargs):
        if self.forma_pagamento == 'AV':
            self.condicao_prazo = None
        if self.produto and self.quantidade:
            self.valor_total = self.produto.preco_venda * self.quantidade
        else : 
            self.valor_total = Decimal('0.00') 
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"     
        ordering = ['-data_venda']
        
    def get_absolute_url(self):
        return reverse('venda_editar', kwargs={'pk': self.pk}) # ALTERADO AQUI

class ContaPagar(models.Model):
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='contas_pagar_fornecedor')
    descricao = models.CharField(max_length= 255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_lancamento = models.DateField(auto_now_add=True)
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('PAGO', 'Pago'),
        ('ATRASADO', 'Atrasado'),
        ('CANCELADO', 'Cancelado'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ABERTO')
    
    def __str__(self):
        return f"Pagar a {self.fornecedor.nome_empresa if self.fornecedor else 'N/A'} - R${self.valor} ({self.status})"

    class Meta:
        verbose_name = "Conta a Pagar"
        verbose_name_plural = "Contas a Pagar"
        ordering = ['data_vencimento']
    
    def get_absolute_url(self):
        return reverse('conta_pagar_editar', kwargs={'pk': self.pk}) # ALTERADO AQUI
        
class ContaReceber(models.Model):
    venda = models.OneToOneField(Venda, on_delete=models.CASCADE, related_name='conta_receber_venda', null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='contas_receber_cliente')
    descricao = models.CharField(max_length= 255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_lancamento = models.DateField(auto_now_add=True)
    data_vencimento = models.DateField()
    data_recebimento = models.DateField(null=True, blank=True)

    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('RECEBIDO', 'Recebido'),
        ('ATRASADO', 'Atrasado'),
        ('CANCELADO', 'Cancelado'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ABERTO')

    def __str__(self):
        return f"Receber de {self.cliente.nome if self.cliente else 'N/A'} - R${self.valor} ({self.status})"

    class Meta:
        verbose_name = "Conta a Receber"
        verbose_name_plural = "Contas a Receber"
        ordering = ['data_vencimento']
    
    def get_absolute_url(self):
        return reverse('conta_receber_editar', kwargs={'pk': self.pk}) # ALTERADO AQUI