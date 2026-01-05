# Análise UX/UI - Niterói Raquetes

O projeto **Niterói Raquetes** (PickleMatch Advisor) possui uma base sólida com Next.js e shadcn/ui, focada em uma experiência mobile-first (PWA). Abaixo está a análise detalhada e as recomendações de melhoria.

## 1. Diagnóstico Atual

### Pontos Fortes
- **Arquitetura Limpa**: Uso de componentes modulares (`PaddleCard`, `FilterDrawer`).
- **Foco Mobile**: Layout pensado para uso em dispositivos móveis, facilitando a consulta rápida.
- **Performance**: Stack moderna que garante carregamento rápido.

### Oportunidades de Melhoria
- **Engajamento Emocional**: O design atual é funcional (cinza/branco), mas carece da energia vibrante dos esportes de raquete.
- **Diferencial Competitivo**: Falta uma ferramenta de "Advisor" real (ex: Quiz guiado) ao invés de apenas filtros passivos.
- **Densidade de Informação**: As cartas de produto poderiam mostrar atributos técnicos essenciais (Peso, Balanço, Controle vs Potência) sem poluir o visual.
- **Micro-interações**: Faltam feedbacks visuais mais "premium" ao interagir com elementos.

---

## 2. Proposta de Evolução UI/UX

### A. Identidade Visual "Sporty Premium"
- **Paleta de Cores**: Introduzir um "Action Color" vibrante (ex: Volt Green `#CEFF00` ou Electric Blue) para botões de CTA e destaques de performance.
- **Tipografia**: Usar fontes com pesos mais variados para criar hierarquia clara (ex: Inter ou Montserrat).

### B. Funcionalidade "Racket Finder" (O Advisor)
- Substituir a busca puramente por filtros por um fluxo de **Onboarding/Quiz**:
  1. *Qual seu nível?* (Iniciante, Intermediário, Pro)
  2. *Qual seu estilo de jogo?* (Potência, Controle, Híbrido)
  3. *Qual seu orçamento?*
- Resultado personalizado com "Match Percentage".

### C. Refinamento de Componentes
- **PaddleCard**: Adicionar um mini-gráfico de radar ou badges de atributos (ex: ⚡ Potência, 🛡️ Controle).
- **Empty States**: Ilustrações personalizadas quando nenhum produto for encontrado.
- **Loading Skeletons**: Melhorar a percepção de velocidade durante o fetch de dados.

---

## 3. Prompt para o Agente Especialista

Este prompt foi desenhado para que um agente especialista em Frontend/UI possa executar as mudanças de forma autônoma e com alta qualidade técnica.

> **Prompt:**
> "Atue como um Engenheiro Frontend Sênior e UI Designer. Sua tarefa é elevar o nível de UX/UI do projeto 'Niterói Raquetes'. 
> 
> **Objetivo:** Transformar o MVP atual em uma plataforma 'Premium Sporty Advisor'.
> 
> **Requisitos Técnicos:**
> 1.  **Refinamento do Design System**: Atualize o `globals.css` e o tema do Tailwind para incluir uma cor de destaque vibrante (ex: Lime Green ou Cyan) e garanta que o Dark Mode seja impecável.
> 2.  **Componente 'Racket Finder'**: Crie um novo componente de Quiz guiado (Step-by-step) usando Framer Motion para transições suaves. Este quiz deve coletar Nível de Jogo e Estilo de Jogo para filtrar os Paddles.
> 3.  **Upgrade do PaddleCard**: Melhore a ficha do produto para incluir atributos técnicos (Peso, Superfície) usando ícones ou uma barra de progresso discreta. Adicione um efeito de hover/active mais refinado.
> 4.  **Página de Detalhes**: Implemente uma visualização detalhada (pode ser via Drawer ou página interna) que mostre a descrição completa e uma comparação rápida com modelos similares.
> 5.  **Feedback Visual**: Integre `framer-motion` para animações de entrada na lista de produtos e feedback tátil em botões.
> 
> Mantenha a consistência com `shadcn/ui` e garanta que o código seja tipado corretamente em TypeScript."
