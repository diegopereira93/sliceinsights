#!/bin/bash

# Diretório base do template na máquina
TEMPLATE_DIR="$HOME/.gsd-omni-template"

echo "📦 Salvando a configuração do Omni-Agent..."
rm -rf "$TEMPLATE_DIR"
mkdir -p "$TEMPLATE_DIR"

# 1. Copia as super-configurações fundidas do OpenCode
cp -r .opencode "$TEMPLATE_DIR/"

# 2. Copia o manifesto central do GSD
mkdir -p "$TEMPLATE_DIR/.agent"
if [ -f ".agent/AGENT_CAPABILITIES.md" ]; then
    cp .agent/AGENT_CAPABILITIES.md "$TEMPLATE_DIR/.agent/"
fi

# 3. Copia a regra do Claude Code
mkdir -p "$TEMPLATE_DIR/.claude/rules"
if [ -f ".claude/rules/synergy-awareness.md" ]; then
    cp .claude/rules/synergy-awareness.md "$TEMPLATE_DIR/.claude/rules/"
fi

# 4. Cria o atalho mágico de instalação para novos projetos
cat << 'EOF' > "$TEMPLATE_DIR/apply-omni-setup.sh"
#!/bin/bash
# Esse script injeta o ECC integrado nas raízes de um projeto novo.

echo "🚀 Injetando setup Omni-Agent (OpenCode + ECC + GSD) neste diretório..."

# Copia pastas
cp -r ~/.gsd-omni-template/.opencode ./
mkdir -p .agent
cp ~/.gsd-omni-template/.agent/AGENT_CAPABILITIES.md .agent/ 2>/dev/null
mkdir -p .claude/rules
cp ~/.gsd-omni-template/.claude/rules/synergy-awareness.md .claude/rules/ 2>/dev/null

# Instala a dependência do OpenCode silenciosamente
echo "📦 Instalando dependências de background do OpenCode..."
cd .opencode && npm install ecc-universal --silent && cd ..

echo "✅ Setup perfeito concluído! Seu novo projeto já nasceu Autoconsciente."
EOF

chmod +x "$TEMPLATE_DIR/apply-omni-setup.sh"

echo ""
echo "✅ Exportação Concluída!"
echo "O seu ambiente 'padrão ouro' foi salvo em: $TEMPLATE_DIR"
echo ""
echo "👉 MANUAL DE USO MÁGICO PARA FUTUROS PROJETOS:"
echo "Sempre que iniciar um repositório novo do zero, basta entrar na pasta dele e rodar:"
echo "   ~/.gsd-omni-template/apply-omni-setup.sh"
echo ""
