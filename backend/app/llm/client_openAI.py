# app/llm/client.py
""" 
Módulo unificado para gerar e avaliar ideias em mesas de bar usando **OpenAI** ou **Gemini**.
O _frontend_ deve enviar:
- **provider**: "openai" ou "gemini" (defaults para "openai").
- **model_name**: nome exato do modelo a ser usado.
- **api_key** (opcional): chave a ser usada; se `None`, a chave será lida das variáveis de ambiente.

Todas as assinaturas de função foram preservadas; apenas receberam parâmetros opcionais `provider` e/ou `model_name` para permitir que o frontend escolha o modelo.
"""

from __future__ import annotations

import os
import json
from typing import List, Dict, Literal, Any
from dotenv import load_dotenv

# Tipos -------------------------------------------------------------
Provider = Literal["openai", "gemini"]

# Carrega variáveis de ambiente ------------------------------------
load_dotenv()

# Chave configurada pelo LLMManager (vinda do frontend) ------------
_module_api_key: str | None = None

def configure_api_key(api_key: str | None) -> None:
    """Armazena a chave para ser usada como fallback nas funções públicas.

    Espelha a interface de client_gemini.configure_api_key, permitindo que o
    LLMManager configure a chave da OpenAI da mesma forma que faz com Gemini.
    """
    global _module_api_key
    _module_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not _module_api_key:
        print("AVISO: Chave da API da OpenAI não configurada.")

