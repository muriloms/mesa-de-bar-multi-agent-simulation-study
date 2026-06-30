"""Backward-compatibility shim.

A partir da Fase 1, os modelos vivem em `app.domain.*`. Este módulo
continua existindo enquanto módulos antigos ainda importam daqui.
Será removido em uma fase futura.
"""
from domain.persona import LlmOverride, AIPersonaSetup
from domain.player import Player
from domain.session import GlobalLlmConfig, SetupPayload, GameState
from domain.round import ChatMessage, IdeaProposal
from domain.payloads import UserBidPayload, VotePayload, DelegateVotePayload
from domain.exports import LabIdea

__all__ = [
    "LlmOverride", "AIPersonaSetup", "Player",
    "GlobalLlmConfig", "SetupPayload", "GameState",
    "ChatMessage", "IdeaProposal",
    "UserBidPayload", "VotePayload", "DelegateVotePayload",
    "LabIdea",
]
