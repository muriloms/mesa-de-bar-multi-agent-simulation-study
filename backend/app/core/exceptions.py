"""Exceções customizadas para sinalizar problemas semânticos."""


class MesaDeBarError(Exception):
    """Base para todos os erros do projeto."""


class SessionNotFoundError(MesaDeBarError):
    pass


class ProtocolError(MesaDeBarError):
    pass


class PromptNotFoundError(MesaDeBarError):
    pass


class LLMError(MesaDeBarError):
    pass