# ------------------------------------------------------------------
# Fábrica de cliente LLM -------------------------------------------
# ------------------------------------------------------------------
class LLMClient:
    """Cliente genérico que conversa com OpenAI ou Gemini, conforme *provider*."""

    def __init__(self, provider: Provider = "openai", api_key: str | None = None, model_name: str | None = None):
        self.provider: Provider = provider.lower()  # type: ignore

        if self.provider == "openai":
            # ---------- OpenAI ----------
            from openai import OpenAI  # import tardio para evitar dependência obrigatória
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY não configurada.")
            self.client = OpenAI(api_key=key)
            self.model_name = model_name or os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
        elif self.provider == "gemini":
            # ---------- Gemini ----------
            import google.generativeai as genai  # type: ignore
            key = api_key or os.getenv("GOOGLE_API_KEY")
            if not key:
                raise ValueError("GOOGLE_API_KEY não configurada.")
            genai.configure(api_key=key)
            self.client = genai  # guardamos o módulo para uso futuro
            self.model_name = model_name or os.getenv("GENAI_DEFAULT_MODEL", "gemini-1.5-flash")
        else:
            raise ValueError("Provider não suportado: use 'openai' ou 'gemini'.")

    # ---------------- Helpers ----------------
    def run(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 300) -> str:
        """Envia *prompt* e devolve o *content* da resposta."""
        if self.provider == "openai":
            response = self.client.chat.completions.create(  # type: ignore[attr-defined]
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        else:  # gemini
            model = self.client.GenerativeModel(model_name=self.model_name)  # type: ignore[attr-defined]
            response = model.generate_content(prompt)
            return response.text.strip()

# ------------------------------------------------------------------
# Funções públicas --------------------------------------------------
# ------------------------------------------------------------------

def generate_ai_proposal(
    ai_player: Any,
    topic: str,
    conversation_history: List[Any],
    balance: float,
    *,
    provider: Provider = "openai",
    model_name: str | None = None,
    api_key: str | None = None,
) -> Dict:
    """Gera uma proposta em JSON contendo *idea* e *bid*."""

    history_prompt = "\n".join([f"{msg.player_name}: {msg.message}" for msg in conversation_history])
    max_bid = min(balance * 0.3, 200)

    prompt = f"""
Você está em uma mesa de bar discutindo uma ideia.
Tópico: {topic}
Seu saldo atual é ${balance:.2f}.

**Sua Identidade Detalhada:**
- Nome: {ai_player.persona.name}
- Papel (Role): {ai_player.persona.role}
- Objetivo (Goal): {ai_player.persona.goal}
- Descrição: {ai_player.persona.description}
- Instruções de Comportamento: {ai_player.persona.instructions}

Histórico da Conversa:
{history_prompt}

Sua tarefa é criar uma continuação para a ideia e decidir quanto apostar nela, seguindo estritamente sua identidade detalhada.
Sua aposta deve ser um número entre 1 e {max_bid:.2f}.

Responda APENAS com um objeto JSON com duas chaves: "idea" (string) e "bid" (número).
""".strip()

    llm = LLMClient(provider, api_key or _module_api_key, model_name)

    try:
        raw = llm.run(prompt, temperature=0.7, max_tokens=300)
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        proposal_data = json.loads(cleaned)
        proposal_data["bid"] = min(float(proposal_data.get("bid", 1)), max_bid)
        return proposal_data
    except (Exception, json.JSONDecodeError) as e:
        print(f"Erro ao gerar proposta da IA ({getattr(ai_player, 'name', 'AI')}): {e}")
        return {"idea": "Fiquei pensativo e não consegui formular bem minha ideia.", "bid": 1.0}


def choose_best_idea(
    proposals: List[Any],
    topic: str,
    *,
    provider: Provider = "openai",
    model_name: str | None = None,
    api_key: str | None = None,
) -> int:
    """Retorna o *player_id* vencedor, escolhido pelo Garçom."""

    proposals_text = "\n".join(
        [f"ID {p.player_id} ({p.player_name}) propôs: '{p.idea_text}' (Aposta: ${p.bid_amount:.2f})" for p in proposals]
    )

    prompt = f"""
Você é o Garçom do bar, um observador neutro e sábio.
Os clientes estão discutindo o seguinte tópico: {topic}.
As seguintes propostas foram feitas nesta rodada:
{proposals_text}

Sua tarefa é escolher a proposta mais criativa, construtiva e interessante que melhor desenvolve o tópico.
Responda APENAS com o número do ID do jogador vencedor.
""".strip()

    llm = LLMClient(provider, api_key or _module_api_key, model_name)

    try:
        raw = llm.run(prompt, temperature=0.5, max_tokens=10)
        winner_id = int(raw)
        if winner_id in [p.player_id for p in proposals]:
            return winner_id
        return proposals[0].player_id
    except (Exception, ValueError) as e:
        print(f"Erro na escolha do Garçom: {e}")
        return proposals[0].player_id


def generate_personas_from_theme(
    theme: str,
    *,
    provider: Provider = "openai",
    model_name: str | None = None,
    api_key: str | None = None,
) -> Dict:
    """Gera 4 personas de IA com base em *theme*."""

    prompt = f"""
Sua tarefa é criar um time de 4 personas distintas e criativas para uma discussão em uma mesa de bar, com base no seguinte tema: "{theme}".

Para cada persona, gere os seguintes campos:
- name: Um nome curto e evocativo.
- description: Um resumo de uma frase da personalidade, para ser exibido no card inicial.
- role: O papel específico na discussão (ex: 'O Advogado do Diabo', 'O Otimista', 'O Realista').
- goal: O que esta persona quer alcançar ou provar na discussão.
- instructions: Regras específicas de como a persona deve se comportar, falar e argumentar.

Responda APENAS com um objeto JSON contendo uma única chave "team". O valor de "team" deve ser um array de 4 objetos, cada um com as chaves: "name", "description", "role", "goal", "instructions".
"""

    llm = LLMClient(provider, api_key or _module_api_key, model_name)

    try:
        raw = llm.run(prompt, temperature=0.5, max_tokens=500)
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except (Exception, json.JSONDecodeError) as e:
        print(f"Erro ao gerar personas: {e}")
        return {"team": []}


def summarize_conversation(
    topic: str,
    conversation_history: List[Any],
    *,
    provider: Provider = "openai",
    model_name: str | None = None,
    api_key: str | None = None,
) -> str:
    """Retorna um resumo final bem estruturado da conversa."""

    history_prompt = "\n".join(
        [f"- {msg.player_name} disse: {msg.message}" for msg in conversation_history if getattr(msg, "player_id", 1) != 0]
    )

    prompt = f"""
Você é o Dono do Bar, fechando o estabelecimento. Você ouviu toda a conversa sobre o tópico "{topic}".
Sua tarefa é sintetizar os pontos chave, as reviravoltas e as conclusões da discussão abaixo em um conceito final coeso e bem organizado.
Use títulos, listas e parágrafos para estruturar a ideia final de forma clara e profissional.

Histórico da Conversa:
{history_prompt}

Agora, organize tudo isso em um Resumo Final da Ideia:
"""

    llm = LLMClient(provider, api_key or _module_api_key, model_name)

    try:
        return llm.run(prompt, temperature=0.5, max_tokens=700)
    except Exception as e:
        print(f"Erro ao gerar resumo final: {e}")
        return "A conversa foi boa, mas a ideia final se perdeu no barulho do bar."


def structure_summary_for_lab(
    summary: str,
    *,
    provider: Provider = "openai",
    model_name: str | None = None,
    api_key: str | None = None,
) -> Dict:
    """Converte *summary* em proposta de projeto estruturada em JSON."""

    prompt = f"""
Você é um Analista de Negócios e Gerente de Produto sênior. Sua tarefa é converter o resumo de uma sessão de brainstorming em um documento de proposta de projeto claro e profissional.
Analise o resumo da ideia abaixo:
---
{summary}
---
Agora, estruture essa informação nos seguintes campos. Seja conciso, profissional e focado em negócios.
Responda APENAS com um objeto JSON com as seguintes chaves:
"title", "problem_statement", "core_solution", "key_features", "target_audience", "potential_impact", "next_steps"
"""

    llm = LLMClient(provider, api_key or _module_api_key, model_name)

    try:
        raw = llm.run(prompt, temperature=0.5, max_tokens=700)
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)

        # Garante que todas as chaves existam e sejam do tipo correto
        return {
            "title": data.get("title", ""),
            "problem_statement": data.get("problem_statement", ""),
            "core_solution": data.get("core_solution", ""),
            "key_features": data.get("key_features", []) or [],
            "target_audience": data.get("target_audience", ""),
            "potential_impact": data.get("potential_impact", ""),
            "next_steps": (
                "\n".join(data["next_steps"])
                if isinstance(data.get("next_steps"), list)
                else str(data.get("next_steps", ""))
            ),
        }

    except (Exception, json.JSONDecodeError) as e:
        print(f"Erro ao estruturar ideia para o Lab: {e}")
        return {
            "title": "",
            "problem_statement": "",
            "core_solution": "",
            "key_features": [],
            "target_audience": "",
            "potential_impact": "",
            "next_steps": "",
        }


